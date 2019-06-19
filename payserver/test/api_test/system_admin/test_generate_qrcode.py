# -*- coding: utf-8 -*-
#
#       File ：  test_generate_qrcode
#    Project ：  payunion
#     Author ：  Tian Xu
#     Create ：  18-8-27
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import time

from rest_framework import status

from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class TestGenerateQrCode(AdminSystemTestBase):
    """ 测试批量生成二维码 """
    image_url = ('https://ss1.mvpalpha.muchbo.com/payunion/'
                 '758d723e-9fe1-47b2-9df0-ce29d054dd8a.jpg')
    qrcode_num = 1
    path = "/api/admin/qrcode/"

    def test_generate_qrcode_not_login_in(self):
        # 测试没有登录的情况
        timestamp = str(time.time()).split('.')[0]

        resp = self.client.get(self.path,
                               data={'timestamp': timestamp,
                                     'qrcode_image_url': self.image_url,
                                     'qrcode_num': self.qrcode_num})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.json()["error_code"], "permission_denied")

    def test_generate_qrcode_logged_in(self):
        # 已经登录
        self.set_login_status()

        # 生成成功
        timestamp = str(time.time()).split('.')[0]
        resp = self.client.get(self.path,
                               data={'timestamp': timestamp,
                                     'qrcode_image_url': self.image_url,
                                     'qrcode_num': self.qrcode_num})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_generate_qrcode_redirect(self):
        # 测试生成单张重定向
        self.set_login_status()

        url = "/api/admin/merchant_qrcode/"

        resp = self.client.get(url,
                               data={'qid': 111, 'uuid': 'sfsdfwesadfsdfwewfe'})
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)

