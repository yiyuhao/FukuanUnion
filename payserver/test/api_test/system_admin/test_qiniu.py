# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class QinNiuTests(AdminSystemTestBase):

    def test_get_upload_token(self):
        """ 获取七牛token """

        url = '/api/admin/qiniu/uptoken'

        resp = self.client.post(url)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('upload_token', resp_json)
        self.assertIn('bucket_domain', resp_json)
        self.assertEqual(len(resp_json), 2)
