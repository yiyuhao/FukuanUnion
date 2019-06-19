#      File: manually_test_login.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/22
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.error_handler import MerchantError
from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES
from test.test_config import ManuallyTestMinaConfig as Config
from test.unittest.fake_factory import PayunionFactory


class TestAuth(APITestCase):
    def setUp(self):
        factory = PayunionFactory()
        self.merchant_admin = factory.create_merchant_admin(
            wechat_openid=Config.my_account_openid,
            status=SYSTEM_USER_STATUS['USING'],
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

    def test_login_and_auth_success(self):
        self.merchant_admin.work_merchant.name = '就是这个公司'
        self.merchant_admin.work_merchant.save()

        # login
        url = reverse('merchant-admin-login')
        data = {'code': Config.wechat_login_code}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        resp_json = response.json()
        token = resp_json['token']
        admin_type = resp_json['merchant_admin_type']
        merchant_status = resp_json['merchant_status']
        self.assertIsInstance(token, str)
        self.assertEqual(admin_type, MERCHANT_ADMIN_TYPES['CASHIER'])
        self.assertEqual(merchant_status, self.merchant_admin.work_merchant.status)

        # auth by token
        url = reverse('merchant-auth')
        response = self.client.get(url, Token=token)
        merchant_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(merchant_json['name'], '就是这个公司')

    def test_login_code_error(self):
        url = reverse('merchant-admin-login')
        data = {'code': 'wrong login code'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        resp_json = response.json()
        self.assertEqual(resp_json['non_field_errors'], [MerchantError.get_openid_error['detail']])

        self.assertEqual(resp_json['error_code'], MerchantError.get_openid_error['code'])

    def test_merchant_admin_not_exist_error(self):
        self.merchant_admin.wechat_openid = 'wrong open id'
        self.merchant_admin.save()

        url = reverse('merchant-admin-login')
        data = {'code': Config.wechat_login_code}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        resp_json = response.json()
        self.assertEqual(resp_json['non_field_errors'], [MerchantError.user_is_not_a_merchant_admin['detail']])

        self.assertEqual(resp_json['error_code'], MerchantError.user_is_not_a_merchant_admin['code'])
