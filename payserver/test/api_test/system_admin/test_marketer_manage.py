# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: Tian Xu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.utils import timezone

from rest_framework import status

from common.models import Marketer
from config import SYSTEM_USER_STATUS, MARKETER_TYPES, MERCHANT_STATUS
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class MarketerManageTests(AdminSystemTestBase):
    now = str(timezone.now()).split(' ')[0]
    start_date = str(timezone.now() - timezone.timedelta(days=1)).split(' ')[0]
    future_date = str(timezone.now() + timezone.timedelta(days=1)).split(' ')[0]

    def test_get_marketer_list_not_logged_in(self):
        """ 未登陆管理员获取marketer列表 """

        url = "/api/admin/inviters/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

        url = "/api/admin/salesman/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_get_marketer_list_logged_in(self):
        """ 已登录管理员获取marketer列表 """

        temp_name_inviter = "我就是测试的inviter"
        temp_name_salesman = "我就是测试的salesman"

        self.set_login_status()

        self.factory.create_marketer(number=2,
                                     inviter_type=MARKETER_TYPES['MARKETER'],
                                     status=SYSTEM_USER_STATUS['DISABLED'])
        self.factory.create_marketer(number=2,
                                     inviter_type=MARKETER_TYPES['SALESMAN'],
                                     status=SYSTEM_USER_STATUS['DISABLED'])
        self.factory.create_marketer(name=temp_name_inviter,
                                     inviter_type=MARKETER_TYPES['MARKETER'],
                                     status=SYSTEM_USER_STATUS['USING'])
        self.factory.create_marketer(name=temp_name_salesman,
                                     inviter_type=MARKETER_TYPES['SALESMAN'],
                                     status=SYSTEM_USER_STATUS['USING'])

        self.assertEqual(Marketer.objects.all().count(), 6)

        url = "/api/admin/inviters/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 3)

        #  根据name搜索
        resp = self.client.get(url, {"name": temp_name_inviter})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], temp_name_inviter)

        #  根据status查询
        resp = self.client.get(url, {"status": 0})
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(url, {"status": 1})
        self.assertEqual(resp.json()["count"], 2)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        url = "/api/admin/salesman/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 3)

        #  根据name搜索
        resp = self.client.get(url, {"name": temp_name_salesman})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]["name"], temp_name_salesman)

        #  根据status查询
        resp = self.client.get(url, {"status": 0})
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(url, {"status": 1})
        self.assertEqual(resp.json()["count"], 2)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_marketer(self):
        """ 已登录管理员获取单个marketer信息 """

        temp_marketer_name = "我就是测试的inviter"
        self.set_login_status()
        self.factory.create_marketer(name=temp_marketer_name,
                                     inviter_type=MARKETER_TYPES['MARKETER'],
                                     status=SYSTEM_USER_STATUS['USING'])
        self.assertEqual(Marketer.objects.filter(name=temp_marketer_name,
                                                 inviter_type=MARKETER_TYPES['MARKETER']).count(), 1)
        pk = Marketer.objects.filter(name=temp_marketer_name)[0].id

        url = "/api/admin/inviters/{}/".format(pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), temp_marketer_name)

        temp_marketer_name = "我就是测试的salesman"
        self.set_login_status()
        self.factory.create_marketer(name=temp_marketer_name,
                                     inviter_type=MARKETER_TYPES['SALESMAN'],
                                     status=SYSTEM_USER_STATUS['USING'])
        self.assertEqual(Marketer.objects.filter(name=temp_marketer_name,
                                                 inviter_type=MARKETER_TYPES['SALESMAN']).count(), 1)
        pk = Marketer.objects.filter(name=temp_marketer_name)[0].id

        url = "/api/admin/salesman/{}/".format(pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), temp_marketer_name)

    def test_partial_update_marketer(self):
        """ 已登录管理员更新单个marketer信息 """

        temp_marketer_name = "我就是测试的inviter"
        self.set_login_status()

        self.factory.create_marketer(name=temp_marketer_name,
                                     inviter_type=MARKETER_TYPES['MARKETER'],
                                     status=SYSTEM_USER_STATUS['USING'])
        self.assertEqual(Marketer.objects.filter(inviter_type=MARKETER_TYPES['MARKETER']).count(), 1)
        pk = Marketer.objects.filter(name="我就是测试的inviter")[0].id

        url = "/api/admin/inviters/{}/".format(pk)
        resp = self.client.patch(url, data={"name": "我是测试更新后的inviter"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), "我是测试更新后的inviter")

        temp_marketer_name = "我就是测试的salesman"
        self.set_login_status()

        self.factory.create_marketer(name=temp_marketer_name,
                                     inviter_type=MARKETER_TYPES['SALESMAN'],
                                     status=SYSTEM_USER_STATUS['USING'])
        self.assertEqual(Marketer.objects.filter(inviter_type=MARKETER_TYPES['SALESMAN']).count(), 1)
        pk = Marketer.objects.filter(name="我就是测试的salesman")[0].id

        url = "/api/admin/salesman/{}/".format(pk)
        resp = self.client.patch(url, data={"name": "我就是测试更新后的salesman"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("name"), "我就是测试更新后的salesman")

    def test_areas(self):
        """ 测试区域信息 """
        self.set_login_status()

        url = "/api/admin/areas/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_marketer_invited_mcerchant(self):
        """ 测试 获取邀请人邀请的商户列表 """
        self.set_login_status()

        temp_salesman_name = "我是测试业务员"
        temp_merchant_name = "我是被邀请的店铺"

        salesman = self.factory.create_marketer(name=temp_salesman_name,
                                     inviter_type=MARKETER_TYPES['SALESMAN'],
                                     status=SYSTEM_USER_STATUS['USING'])
        merchant = self.factory.create_merchant(name=temp_merchant_name,
                                                status=MERCHANT_STATUS['USING'],
                                                inviter=salesman)
        ship = self.factory.create_merchant_marketer_ship(merchant=merchant,
                                                marketer=salesman,
                                                audit_datetime=self.start_date,
                                                audit_info=temp_salesman_name)

        url = "/api/admin/marketer_merchants/"
        # 测试邀请人邀请的店铺
        resp = self.client.get(url, {"uid": salesman.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]['name'], temp_merchant_name)

        # 测试业务员审核的店铺
        resp = self.client.get(url, {"uid": salesman.id, "audit": "true", "page": 1})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()['results'][0]['name'], temp_merchant_name)

        # 测试业务员在指定时间范围审核的店铺
        resp = self.client.get(url, {"uid": salesman.id, "audit": "true", "page": 1,
                                     "start_date": self.start_date, "end_date": self.future_date})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()['results'][0]['name'], temp_merchant_name)

        # 测试不在时间范围内
        resp = self.client.get(url, {"uid": salesman.id, "audit": "true", "page": 1,
                                     "start_date": self.now, "end_date": self.future_date})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 0)

    def test_merchant_marketer_ship(self):
        """ 测试商户/业务员审核 """
        self.set_login_status()

        temp_salesman_name = "我是测试审核的业务员"
        temp_merchant_name = "我是被审核的店铺"

        salesman = self.factory.create_marketer(name=temp_salesman_name,
                                                inviter_type=MARKETER_TYPES['SALESMAN'],
                                                status=SYSTEM_USER_STATUS['USING'])
        merchant = self.factory.create_merchant(name=temp_merchant_name,
                                                status=MERCHANT_STATUS['USING'],
                                                inviter=salesman)
        ship = self.factory.create_merchant_marketer_ship(merchant=merchant,
                                                          marketer=salesman,
                                                          audit_datetime=self.start_date,
                                                          audit_info=temp_salesman_name)

        url = "/api/admin/merchants_auditors_ship/"
        # 所有时间
        resp = self.client.get(url, {"uid": salesman.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()["results"][0]['merchant'], merchant.id)

        # 测试业务员在指定时间范围审核的店铺
        resp = self.client.get(url, {"uid": salesman.id, "page": 1,
                                     "start_date": self.start_date, "end_date": self.future_date})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 1)
        self.assertEqual(resp.json()['results'][0]['merchant'], merchant.id)

        # 测试不在时间范围内
        resp = self.client.get(url, {"uid": salesman.id, "start_date": self.now,
                                     "end_date": self.future_date})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["count"], 0)