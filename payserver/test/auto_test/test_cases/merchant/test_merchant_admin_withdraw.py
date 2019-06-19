#!/usr/bin/python3
#
#   Project: payunion
#    Author: Tian Xu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid

from dynaconf import settings as dynasettings

import config
from common import models
from common.model_manager.payment_manager import alipay_payment
from common.model_manager.utils import set_amount
from common.models import Account, Area, MerchantAdmin
from test.auto_test.steps.alipay import AlipayPaymentSteps
from test.auto_test.steps.client import ClientSteps
from test.auto_test.steps.common_object import WechatPerson, fake
from test.auto_test.steps.inviter import GetUserInfoStep
from test.auto_test.steps.merchant import TransactionStep
from test.auto_test.steps.shared_pay import SharedPaySteps
from test.auto_test.steps.system_admin import LoginStep, FinancialQueryStep
from test.auto_test.test_cases.merchant.merchant_clinet_test_base import \
    MerchantClientTestBase
from test.auto_test.workflows.pre_inviter import GenerateInviterWorkflow
from test.test_config import AutoTestConfig
from test.unittest.fake_factory import PayunionFactory
from test.unittest.system_admin.base_data import create_base_data


class TestMerchantWithdraw(MerchantClientTestBase):

    def setUp(self):
        self.ALIPAY_PUBLIC_KEY_backup = dynasettings.ALIPAY_PUBLIC_KEY
        dynasettings.ALIPAY_PUBLIC_KEY = AutoTestConfig.self_generated_alipay_public_key
        alipay_payment.api_instance.alipay_public_key = AutoTestConfig.self_generated_alipay_public_key
        create_base_data()

        self.factory = PayunionFactory()
        try:
            self.platform_account = Account.objects.get(id=1)
        except Account.DoesNotExist:
            self.platform_account = self.factory.create_account(
                id=1,
                balance=100,
                withdrawable_balance=100,
                alipay_balance=100,
                alipay_withdrawable_balance=100)

        merchant_data = dict(
            address_info=dict(
                adcode='510107062000',
                address='成都市武侯区锦城大道666号奥克斯广场F1',
                location_lon=30.57592,
                location_lat=104.06147
            ),
            merchant_name='提现测试商户',
            merchant_acct_data=dict(
                bank_name="工商银行",
                bank_card_number='622312131213121',
                real_name="提现测试"
            ),
        )

        inviter_workflow = GenerateInviterWorkflow(self)
        new_work_ids = [area.id for area in
                        Area.objects.filter(parent__name='武侯区')]
        salesman_info = dict(
            set_salesman=True,
            system_admin_name='admin@mishitu.com',
            system_admin_password='123456',
            new_work_ids=new_work_ids,
            worker_number='00001'
        )
        res_info = inviter_workflow.generate_inviter(name='提现测试邀请人a',
                                                     salesman_info=salesman_info)
        res_data = inviter_workflow.invite_merchant(
            inviter_token=res_info['token'],
            merchant_info=merchant_data)

        inviter_workflow.aduit_merchant(config.MERCHANT_STATUS.USING,
                                        token=res_info['token'],
                                        merchant_id=res_data['merchant_id'])

        self.merchant_info = res_data

        super(TestMerchantWithdraw, self).setUpTestData()

    @staticmethod
    def set_account_balance(account_instance, amount, channel):
        """
        为instance设置金额
        :param account_instance: Account实例
        :param amount:  设置的金额
        :param channel:  相关渠道
        :return: account对象
        """
        assert isinstance(account_instance, Account)
        amount = set_amount(amount)

        if channel == config.PAY_CHANNELS.ALIPAY:
            account_instance.alipay_balance = amount
            account_instance.alipay_withdrawable_balance = amount
        elif channel == config.PAY_CHANNELS.WECHAT:
            account_instance.balance = amount
            account_instance.withdrawable_balance = amount
        else:
            assert channel in (config.PAY_CHANNELS.WECHAT,
                               config.PAY_CHANNELS.ALIPAY)

        account_instance.save()
        return account_instance

    def test_merchant_withdraw(self):
        # 商户管理员登录token
        merchant_admin = MerchantAdmin.objects.filter(
            work_merchant_id=self.merchant_info['merchant_id'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN
        ).first()
        merchant_admin_token = self.mock_merchant_admin_or_cashier_login_success(
            WechatPerson(unionid=merchant_admin.wechat_unionid,
                         subscription_openid=merchant_admin.wechat_openid
                         ))

        amounts = {
            'alipay': {
                'lt': 0.5,
                'normal': 10,
                'gt': 50001
            },
            'wechat': {
                'lt': 0.5,
                'normal': 10,
                'gt': 20001
            }
        }
        trans_step = TransactionStep(self, merchant_admin_token)

        # 支付宝提现
        self.set_account_balance(
            account_instance=merchant_admin.work_merchant.account,
            amount=amounts['alipay']['normal'],
            channel=config.PAY_CHANNELS.ALIPAY)

        # 1丶 不可提现金额: 0.5元
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.ALIPAY,
                                   amount=amounts['alipay']['lt'],
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'], 'min_value')

        # 2丶 不可提现金额: 50001元
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.ALIPAY,
                                   amount=amounts['alipay']['gt'],
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'], 'max_value')

        # 3丶 商户可提现余额不足
        account1 = merchant_admin.work_merchant.account
        print(account1.alipay_balance)
        print(account1.alipay_withdrawable_balance)

        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.ALIPAY,
                                   amount=amounts['alipay']['normal'] + 1,
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'],
                         'withdrawable balance is not sufficient')

        # 3丶 正常提现金额: 10元
        if self.platform_account.alipay_withdrawable_balance < \
                amounts['alipay']['normal']:
            self.set_account_balance(
                account_instance=merchant_admin.work_merchant.account,
                amount=amounts['alipay']['normal'],
                channel=config.PAY_CHANNELS.ALIPAY)

        # TODO 支付宝sign data error
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.ALIPAY,
                                   amount=amounts['alipay']['normal'],  # TODO 去掉 +1
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.status_code, 200)

        # 微信提现
        self.set_account_balance(
            account_instance=merchant_admin.work_merchant.account,
            amount=amounts['wechat']['normal'],
            channel=config.PAY_CHANNELS.WECHAT)

        # 1丶 不可提现金额: 0.5元
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.WECHAT,
                                   amount=amounts['wechat']['lt'],
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'], 'min_value')

        # 2丶 不可提现金额: 20001元
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.WECHAT,
                                   amount=amounts['wechat']['gt'],
                                   admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'],
                         'exceeding the wechat maximum withdrawal balance')

        # 3丶 商户可提现余额不足
        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.WECHAT,
                                      amount=amounts['wechat']['normal'] + 1,
                                      admin_token=merchant_admin_token)

        self.assertEqual(resp.data['error_code'],
                         'withdrawable balance is not sufficient')

        # 3丶 正常提现金额: 10元
        if self.platform_account.alipay_withdrawable_balance < \
                amounts['wechat']['normal']:
            self.set_account_balance(
                account_instance=merchant_admin.work_merchant.account,
                amount=amounts['wechat']['normal'],
                channel=config.PAY_CHANNELS.WECHAT)

        resp = trans_step.withdraw(channel=config.PAY_CHANNELS.WECHAT,
                                      amount=amounts['wechat']['normal'],
                                      admin_token=merchant_admin_token)

        self.assertEqual(resp.status_code, 200)
