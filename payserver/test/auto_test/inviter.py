# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import json
import re
import uuid

import requests_mock
from django.test import TestCase
from django.urls import reverse
from faker import Factory
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from test.auto_test.callback import inviter as INVITER_CALLBACK
from test.auto_test.callback.inviter import SendMessageCallback

fake = Factory().create('zh_CN')


class Inviter(TestCase):
    def __init__(self):
        self.client = APIClient()
        self.info = {}
        self.token = None
        self.verify_code = None
        self.mini_unionid = None
        self.id = None
        super(Inviter, self).__init__()

    def entry_mini_program(self):
        """ mock 进入小程序 """

        mock_code = uuid.uuid4()
        mock_resp_data = INVITER_CALLBACK.js_code2session()
        self.mini_unionid = mock_resp_data['unionid']

        def validator_callback(request, context):
            self.assertIn(f"js_code={mock_code}", request.query)
            return mock_resp_data

        pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/jscode2session?[\w\W]*')
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', pattern, json=validator_callback)
            # url = "/api/marketer/login/"
            url = reverse('login/')
            resp = self.client.post(url, data={"code": mock_code})
            self.token = resp.json()['token']
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            return resp

    def click_button_to_register_become_inviter(self):
        """ mock 点击注册成为邀请人"""

        mock_code = uuid.uuid4()
        mock_resp_data_access_token = INVITER_CALLBACK.sns_oauth2_access_token()
        mock_resp_data_use_info = INVITER_CALLBACK.sns_userinfo()
        mock_resp_data_use_info.update({"unionid": self.mini_unionid})

        def validator_callback_get_access_token(request, context):
            self.assertIn(f"code={mock_code}", request.query)
            return mock_resp_data_access_token

        def validator_callback_get_use_info(request, context):
            self.assertIn(f"openid={mock_resp_data_access_token['openid']}", request.query)
            self.assertIn(f"access_token={mock_resp_data_access_token['access_token']}",
                          request.query)
            return mock_resp_data_use_info

        pattern_get_access_token = re.compile(
            r'^https://api\.weixin\.qq\.com/sns/oauth2/access_token?[\w\W]*')
        pattern_get_use_info = re.compile(r'^https://api\.weixin\.qq\.com/sns/userinfo?[\w\W]*')
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', pattern_get_access_token,
                           json=validator_callback_get_access_token)
            m.register_uri('GET', pattern_get_use_info, json=validator_callback_get_use_info)
            # url = "/api/marketer/get-marketer-wechat-info/"
            url = reverse('get-marketer-wechat-info')
            resp = self.client.get(url, data={"code": mock_code})

            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            resp_context = resp.content.decode('utf-8')
            self.assertIn("已成功授权", resp_context)
            self.assertIn(mock_resp_data_use_info['nickname'], resp_context)
            return resp

    def set_info(self, info_data=None):
        """ mock 填写注册信息 """

        default_info = {
            "name": fake.name(),
            "phone": fake.phone_number(),
            "id_card_front_url": fake.url(),
            "id_card_back_url": fake.url(),
        }

        self.info = info_data if info_data else default_info

    def send_message(self):
        """ mock 注册发送短息 """

        def validator_callback(request, context):
            self.verify_code = json.loads(request.text)['datas'][0]
            return INVITER_CALLBACK.SendMessageCallback().mock_success(request,
                                                                       context)

        pattern = re.compile(
            r'^https://app.cloopen.com:8883/2013-12-26/Accounts/[\w\W]*')
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern, json=validator_callback)
            # url = "/api/marketer/check-phone/"
            url = reverse('check-phone')
            resp = self.client.get(url, data={"phone": self.info['phone']})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.json(), {'code': 1, 'message': '可以使用'})

            # url = "/api/marketer/message-send/"
            url = reverse('message-send/')
            self.client.credentials(HTTP_TOKEN=self.token)
            resp = self.client.post(url, data={"phone": self.info['phone']})
            self.assertEqual(resp.json(), {'code': 0, 'message': '验证码发送成功'})

            return resp

    def register(self):
        """ mock 提交注册信息 """

        self.info.update({"verify_code": self.verify_code})
        # url = "/api/marketer/create-marketer/"
        url = reverse('create-marketer-create')
        resp = self.client.post(url, data=self.info)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp_json = resp.json()

        self.assertEqual(self.info['name'], resp_json['name'])
        self.assertEqual(self.info['phone'], resp_json['phone'])
        self.assertEqual(self.info['id_card_front_url'], resp_json['id_card_front_url'])
        self.assertEqual(self.info['id_card_back_url'], resp_json['id_card_back_url'])

        self.id = resp_json['id']


class SendMessageStep(APITestCase):
    def __init__(self):
        super().__init__()
        self.verify_code = None

    def validate(self, request):
        self.verify_code = json.loads(request.text)['datas'][0]
        return True

    def send_message(self):
        pattern = re.compile(r'^https://app.cloopen.com:8883/2013-12-26/Accounts/[\w\W]*')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern, json=SendMessageCallback(self.validate).mock_success)
            # url = "/api/marketer/message-send/"
            url = reverse('message-send')
            self.client.credentials(HTTP_TOKEN=self.token)
            resp = self.client.post(url, data={"phone": self.info['phone']})
            self.assertEqual(resp.json(), {'code': 0, 'message': '验证码发送成功'})
            return dict(
                resp_json=resp.json(),
                data=self.verify_code
            )