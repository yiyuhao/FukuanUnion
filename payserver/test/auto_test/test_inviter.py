# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import json
import logging
import random
import uuid
from queue import Queue

from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APITestCase

import config
from common.models import Marketer, Area
from marketer.config import PAYMENT_QR_CODE_STATUS
from test.auto_test.steps.inviter import (
    InviteMerchantStep,
    CreateQrCodeStep,
)
from test.auto_test.steps.inviter import LoginStep, GetMarketerWechatInfoStep, \
    SendRegisterMessageStep, \
    GetQiniuUpTokenStep
from test.auto_test.workflows.inviter import RegisterInviterWorkflow, \
    GetMerchantAdminWechatInfoWorkflow, \
    GetMerchantAdminAlipayInfoWorkflow, InviteMerchantWorkflow, AuditMerchantWorkflow
from test.auto_test.workflows.pre_inviter import GenerateInviterWorkflow
from test.unittest.system_admin.base_data import create_base_data

logger = logging.getLogger(__name__)


class InviterTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        create_base_data()

    def test_code2session(self):
        mock_code = uuid.uuid4()
        resp = LoginStep(code=mock_code).go(request_data={'code': mock_code})
        pass

    def test_get_wechat_info(self):
        mock_code = uuid.uuid4()
        resp = GetMarketerWechatInfoStep(code=mock_code).go(request_data={'code': mock_code},
                                                            extra_res_keys=('unionid', 'openid'))
        content = resp[0].content.decode('utf8')
        pass

    def test_send_message(self):
        mock_code = uuid.uuid4()
        token_resp = LoginStep(code=mock_code).go(request_data={'code': mock_code})
        resp = SendRegisterMessageStep().go(request_data={'phone': '13730897717'},
                                            token=token_resp[0].data.get('token'),
                                            extra_res_keys='get_send_code')
        pass

    def test_get_qiniu_token(self):
        resp = GetQiniuUpTokenStep().go()
        pass

    def test_success_register_marketer(self):
        RegisterInviterWorkflow(unionid=str(uuid.uuid4())).go()

    def test_get_merchant_wechat_info(self):
        mock_code = str(uuid.uuid4())
        channel = random.random()
        resp = LoginStep(code=mock_code).go(request_data={'code': mock_code})
        token = resp[0].data.get('token')

        resp = GetMerchantAdminWechatInfoWorkflow(channel=channel, token=token).go()
        pass

    def test_get_merchant_alipay_info(self):
        mock_code = str(uuid.uuid4())
        channel = random.random()
        resp = LoginStep(code=mock_code).go(request_data={'code': mock_code})
        token = resp[0].data.get('token')
        resp = GetMerchantAdminAlipayInfoWorkflow(channel=channel, token=token).go()
        pass

    def test_get_category(self):
        res = InviteMerchantWorkflow().choose_category()
        pass

    def test_invite_merchant(self):
        token, unionid = RegisterInviterWorkflow(unionid=str(uuid.uuid4())).go()
        InviteMerchantWorkflow(token=token, unionid=unionid).go()

    def test_audit_merchant(self):
        token, unionid = RegisterInviterWorkflow(unionid=str(uuid.uuid4())).go()

        # todo real request to update Inviter to Marketer
        area_instance = Area.objects.get(adcode=110105004000)
        marketer = Marketer.objects.get(wechat_unionid=unionid)
        marketer.inviter_type = config.MARKETER_TYPES.SALESMAN
        marketer.working_areas.add(area_instance)
        marketer.save()

        merchant_id_resp = InviteMerchantWorkflow(token=token, unionid=unionid).go()
        merchant_id = merchant_id_resp[0].data.get('id')
        resp = AuditMerchantWorkflow(merchant_id=merchant_id).go(
            to_status=config.MERCHANT_STATUS.USING,
            token=token)
        pass


