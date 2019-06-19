# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from rest_framework import status

from common.models import SystemAdmin
from config import SYSTEM_USER_STATUS
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase
from test.unittest.fake_factory.fake_factory import fake


class SystemAdminTests(AdminSystemTestBase):
    def test_login_failed(self):
        """ 管理员登陆失败 """

        url = "/api/admin/system_admins/login"
        resp = self.client.post(url, format='json')
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_json.get("non_field_errors")[0], "用户名或密码错误")

        data = {"username": self.temp_admin_username, 'password': self.temp_admin_password+"aa"}
        resp = self.client.post(url, data=data, format='json')
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_json.get("non_field_errors")[0], "用户名或密码错误")

    def test_login_success(self):
        """ 管理员登陆成功 """

        self.set_login_status()

        url = '/api/admin/system_admins/me'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("username"), self.temp_admin_username)

    def test_login_out(self):
        """ 管理员退出登录 """

        self.set_login_status()
        url = '/api/admin/system_admins/me'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("username"), self.temp_admin_username)

        url = "/api/admin/system_admins/logout"
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        url = '/api/admin/system_admins/me'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_platform_admin_get_system_admin_list(self):
        """ 平台管理员获取后台用户列表 """

        self.set_login_status(is_super=True, permissions="PLATFORM_ADMIN")
        self.factory.create_system_admin(username="test1", status=SYSTEM_USER_STATUS['USING'], is_super=False)
        self.factory.create_system_admin(username="test2", status=SYSTEM_USER_STATUS['DISABLED'], is_super=False)

        url = "/api/admin/system_admins/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("count"), 2)

    def test_is_not_platform_admin_get_system_admin_list(self):
        """ 非平台管理员获取后台用户列表 """

        self.set_login_status(is_super=False)

        url = "/api/admin/system_admins/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_platform_admin_partial_update_system_admin(self):
        """ 平台管理员更新跟后台用户信息 """

        self.set_login_status(is_super=True, permissions="PLATFORM_ADMIN")

        update_test_admin = self.factory.create_system_admin(
                                            name="test_temp_name",
                                            is_super=False,
                                            status=SYSTEM_USER_STATUS['USING'])

        pk = update_test_admin.id
        update_name = "new_test_name"
        self.assertNotEqual(update_test_admin.name, update_name)

        url = "/api/admin/system_admins/{}/".format(pk)
        data = {"name": update_name}
        resp = self.client.patch(url, data=data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['name'], update_name)

    def test_platform_admin_create_system_admin(self):
        """ 平台管理员创建后台用户 """

        self.set_login_status(is_super=True, permissions="PLATFORM_ADMIN")

        username = fake.email()
        password = fake.password()
        is_super = False
        name = fake.name()
        admin_status = SYSTEM_USER_STATUS['USING']
        permissions = 'some permission'

        data = {
            "username": username,
            "password": password,
            "is_super": is_super,
            "name": name,
            "status": admin_status,
            "permissions": permissions
        }

        url = "/api/admin/system_admins/"
        resp = self.client.post(url, data=data, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['username'], username)
        self.assertEqual(resp.json()['name'], name)

        sys_admin = SystemAdmin.objects.get(pk=resp.json()['id'])
        self.assertEqual(sys_admin.username, username)
        self.assertEqual(sys_admin.name, name)

    def test_platform_admin_retrieve_system_admin(self):
        """ 平台管理员获取具体某个后台用户信息 """

        self.set_login_status(is_super=True, permissions="PLATFORM_ADMIN")
        test_admin = self.factory.create_system_admin(
            status=SYSTEM_USER_STATUS['USING'], is_super=False,)
        pk = test_admin.id

        url = "/api/admin/system_admins/{}/".format(pk)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['name'], test_admin.name)
        self.assertEqual(resp.json()['username'], test_admin.username)
