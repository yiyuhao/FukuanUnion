#      File: test_wechat_pay_apis.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/13
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import unittest

from django.test import TestCase
from dynaconf import settings as dynasettings

from common.doclink.wechat_pay_apis import WechatPayApis
from common.payment.util import generate_serial_number


class TestWechatPayApis(TestCase):
    test_app_id = dynasettings.CLIENT_MINI_APP_ID
    test_mch_id = dynasettings.WECHAT_MERCHANT_ID
    test_mch_key = dynasettings.WECHAT_MERCHANT_API_KEY
    test_wechat_public_key = dynasettings.WECHAT_PUBLIC_KEY

    test_cert = dynasettings.WECHAT_MERCHANT_CERT
    test_cert_key = dynasettings.WECHAT_MERCHANT_CERT_KEY

    def test_sign_message(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        params = {'body': u'\u6d4b\u8bd5\u8ba2\u5355', 'openid': 'oUpF8uMuAJO_M2pxb1Q9zNjWeS6o',
                  'trade_type': 'JSAPI', u'nonce_str': u'c7FP0AzOVMcu3lgek3OUxSMx4GXGXoYN',
                  u'mch_id': '1313364101', 'out_trade_no': '20180716171957238778426463428649',
                  'total_fee': 22, u'appid': 'wx028a01935f0d0fc2',
                  u'notify_url': 'http://mishitu.net', 'spbill_create_ip': '180.44.23.5'}
        wechat_pay_apis.sign_message(params)
        assert params['sign'] == '345C48AAFB0C627E2F41E245204D95C8'

    def test_build_xml_message(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        params = {'body': u'\u6d4b\u8bd5\u8ba2\u5355', 'openid': 'oUpF8uMuAJO_M2pxb1Q9zNjWeS6o',
                  'trade_type': 'JSAPI', u'nonce_str': u'c7FP0AzOVMcu3lgek3OUxSMx4GXGXoYN',
                  u'mch_id': '1313364101', 'out_trade_no': '20180716171957238778426463428649',
                  'total_fee': 22, u'appid': 'wx028a01935f0d0fc2',
                  u'notify_url': 'http://mishitu.net', 'spbill_create_ip': '180.44.23.5'}
        xml_msg = wechat_pay_apis.build_xml_message(params)

        assert xml_msg == '<xml><body>测试订单</body><openid>oUpF8uMuAJO_M2pxb1Q9zNjWeS6o</openid>' \
                          '<trade_type>JSAPI</trade_type><nonce_str>c7FP0AzOVMcu3lgek3OUxSMx4GXG' \
                          'XoYN</nonce_str><mch_id>1313364101</mch_id><out_trade_no>201807161719' \
                          '57238778426463428649</out_trade_no><total_fee>22</total_fee><appid>wx' \
                          '028a01935f0d0fc2</appid><notify_url>http://mishitu.net</notify_url><s' \
                          'pbill_create_ip>180.44.23.5</spbill_create_ip></xml>'

    def test_parse_xml_message(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        xml_msg = '<xml><body>测试订单</body><openid>oUpF8uMuAJO_M2pxb1Q9zNjWeS6o</openid>' \
                  '<trade_type>JSAPI</trade_type><nonce_str>c7FP0AzOVMcu3lgek3OUxSMx4GXG' \
                  'XoYN</nonce_str><mch_id>1313364101</mch_id><out_trade_no>201807161719' \
                  '57238778426463428649</out_trade_no><total_fee>22</total_fee><appid>wx' \
                  '028a01935f0d0fc2</appid><notify_url>http://mishitu.net</notify_url><s' \
                  'pbill_create_ip>180.44.23.5</spbill_create_ip></xml>'
        params = wechat_pay_apis.parse_xml_message(xml_msg)

        expected_params = {'body': u'\u6d4b\u8bd5\u8ba2\u5355',
                           'openid': 'oUpF8uMuAJO_M2pxb1Q9zNjWeS6o',
                           'trade_type': 'JSAPI', u'nonce_str': u'c7FP0AzOVMcu3lgek3OUxSMx4GXGXoYN',
                           u'mch_id': '1313364101',
                           'out_trade_no': '20180716171957238778426463428649',
                           'total_fee': '22', u'appid': 'wx028a01935f0d0fc2',
                           u'notify_url': 'http://mishitu.net', 'spbill_create_ip': '180.44.23.5'}
        assert len(params) == len(expected_params)
        for k, v in params.items():
            assert v == expected_params[k]

    def test_place_order(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        result = wechat_pay_apis.place_order(
            order_title='测试订单',
            payment_serial_number=generate_serial_number(),
            total_fee=10000,
            notify_url='http://mishitu.net',
            spbill_create_ip='180.44.23.5',
            openid='oUkVN5ZFKfLOkAFwkk4oGYVc0rfg'
        )
        assert result['prepay_id']

    def test_cancel_order(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        payment_serial_number = generate_serial_number()
        result = wechat_pay_apis.place_order(
            order_title='测试订单',
            payment_serial_number=payment_serial_number,
            total_fee=10000,
            notify_url='http://mishitu.net',
            spbill_create_ip='180.44.23.5',
            openid='oUkVN5ZFKfLOkAFwkk4oGYVc0rfg'
        )
        assert result['prepay_id']

        result = wechat_pay_apis.cancel(payment_serial_number)
        assert result['result_code'] == 'SUCCESS'

    def test_generate_client_payment_params(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key)
        client_payment_params = wechat_pay_apis.generate_client_payment_params(
            'wx1716211050672758efcbdf2e1219937119')
        assert client_payment_params

    @unittest.skip('The payment_serial_number must be paid manually before refund.')
    def test_refund(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        result = wechat_pay_apis.refund(
            payment_serial_number='20180918103408054636745554716518',
            refund_serial_number=generate_serial_number(),
            total_fee=2,
            refund_fee=2,
            notify_url='http://payserver.alpha.muchbo.com/api/user/payment_callback/wechat_refund_callback',
        )

        assert result['refund_id']

    @unittest.skip('wechat_public_key never change.')
    def test_get_wechat_public_key(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        result = wechat_pay_apis.get_wechat_public_key()
        assert result['pub_key']

    def test_query_refund(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        result = wechat_pay_apis.refund_query('20180907161025889841392482212063')
        assert result['refund_status_0'] == 'SUCCESS'

    @unittest.skip('need enough balance')
    def test_pay_to_bank(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        result = wechat_pay_apis.pay_to_bank(
            partner_trade_no=generate_serial_number(),
            bank_no='6214930121469976',
            true_name='谢汪益',
            bank_code=1001,
            amount=1,
            desc='测试付款'
        )

        assert result

    @unittest.skip('need enough balance')
    def test_pay_to_wechat(self):
        wechat_pay_apis = WechatPayApis('wx3f75ca357f606548', self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        result = wechat_pay_apis.pay_to_wechat(
            partner_trade_no=generate_serial_number(),
            openid='ocBww1n_-2iKlWyp4lXBS73iWwAc',
            amount=1000,
            desc='测试付款',
            spbill_create_ip='180.2.4.23'
        )

        assert result

    def test_decrypt_data(self):
        wechat_pay_apis = WechatPayApis(self.test_app_id, self.test_mch_id, self.test_mch_key,
                                        self.test_wechat_public_key,
                                        self.test_cert,
                                        self.test_cert_key
                                        )
        raw_data = wechat_pay_apis.decrypt_data(
            "Zi4PIwGuIhEQUh/z7zKEH0TWHqiwWW4Tfys/5o4YzEsqYVe1NndQk0HlDbfLkOTxdnJ56bxJSyuP9XXgBezmRdqwi/p6maI9P3+ZAyYxVBkR85aYwWXWvVWNQj2iIBmsGuOgi5pD3ZeqmCM3c4AwK9ifHJ48l8H4sj8elGQ1c2kPPgMS4zhn9W8cE6O1i8ai1h82NEr0E/aKebt62xb3FqBrVrioImH8BdFuSmUua0toatrpVWC+/kMAWWIBl2wyJC+bdsFFQVP+/0+PCuDFVSKUidkxzNE8e8g8AD2HRowcbILj5nDp4LvZ2WTx25mTezJoe6DDgRXinjgtSDB194NueanNMHEzE6E5TEiBCPfjI0Ag/59S0Ww7FSoJsaYhQAGYvyhIFpRWvycy7u0Ocr6CWF/gwAvPlLzQZ9wUoKlXVX74MaI1g5Pk0JjFQH9rcr8lh/mT5hUaeNxK5brQ39LZqeWlV+ygGOqEilNgDC41LKWckrnqSHVPqtbQcxQkEBr0SZ1mIhv1YrzisGPdtQge9co5zwYnmwIaQBBiqaLR4mN50dvv/6C0WRnfIygHJHvotzrIdtVJamRzpujvnXmnNTRaVpNwUxQj+dYPYMRcgdIqPv2g0r0CSreycLFwjK57q0NDDDmiRFjoCXThc7mYPCIHem6+7Tf0yNm95tZjjNYF2N9zWOwP2KC9ZzNhSMYHMwYVfPCofQkSed7PcJyMRDcNwRMsfNMAPT/yKifKuA4+h+UNgd4jRVQqUQpSyyxl2VfQb57GYUVkHY3T9GxwBgokeTlr89V/2Q/tov3aHMj1pFPMU8MsUQDprJgaJQqgQm8cr9irccxRCav7CEn3wS1xWfgXXhdLmrFpXztt7WlZ80xTBos3jb0HO+O5edNjaEkO9szLV0DL937MDBOlWvEj3WWc55ifRbRaBLYSQktyDGCUQtp5n0UoiJbiAZxh7UK/IRPQqKzwSD4jfufGkUYPBY6vjVPL5a3Y6K5+q/Hhu2YfK02OQ9RF0CJRkSPJd5X0jihUdDDR33TkDvccIhwf2l24dqdiSvwJLW5AIAmNWTYFroL+Zgs93bm2HcPoFsYOHnDY9+CZKrmZEw==")

        assert raw_data == """<root>
<out_refund_no><![CDATA[20180918112315706748424458673805]]></out_refund_no>
<out_trade_no><![CDATA[20180918103408054636745554716518]]></out_trade_no>
<refund_account><![CDATA[REFUND_SOURCE_RECHARGE_FUNDS]]></refund_account>
<refund_fee><![CDATA[2]]></refund_fee>
<refund_id><![CDATA[50000708282018091806360684199]]></refund_id>
<refund_recv_accout><![CDATA[支付用户零钱]]></refund_recv_accout>
<refund_request_source><![CDATA[API]]></refund_request_source>
<refund_status><![CDATA[SUCCESS]]></refund_status>
<settlement_refund_fee><![CDATA[2]]></settlement_refund_fee>
<settlement_total_fee><![CDATA[2]]></settlement_total_fee>
<success_time><![CDATA[2018-09-18 11:24:19]]></success_time>
<total_fee><![CDATA[2]]></total_fee>
<transaction_id><![CDATA[4200000180201809180521596767]]></transaction_id>
</root>"""