class InviteMerchantTest(APITestCase):
    """ 邀请商户流程测试　"""
    inviter_data = None
    merchant_data = None

    @classmethod
    def setUpTestData(cls):
        create_base_data()

    @classmethod
    def init_method_with_merchant_data(cls, inviter_data, merchant_data):
        """
        备选构造方法, 传递完整的商户数据
        :param inviter_data: 创建邀请人的数据
        :param merchant_data: 创建商户需要的数据
        :return:
        """
        cls.inviter_data = inviter_data
        cls.merchant_data = merchant_data
        return cls()

    def test_invite_merchant(self):
        # 注册一个邀请人
        gen_inviter_workflow = GenerateInviterWorkflow(self)
        if not self.inviter_data:
            self.inviter_data = dict(
                name="默认邀请人a"
            )
        inviter_res = gen_inviter_workflow.generate_inviter(**self.inviter_data)

        # 开始邀请商户
        invite_merchant_obj = InviteMerchantStep()

        # generate token
        self.token = inviter_res.get('token')

        # get category success
        categories = invite_merchant_obj.get_category(self.token).data
        assert len(categories) > 0
        self.category_id = random.choice(categories).get('id')

        # check qr code
        code = uuid.uuid4()  # not exists
        resp = invite_merchant_obj.check_qr_code(code=code, token=self.token)
        assert resp.data.get('code') == PAYMENT_QR_CODE_STATUS['DOES_NOT_EXIST']

        self.uuid = CreateQrCodeStep.create_qr_code()
        resp = invite_merchant_obj.check_qr_code(code=self.uuid,
                                                 token=self.token)
        assert resp.data.get('code') == PAYMENT_QR_CODE_STATUS['CAN_USE']

        # 存放消息的队列
        message_queue = Queue()

        # create ws connect for wechat auth
        ws_client_wechat = invite_merchant_obj.websocket_event(
            token=self.token,
            channel='merchant_web_auth',
            message_queue=message_queue)
        resp = invite_merchant_obj.get_wechat_user_info()
        resp_context = resp.content.decode('utf-8')
        assert '<title>邀请商户</title>' in resp_context

        ws_client_wechat.join()
        if message_queue.empty():
            logger.error(
                "message_queue is empty, web-socket not receive message")
            raise Exception(
                "message_queue is empty, web-socket not receive message")
        msg = message_queue.get()
        wechat_user_info = json.loads(msg['message'])
        print("微信用户信息： ", wechat_user_info)
        assert wechat_user_info['nickname'] == 'wechat nick name'

        # create ws connect for alipay auth
        ws_client_alipay = invite_merchant_obj.websocket_event(
            token=self.token,
            channel='alipay_web_auth',
            message_queue=message_queue)
        resp = invite_merchant_obj.get_alipay_user_info()
        resp_context = resp.content.decode('utf-8')
        assert '<title>商户管理员</title>' in resp_context

        ws_client_alipay.join()
        if message_queue.empty():
            logger.error(
                "message_queue is empty, web-socket not receive message")
            raise Exception(
                "message_queue is empty, web-socket not receive message")
        msg = message_queue.get()
        alipay_user_info = json.loads(msg['message'])
        print("支付宝用户信息： ", alipay_user_info)
        assert alipay_user_info['nick_name'] == "alipay nickname"

        # 创建商户
        if not self.merchant_data:
            self.merchant_data = dict(
                payment_qr_code=str(self.uuid),
                category_id=self.category_id,
                merchant_acct_data=dict(),
                merchant_admin_data=dict(
                    wechat_openid=wechat_user_info['openid'],
                    wechat_unionid=wechat_user_info['unionid'],
                    wechat_avatar_url=wechat_user_info['headimgurl'],
                    wechat_nickname=wechat_user_info['nickname'],
                    alipay_userid=alipay_user_info['user_id'],
                    alipay_user_name=alipay_user_info['nick_name'],
                )
            )
        resp = invite_merchant_obj.submit_merchant_data(
            token=self.token, **self.merchant_data)
        assert resp.status_code == HTTP_201_CREATED  # TODO