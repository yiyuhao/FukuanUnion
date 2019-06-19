# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import status
from rest_framework.test import APITestCase

from config import SYSTEM_USER_STATUS, MERCHANT_STATUS
from common.password_backend import make_password
from common.models import Merchant, SystemAdmin
from test.unittest.fake_factory.fake_factory import PayunionFactory


class AdminSystemTestBase(APITestCase):
    temp_admin_username = "zhangsansa"
    temp_admin_password = "sdfdsfdfsfzlkdjfkdfik"
    password = make_password(temp_admin_password)
    factory = PayunionFactory()

    def set_test_admin(self, is_super=False, permissions=None):
        test_admin = self.factory.create_system_admin(username=self.temp_admin_username,
                                                      password=self.password,
                                                      status=SYSTEM_USER_STATUS['USING'],
                                                      permissions=permissions,
                                                      is_super=is_super
                                                      )
        sys_admin = SystemAdmin.objects.get(pk=test_admin.id)
        self.assertEqual(sys_admin.username, test_admin.username)
        self.assertEqual(sys_admin.name, test_admin.name)

    def set_login_status(self, is_super=False, permissions=None):
        self.set_test_admin(is_super=is_super, permissions=permissions)

        url = "/api/admin/system_admins/login"
        data = {"username": self.temp_admin_username, "password": self.temp_admin_password}
        resp = self.client.post(url, data=data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("username"), self.temp_admin_username)
