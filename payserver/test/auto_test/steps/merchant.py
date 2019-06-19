# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import asyncio
import json
import logging
import random
import re
import threading
import uuid
from queue import Queue
from urllib.parse import parse_qs

import requests_mock
from channels.testing import WebsocketCommunicator
from rest_framework.reverse import reverse

from payserver.asgi import application
from test.auto_test.callback.merchant import (
    WechatGetUserInfoCallback,
    WechatGetAccessToken
)
from test.auto_test.callback.wechat import (
    WXCode2SessionCallback
)
from test.auto_test.callback.wechat_pay import WechatPayCallback
from test.auto_test.callback.alipay_pay import AlipayPaymentCallback

logger = logging.getLogger()
logger.level = logging.DEBUG


class WebSocketThread(threading.Thread):
    def __init__(self, event_obj, merchant_token, channel, queue):
        super().__init__()
        self.event = event_obj
        self.merchant_token = merchant_token
        self.channel = channel
        self.queue = queue

    def run(self):
        self.start_create_web_socket()

    def start_create_web_socket(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        logger.info(f'start to create web-socket')

        ws_url = f'/ws/ws-service/{self.channel}/?token={self.merchant_token}'

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

        coro = asyncio.coroutine(t_run)
        event_loop.run_until_complete(coro())
        event_loop.close()
        logger.info("WebSocketThread will be destroy")


class CashierManagerStep(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def add_cashier(self, merchant_token=None, cashier_info=None):
        self.test_case.assertIsNotNone(merchant_token)
        mock_code = str(uuid.uuid4())  # wx.login()_code
        mock_state = random.random()  # channel_key
        mock_access_token = str(uuid.uuid4())
        mock_openid = str(uuid.uuid4())
        if cashier_info and cashier_info.get('openid'):
            mock_openid = cashier_info.get('openid')

        def validate_login(request):
            self.test_case.assertIn(f"code={mock_code}", request.query)
            return True

        def validate_user_info(request):
            self.test_case.assertIn(f"openid={mock_openid}", request.query)
            self.test_case.assertIn(f"access_token={mock_access_token}", request.query)
            return True

        login_callback = WechatGetAccessToken(access_token=mock_access_token,
                                              openid=mock_openid,
                                              validate=validate_login)
        info_callback = WechatGetUserInfoCallback(user_info=cashier_info,
                                                  validate=validate_user_info)

        event_obj = threading.Event()  # 创建一个事件
        message_queue = Queue()  # 消息

        create_ws_thread = WebSocketThread(merchant_token=merchant_token, event_obj=event_obj,
                                           channel=mock_state, queue=message_queue)
        create_ws_thread.start()
        event_obj.wait()
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', login_callback.url_pattern, json=login_callback.mock_success)
            m.register_uri('GET', info_callback.url_pattern, json=info_callback.mock_success)
            # url = "/api/merchant/add_cashier/wechat_auth_redirect/"
            url = reverse('add_cashier-wechat_auth_redirect')

            cashier_scan_code_resp = self.test_case.client.get(url, data={"code": mock_code,
                                                                          'state': mock_state})

            create_ws_thread.join()
            if message_queue.empty():
                logger.error("message_queue is empty, web-socket not receive message")
                raise Exception("message_queue is empty, web-socket not receive message")
            msg = message_queue.get()
            message_info = json.loads(msg['message'])

            #  添加收银员
            # url = "/api/merchant/cashier/"
            url = reverse('cashier-list')
            self.test_case.client.credentials(HTTP_TOKEN=merchant_token)
            data = dict(
                wechat_openid=message_info['openid'],
                wechat_unionid=message_info['unionid'],
                wechat_avatar_url=message_info['headimgurl'],
                wechat_nickname=message_info['nickname']
            )
            resp = self.test_case.client.post(url, data=data)

            return dict(cashier_scan_code_resp=cashier_scan_code_resp,
                        socket_message_info=message_info,
                        merchant_add_cashier_resp=resp)

    def remove_cashier(self, merchant_token, cashier_id):
        # url = f'/api/merchant/cashier/{cashier_id}/remove/'
        url = reverse('cashier-remove', args=[cashier_id])
        self.test_case.client.credentials(HTTP_TOKEN=merchant_token)
        resp = self.test_case.client.get(url)
        return resp

    def get_all_cashiers(self, merchant_token):
        # url = '/api/merchant/cashier/'
        url = reverse('cashier-list')
        self.test_case.client.credentials(HTTP_TOKEN=merchant_token)
        resp = self.test_case.client.get(url)
        return resp


class CashierStep:
    def __init__(self, test_case, token):
        self.test_case = test_case
        self.token = token

    def remove(self, cashier_id):
        # url = '/api/merchant/cashier/{}/remove/'.format(cashier_id)
        url = reverse('cashier-remove', args=[cashier_id])
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def list(self):
        url = reverse('cashier-list')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def create(self, wechat_openid, wechat_unionid, wechat_avatar_url, wechat_nickname):
        url = reverse('cashier-list')
        data = dict(
            wechat_openid=wechat_openid,
            wechat_unionid=wechat_unionid,
            wechat_avatar_url=wechat_avatar_url,
            wechat_nickname=wechat_nickname,
        )
        response = self.test_case.client.post(url, data=data, Token=self.token, format='json')
        return response


class CouponStep:

    def __init__(self, test_case, token):
        self.test_case = test_case
        self.token = token

    def list(self):
        # url = reverse('couponrule-list')
        url = reverse('coupon-list')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def retrieve(self, coupon_rule_id):
        # url = '/api/merchant/coupon/{}/'.format(coupon_rule_id)
        url = reverse('coupon-detail', args=[coupon_rule_id])
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def create(self, discount=None, min_charge=None, stock=None, valid_strategy=None,
               start_date=None, end_date=None, expiration_days=None, photo_url=None, note=None):
        # url = '/api/merchant/coupon/'
        url = reverse('coupon-list')
        data = dict(
            discount=discount,
            min_charge=min_charge,
            valid_strategy=valid_strategy,
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            expiration_days=expiration_days,
            photo_url=photo_url,
            note=note
        )
        data = {k: v for k, v in data.items() if v is not None}
        response = self.test_case.client.post(url, data=data, Token=self.token, format='json')
        return response

    def update(self, coupon_rule_id, stock):
        # url = '/api/merchant/coupon/{}/'.format(coupon_rule_id)
        url = reverse('coupon-detail', args=[coupon_rule_id])
        response = self.test_case.client.put(url, data=dict(stock=stock), Token=self.token,
                                             format='json')
        return response


class MerchantStep:

    def __init__(self, test_case, token=None):
        self.test_case = test_case
        self.token = token

    def statistics(self):
        url = reverse('merchant-statistics')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def count(self, start_date: str, end_date: str):
        """
        :param start_date: '%Y-%m-%d'
        :param end_date: '%Y-%m-%d'
        """
        url = reverse('merchant-count')
        response = self.test_case.client.get(
            url, {'start_date': start_date, 'end_date': end_date}, Token=self.token, format='json')
        return response

    def info(self):
        url = reverse('merchant-info')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def day_begin_minute(self, day_begin_minute: int):
        url = reverse('merchant-day-begin-minute')
        response = self.test_case.client.put(
            url, data={'day_begin_minute': day_begin_minute}, Token=self.token, format='json')
        return response

    def me(self):
        url = reverse('merchant-me')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def modify(self, name=None, category=None, photo_url=None, description=None, contact_phone=None,
               area=None,
               location_lon=None, location_lat=None, address=None, id_card_front_url=None,
               id_card_back_url=None,
               license_url=None):
        url = reverse('merchant-modify')
        data = dict(
            name=name,
            category=category,
            photo_url=photo_url,
            description=description,
            contact_phone=contact_phone,
            area=area,
            location_lon=location_lon,
            location_lat=location_lat,
            address=address,
            id_card_front_url=id_card_front_url,
            id_card_back_url=id_card_back_url,
            license_url=license_url,
        )
        data = {k: v for k, v in data if v is not None}
        response = self.test_case.client.put(url, data=data, Token=self.token, format='json')
        return response

    def category(self):
        url = reverse('merchant-category')
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def balance(self):
        url = reverse('merchant-balance')
        response = self.test_case.client.get(url, Token=self.token)
        return response


class MerchantLoginMockStep:

    def __init__(self, test_case):
        self.test_case = test_case

    def login(self, code, *args, **kwargs):
        code_to_session_callback = WXCode2SessionCallback(code,
                                                          mocked_openid=kwargs.get('mocked_openid',
                                                                                   None),
                                                          mocked_session_key=kwargs.get(
                                                              'mocked_session_key', None),
                                                          mocked_unionid=kwargs.get(
                                                              'mocked_unionid', None),
                                                          validate=kwargs.get('validate', None)
                                                          )
        pattern = re.compile(r'^https://api\.weixin\.qq\.com/sns/jscode2session\?.+$')
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', pattern, json=code_to_session_callback.mock_success)
            url = reverse('merchant-admin-login')
            json_resp = self.test_case.client.post(url, data={'code': code}, format='json')
            return json_resp


class TransactionStep:
    def __init__(self, test_case, token=None, app_id=None, mch_id=None):
        self.test_case = test_case
        self.token = token
        self.app_id = app_id
        self.mch_id = mch_id

    def list(self, page=1):
        url = reverse('transaction-list')
        response = self.test_case.client.get(url, dict(page=page), Token=self.token)
        return response

    def retrieve(self, transaction_id):
        # url = '/api/merchant/transaction/{}/'.format(transaction_id)
        url = reverse('transaction', args=[transaction_id])
        response = self.test_case.client.get(url, Token=self.token)
        return response

    def update(self, transaction_id, note):
        # url = '/api/merchant/transaction/{}/'.format(transaction_id)
        url = reverse('transaction', args=[transaction_id])
        response = self.test_case.client.put(url, data=dict(note=note), Token=self.token,
                                             format='json')
        return response

    def refund(self, payment_id):
        pattern_wechat = re.compile(r'^https://api\.mch\.weixin\.qq\.com/secapi/pay/refund$')
        pattern_alipay = re.compile(r'^https://openapi\.alipaydev\.com/gateway\.do\?'
                                    r'.*method=alipay\.trade\.refund.*$')
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern_wechat,
                           text=WechatPayCallback(self.app_id, self.mch_id).mock_refund_success)
            m.register_uri('POST', pattern_alipay,
                           text=AlipayPaymentCallback().mock_refund_success)
            url = reverse('transaction-refund', args=[payment_id])
            response = self.test_case.client.get(url, Token=self.token, format='json')
            return response

    def alipay_refund(self, admin_token=None, payment_serial_number=None):
        pattern = re.compile(r'^https://openapi\.alipaydev\.com/gateway\.do\?'
                             r'.*method=alipay\.trade\.refund.*$')
        
        def validate(request):
            params = parse_qs(request.query)
            biz_content = json.loads(params['biz_content'][0])
            out_trade_no = biz_content['out_trade_no']
            self.test_case.assertEqual(payment_serial_number, out_trade_no)
            return True
        
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern, text=AlipayPaymentCallback(validate=validate).mock_refund_success)
            url = reverse('transaction-refund', args=[payment_serial_number])
            response = self.test_case.client.get(url, Token=admin_token, format='json')
            return response

    def withdraw(self, channel, amount, admin_token=None):
        pattern_alipay = re.compile(r'^https://openapi\.alipaydev\.com/gateway\.do\?'
                             r'.*method=alipay\.fund\.trans\.toaccount\.transfer')
        pattern_wechat = re.compile(r'https://api\.mch\.weixin\.qq\.com/'
                                    r'mmpaymkttransfers/promotion/transfers')

        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('POST', pattern_alipay,
                           text=AlipayPaymentCallback().mock_withdraw_success)
            m.register_uri('POST', pattern_wechat,
                           text=WechatPayCallback(self.app_id, self.mch_id).mock_withdraw_success)

            url = reverse('merchant-withdraw')
            response = self.test_case.client.put(
                url,
                data=dict(channel=channel, amount=amount),
                Token=admin_token, format='json')
            return response