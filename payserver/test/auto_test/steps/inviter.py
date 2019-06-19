# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import asyncio
import logging
import random
import re
import threading
import uuid
from collections import Iterable

import requests_mock
from channels.testing import WebsocketCommunicator
from django.urls import reverse

from common.models import PaymentQRCode, Area
from payserver.asgi import application
from test.auto_test.callback.alipay import (
    AlipayCode2AccessTokenCallback,
    AlipayAccessToken2InfoCallback
)
from test.auto_test.callback.inviter import SendMessageCallback
from test.auto_test.callback.wechat import (
    WXCode2SessionCallback,
    WXWebCode2AccessTokenCallback,
    WXAccessToken2InfoCallback,
)
from test.auto_test.steps.base import BaseStep

logger = logging.getLogger(__name__)


# def add_marketer_api(path):
#     return f'/api/marketer/{path}'


def add_mock_request(func):
    def wrapper(self, data_dict, token=None):
        with requests_mock.Mocker(real_http=False) as m:
            for args in self.mock_args_list:
                m.register_uri(args['method'], args['pattern'], json=args['callback'])
            return func(self, data_dict, token)

    return wrapper


class InviterBaseStep(BaseStep):
    url = ''
    action = ''

    def __init__(self, instance_pk=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_pk = instance_pk

    def _request(self, data_dict, token=None):
        if token:
            self.client.credentials(HTTP_TOKEN=token)
        if self.instance_pk:
            self.url = reverse(f'{self.url}-detail', args=[self.instance_pk])
            # self.url = f'{self.url}{self.instance_pk}/'
        return getattr(self.client, self.action)(self.url, data=data_dict or {}, format='json')

    def go(self, request_data=None, token=None):
        return self._request(data_dict=request_data, token=token), None


class InviterMockStep(InviterBaseStep):
    mock_args_list = []

    def mock_callback_init(self, *args, **kwargs):
        raise NotImplementedError('`_mock_callback_init()` must be implemented.')

    def add_callback_list(self, method, pattern, callback):
        self.mock_args_list.append({'method': method, 'pattern': pattern, 'callback': callback})

    @add_mock_request
    def _request(self, data_dict, token=None):
        return super()._request(data_dict=data_dict, token=token)

    def go(self, callback_data=None, request_data=None, token=None, extra_res_keys=None):
        extra_res, callback_data = {}, callback_data or {}
        callback_instance = self.mock_callback_init(**callback_data)
        resp_res = self._request(data_dict=request_data, token=token)
        if callback_instance and isinstance(extra_res_keys, Iterable):
            extra_res_keys = (extra_res_keys,) if isinstance(extra_res_keys,
                                                             str) else extra_res_keys
            for k in extra_res_keys:
                extra_res[k] = getattr(callback_instance, k)
        return resp_res, extra_res


class LoginStep(InviterMockStep):
    # url = add_marketer_api('login/')
    url = reverse('login')
    action = 'post'

    def __init__(self, code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code

    def mock_callback_init(self, unionid=None):
        callback = WXCode2SessionCallback(self.code, mocked_unionid=unionid)
        pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/jscode2session\?[\w\W]*')
        self.add_callback_list('GET', pattern, callback.mock_callback)
        return callback


class GetMarketerWechatInfoStep(InviterMockStep):
    # url = '/api/marketer/get-marketer-wechat-info/'
    url = reverse('get-marketer-wechat-info')
    action = 'get'

    def __init__(self, code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code
        self.access_token = None
        self.openid = None

    def mock_callback_init(self, access_token=None, openid=None, unionid=None):
        pattern_get_access_token = re.compile(
            r'^https://api\.weixin\.qq\.com/sns/oauth2/access_token\?[\w\W]*')
        pattern_get_use_info = re.compile(r'^https://api\.weixin\.qq\.com/sns/userinfo\?[\w\W]*')
        get_access_token_callback = WXWebCode2AccessTokenCallback(code=self.code)
        self.access_token = get_access_token_callback.mock_success()['access_token']
        self.openid = get_access_token_callback.mock_success()['openid']
        get_user_info_callback = WXAccessToken2InfoCallback(
            access_token=access_token or self.access_token,
            openid=openid or self.openid,
            unionid=unionid)
        self.add_callback_list('GET', pattern_get_access_token,
                               get_access_token_callback.mock_callback)
        self.add_callback_list('GET', pattern_get_use_info, get_user_info_callback.mock_callback)
        return get_user_info_callback


class SendRegisterMessageStep(InviterMockStep):
    # url = '/api/marketer/message-send/'
    url = reverse('message-send')
    action = 'post'

    def mock_callback_init(self):
        pattern = re.compile(r'^https://app.cloopen.com:8883/2013-12-26/Accounts/[\w\W]*')
        send_message_callback = SendMessageCallback()
        self.add_callback_list('POST', pattern, send_message_callback.mock_callback)
        return send_message_callback


class VerifyCodeStep(InviterBaseStep):
    # url = '/api/marketer/sms-code-verify/'
    url = reverse('sms-code-verify')
    action = 'post'


class GetQiniuUpTokenStep(InviterBaseStep):
    url = '/api/admin/qiniu/uptoken'
    action = 'get'


class CreateMarketerStep(InviterBaseStep):
    # url = '/api/marketer/create-marketer/'
    url = reverse('create-marketer-list')
    action = 'post'


class GetUserInfoStep(InviterBaseStep):
    # url = '/api/marketer/get-info/'
    url = reverse('get-info')
    action = 'get'


class GetCategoryStep(InviterBaseStep):
    # url = '/api/marketer/get-category/'
    url = reverse('get-category')
    action = 'get'


class CheckMarketerStep(InviterBaseStep):
    # url = '/api/marketer/has_marketer/'
    url = reverse('has_marketer')
    action = 'get'


class CheckCodeStep(InviterBaseStep):
    # url = '/api/marketer/check-code/'
    url = reverse('check-code')
    action = 'get'


class GetMerchantWechatInfoStep(GetMarketerWechatInfoStep):
    # url = '/api/marketer/get-merchant-wechat-info/'
    url = reverse('get-merchant-wechat-info')
    action = 'get'


class GetMerchantAlipayInfoStep(InviterMockStep):
    # url = '/api/marketer/get-merchant-alipay-info/'
    url = reverse('get-merchant-alipay-info')
    action = 'get'

    def __init__(self, code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = code
        self.access_token = None

    def mock_callback_init(self, access_token=None):
        pattern_get_access_token = re.compile(
            r'^https://openapi\.alipay[\w\W]*\.com/gateway\.do[\w\W]*'
            r'&method=alipay\.system\.oauth\.token[\w\W]*')
        pattern_get_use_info = re.compile(
            r'^https://openapi\.alipay[\w\W]*\.com/gateway\.do[\w\W]*'
            r'&method=alipay\.user\.info\.share[\w\W]*')
        get_access_token_callback = AlipayCode2AccessTokenCallback(
            code=self.code)
        self.access_token = get_access_token_callback. \
            mock_success()['alipay_system_oauth_token_response']['access_token']
        get_user_info_callback = AlipayAccessToken2InfoCallback(
            access_token=access_token or self.access_token)
        self.add_callback_list('POST', pattern_get_access_token,
                               get_access_token_callback.mock_callback)
        self.add_callback_list('POST', pattern_get_use_info, get_user_info_callback.mock_callback)
        return get_user_info_callback


class CheckAdminExistStep(InviterBaseStep):
    # url = '/api/marketer/check-admin/'
    url = reverse('check-admin')
    action = 'get'


class CreateMerchantStep(InviterBaseStep):
    # url = '/api/marketer/create-merchant/'
    url = reverse('create-merchant-list')
    action = 'post'


class ShowInvitedMerchantsStep(InviterBaseStep):
    # url = '/api/marketer/invited-merchants/'
    url = reverse('invited-merchants-list')
    action = 'get'


class ShowToBeAuditedMerchantStep(InviterBaseStep):
    # url = '/api/marketer/show-audited/'
    url = reverse('show-audited-list')
    action = 'get'


class ShowOperationsViewStep(InviterBaseStep):
    # url = add_marketer_api('show-operation/')
    url = reverse('show-operation-list')
    action = 'get'


class GetMerchantDetailsStep(InviterBaseStep):
    url = 'merchant-details'
    action = 'get'


class AuditMerchantStep(InviterBaseStep):
    # url = add_marketer_api('audit-merchant/')
    url = 'audit-merchant'  # 这里是iurl_name
    action = 'patch'


class AuthenticatedMarketerMSGSend(SendRegisterMessageStep):
    # url = add_marketer_api('authenticated-message-send/')
    url = reverse('authenticated-message-send')
    action = 'post'


class GetAccountWithdrawableBalanceStep(InviterBaseStep):
    # url = add_marketer_api('get-balance/')
    url = reverse('get-balance')
    action = 'get'


class UpdateMarketerInfoStep(InviterBaseStep):
    # url = add_marketer_api('check-phone/')
    url = reverse('update-marketer')
    action = 'put'


class CheckPhoneExistStep(InviterBaseStep):
    # url = add_marketer_api('check-phone/')
    url = reverse('check-phone')
    action = 'get'


class AlipayAuthStep(BaseStep):
    """ 支付宝 web 授权 """

    def __init__(self, code, state=None):
        self.code = code
        self.state = state
        self.access_token = None
        self.openid = None

    def code2user_info(self, code=None, access_token=None,
                       openid=None, auth_type='merchant'):
        auth_url_map = {
            # 'merchant': '/api/marketer/get-merchant-alipay-info/'
            'merchant': reverse('get-merchant-alipay-info')
        }
        pattern_get_access_token = re.compile(
            r'^https://openapi.alipay[\w\W]*.com/gateway.do[\w\W]*'
            r'&method=alipay.system.oauth.token[\w\W]*')
        pattern_get_use_info = re.compile(
            r'^https://openapi.alipay[\w\W]*.com/gateway.do[\w\W]*'
            r'&method=alipay.user.info.share.[\w\W]*')
        get_access_token_callback = AlipayCode2AccessTokenCallback(
            code=self.code)
        self.access_token = get_access_token_callback. \
            mock_success()['alipay_system_oauth_token_response']['access_token']
        get_user_info_callback = AlipayAccessToken2InfoCallback(
            access_token=access_token or self.access_token)

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern_get_access_token,
                           json=get_access_token_callback.mock_callback)

            m.register_uri('POST', pattern_get_use_info,
                           json=get_user_info_callback.mock_callback)
            url = auth_url_map[auth_type]
            return self.client.get(url, data={'auth_code': code or self.code,
                                              'state': self.state})


class CreateQrCodeStep(BaseStep):
    """ 创建付款二维码　"""

    @staticmethod
    def create_qr_code(number=10):
        uuids = []
        qr_objs = []
        for i in range(number):
            obj = PaymentQRCode()
            qr_objs.append(obj)
            uuids.append(obj.uuid)
        PaymentQRCode.objects.bulk_create(qr_objs)
        return random.choice(uuids)


class WebSocketThread(threading.Thread):
    def __init__(self, event, marketer_token, channel, queue):
        super().__init__()
        self.event = event
        self.marketer_token = marketer_token
        self.channel = channel
        self.queue = queue

    def run(self):
        self.start_create_web_socket()

    def start_create_web_socket(self):
        logger.info(f'start to create web-socket')

        ws_url = f'/ws/ws-service/{self.channel}/?token={self.marketer_token}'

        async def t_run():
            try:
                communicator = WebsocketCommunicator(application, ws_url)
                connected, subprotocol = await communicator.connect()
                assert connected
                logger.info("websocket connect success")
                self.event.set()

                message = await communicator.receive_json_from()
                logger.info(f"web-socket receive message: {message}")
                self.queue.put(message)

                await communicator.disconnect()
                logger.info("disconnect web-socket")
            except Exception as e:
                logger.error(e)
                self.event.set()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        coro = asyncio.coroutine(t_run)
        loop.run_until_complete(coro())
        loop.close()
        logger.info("WebSocketThread will be destroy")
        print("WebSocketThread will be destroy")


class InviteMerchantStep(BaseStep):
    """ 邀请商户　"""

    def get_category(self, token):
        """ 获取商户分类　"""
        url = reverse('get-category')
        self.client.credentials(HTTP_TOKEN=token)
        response = self.client.get(url)
        return response

    def check_admin(self, unionid, token):
        """ 验证该用户是否是商户管理员/收银员 """
        url = reverse('check-admin')
        self.client.credentials(HTTP_TOKEN=token)
        response = self.client.get(url, data={'unionid': unionid})
        return response

    def check_qr_code(self, code, token):
        """ 验证付款码是否可用　"""
        url = reverse('check-code')
        self.client.credentials(HTTP_TOKEN=token)
        response = self.client.get(url, data={'code': code})
        return response

    def check_salesman_exists(self, adcode, token):
        """" 验证区域是否存在业务员 """
        url = reverse('has_marketer')
        self.client.credentials(HTTP_TOKEN=token)
        response = self.client.get(url, data={'adcode': adcode})
        return response

    def websocket_event(self, token, channel, message_queue):
        """ 建立websocket发送消息 """
        event = threading.Event()  # 创建一个事件
        ws_client = WebSocketThread(marketer_token=token,
                                    event=event,
                                    channel=channel,
                                    queue=message_queue)
        ws_client.start()
        event.wait()
        return ws_client

    def get_wechat_user_info(self):
        """ 获取微信用户信息，websocket推送　"""
        code = uuid.uuid4()  # 模拟生成一个授权code
        state = 'merchant_web_auth'
        response = WXWebAuthStep(code=code, state=state).code2user_info(
            auth_type='merchant'
        )
        return response

    def get_alipay_user_info(self):
        """ 获取支付宝用户信息，websocket推送 """
        code = uuid.uuid4()  # 模拟生成一个授权code
        state = 'alipay_web_auth'
        response = AlipayAuthStep(code=code, state=state).code2user_info(
            auth_type='merchant'
        )
        return response

    def submit_merchant_data(self, token, **kwargs):
        """ 提交商户信息 创建商户 """
        url = reverse('create-merchant-list')
        area_id = random.choice(Area.objects.exclude(parent=None)).adcode

        merchant_data = dict(
            name=kwargs.get('name', '大宝天天见'),
            payment_qr_code=kwargs.get('payment_qr_code'),
            category_id=kwargs.get('category_id'),
            contact_phone=kwargs.get('phone', '13333333333'),
            area_id=kwargs.get('area_id', area_id),
            address=kwargs.get('address', '高新区吉泰路'),
            location_lon=kwargs.get('location_lon', 45),
            location_lat=kwargs.get('location_lat', 46),
            description=kwargs.get('description', "很不错的哟，推荐给大家"),
            avatar_url=kwargs.get('avatar_url', 'https://www.baidu.com'),
            photo_url=kwargs.get('photo_url', 'https://www.baidu.com'),
            license_url=kwargs.get('license_url', 'https://www.baidu.com'),
            id_card_front_url=kwargs.get('id_card_front_url', 'https://www.baidu.com'),
            id_card_back_url=kwargs.get('id_card_back_url', 'https://www.baidu.com'),
            merchant_admin_data=kwargs.get('merchant_admin_data', {}),
            merchant_acct_data=kwargs.get('merchant_acct_data', {}),
        )

        self.client.credentials(HTTP_TOKEN=token)
        response = self.client.post(url, data=merchant_data, format='json')
        return response


class WXWebAuthStep(BaseStep):
    def __init__(self, code, state=None):
        self.code = code
        self.state = state
        self.access_token = None
        self.openid = None

    def code2user_info(self, code=None, access_token=None, openid=None, auth_type='marketer'):
        auth_url_map = {
            # 'marketer': '/api/marketer/get-marketer-wechat-info/',
            'marketer': reverse('get-marketer-wechat-info'),
            # 'merchant': '/api/marketer/get-merchant-wechat-info/'
            'merchant': reverse('get-merchant-wechat-info')
        }
        pattern_get_access_token = re.compile(
            r'^https://api\.weixin\.qq\.com/sns/oauth2/access_token?[\w\W]*')
        pattern_get_use_info = re.compile(r'^https://api\.weixin\.qq\.com/sns/userinfo?[\w\W]*')
        get_access_token_callback = WXWebCode2AccessTokenCallback(code=self.code)
        self.access_token = get_access_token_callback.mock_success()['access_token']
        self.openid = get_access_token_callback.mock_success()['openid']
        get_user_info_callback = WXAccessToken2InfoCallback(
            access_token=access_token or self.access_token,
            openid=openid or self.openid)

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', pattern_get_access_token,
                           json=get_access_token_callback.mock_callback)

            m.register_uri('GET', pattern_get_use_info, json=get_user_info_callback.mock_callback)
            url = auth_url_map[auth_type]
            return self.client.get(url, data={'code': code or self.code, 'state': self.state})
