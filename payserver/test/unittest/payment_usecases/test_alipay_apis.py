#      File: test_alipay_apis.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/13
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import unittest

from django.test import TestCase
from dynaconf import settings as dynasettings

from common.doclink.alipay_apis import AlipayApis
from common.payment.util import generate_serial_number


class TestAlipayApis(TestCase):
    test_app_id = dynasettings.ALIPAY_APP_ID
    test_private_key = dynasettings.ALIPAY_APP_PRIVATE_KEY
    test_public_key = dynasettings.ALIPAY_APP_PUBLIC_KEY
    alipay_public_key = dynasettings.ALIPAY_PUBLIC_KEY

    @unittest.skip('Code must be generated manually.')
    def test_exchange_access_token(self):
        code = '9578ea502648420384467fba85b1WX87'
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.test_public_key)
        result = alipay_apis.exchange_access_token(code)
        assert result['access_token']
        assert result['user_id']

    def test_sign_and_verify(self):
        params = dict(
            a=1,
            b=2,
            c=3,
            title='我是测试参数',
            sign_type='RSA2'
        )
        string_a = '&'.join([f'{k}={params[k]}' for k in sorted(params.keys()) if params[k]])

        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.test_public_key)
        alipay_apis.sign_request(params)

        pass_verify = alipay_apis.verify_sign_of_sync_msg(string_a, params['sign'])
        assert pass_verify

    def test_sign_request(self):
        params = dict(
            a=1,
            b=2,
            c=3,
            title='我是测试参数',
            sign_type='RSA2'
        )

        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        alipay_apis.sign_request(params)

        assert params[
                   'sign'] == 'sHDTZ6uNkRm3GOc6uofAh0G0HynakJFHimGPn20ogv9OkWfwqD6nkB9oab4h6T+A9APOvgPpHThVFrHy0W869E7PTKIqmraDGR5/ADKtukxuaHxD3vGL6zOUTMoYv4gKjwdZmvJsj1hAZi9Na2ssOKx/RxZyDmvzUAZR+BcxO3IhfUs0oQGPpaqpknOagwHoI+QJdSL7OZaWVLVmB6zvaqxKHGQ/LlSnH188N1yCK7C8NvKnx7OK+Sd2XgmJpG+IZ8lNzr8mKzHXUkNtYwxjJ+f1V5oFpS8Ov99vPilfXuTsgoVvwztH23xiUnl21CD2vrcKrhLJomKQsqld4YJvuA=='

    def test_verify_sign_of_sync_msg(self):
        signed_data = '{"code":"40004","msg":"Business Failed","sub_code":"ACQ.BUYER_NOT_EXIST","sub_msg":"买家不存在"}'
        sign = 'bs/vu7Z4VmoNVyhjEJ6Ta8m8/Q0qk/WSvhbcOnYN60ccEgkXNCGRe8jqvC8RGuvqbRLJwpOBwXk2sAkNW9N6Ko5M1QUhv4zex8jGM5ooM+V8LB6ULtZnJ8HiW+GMq6Ir7hDdjB0+9gceM5xvYRlSKSECgRGt2q/b4QFm4AKQgKkyqVnXHs7gBbWcvuGWWHZx7VYWhf63D+OBUwbel7ZYgmlaMHKBM5Ouko8TXfjdG22bnhldjasYP+s3ZS9v2BwJo/XV5Xqdmxzj35yzUq0kZT/tl88RKOswPsUanWnaqr7NVstsyOxNE1RLeHzoy/udFivJqwWBH7ku7z3IHRza4A=='

        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        verify_pass = alipay_apis.verify_sign_of_sync_msg(
            signed_data,
            sign
        )
        assert verify_pass

    def test_place_order(self):
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        result = alipay_apis.place_order(
            notify_url='https://mishitu.net/',
            order_title='测试订单',
            payment_serial_number=generate_serial_number(),
            total_amount=88,
            buyer_id='2088102176283877'
        )
        assert result['trade_no']

    def test_query_order(self):
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        payment_serial_number = generate_serial_number()
        place_order_result = alipay_apis.place_order(
            notify_url='https://mishitu.net/',
            order_title='测试订单',
            payment_serial_number=payment_serial_number,
            total_amount=88,
            buyer_id='2088102176283877'
        )
        query_order_result = alipay_apis.query_payment(payment_serial_number)

        assert query_order_result['trade_no']
        assert query_order_result['trade_no'] == place_order_result['trade_no']

    def test_cancel_order(self):
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        payment_serial_number = generate_serial_number()
        result = alipay_apis.place_order(
            notify_url='https://mishitu.net/',
            order_title='测试订单',
            payment_serial_number=payment_serial_number,
            total_amount=88,
            buyer_id='2088102176283877'
        )
        assert result['trade_no']

        result = alipay_apis.cancel(payment_serial_number)
        assert result['trade_no']

    @unittest.skip('payment_serial_number must be payed manually before refund.')
    def test_refund(self):
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        result = alipay_apis.refund(
            payment_serial_number='20180715104004245828075069106004',
            refund_serial_number=generate_serial_number(),
            refund_amount=88
        )
        assert result

    def test_pay_to_alipay(self):
        alipay_apis = AlipayApis(self.test_app_id, self.test_private_key, self.alipay_public_key)
        serial_number = generate_serial_number()
        result = alipay_apis.pay_to_alipay(serial_number, '2088102176283877', 100,
                                           '付款联盟提现', 'ALIPAY_USERID')
        assert result
