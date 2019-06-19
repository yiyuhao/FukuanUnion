# -*- coding=utf-8 -*-
#
#   Project=payunion
#   Author=zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid
import json

import requests_mock
from django.core.cache import cache
from rest_framework.test import APITestCase

import config
from common.models import MerchantCategory
from test.api_test.marketer.test_marketer_config import CREATE_MERCHANT_DATA
from test.auto_test.callback.wechat_message import WechatPushMessageCallback
from test.auto_test.steps.merchant import CashierManagerStep
from test.unittest.fake_factory.fake_factory import PayunionFactory, fake
from rest_framework.reverse import reverse
from rest_framework import status


class TestMessageSend(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        from payserver import celery_config
        celery_config.CELERY_ALWAYS_EAGER = True
        
        cls.factory = PayunionFactory()
        cls.inviter_account = cls.factory.create_account(
            withdrawable_balance=0,
            bank_card_number='123456'
        )
        cls.marketer = cls.factory.create_marketer(
            wechat_openid='this open id',
            name='this marketer',
            account=cls.inviter_account,
            inviter_type=config.MARKETER_TYPES.SALESMAN,
            working_areas_name=['working area1', 'working area2'],
            status=config.SYSTEM_USER_STATUS.USING,
            phone='15888888888'
        )
        cls.token = uuid.uuid4()
        cache.set(cls.token, dict(
            openid=cls.marketer.wechat_openid,
            unionid=cls.marketer.wechat_unionid,
            session_key='session key'),
                  300)
    
    def test_create_merchant(self):
        def validate(request):
            print(request)
            # do validate
            return True
        
        push_message_callback = WechatPushMessageCallback(validate=validate)
        
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', push_message_callback.url_pattern, json=push_message_callback.mock_success)
            # url = "/api/merchant/add_cashier/wechat_auth_redirect/"
            url = reverse('add_cashier-wechat_auth_redirect')
            self.factory.create_area(adcode='110119110000')
            self.factory.create_merchant_category(name='this category')
            self.factory.create_payment_qrcode()
            category = MerchantCategory.objects.get(name='this category').id
            payment_qr_code = self.factory.create_payment_qrcode().uuid
            CREATE_MERCHANT_DATA['area_id'] = '110119110000'
            CREATE_MERCHANT_DATA['category_id'] = category
            CREATE_MERCHANT_DATA['payment_qr_code'] = payment_qr_code
            json_data = json.dumps(CREATE_MERCHANT_DATA)
            url = reverse('create-merchant-list')
            response = self.client.post(url, data=json_data, Token=self.token, content_type='application/json')
            print(response)
            print(response.json())

