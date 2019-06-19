# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from rest_framework import status

from common.models import Merchant
from config import MERCHANT_STATUS
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class MerchantManageTests(AdminSystemTestBase):

    def test_get_merchant_list_not_logged_in(self):
        """ 未登陆管理员获取商户 """

        url = "/api/admin/merchants/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_get_merchant_list_logged_in(self):
        """ 已登录管理员获取商户列表 """

        temp_name = "一个商户的名字很独特"
        self.set_login_status()

        self.factory.create_merchant(number=2,
                                     status=MERCHANT_STATUS['USING'])
        self.factory.create_merchant(number=2,
                                     status=MERCHANT_STATUS['REVIEWING'])
        self.factory.create_merchant(number=2,
                                     status=MERCHANT_STATUS['REJECTED'])
        self.factory.create_merchant(number=2,
                                     status=MERCHANT_STATUS['DISABLED'])
        self.factory.create_merchant(name=temp_name,
                                     status=MERCHANT_STATUS['USING'])

        self.assertEqual(len(Merchant.objects.all()), 9)

        url = "/api/admin/merchants/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 9)

        #  根据id或name搜索
        resp = self.client.get(url, {"id_name": temp_name})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], temp_name)

    def test_retrieve_merchant(self):
        """ 已登录管理员获取单个商户信息 """

        temp_merchant_name = "一个商户的名字很独特"
        self.set_login_status()
        self.factory.create_merchant(name=temp_merchant_name,
                                     status=MERCHANT_STATUS['USING'])
        self.assertEqual(len(Merchant.objects.filter(name=temp_merchant_name)), 1)
        pk = Merchant.objects.filter(name=temp_merchant_name)[0].id

        url = "/api/admin/merchants/{}/".format(pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), temp_merchant_name)

    def test_partial_update_merchant(self):
        """ 已登录管理员跟新单个商户信息 """

        temp_merchant_name = "一个商户的名字很独特"
        self.set_login_status()

        self.factory.create_merchant(name=temp_merchant_name,
                                     status=MERCHANT_STATUS['USING'])
        self.assertEqual(len(Merchant.objects.all()), 1)
        pk = Merchant.objects.filter(name="一个商户的名字很独特")[0].id

        url = "/api/admin/merchants/{}/".format(pk)
        resp = self.client.patch(url, data={"name": "一个商户的更新后的名字很独特"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), "一个商户的更新后的名字很独特")
