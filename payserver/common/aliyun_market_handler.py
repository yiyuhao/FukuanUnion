import requests
import base64
import hmac
from hashlib import sha256
import time
import uuid
from urllib.parse import urlparse

from marketer.config import ALIYUN_MARKET_API_CONFIG, ALIYUN_ACCOUNT_CONFIG
from marketer.exceptions import AliyunMarketApiParamsException

SYSTEM_HEADERS = (
    X_CA_SIGNATURE, X_CA_SIGNATURE_HEADERS, X_CA_TIMESTAMP, X_CA_NONCE, X_CA_KEY
) = (
    'X-Ca-Signature', 'X-Ca-Signature-Headers', 'X-Ca-Timestamp', 'X-Ca-Nonce', 'X-Ca-Key'
)

HTTP_HEADERS = (
    HTTP_HEADER_ACCEPT, HTTP_HEADER_CONTENT_MD5,
    HTTP_HEADER_CONTENT_TYPE, HTTP_HEADER_USER_AGENT, HTTP_HEADER_DATE
) = (
    'Accept', 'Content-MD5',
    'Content-Type', 'User-Agent', 'Date'
)

HTTP_PROTOCOL = (
    HTTP, HTTPS
) = (
    'http', 'https'
)

HTTP_METHOD = (
    GET, POST, PUT, DELETE, HEADER
) = (
    'GET', 'POST', 'PUT', 'DELETE', 'HEADER'
)

CONTENT_TYPE = (
    CONTENT_TYPE_FORM, CONTENT_TYPE_STREAM,
    CONTENT_TYPE_JSON, CONTENT_TYPE_XML, CONTENT_TYPE_TEXT
) = (
    'application/x-www-form-urlencoded', 'application/octet-stream',
    'application/json', 'application/xml', 'application/text'
)

BODY_TYPE = (
    FORM, STREAM
) = (
    'FORM', 'STREAM'
)


class AliyunMarketHandler:
    appcode = ALIYUN_ACCOUNT_CONFIG['appcode']
    app_key = ALIYUN_ACCOUNT_CONFIG['app_key']
    app_secret = ALIYUN_ACCOUNT_CONFIG['app_secret']
    _config = ALIYUN_MARKET_API_CONFIG

    def __init__(self, api_name):
        self.api_config = self._config[api_name]

    def _generate_string_to_sign(self):
        http_method = self.api_config['method'].upper()
        accept = self._headers['Accept']
        content_md5 = ''
        content_type = self._headers.get('Content-Type', '')
        date = self._headers['Date']
        headers_dict = {
            'X-Ca-Key': self.app_key,
            'X-Ca-Timestamp': self._headers[X_CA_TIMESTAMP],
            'X-Ca-Nonce': self._headers[X_CA_NONCE],

        }
        headers = ''.join(f'{k}:{headers_dict[k]}\n' for k in sorted(headers_dict.keys()))
        params_str = ''
        for k, v in self.params.items():
            params_str += f'&{k}={v}'
        url = f'{urlparse(self.api_config["url"]).path}?{params_str[1:]}'
        return f'{http_method}\n{accept}\n{content_md5}\n{content_type}\n{date}\n{headers}{url}'

    def _sign_string(self, str_to_sign):
        h = hmac.new(key=self.app_secret.encode('utf8'), msg=str_to_sign.encode('utf8'), digestmod=sha256)
        signature = base64.b64encode(h.digest()).strip()
        return signature

    def _build_header(self):
        self._headers = dict()
        self._headers['Accept'] = self.api_config.get('accept', '*/*')
        content_type = self.api_config.get('content_type', '')
        if content_type:
            self._headers['Content-Type'] = content_type
        self._headers[X_CA_KEY] = self.app_key
        self._headers[X_CA_NONCE] = str(uuid.uuid4())
        self._headers[X_CA_TIMESTAMP] = str(int(time.time() * 1000))
        self._headers[X_CA_SIGNATURE_HEADERS] = f'{X_CA_NONCE},{X_CA_KEY},{X_CA_TIMESTAMP}'
        self._headers['Date'] = time.strftime('%a, %d %b %Y %X GMT', time.gmtime())
        str_to_sign = self._generate_string_to_sign()
        signature = self._sign_string(str_to_sign)
        self._headers[X_CA_SIGNATURE] = signature

    def _verify_params(self, params_dict):
        keys = set(params_dict.keys())
        params_keys = set(self.api_config['params'])
        delta_keys = params_keys - keys
        if delta_keys:
            delta_keys_str = ','.join(delta_keys)
            raise AliyunMarketApiParamsException(f'`{delta_keys_str}`is needed request params')
        self.params = params_dict

    def go(self, params):
        self._verify_params(params)
        self._build_header()
        return getattr(requests, self.api_config['method'])(self.api_config['url'], self.params, headers=self._headers)

