# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework import status

from common.models import Message
from config import MESSAGE_STATUS, MESSAGE_TYPE
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase


class MessageTests(AdminSystemTestBase):

    def test_message(self):
        """ 获取更新首页消息 """

        data = dict(content="区域没有业务员", # 消息内容
            status=MESSAGE_STATUS['UNHANDLED'],  # 消息状态
            type=MESSAGE_TYPE['AREA_WITHOUT_MARKETER']  # 消息类型
        )
        msg1 = Message.objects.create(**data)
        msg2 = Message.objects.create(**data)

        self.set_login_status(is_super=True)
        url = "/api/admin/messages/?page=1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['count'], 2)
        results = resp_json['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['status'], MESSAGE_STATUS['UNHANDLED'])
        self.assertEqual(results[0]['type'], MESSAGE_TYPE['AREA_WITHOUT_MARKETER'])
        self.assertEqual(results[1]['status'], MESSAGE_STATUS['UNHANDLED'])
        self.assertEqual(results[1]['type'], MESSAGE_TYPE['AREA_WITHOUT_MARKETER'])


        update_url = f"/api/admin/messages/{msg1.id}/"
        resp = self.client.patch(update_url, data={"id": msg1.id, "status": MESSAGE_STATUS['HANDLED']}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        msg1.refresh_from_db()
        self.assertEqual(msg1.status, MESSAGE_STATUS['HANDLED'])
        self.assertEqual(resp_json['status'], MESSAGE_STATUS['HANDLED'])
        self.assertEqual(resp_json['id'], msg1.id)
