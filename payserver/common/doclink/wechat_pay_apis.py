#      File: wechat_pay_apis.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
import xml.etree.ElementTree as ET
from base64 import b64encode

import requests
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from common.aes import AesCrypter
from common.doclink.exceptions import ApiRequestError, ApiReturnedError, SignError

logger = logging.getLogger(__name__)


class WechatPayApis(object):
    API_BASE = 'https://api.mch.weixin.qq.com'
    GET_WECHAT_PUB_KEY = 'https://fraud.mch.weixin.qq.com/risk/getpublickey'

    def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None, cert_key=None):
        self.app_id = app_id
        self.mch_id = mch_id
        self.mch_key = mch_key
        self.wechat_public_key = wechat_public_key
        self.cert = cert
        self.cert_key = cert_key

    @property
    def PATH_SET(self):
        return dict(
            UNIFIED_ORDER='/pay/unifiedorder',
            REFUND='/secapi/pay/refund',
            REFUND_QUERY='/pay/refundquery',
            CANCEL='/pay/closeorder',
            PAY_BANK='/mmpaysptrans/pay_bank',
            PAY_WECHAT='/mmpaymkttransfers/promotion/transfers'
        )

    def rsa_encrypt(self, message):
        # wechat_public_key = b64decode(self.wechat_public_key)
        # wechat_public_key = RSA.importKey(wechat_public_key)
        wechat_public_key = "-----BEGIN PUBLIC KEY-----\r\n" \
                            "{}\r\n" \
                            "-----END PUBLIC KEY-----".format(self.wechat_public_key)
        wechat_public_key = RSA.importKey(wechat_public_key)

        cipher = PKCS1_OAEP.new(wechat_public_key)
        cipher_text = cipher.encrypt(message.encode(encoding='utf8'))
        return b64encode(cipher_text).decode()

    def sign_message(self, params, sign_type='MD5'):
        if sign_type not in ('MD5', 'HMAC-SHA256'):
            raise SignError(f'Unsupported sign_type:{sign_type}')

        string_a = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()) if params[k])
        string_sign_temp = string_a + f'&key={self.mch_key}'

        if sign_type == 'HMAC-SHA256':
            byte_key = base64.b64decode(self.mch_key)
            byte_string_sign_temp = string_sign_temp.encode('utf-8')
            sign = hmac.new(byte_key, byte_string_sign_temp, hashlib.sha256).hexdigest().upper()
        else:
            md5_hash = hashlib.md5()
            md5_hash.update(string_sign_temp.encode(encoding='utf-8'))
            sign = md5_hash.hexdigest().upper()

        params['sign'] = sign
        if sign_type != 'MD5':
            params['sign_type'] = sign_type
        return params

    @staticmethod
    def build_xml_message(params):
        root = ET.Element('xml')

        for p in params.keys():
            ET.SubElement(root, p).text = str(params[p])

        return ET.tostring(root, encoding='utf-8', method='xml').decode(encoding='utf-8')

    @staticmethod
    def parse_xml_message(xml_message):
        response_root = ET.fromstring(xml_message)
        result = dict()
        for child in response_root:
            result[child.tag] = child.text
        return result

    def decrypt_data(self, encrypt_data):
        raw_data = AesCrypter(self.mch_key).decrypt(encrypt_data)
        return raw_data

    def encrypt_data(self, raw_data):
        encrypt_data = AesCrypter(self.mch_key).encrypt(raw_data)
        return encrypt_data

    def generate_client_payment_params(self, prepay_id):
        params = dict(
            appId=self.app_id,
            timeStamp=str(int(time.time())),
            nonceStr=uuid.uuid4().hex,
            package=f'prepay_id={prepay_id}',
            signType='MD5'
        )
        self.sign_message(params)
        sign = params.pop('sign')
        params['paySign'] = sign
        return params

    def execute_request(self, url, params):
        self.sign_message(params)
        body = self.build_xml_message(params)

        headers = {
            'Content-Type': 'text/xml',
        }

        logger.info('Wechat Request Url:{}'.format(url))
        logger.info('Wechat Request Body:{}'.format(body))
        try:
            if self.cert:
                resp = requests.post(url, data=body.encode('utf-8'), headers=headers,
                                     cert=(self.cert, self.cert_key))
            else:
                resp = requests.post(url, data=body.encode('utf-8'), headers=headers)

            logger.debug(f'Wechat withdraw, wechat response: {resp.text}')

            resp.raise_for_status()
        except requests.RequestException as e:
            raise ApiRequestError(e)

        try:
            result = self.parse_xml_message(resp.content)
        except ET.ParseError as e:
            raise ApiRequestError(e)

        if result['return_code'] != 'SUCCESS' or result['result_code'] != 'SUCCESS':
            logger.error(f'Wechat returned error: {json.dumps(result)}')
            raise ApiReturnedError(result['return_code'], result)

        return result

    def get_wechat_public_key(self):
        url = self.GET_WECHAT_PUB_KEY

        params = dict()
        params['mch_id'] = self.mch_id
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def place_order(self, order_title, payment_serial_number,
                    total_fee, spbill_create_ip, notify_url, openid):
        """
        Call the wechat unifiedorder api.
        see: https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1
        :param order_title:
        :param payment_serial_number:
        :param total_fee:
        :param spbill_create_ip:
        :param notify_url:
        :param openid:
        :return:
        """
        url = self.API_BASE + self.PATH_SET['UNIFIED_ORDER']

        params = dict()
        params['appid'] = self.app_id
        params['mch_id'] = self.mch_id
        params['body'] = order_title
        params['out_trade_no'] = payment_serial_number
        params['total_fee'] = total_fee
        params['spbill_create_ip'] = spbill_create_ip
        params['notify_url'] = notify_url
        params['trade_type'] = 'JSAPI'
        params['openid'] = openid
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def refund(self, payment_serial_number, refund_serial_number, total_fee, refund_fee,
               notify_url):
        """
        Call the wechat refund api.
        :param payment_serial_number:
        :param refund_serial_number:
        :param total_fee:
        :param refund_fee:
        :param notify_url:
        :return: Api result
        :raise ApiRequestError, ApiReturnedError
        """
        url = self.API_BASE + self.PATH_SET['REFUND']

        params = dict()
        params['appid'] = self.app_id
        params['mch_id'] = self.mch_id
        params['out_trade_no'] = payment_serial_number
        params['out_refund_no'] = refund_serial_number
        params['total_fee'] = total_fee
        params['refund_fee'] = refund_fee
        params['notify_url'] = notify_url
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def refund_query(self, refund_serial_number):
        """
        Query
        :param refund_serial_number:
        :return:
        """
        url = self.API_BASE + self.PATH_SET['REFUND_QUERY']
        params = dict()
        params['appid'] = self.app_id
        params['mch_id'] = self.mch_id
        params['out_refund_no'] = refund_serial_number
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def cancel(self, payment_serial_number):
        """
        Cancel the order.
        :param payment_serial_number:
        :return:
        """
        url = self.API_BASE + self.PATH_SET['CANCEL']

        params = dict()
        params['appid'] = self.app_id
        params['mch_id'] = self.mch_id
        params['out_trade_no'] = payment_serial_number
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def pay_to_bank(self, partner_trade_no, bank_no, true_name, bank_code, amount, desc):
        """
        Call the payment to card API.
        see: https://pay.weixin.qq.com/wiki/doc/api/tools/mch_pay.php?chapter=24_2
        :param partner_trade_no:
        :param bank_no:
        :param true_name:
        :param bank_code:
        :param amount:
        :param desc:
        :return:
        """
        url = self.API_BASE + self.PATH_SET['PAY_BANK']

        params = dict()
        params['mch_id'] = self.mch_id
        params['partner_trade_no'] = partner_trade_no
        params['enc_bank_no'] = self.rsa_encrypt(bank_no)
        params['enc_true_name'] = self.rsa_encrypt(true_name)
        params['bank_code'] = bank_code
        params['amount'] = amount
        params['desc'] = desc
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)

    def pay_to_wechat(self, partner_trade_no, openid, amount, desc, spbill_create_ip,
                      app_id=None):
        url = self.API_BASE + self.PATH_SET['PAY_WECHAT']

        params = dict()
        params['mch_appid'] = app_id or self.app_id
        params['mchid'] = self.mch_id
        params['partner_trade_no'] = partner_trade_no
        params['openid'] = openid
        params['check_name'] = 'NO_CHECK'
        params['amount'] = amount
        params['desc'] = desc
        params['spbill_create_ip'] = spbill_create_ip
        params['nonce_str'] = uuid.uuid4().hex

        return self.execute_request(url, params)
