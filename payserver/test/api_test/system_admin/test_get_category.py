# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

from common.models import MerchantCategory
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class CategoryTests(AdminSystemTestBase):

    def test_get_category(self):
        """ 获取商户分类 """

        merchant_categories = {
            '美食': ['火锅', '串串'],
            '饮品': ['啤酒', '可乐'],
            '珠宝': [],
        }
        for k, v in merchant_categories.items():
            p = MerchantCategory.objects.create(name=k, parent=None)
            for item in v:
                MerchantCategory.objects.create(name=item, parent=p)

        self.set_login_status(is_super=True)
        url = "/api/admin/merchant_category/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        temp_dict = {}
        for category in resp_json:
            p_name = category['name']
            temp_dict[p_name] = []
            for sub_cate in category.get('children', []):
                temp_dict[p_name].append(sub_cate['name'])
        self.assertEqual(merchant_categories, temp_dict)
