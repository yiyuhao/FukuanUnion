#      File: alipay_apis.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/10
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import base64
import json
import logging
import re
from urllib.parse import urlencode

import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from django.utils import timezone
from dynaconf import settings as dynasettings

from common.doclink.exceptions import ApiRequestError, SignError, ApiReturnedError

logger = logging.getLogger(__name__)


class AlipayApis(object):
    SUCCESS_CODE = '10000'
    signed_data_pattern = r'response":(.+),"sign":"'

    @property
    def API_GATEWAY(self):
        if dynasettings.IS_DEBUG:
            return 'https://openapi.alipaydev.com/gateway.do'
        else:
            return 'https://openapi.alipay.com/gateway.do'

    def __init__(self, app_id, private_key, alipay_public_key):
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key

    def sign_request(self, params):
        private_key = "-----BEGIN RSA PRIVATE KEY-----\r\n" \
                      "{}\r\n" \
                      "-----END RSA PRIVATE KEY-----".format(self.private_key)

        string_a = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()) if params[k])
        sign_content = string_a.encode('utf8')
        key = RSA.importKey(private_key)
        message_hash = SHA256.new(sign_content)
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(message_hash)
        sign = base64.b64encode(signature)
        sign = str(sign, 'utf8')

        params['sign'] = sign
        return sign

    def verify_sign_of_async_msg(self, params, sign):
        string_a = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()) if params[k])
        return self.verify_sign_of_sync_msg(string_a, sign)

    def verify_sign_of_sync_msg(self, signed_data, sign):
        public_key = "-----BEGIN PUBLIC KEY-----\r\n" \
                     "{}\r\n" \
                     "-----END PUBLIC KEY-----".format(self.alipay_public_key)
        sign = base64.b64decode(sign)

        key = RSA.importKey(public_key)
        h = SHA256.new(signed_data.encode('utf-8'))
        verifier = PKCS1_v1_5.new(key)
        if verifier.verify(h, sign):
            return True
        return False

    def build_request(self, method, biz_content=None, notify_url=None):
        qs_params = dict()  # query string paramters
        qs_params['app_id'] = self.app_id
        qs_params['method'] = method
        qs_params['charset'] = 'utf-8'
        qs_params['timestamp'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        qs_params['version'] = '1.0'
        qs_params['sign_type'] = 'RSA2'
        if biz_content:
            qs_params['biz_content'] = json.dumps(biz_content)
        if notify_url:
            qs_params['notify_url'] = notify_url
        return qs_params

    def execute_request(self, api_name, biz_content=None,
                        notify_url=None, response_name=None, verify_sign=True):

        qs_params = self.build_request(api_name, biz_content, notify_url)
        self.sign_request(qs_params)

        try:
            logger.debug(f'{api_name} request: {self.API_GATEWAY}, {qs_params}')
            resp = requests.post(self.API_GATEWAY + '?' + urlencode(qs_params))
            logger.debug(f'{api_name} response: {resp.status_code}, {resp.text}')
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.debug(f'{api_name} requests.RequestException: {requests.RequestException}')
            raise ApiRequestError(e)

        resp_json = resp.json()

        if verify_sign:
            sign = resp_json['sign']
            signed_data = re.search(self.signed_data_pattern, str(resp.content, 'utf-8'))

            if not signed_data:
                logger.debug(f'{api_name} SignError')
                raise SignError()
            if not self.verify_sign_of_sync_msg(signed_data.group(1), sign):
                logger.debug(f'{api_name} SignError')
                raise SignError()

        if not response_name:
            response_name = api_name.replace('.', '_') + '_response'

        if response_name not in resp_json:
            logger.debug(response_name + ' not found')
            raise ApiReturnedError(response_name + ' not found', resp_json)

        response = resp_json[response_name]

        if response['code'] != self.SUCCESS_CODE:
            logger.debug(response_name + ' has an error code.')
            raise ApiReturnedError(response['code'],
                                   response)

        return response

    def exchange_access_token(self, code):
        biz_content = dict(
            code=code,
            grant_type='authorization_code'
        )
        qs_params = self.build_request('alipay.system.oauth.token')
        qs_params.update(**biz_content)
        self.sign_request(qs_params)

        try:
            resp = requests.post(self.API_GATEWAY + '?' + urlencode(qs_params))
            resp.raise_for_status()
            logger.debug(f'alipay.system.oauth.token response: {resp.text}')
        except requests.RequestException as e:
            raise ApiRequestError(e)

        resp_json = resp.json()

        alipay_system_oauth_token_response = resp_json['alipay_system_oauth_token_response']
        if not alipay_system_oauth_token_response['access_token']:
            raise ApiReturnedError(0, alipay_system_oauth_token_response)

        return alipay_system_oauth_token_response

    def place_order(self, notify_url, order_title, payment_serial_number, total_amount, buyer_id):
        """
        Create a payment order.
        see: https://docs.open.alipay.com/api_1/alipay.trade.create/
        :param notify_url:
        :param order_title:
        :param payment_serial_number:
        :param total_amount:
        :param buyer_id:
        :return:
        """

        biz_content = dict(
            subject=order_title,
            out_trade_no=payment_serial_number,
            timeout_express='30m',
            total_amount=total_amount / 100.0,
            buyer_id=buyer_id
        )

        return self.execute_request('alipay.trade.create', biz_content, notify_url)

    def query_payment(self, payment_serial_number):
        biz_content = dict(
            out_trade_no=payment_serial_number
        )
        return self.execute_request('alipay.trade.query', biz_content)

    def refund(self, payment_serial_number, refund_serial_number, refund_amount):
        biz_content = dict(
            out_trade_no=payment_serial_number,
            refund_amount=refund_amount / 100.0,
            out_request_no=refund_serial_number
        )

        return self.execute_request('alipay.trade.refund', biz_content)

    def cancel(self, payment_serial_number):
        biz_content = dict(
            out_trade_no=payment_serial_number
        )

        return self.execute_request('alipay.trade.cancel', biz_content)

    def pay_to_alipay(self, serial_number, receiver_alipay_id, amount, desc, payee_type,
                      payee_real_name=None):
        biz_content = dict(
            out_biz_no=serial_number,
            payee_type=payee_type,
            payee_account=receiver_alipay_id,
            amount=amount / 100.0,
            payer_show_name='付款联盟',
            remark=desc,
        )
        if payee_real_name:
            biz_content.update(payee_real_name=payee_real_name)

        return self.execute_request('alipay.fund.trans.toaccount.transfer', biz_content)
