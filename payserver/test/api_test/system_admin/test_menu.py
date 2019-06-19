# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from rest_framework import status

from padmin.views.menu import NOT_SUPER_MENU, SUPER_EXTRA_MENU
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class MenuTests(AdminSystemTestBase):
    not_super_menu = [item['name'] for item in NOT_SUPER_MENU]
    supper_extra_menu = [item['name'] for item in SUPER_EXTRA_MENU]

    def test_get_menu_not_logged_in(self):
        """ 未登录管理员获取菜单列表 """

        url = "/api/admin/menus/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_get_menu_is_not_super_logged_in(self):
        """ 非超级管理员菜单列表 """

        self.set_login_status()
        url = "/api/admin/menus/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        menu_list = [item['name'] for item in resp.json()]
        for menu in self.not_super_menu:
            self.assertIn(menu, menu_list)
        for menu in self.supper_extra_menu:
            self.assertNotIn(menu, menu_list)

    def test_get_menu_is_super_logged_in(self):
        """ 超级管理员菜单列表 """

        self.set_login_status(is_super=True)
        url = "/api/admin/menus/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        menu_list = [item['name'] for item in resp.json()]
        for menu in self.not_super_menu:
            self.assertIn(menu, menu_list)
        for menu in self.supper_extra_menu:
            self.assertIn(menu, menu_list)


