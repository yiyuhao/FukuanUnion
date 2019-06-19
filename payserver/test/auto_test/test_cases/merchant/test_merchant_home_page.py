# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import uuid

from rest_framework import status
from rest_framework.test import APITestCase

import config
from test.unittest.fake_factory import PayunionFactory
from test.auto_test.steps.common_object import WechatPerson
from test.auto_test.steps.merchant import MerchantLoginMockStep


class TestHomePage(APITestCase):
    """ 商户端-首页测试"""
    
    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

    def test_merchant_not_register(self):
        """ 未注册状态 """
        wechat_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)

        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                 mocked_openid=wechat_person.mini_openid,
                                 mocked_session_key=wechat_person.mini_session_key,
                                 mocked_unionid=wechat_person.unionid,
                                )
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_json, {'non_field_errors': ['该用户不是商户管理员或收银员'],
                                     'error_code': 'user is not a merchant admin or cashier'})
        
    def test_merchant_in_reviewing(self):
        """ 商户审核中 """
        # 创建一个审核中的商户，设置其管理员
        wechat_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)
        self.factory.create_merchant_admin(
                wechat_openid=wechat_person.subscription_openid,
                wechat_unionid=wechat_person.unionid,
                wechat_avatar_url=wechat_person.user_info['headimgurl'],
                wechat_nickname=wechat_person.user_info['nickname'],
                merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
                status=config.SYSTEM_USER_STATUS['USING'],
                work_merchant=self.factory.create_merchant(status=config.MERCHANT_STATUS['REVIEWING'])
            )

        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=wechat_person.mini_openid,
                                mocked_session_key=wechat_person.mini_session_key,
                                mocked_unionid=wechat_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['ADMIN'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['REVIEWING'])

    def test_merchant_not_pass(self):
        """ 商户驳回状态"""
        # 创建一个驳回的商户，设置其管理员
        wechat_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)
        self.factory.create_merchant_admin(
            wechat_openid=wechat_person.subscription_openid,
            wechat_unionid=wechat_person.unionid,
            wechat_avatar_url=wechat_person.user_info['headimgurl'],
            wechat_nickname=wechat_person.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=self.factory.create_merchant(status=config.MERCHANT_STATUS['REJECTED'])
        )

        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=wechat_person.mini_openid,
                                mocked_session_key=wechat_person.mini_session_key,
                                mocked_unionid=wechat_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['ADMIN'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['REJECTED'])

    def test_merchant_is_disabled(self):
        """ 商户禁用状态"""
        # 创建一个禁用的商户，设置其管理员和收银员
        admin_person = WechatPerson()
        cashier_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)

        work_merchant = self.factory.create_merchant(status=config.MERCHANT_STATUS['DISABLED'])
        self.factory.create_merchant_admin(
            wechat_openid=admin_person.subscription_openid,
            wechat_unionid=admin_person.unionid,
            wechat_avatar_url=admin_person.user_info['headimgurl'],
            wechat_nickname=admin_person.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=work_merchant
        )
        self.factory.create_merchant_admin(
            wechat_openid=cashier_person.subscription_openid,
            wechat_unionid=cashier_person.unionid,
            wechat_avatar_url=cashier_person.user_info['headimgurl'],
            wechat_nickname=cashier_person.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['CASHIER'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=work_merchant
        )

        # 管理员登陆
        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=admin_person.mini_openid,
                                mocked_session_key=admin_person.mini_session_key,
                                mocked_unionid=admin_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['ADMIN'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['DISABLED'])

        # 收银员登陆
        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=cashier_person.mini_openid,
                                mocked_session_key=cashier_person.mini_session_key,
                                mocked_unionid=cashier_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['CASHIER'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['DISABLED'])

    def test_merchant_login_by_admin(self):
        """ 商户通过审核， 管理员登录 """
        # 创建一个通过审核的商户，设置其管理员
        admin_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)

        self.factory.create_merchant_admin(
            wechat_openid=admin_person.subscription_openid,
            wechat_unionid=admin_person.unionid,
            wechat_avatar_url=admin_person.user_info['headimgurl'],
            wechat_nickname=admin_person.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=self.factory.create_merchant(status=config.MERCHANT_STATUS['USING'])
        )
        # 管理员登陆
        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=admin_person.mini_openid,
                                mocked_session_key=admin_person.mini_session_key,
                                mocked_unionid=admin_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['ADMIN'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['USING'])

    def test_merchant_login_by_cashier(self):
        """ 商户通过审核， 收银员登录  """
        # 创建一个通过审核的商户，设置其收银员
        cashier_person = WechatPerson()
        login_step = MerchantLoginMockStep(self)

        self.factory.create_merchant_admin(
            wechat_openid=cashier_person.subscription_openid,
            wechat_unionid=cashier_person.unionid,
            wechat_avatar_url=cashier_person.user_info['headimgurl'],
            wechat_nickname=cashier_person.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['CASHIER'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=self.factory.create_merchant(status=config.MERCHANT_STATUS['USING'])
        )

        # 收银员登陆
        mock_code = str(uuid.uuid4())
        resp = login_step.login(mock_code,
                                mocked_openid=cashier_person.mini_openid,
                                mocked_session_key=cashier_person.mini_session_key,
                                mocked_unionid=cashier_person.unionid,
                                )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp_json = resp.json()
        self.assertEqual(resp_json['merchant_admin_status'], config.SYSTEM_USER_STATUS['USING'])
        self.assertEqual(resp_json['merchant_admin_type'], config.MERCHANT_ADMIN_TYPES['CASHIER'])
        self.assertEqual(resp_json['merchant_status'], config.MERCHANT_STATUS['USING'])



