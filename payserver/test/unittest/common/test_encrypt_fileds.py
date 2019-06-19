# -*- coding: utf-8 -*-
#  
#       File ：  test_encrypt_fileds
#    Project ：  payunion
#     Author ：  Tian Xu
#     Create ：  18-8-31
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.test import TestCase

from common.models import Client, Marketer, MerchantAdmin
from test.unittest.fake_factory import PayunionFactory


class TestEncryptCharFileds(TestCase):
    """ 测试自定义的EncryptCharFiled"""

    value_list = ['', ' ', '0', '12344', 'asdasdasd', 'kjhfujewhff=ds+sd==']

    def test_encrypt_filed(self):
        self.factory = PayunionFactory()
        for i in self.value_list:
            merchant_admin = self.factory.create_merchant_admin(
                wechat_openid=i,
            )
            self.assertEqual(merchant_admin.wechat_openid, i)

            marketer = self.factory.create_marketer(
                wechat_openid=i,
            )
            self.assertEqual(marketer.wechat_openid, i)

            client = self.factory.create_client(
                 openid=i,
            )
            self.assertEqual(client.openid, i)
