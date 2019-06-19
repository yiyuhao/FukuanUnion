#      File: test_wechat_pay.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from dynaconf import settings as dynasettings

from common.models import Payment, Account, Refund, Withdraw
from common.payment.exceptions import BalanceInsufficient
from common.payment.wechat import WechatPaymentUseCases
from config import PAYMENT_STATUS, PAY_CHANNELS, PLATFORM_SHARE_RATE, INVITER_SHARE_RATE, \
    ORIGINATOR_SHARE_RATE, TRANSACTION_TYPE, REFUND_STATUS, MERCHANT_ADMIN_TYPES, COUPON_STATUS, \
    WITHDRAW_STATUS
from test.unittest.fake_factory import PayunionFactory


class WechatPayTestCases(TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.factory = PayunionFactory()

    def setUp(self):
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

        self.client = self.factory.create_client(openid='1234567890')
        self.merchant = self.factory.create_merchant(account=self.merchant_account,
                                                     inviter=self.inviter)
        self.originator = self.factory.create_merchant(account=self.originator_account)
        self.rule = self.factory.create_coupon_rule(merchant=self.merchant)
        self.coupon = self.factory.create_coupon(rule=self.rule, client=self.client,
                                                 originator_merchant=self.originator,
                                                 min_charge=1000, discount=100,
                                                 status=COUPON_STATUS['NOT_USED'])

        self.merchant_admin = self.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,
            work_merchant=self.merchant
        )

    def test_place_order(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def place_order(self, order_title, payment_serial_number,
                            total_fee, spbill_create_ip, notify_url, openid):
                assert notify_url == 'http://test.com'
                assert order_title == self.test_case.merchant.name
                assert len(payment_serial_number) == 32
                assert total_fee == 1900
                assert openid == self.test_case.client.openid
                assert spbill_create_ip == '111.222.111.222'

                return {'prepay_id': 'prepay_id123'}

            def generate_client_payment_params(self, prepay_id):
                assert prepay_id == 'prepay_id123'
                return 'place_order_success'

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        result = wechat_pay_usecases.place_order(
            self.client,
            self.merchant,
            self.coupon,
            2000,
            '111.222.111.222',
            'http://test.com',
        )
        assert result['client_payment_params'] == 'place_order_success'
        assert len(result['payment_serial_number']) == 32

        new_payment = Payment.objects.all().order_by('-datetime')[0]

        assert new_payment
        assert len(new_payment.serial_number) == 32
        assert len(new_payment.transactions.all()) == 0
        assert (timezone.now() - new_payment.datetime) < timedelta(seconds=30)
        assert new_payment.pay_channel == PAY_CHANNELS.WECHAT
        assert new_payment.merchant_id == self.merchant.id
        assert new_payment.status == PAYMENT_STATUS.UNPAID
        assert new_payment.client_id == self.client.id
        assert new_payment.order_price == 2000
        assert new_payment.coupon_id == self.coupon.id
        assert new_payment.platform_share == round(1900 * PLATFORM_SHARE_RATE)
        assert new_payment.inviter_share == round(1900 * INVITER_SHARE_RATE)
        assert new_payment.originator_share == round(1900 * ORIGINATOR_SHARE_RATE)
        assert new_payment.note is None

    def test_place_order_without_coupon(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def place_order(self, order_title, payment_serial_number,
                            total_fee, spbill_create_ip, notify_url, openid):
                assert notify_url == 'http://test.com'
                assert order_title == self.test_case.merchant.name
                assert len(payment_serial_number) == 32
                assert total_fee == 2000
                assert openid == self.test_case.client.openid
                assert spbill_create_ip == '111.222.111.222'

                return {'prepay_id': 'prepay_id123'}

            def generate_client_payment_params(self, prepay_id):
                assert prepay_id == 'prepay_id123'
                return 'place_order_success'

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        result = wechat_pay_usecases.place_order(
            self.client,
            self.merchant,
            None,
            2000,
            '111.222.111.222',
            'http://test.com',
        )
        assert result['client_payment_params'] == 'place_order_success'
        assert len(result['payment_serial_number']) == 32

        new_payment = Payment.objects.all().order_by('-datetime')[0]

        assert new_payment
        assert len(new_payment.serial_number) == 32
        assert len(new_payment.transactions.all()) == 0
        assert (timezone.now() - new_payment.datetime) < timedelta(seconds=30)
        assert new_payment.pay_channel == PAY_CHANNELS.WECHAT
        assert new_payment.merchant_id == self.merchant.id
        assert new_payment.status == PAYMENT_STATUS.UNPAID
        assert new_payment.client_id == self.client.id
        assert new_payment.order_price == 2000
        assert new_payment.coupon is None
        assert new_payment.platform_share == 0
        assert new_payment.inviter_share == 0
        assert new_payment.originator_share == 0
        assert new_payment.note is None

    def test_cancel_order(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def cancel(self, payment_serial_number):
                assert len(payment_serial_number) == 32
                return 'cancel_order_success'

        self.test_place_order()

        new_payment = Payment.objects.all().order_by('-datetime')[0]

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        new_coupon = wechat_pay_usecases.cancel_order(new_payment)

        # Check the payment data
        payment = Payment.objects.get(serial_number=new_payment.serial_number)
        assert payment.serial_number == new_payment.serial_number
        assert len(payment.transactions.all()) == 0
        assert payment.status == PAYMENT_STATUS.CANCELLED
        assert payment.coupon.status == COUPON_STATUS.DESTROYED

        assert new_coupon.rule == payment.coupon.rule
        assert new_coupon.client == payment.coupon.client
        assert new_coupon.discount == payment.coupon.discount
        assert new_coupon.min_charge == payment.coupon.min_charge
        assert new_coupon.originator_merchant == payment.coupon.originator_merchant
        assert new_coupon.status == COUPON_STATUS.NOT_USED
        assert new_coupon.obtain_datetime == payment.coupon.obtain_datetime
        assert new_coupon.use_datetime is None

    def test_cancel_order_without_coupon(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def cancel(self, payment_serial_number):
                assert len(payment_serial_number) == 32
                return 'cancel_order_success'

        self.test_place_order_without_coupon()

        new_payment = Payment.objects.all().order_by('-datetime')[0]

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        new_coupon = wechat_pay_usecases.cancel_order(new_payment)

        # Check the payment data
        payment = Payment.objects.get(serial_number=new_payment.serial_number)
        assert payment.serial_number == new_payment.serial_number
        assert len(payment.transactions.all()) == 0
        assert payment.status == PAYMENT_STATUS.CANCELLED
        assert payment.coupon is None

        assert new_coupon is None

    def test_on_payment_success(self):
        self.test_place_order()
        new_payment = Payment.objects.all().order_by('-datetime')[0]
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_payment_success(new_payment)

        # Check the payment data
        payment = Payment.objects.get(serial_number=new_payment.serial_number)
        assert payment.serial_number == new_payment.serial_number
        assert len(payment.transactions.all()) == 3
        assert payment.datetime == new_payment.datetime
        assert payment.pay_channel == PAY_CHANNELS.WECHAT
        assert payment.status == PAYMENT_STATUS.FROZEN
        assert payment.merchant_id == self.merchant.id
        assert payment.client_id == self.client.id
        assert payment.order_price == 2000
        assert payment.coupon_id == self.coupon.id
        assert payment.platform_share == round(1900 * PLATFORM_SHARE_RATE)
        assert payment.inviter_share == round(1900 * INVITER_SHARE_RATE)
        assert payment.originator_share == round(1900 * ORIGINATOR_SHARE_RATE)
        assert payment.note is None

        # Check the transactions.
        transactions = payment.transactions.all().order_by('id')
        assert transactions[0].object_id == payment.serial_number
        assert transactions[0].content_object.serial_number == payment.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.PLATFORM_RECEIVE
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.platform_account.id
        assert transactions[0].amount == 1900
        assert transactions[0].balance_after_transaction == 1900

        assert transactions[1].object_id == payment.serial_number
        assert transactions[1].content_object.serial_number == payment.serial_number
        assert transactions[1].transaction_type == TRANSACTION_TYPE.PLATFORM_EXPEND_MERCHANT_RECEIVE
        assert (timezone.now() - transactions[1].datetime) < timedelta(seconds=30)
        assert transactions[1].account_id == self.platform_account.id
        assert transactions[1].amount == - 1900 + (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert transactions[1].balance_after_transaction == (
                payment.platform_share + payment.inviter_share + payment.originator_share)

        assert transactions[2].object_id == payment.serial_number
        assert transactions[2].content_object.serial_number == payment.serial_number
        assert transactions[2].transaction_type == TRANSACTION_TYPE.MERCHANT_RECEIVE
        assert (timezone.now() - transactions[2].datetime) < timedelta(seconds=30)
        assert transactions[2].account_id == self.merchant_account.id
        assert transactions[2].amount == 1900 - (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert transactions[2].balance_after_transaction == 1900 - (
                payment.platform_share + payment.inviter_share + payment.originator_share)

        # Check the account
        self.platform_account.refresh_from_db()
        self.merchant_account.refresh_from_db()
        assert self.platform_account.balance == (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert self.platform_account.withdrawable_balance == 0

        assert self.merchant_account.balance == 1900 - (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert self.merchant_account.withdrawable_balance == 0

    def test_on_payment_success_without_coupon(self):
        self.test_place_order_without_coupon()
        new_payment = Payment.objects.all().order_by('-datetime')[0]
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_payment_success(new_payment)

        # Check the payment data
        payment = Payment.objects.get(serial_number=new_payment.serial_number)
        assert payment.serial_number == new_payment.serial_number
        assert len(payment.transactions.all()) == 3
        assert payment.datetime == new_payment.datetime
        assert payment.pay_channel == PAY_CHANNELS.WECHAT
        assert payment.status == PAYMENT_STATUS.FROZEN
        assert payment.merchant_id == self.merchant.id
        assert payment.client_id == self.client.id
        assert payment.order_price == 2000
        assert payment.coupon is None
        assert payment.platform_share == 0
        assert payment.inviter_share == 0
        assert payment.originator_share == 0
        assert payment.note is None

        # Check the transactions.
        transactions = payment.transactions.all().order_by('id')
        assert transactions[0].object_id == payment.serial_number
        assert transactions[0].content_object.serial_number == payment.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.PLATFORM_RECEIVE
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.platform_account.id
        assert transactions[0].amount == 2000
        assert transactions[0].balance_after_transaction == 2000

        assert transactions[1].object_id == payment.serial_number
        assert transactions[1].content_object.serial_number == payment.serial_number
        assert transactions[1].transaction_type == TRANSACTION_TYPE.PLATFORM_EXPEND_MERCHANT_RECEIVE
        assert (timezone.now() - transactions[1].datetime) < timedelta(seconds=30)
        assert transactions[1].account_id == self.platform_account.id
        assert transactions[1].amount == - 2000
        assert transactions[1].balance_after_transaction == 0

        assert transactions[2].object_id == payment.serial_number
        assert transactions[2].content_object.serial_number == payment.serial_number
        assert transactions[2].transaction_type == TRANSACTION_TYPE.MERCHANT_RECEIVE
        assert (timezone.now() - transactions[2].datetime) < timedelta(seconds=30)
        assert transactions[2].account_id == self.merchant_account.id
        assert transactions[2].amount == 2000
        assert transactions[2].balance_after_transaction == 2000

        # Check the account
        self.platform_account.refresh_from_db()
        self.merchant_account.refresh_from_db()
        assert self.platform_account.balance == 0
        assert self.platform_account.withdrawable_balance == 0

        assert self.merchant_account.balance == 2000
        assert self.merchant_account.withdrawable_balance == 0

    def test_refund(self):
        self.test_on_payment_success()
        payment = Payment.objects.all().order_by('-datetime')[0]

        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY
                self.payment = payment

            def refund(self, payment_serial_number, refund_serial_number, total_fee, refund_fee,
                       notify_url):
                assert payment_serial_number == self.payment.serial_number
                assert len(refund_serial_number) == 32
                assert total_fee == 1900
                assert refund_fee == 1900
                assert notify_url == 'http://test.com'
                return 'refund_request_success'

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        result = wechat_pay_usecases.request_refund(payment, notify_url='http://test.com')
        assert result == 'refund_request_success'

        # Check the refund data
        refund = Refund.objects.all().order_by('-datetime')[0]
        assert len(refund.serial_number) == 32
        assert len(refund.transactions.all()) == 0
        assert (timezone.now() - refund.datetime) < timedelta(seconds=30)
        assert refund.status == REFUND_STATUS.REQUESTED
        assert refund.payment.serial_number == payment.serial_number

    def test_on_refund_success(self):
        self.test_refund()
        refund = Refund.objects.all().order_by('-datetime')[0]

        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_refund_success(refund)

        # Check the payment data
        payment = Payment.objects.all().order_by('-datetime')[0]
        assert payment.status == PAYMENT_STATUS.REFUND

        # Check the refund
        refund.refresh_from_db()
        assert len(refund.serial_number) == 32
        assert len(refund.transactions.all()) == 3
        assert (timezone.now() - refund.datetime) < timedelta(seconds=30)
        assert refund.status == REFUND_STATUS.FINISHED
        assert refund.payment.serial_number == payment.serial_number

        # Check the transactions.
        transactions = refund.transactions.all().order_by('id')
        assert transactions[0].object_id == refund.serial_number
        assert transactions[0].content_object.serial_number == refund.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.MERCHANT_REFUND
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.merchant_account.id
        assert transactions[0].amount == -1900 + (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert transactions[0].balance_after_transaction == 0

        assert transactions[1].object_id == refund.serial_number
        assert transactions[1].content_object.serial_number == refund.serial_number
        assert transactions[1].transaction_type == TRANSACTION_TYPE.PLATFORM_EARNING_MERCHANT_REFUND
        assert (timezone.now() - transactions[1].datetime) < timedelta(seconds=30)
        assert transactions[1].account_id == self.platform_account.id
        assert transactions[1].amount == 1900 - (
                payment.platform_share + payment.inviter_share + payment.originator_share)
        assert transactions[1].balance_after_transaction == 1900

        assert transactions[2].object_id == refund.serial_number
        assert transactions[2].content_object.serial_number == refund.serial_number
        assert transactions[2].transaction_type == TRANSACTION_TYPE.PLATFORM_REFUND
        assert (timezone.now() - transactions[2].datetime) < timedelta(seconds=30)
        assert transactions[2].account_id == self.platform_account.id
        assert transactions[2].amount == -1900
        assert transactions[2].balance_after_transaction == 0

        # Check the account
        self.platform_account.refresh_from_db()
        self.merchant_account.refresh_from_db()
        assert self.platform_account.balance == 0
        assert self.platform_account.withdrawable_balance == 0

        assert self.merchant_account.balance == 0
        assert self.merchant_account.withdrawable_balance == 0

        # check the coupon
        self.assertEqual(payment.coupon.status, COUPON_STATUS.DESTROYED)

        coupon = payment.coupon
        new_coupon = payment.coupon.client.coupon_set.exclude(
            status=COUPON_STATUS.DESTROYED).first()
        self.assertEqual(new_coupon.rule, coupon.rule)
        self.assertEqual(new_coupon.discount, coupon.discount)
        self.assertEqual(new_coupon.min_charge, coupon.min_charge)
        self.assertEqual(new_coupon.originator_merchant, coupon.originator_merchant)
        self.assertEqual(new_coupon.status, COUPON_STATUS.NOT_USED)
        self.assertEqual(new_coupon.obtain_datetime, coupon.obtain_datetime)

    def test_refund_without_coupon(self):
        self.test_on_payment_success_without_coupon()
        payment = Payment.objects.all().order_by('-datetime')[0]

        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY
                self.payment = payment

            def refund(self, payment_serial_number, refund_serial_number, total_fee, refund_fee,
                       notify_url):
                assert payment_serial_number == self.payment.serial_number
                assert len(refund_serial_number) == 32
                assert total_fee == 2000
                assert refund_fee == 2000
                assert notify_url == 'http://test.com'
                return 'refund_request_success'

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        result = wechat_pay_usecases.request_refund(payment, notify_url='http://test.com')
        assert result == 'refund_request_success'

        # Check the refund data
        refund = Refund.objects.all().order_by('-datetime')[0]
        assert len(refund.serial_number) == 32
        assert len(refund.transactions.all()) == 0
        assert (timezone.now() - refund.datetime) < timedelta(seconds=30)
        assert refund.status == REFUND_STATUS.REQUESTED
        assert refund.payment.serial_number == payment.serial_number

    def test_on_refund_success_without_coupon(self):
        self.test_refund_without_coupon()
        refund = Refund.objects.all().order_by('-datetime')[0]

        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_refund_success(refund)

        # Check the payment data
        payment = Payment.objects.all().order_by('-datetime')[0]
        assert payment.status == PAYMENT_STATUS.REFUND

        # Check the refund
        refund.refresh_from_db()
        assert len(refund.serial_number) == 32
        assert len(refund.transactions.all()) == 3
        assert (timezone.now() - refund.datetime) < timedelta(seconds=30)
        assert refund.status == REFUND_STATUS.FINISHED
        assert refund.payment.serial_number == payment.serial_number

        # Check the transactions.
        transactions = refund.transactions.all().order_by('id')
        assert transactions[0].object_id == refund.serial_number
        assert transactions[0].content_object.serial_number == refund.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.MERCHANT_REFUND
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.merchant_account.id
        assert transactions[0].amount == -2000
        assert transactions[0].balance_after_transaction == 0

        assert transactions[1].object_id == refund.serial_number
        assert transactions[1].content_object.serial_number == refund.serial_number
        assert transactions[1].transaction_type == TRANSACTION_TYPE.PLATFORM_EARNING_MERCHANT_REFUND
        assert (timezone.now() - transactions[1].datetime) < timedelta(seconds=30)
        assert transactions[1].account_id == self.platform_account.id
        assert transactions[1].amount == 2000
        assert transactions[1].balance_after_transaction == 2000

        assert transactions[2].object_id == refund.serial_number
        assert transactions[2].content_object.serial_number == refund.serial_number
        assert transactions[2].transaction_type == TRANSACTION_TYPE.PLATFORM_REFUND
        assert (timezone.now() - transactions[2].datetime) < timedelta(seconds=30)
        assert transactions[2].account_id == self.platform_account.id
        assert transactions[2].amount == -2000
        assert transactions[2].balance_after_transaction == 0

        # Check the account
        self.platform_account.refresh_from_db()
        self.merchant_account.refresh_from_db()
        assert self.platform_account.balance == 0
        assert self.platform_account.withdrawable_balance == 0

        assert self.merchant_account.balance == 0
        assert self.merchant_account.withdrawable_balance == 0

    def test_merchant_withdraw(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def pay_to_wechat(self, partner_trade_no, openid, amount, desc,
                              spbill_create_ip, app_id=None):
                assert len(partner_trade_no) == 32
                assert openid == self.test_case.merchant_admin.wechat_openid
                assert amount == 1000
                assert desc == '付款联盟提现'
                assert spbill_create_ip == '111.222.111.222'
                return 'refund_request_success'

        self.merchant_account.balance = 10000
        self.merchant_account.withdrawable_balance = 5000
        self.merchant_account.save()

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.withdraw(self.merchant_account, 1000, '111.222.111.222')

        withdraw = Withdraw.objects.all().order_by('-datetime')[0]

        # Check withdraw
        assert len(withdraw.serial_number) == 32
        assert len(withdraw.transactions.all()) == 1
        assert (timezone.now() - withdraw.datetime) < timedelta(seconds=30)
        assert withdraw.account_id == self.merchant_account.id
        assert withdraw.amount == 1000
        assert withdraw.status == WITHDRAW_STATUS.FINISHED

        # Check the transaction
        transactions = withdraw.transactions.all().order_by('id')
        assert transactions[0].object_id == withdraw.serial_number
        assert transactions[0].content_object.serial_number == withdraw.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.MERCHANT_WITHDRAW
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.merchant_account.id
        assert transactions[0].amount == -1000
        assert transactions[0].balance_after_transaction == 9000

        # Check the balance
        self.merchant_account.refresh_from_db()
        assert self.merchant_account.balance == 9000
        assert self.merchant_account.withdrawable_balance == 4000

    def test_merchant_withdraw_insufficient(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def pay_to_wechat(self, partner_trade_no, openid, amount, desc,
                              spbill_create_ip, app_id=None):
                assert len(partner_trade_no) == 32
                assert openid == self.test_case.merchant_admin.wechat_openid
                assert true_name == self.test_case.merchant_account.real_name
                assert amount == 1000
                assert desc == '付款联盟提现'
                assert spbill_create_ip == '111.222.111.222'
                return 'refund_request_success'

        self.merchant_account.balance = 10000
        self.merchant_account.withdrawable_balance = 500
        self.merchant_account.save()

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()

        self.assertRaises(BalanceInsufficient, wechat_pay_usecases.withdraw, self.merchant_account,
                          1000, '111.222.111.222')

        withdraw = Withdraw.objects.all().order_by('-datetime')[0]

        # Check withdraw
        assert len(withdraw.serial_number) == 32
        assert len(withdraw.transactions.all()) == 0
        assert (timezone.now() - withdraw.datetime) < timedelta(seconds=30)
        assert withdraw.account_id == self.merchant_account.id
        assert withdraw.amount == 1000
        assert withdraw.status == WITHDRAW_STATUS.FAILED

        # Check the balance
        self.merchant_account.refresh_from_db()
        assert self.merchant_account.balance == 10000
        assert self.merchant_account.withdrawable_balance == 500

    def test_inviter_withdraw(self):
        class WechatPayApisMock(object):
            test_case = self

            def __init__(self, app_id, mch_id, mch_key, wechat_public_key, cert=None,
                         cert_key=None):
                assert app_id == dynasettings.CLIENT_MINI_APP_ID
                assert mch_id == dynasettings.WECHAT_MERCHANT_ID
                assert mch_key == dynasettings.WECHAT_MERCHANT_API_KEY
                assert wechat_public_key == dynasettings.WECHAT_PUBLIC_KEY
                assert cert is None or cert == dynasettings.WECHAT_MERCHANT_CERT
                assert cert_key is None or cert_key == dynasettings.WECHAT_MERCHANT_CERT_KEY

            def pay_to_wechat(self, partner_trade_no, openid, amount, desc,
                              spbill_create_ip, app_id=None):
                assert len(partner_trade_no) == 32
                assert openid == self.test_case.inviter.wechat_openid
                assert amount == 1000
                assert desc == '付款联盟提现'
                assert spbill_create_ip == '111.222.111.222'
                return 'refund_request_success'

        self.inviter_account.balance = 100000
        self.inviter_account.withdrawable_balance = 50000
        self.inviter_account.save()

        WechatPaymentUseCases.api_cls = WechatPayApisMock
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.withdraw(self.inviter_account, 1000, '111.222.111.222')

        withdraw = Withdraw.objects.all().order_by('-datetime')[0]

        # Check withdraw
        assert len(withdraw.serial_number) == 32
        assert len(withdraw.transactions.all()) == 1
        assert (timezone.now() - withdraw.datetime) < timedelta(seconds=30)
        assert withdraw.account_id == self.inviter_account.id
        assert withdraw.amount == 1000
        assert withdraw.status == WITHDRAW_STATUS.FINISHED

        # Check the transaction
        transactions = withdraw.transactions.all().order_by('id')
        assert transactions[0].object_id == withdraw.serial_number
        assert transactions[0].content_object.serial_number == withdraw.serial_number
        assert transactions[0].transaction_type == TRANSACTION_TYPE.MARKETER_WITHDRAW
        assert (timezone.now() - transactions[0].datetime) < timedelta(seconds=30)
        assert transactions[0].account_id == self.inviter_account.id
        assert transactions[0].amount == -1000
        assert transactions[0].balance_after_transaction == 99000

        # Check the balance
        self.inviter_account.refresh_from_db()
        assert self.inviter_account.balance == 99000
        assert self.inviter_account.withdrawable_balance == 49000

    def test_payment_unfreeze(self):
        self.test_on_payment_success()
        new_payment = Payment.objects.all().order_by('-datetime')[0]
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_payment_unfreeze(new_payment)

        new_payment.refresh_from_db()
        assert new_payment.status == PAYMENT_STATUS.FINISHED

        self.platform_account.refresh_from_db()
        assert self.platform_account.balance == new_payment.platform_share
        assert self.platform_account.withdrawable_balance == 0

        self.merchant_account.refresh_from_db()
        assert self.merchant_account.balance == 1900 - sum((
            new_payment.platform_share, new_payment.inviter_share, new_payment.originator_share))
        assert self.merchant_account.withdrawable_balance == 1900 - sum((
            new_payment.platform_share, new_payment.inviter_share, new_payment.originator_share))

        self.inviter_account.refresh_from_db()
        assert self.inviter_account.balance == new_payment.inviter_share
        assert self.inviter_account.withdrawable_balance == new_payment.inviter_share

        self.originator_account.refresh_from_db()
        assert self.originator_account.balance == new_payment.originator_share
        assert self.originator_account.withdrawable_balance == new_payment.originator_share

    def test_payment_unfreeze_without_coupon(self):
        self.test_on_payment_success_without_coupon()

        new_payment = Payment.objects.all().order_by('-datetime')[0]
        wechat_pay_usecases = WechatPaymentUseCases()
        wechat_pay_usecases.on_payment_unfreeze(new_payment)

        new_payment.refresh_from_db()
        assert new_payment.status == PAYMENT_STATUS.FINISHED

        self.platform_account.refresh_from_db()
        assert self.platform_account.balance == 0
        assert self.platform_account.withdrawable_balance == 0

        self.merchant_account.refresh_from_db()
        assert self.merchant_account.balance == 2000
        assert self.merchant_account.withdrawable_balance == 2000

        self.inviter_account.refresh_from_db()
        assert self.inviter_account.balance == 0
        assert self.inviter_account.withdrawable_balance == 0

        self.originator_account.refresh_from_db()
        assert self.originator_account.balance == 0
        assert self.originator_account.withdrawable_balance == 0
