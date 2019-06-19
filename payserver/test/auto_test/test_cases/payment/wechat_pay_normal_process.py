# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import json
import uuid
from urllib.parse import parse_qs

from django.utils import timezone
from dynaconf import settings as dynasettings
from redis import StrictRedis
from rest_framework.test import APITestCase

import config
from common.models import Account, Coupon, Refund
from config import COUPON_STATUS, MERCHANT_ADMIN_TYPES, MERCHANT_STATUS, VALID_STRATEGY
from payserver.celery_config import BROKER_URL
from test.auto_test.steps.client import ClientSteps
from test.auto_test.steps.merchant import MerchantLoginMockStep, MerchantStep, TransactionStep
from test.auto_test.steps.shared_pay import SharedPaySteps
from test.auto_test.steps.wechat_pay import WechatPaySteps
from test.unittest.fake_factory import PayunionFactory


class TestWechatPaySteps(APITestCase):
    def setUp(self):
        self.factory = PayunionFactory()

        try:
            self.platform_account = Account.objects.get(id=1)
        except Account.DoesNotExist:
            self.platform_account = self.factory.create_account(id=1, balance=0,
                                                                withdrawable_balance=0,
                                                                alipay_balance=0,
                                                                alipay_withdrawable_balance=0)
        self.originator_account = self.factory.create_account(real_name='引流商户', balance=0,
                                                              withdrawable_balance=0,
                                                              alipay_balance=0,
                                                              alipay_withdrawable_balance=0)
        self.merchant_account = self.factory.create_account(real_name='收款', balance=0,
                                                            withdrawable_balance=0,
                                                            alipay_balance=0,
                                                            alipay_withdrawable_balance=0)
        self.inviter_account = self.factory.create_account(real_name='邀请人', balance=0,
                                                           withdrawable_balance=0,
                                                           alipay_balance=0,
                                                           alipay_withdrawable_balance=0)
        self.inviter = self.factory.create_marketer(account=self.inviter_account)

        self.test_client = self.factory.create_client(openid='1234567890', status=0)
        self.merchant = self.factory.create_merchant(account=self.merchant_account,
                                                     inviter=self.inviter,
                                                     status=MERCHANT_STATUS.USING)
        self.originator = self.factory.create_merchant(account=self.originator_account)
        self.rule = self.factory.create_coupon_rule(merchant=self.merchant,
                                                    valid_strategy=VALID_STRATEGY.EXPIRATION,
                                                    expiration_days=30)
        self.coupon = self.factory.create_coupon(rule=self.rule, client=self.test_client,
                                                 originator_merchant=self.originator,
                                                 min_charge=1000, discount=100,
                                                 obtain_datetime=timezone.now(),
                                                 status=COUPON_STATUS['NOT_USED'])

        self.merchant_admin = self.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,
            work_merchant=self.merchant
        )
        super(TestWechatPaySteps, self).setUpTestData()

    def test_workflow(self):
        client_steps = ClientSteps()

        # Login
        code = uuid.uuid4().hex

        def validate(request):
            params = parse_qs(request.query)
            self.assertEqual(params['appid'][0], dynasettings.CLIENT_MINI_APP_ID)
            self.assertEqual(params['secret'][0], dynasettings.CLIENT_MINI_APP_SECRET)
            self.assertEqual(params['js_code'][0], code)
            self.assertEqual(params['grant_type'][0], 'authorization_code')
            return True

        login_result = client_steps.wechat_login(code,
                                                 self.test_client.openid,
                                                 's84hYB8FH2ck1sayryNbCg==',
                                                 self.test_client.wechat_unionid,
                                                 validate=validate)
        access_token = login_result['access_token']
        self.assertEqual(len(access_token), 32)

        # Get user info
        me_info = client_steps.me(access_token)
        assert me_info

        # Set phone number
        set_phone_result = client_steps.set_phone(
            access_token,
            iv='hfN9fRyw7F4oezqYRAzj8g==',
            encrypted_data='InF6jgIwHeH2ov7KqGhMXGD5w4Km464346EWahygQ56VM6tqEP9uJCSbgZhV6ar/nw'
                           'NLnW1vh04ngYyNWVm1JiM6PD6AD9/A5SS4DgsiPGcbVqlixkWbsLbNciW0uTbLT2PM'
                           'S4yEGiih+G/wGojToxh0hfivGo/AdgmXtKjbGrzB7aF9S6bHY0V9QF8Q+LxwcNrc+r'
                           'DxZXYVFYc9TgJIaw==')
        self.assertEqual(set_phone_result, {'phone_known': True})

        # Get all coupons
        coupons = client_steps.get_coupons(access_token)
        self.assertEqual(len(coupons), 1)
        self.assertEqual(coupons[0]['id'], self.coupon.id)
        self.assertEqual(coupons[0]['rule']['merchant']['name'], self.merchant.name)
        self.assertEqual(coupons[0]['discount'], self.coupon.discount)
        self.assertEqual(coupons[0]['min_charge'], self.coupon.min_charge)

        # Get merchant info
        merchant_info = client_steps.get_merchant_info(access_token,
                                                       self.merchant.payment_qr_code.uuid)
        self.assertTrue(merchant_info)
        self.assertTrue(merchant_info['id'])
        self.assertTrue(merchant_info['name'])
        self.assertTrue(merchant_info['description'])
        self.assertTrue(merchant_info['avatar_url'])
        self.assertTrue(isinstance(merchant_info['status'], int))

        # Place order
        wechat_pay_steps = WechatPaySteps(
            access_token,
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID)
        shared_pay_stpes = SharedPaySteps(access_token)

        place_order_result = wechat_pay_steps.place_order(
            self.merchant.id, 1000,
            self.coupon.id)

        assert place_order_result
        self.assertEqual(place_order_result['client_payment_params']['appId'],
                         dynasettings.CLIENT_MINI_APP_ID)
        self.assertEqual(len(place_order_result['client_payment_params']['timeStamp']), 10)
        self.assertEqual(len(place_order_result['client_payment_params']['nonceStr']), 32)
        self.assertEqual(len(place_order_result['client_payment_params']['paySign']), 32)
        self.assertEqual(len(place_order_result['client_payment_params']['package']), 46)
        self.assertIn('prepay_id=', place_order_result['client_payment_params']['package'])
        self.assertEqual(len(place_order_result['payment_serial_number']), 32)

        # Cancel the order
        cancel_order_result = wechat_pay_steps.cancel_order(
            place_order_result['payment_serial_number'])
        assert cancel_order_result['new_coupon']
        self.coupon = Coupon.objects.get(id=cancel_order_result['new_coupon']['id'])
        assert self.coupon

        # Place another order
        wechat_pay_steps = WechatPaySteps(
            access_token,
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID)
        place_order_result = wechat_pay_steps.place_order(
            self.merchant.id, 1000,
            self.coupon.id)

        assert place_order_result
        self.assertEqual(place_order_result['client_payment_params']['appId'],
                         dynasettings.CLIENT_MINI_APP_ID)
        self.assertEqual(len(place_order_result['client_payment_params']['timeStamp']), 10)
        self.assertEqual(len(place_order_result['client_payment_params']['nonceStr']), 32)
        self.assertEqual(len(place_order_result['client_payment_params']['paySign']), 32)
        self.assertEqual(len(place_order_result['client_payment_params']['package']), 46)
        self.assertIn('prepay_id=', place_order_result['client_payment_params']['package'])
        self.assertEqual(len(place_order_result['payment_serial_number']), 32)

        poll_result_result = shared_pay_stpes.poll_result(
            place_order_result['payment_serial_number'],
            None, None, None
        )
        assert poll_result_result['payment']['status'] == 0

        # Payment callback
        callback_response = wechat_pay_steps.payment_callback(
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID,
            self.test_client.openid,
            place_order_result['payment_serial_number'],
            900,
        )
        assert 'SUCCESS' in str(callback_response.content)

        poll_result_result = shared_pay_stpes.poll_result(
            place_order_result['payment_serial_number'],
            None, None, None
        )
        assert poll_result_result['payment']['status'] == 1

        # login merchant
        resp = MerchantLoginMockStep(self).login(unionid=self.merchant_admin.wechat_unionid)
        token = resp.json()['token']

        # get merchant info
        me = MerchantStep(self, token=token).me().json()
        self.assertEqual(me['name'], self.merchant.name)

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.FROZEN)

        # refund
        refund_result = TransactionStep(self, token=token).refund(
            payment_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(refund_result, {})

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.REFUND_REQUESTED)

        # refund callback
        refund_callback_result = wechat_pay_steps.refund_callback(
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID,
            place_order_result['payment_serial_number'],
            Refund.objects.get(
                payment__serial_number=place_order_result['payment_serial_number']).serial_number,
            900
        )
        self.assertTrue('SUCCESS' in str(refund_callback_result.content))

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.REFUND)

        # ********************************************
        # Place another to test status sync
        place_order_result = wechat_pay_steps.place_order(
            self.merchant.id, 1000,
            None)

        # Payment callback
        wechat_pay_steps.payment_callback(
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID,
            self.test_client.openid,
            place_order_result['payment_serial_number'],
            1000,
        )

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.FROZEN)

        # Sync refund status, expects nothing happens, because no refund in process.
        redis_cli = StrictRedis.from_url(BROKER_URL)
        queue_length = redis_cli.llen('payunion')
        wechat_pay_steps.refund_status_sync()
        queue_length1 = redis_cli.llen('payunion')
        self.assertEqual(queue_length, queue_length1)

        # refund
        refund_result = TransactionStep(self, token=token).refund(
            payment_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(refund_result, {})

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.REFUND_REQUESTED)

        # Sync refund status
        redis_cli = StrictRedis.from_url(BROKER_URL)
        queue_length = redis_cli.llen('payunion')
        wechat_pay_steps.refund_status_sync()
        queue_length1 = redis_cli.llen('payunion')
        self.assertEqual(queue_length + 1, queue_length1)
        task_info = redis_cli.lpop('payunion')
        task_info = json.loads(task_info)
        self.assertEqual(task_info['headers']['task'], 'puser.tasks.wechat_refund_status_sync')
        self.assertEqual(task_info['headers']['argsrepr'],
                         repr((Refund.objects.get(
                             payment__serial_number=place_order_result[
                                 'payment_serial_number']).serial_number,)))

        # Because celery is not started, call the task directly
        wechat_pay_steps.call_task_refund_status_sync(Refund.objects.get(
            payment__serial_number=place_order_result[
                'payment_serial_number']).serial_number)

        # get order detail
        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.REFUND)

        # ********************************************
        # Place another to test unfreeze
        place_order_result = wechat_pay_steps.place_order(
            self.merchant.id, 1000,
            Coupon.objects.filter(client=self.test_client).order_by('-id').first().id)

        # Payment callback
        wechat_pay_steps.payment_callback(
            dynasettings.CLIENT_MINI_APP_ID,
            dynasettings.WECHAT_MERCHANT_ID,
            self.test_client.openid,
            place_order_result['payment_serial_number'],
            900,
        )

        # Unfreeze and check result.
        shared_pay_stpes.unfreeze_immediately()

        order_detail = TransactionStep(self, token=token).retrieve(
            transaction_id=place_order_result['payment_serial_number']).json()
        self.assertEqual(order_detail['status'], config.PAYMENT_STATUS.FINISHED)
