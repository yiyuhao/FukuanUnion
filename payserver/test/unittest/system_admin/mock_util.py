# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import random

from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import OuterRef, Exists

from common.models import *
from config import *



class TimeUtil(object):
    @classmethod
    def format_time(cls, date_string):
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

class MoneyUtil(object):
    @classmethod
    def yuan_to_fen(cls, yuan):
        return round(100*yuan)

class PaymentUtil(object):
    @classmethod
    def gen_serial_number(cls, t_time):
        return t_time.strftime('%Y%m%d%H%M%S%f') + ('%012d' % random.randint(0, 999999999999))

class MockProcessUtil(object):

    @classmethod
    def mock_get_coupon(cls, client, coupon_rule, obtain_time, originator_merchant):
        new_coupon = Coupon.objects.create(
            rule=coupon_rule,
            client=client,
            discount=coupon_rule.discount,
            min_charge=coupon_rule.min_charge,
            originator_merchant=originator_merchant,
            status=COUPON_STATUS.NOT_USED,
            obtain_datetime=TimeUtil.format_time(obtain_time)
        )

        return new_coupon


    @classmethod
    def mock_request_payment(cls, user_id=None, merchant_id=None, coupon_id=None, order_price=0,
                            pay_time_str=None, pay_way=None):


        client = Client.objects.get(pk=user_id)
        merchant = Merchant.objects.get(pk=merchant_id)
        pay_time = TimeUtil.format_time(pay_time_str)

        coupon = None
        if coupon_id:
            coupon = Coupon.objects.get(pk=coupon_id)
            coupon.status = COUPON_STATUS['USED']
            coupon.use_datetime = pay_time
            coupon.save()


        paid_price = order_price - coupon.discount if coupon else order_price

        new_payment = Payment.objects.create(
            serial_number=PaymentUtil.gen_serial_number(pay_time),
            pay_channel=pay_way, # PAY_CHANNELS['WECHAT'],
            status=PAYMENT_STATUS['UNPAID'],
            merchant=merchant,
            client=client,
            coupon=coupon,
            order_price=order_price,
            datetime=pay_time,
            platform_share=round(max(0, paid_price) * PLATFORM_SHARE_RATE) if coupon else 0,
            inviter_share=round(max(0, paid_price) * INVITER_SHARE_RATE) if coupon else 0,
            originator_share=round(max(0, paid_price) * ORIGINATOR_SHARE_RATE) if coupon else 0,
        )

        return new_payment

    @classmethod
    def mock_on_payment_success(cls, platform_account_id, payment, time_str):
        """ mock_payment """
        with transaction.atomic():
            platform_account = Account.objects.select_for_update().get(id=platform_account_id)
            merchant_account = Account.objects.select_for_update().get(
                id=payment.merchant.account.id)
            payment = Payment.objects.select_for_update().get(serial_number=payment.serial_number)
            timestamp = TimeUtil.format_time(time_str)

            if payment.status != PAYMENT_STATUS['UNPAID']:
                raise Exception("payment's status is invalid") # Duplicated callback
            payment.status = PAYMENT_STATUS['FROZEN']
            payment.save()

            is_wechat_pay = True if payment.pay_channel == PAY_CHANNELS['WECHAT'] else False

            if not payment.coupon:  # 没有使用优惠券的情况
                merchant_account.balance = merchant_account.balance + payment.order_price
                merchant_account.save()

                Transaction.objects.bulk_create([
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_RECEIVE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=payment.order_price,
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) + payment.order_price
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_RECEIVE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-payment.order_price,
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                        datetime=timestamp,
                        account=merchant_account,
                        amount=payment.order_price,
                        balance_after_transaction=merchant_account.balance if is_wechat_pay else merchant_account.alipay_balance
                    )
                ])
            else:  # 使用了优惠券的情况
                paid_price = payment.order_price - payment.coupon.discount
                total_share = payment.platform_share + payment.inviter_share + payment.originator_share

                if is_wechat_pay:
                    platform_account.balance = platform_account.balance + total_share
                    merchant_account.balance = merchant_account.balance + paid_price - total_share
                else:
                    platform_account.alipay_balance = platform_account.alipay_balance + total_share
                    merchant_account.alipay_balance = merchant_account.alipay_balance + paid_price - total_share
                platform_account.save()
                merchant_account.save()

                Transaction.objects.bulk_create([
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_RECEIVE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=paid_price,
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) + paid_price - total_share
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_RECEIVE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-(paid_price - total_share),
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                        datetime=timestamp,
                        account=merchant_account,
                        amount=paid_price - total_share,
                        balance_after_transaction=merchant_account.balance if is_wechat_pay else merchant_account.alipay_balance
                    )
                ])

    @classmethod
    def mock_request_refund(cls, payment, time_str):
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(serial_number=payment.serial_number)

            if payment.status == PAYMENT_STATUS['FROZEN']:
                new_refund = Refund.objects.create(
                    serial_number=PaymentUtil.gen_serial_number(TimeUtil.format_time(time_str)),
                    status=REFUND_STATUS['REQUESTED'],
                    payment=payment,
                    datetime=TimeUtil.format_time(time_str)
                )
            else:
                raise Exception("refund's payment's status is invalid")

            payment.status = PAYMENT_STATUS['REFUND_REQUESTED']
            payment.save()

            return new_refund

    @classmethod
    def mock_on_refund_success(cls,  platform_account_id, refund, time_str):
        with transaction.atomic():
            platform_account = Account.objects.select_for_update().get(id=platform_account_id)
            merchant_account = Account.objects.select_for_update().get(
                id=refund.payment.merchant.account.id)

            payment = Payment.objects.select_for_update().get(
                serial_number=refund.payment.serial_number)
            refund = Refund.objects.select_for_update().get(serial_number=refund.serial_number)
            timestamp = TimeUtil.format_time(time_str)

            if refund.status != REFUND_STATUS['REQUESTED'] \
                    or payment.status != PAYMENT_STATUS['REFUND_REQUESTED']:
                raise Exception("mock_refund failed")

            refund.status = REFUND_STATUS['FINISHED']
            refund.save()

            payment.status = PAYMENT_STATUS['REFUND']
            payment.save()

            is_wechat_pay = True if payment.pay_channel == PAY_CHANNELS['WECHAT'] else False

            if not payment.coupon:  # 没有使用优惠券

                if is_wechat_pay:
                    merchant_account.balance = merchant_account.balance - payment.order_price
                else:
                    merchant_account.alipay_balance = merchant_account.alipay_balance - payment.order_price
                merchant_account.save()

                Transaction.objects.bulk_create([
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'],
                        datetime=timestamp,
                        account=merchant_account,
                        amount=-payment.order_price,
                        balance_after_transaction=merchant_account.balance if is_wechat_pay else merchant_account.alipay_balance
                    ),
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EARNING_MERCHANT_REFUND'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=payment.order_price,
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) + payment.order_price
                    ),
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_REFUND'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-payment.order_price,
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    )
                ])
            else:  # 有使用优惠券的情况
                paid_price = payment.order_price - payment.coupon.discount
                total_share = payment.platform_share + payment.inviter_share + payment.originator_share

                if is_wechat_pay:
                    merchant_account.balance = merchant_account.balance - (paid_price - total_share)
                    platform_account.balance = platform_account.balance - total_share
                else:
                    merchant_account.alipay_balance = merchant_account.alipay_balance - (paid_price - total_share)
                    platform_account.alipay_balance = platform_account.alipay_balance - total_share

                merchant_account.save()
                platform_account.save()

                Transaction.objects.bulk_create([
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'],
                        datetime=timestamp,
                        account=merchant_account,
                        amount=-(paid_price - total_share),
                        balance_after_transaction=merchant_account.balance if is_wechat_pay else merchant_account.alipay_balance
                    ),
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EARNING_MERCHANT_REFUND'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=(paid_price - total_share),
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) + paid_price
                    ),
                    Transaction(
                        content_object=refund,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_REFUND'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-paid_price,
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    )
                ])

                # 设置原优惠券为销毁状态，并退给用户一张新的优惠券
                coupon = Coupon.objects.select_for_update().get(id=payment.coupon_id)
                coupon.status = COUPON_STATUS.DESTROYED
                coupon.save()

                new_coupon = Coupon.objects.create(
                    rule_id=coupon.rule_id,
                    client_id=coupon.client_id,
                    discount=coupon.discount,
                    min_charge=coupon.min_charge,
                    originator_merchant_id=coupon.originator_merchant_id,
                    status=COUPON_STATUS.NOT_USED,
                    obtain_datetime=coupon.obtain_datetime,
                )
                new_coupon.save()

    @classmethod
    def mock_withdraw(cls, account, amount, time_str, withdraw_type):
        with transaction.atomic():
            timestamp = TimeUtil.format_time(time_str)

            is_wechat_pay = True if withdraw_type == WITHDRAW_TYPE['WECHAT'] else False

            account = Account.objects.select_for_update().annotate(
                has_merchant=Exists(Merchant.objects.filter(
                    account=OuterRef('id')
                ))).annotate(
                has_marketer=Exists(Marketer.objects.filter(
                    account=OuterRef('id')
                ))).get(id=account.id)

            if (account.withdrawable_balance if is_wechat_pay else account.alipay_withdrawable_balance) < amount:
                raise Exception("withdrawable_balance less than amount")
            if account.has_merchant:
                transaction_type = TRANSACTION_TYPE.MERCHANT_WITHDRAW
            elif account.has_marketer:
                transaction_type = TRANSACTION_TYPE.MARKETER_WITHDRAW
            else:
                raise Exception("Don't know the owner of the account.")

            new_withdraw = Withdraw.objects.create(
                withdraw_type=WITHDRAW_TYPE['WECHAT'] if is_wechat_pay else WITHDRAW_TYPE['ALIPAY'],
                serial_number=PaymentUtil.gen_serial_number(timestamp),
                status=WITHDRAW_STATUS['PROCESSING'],
                datetime=timestamp,
                account=account,
                amount=amount
            )

            if is_wechat_pay:
                account.withdrawable_balance = account.withdrawable_balance - amount
                account.balance = account.balance - amount
            else:
                account.alipay_withdrawable_balance = account.alipay_withdrawable_balance - amount
                account.alipay_balance = account.alipay_balance - amount
            account.save()

            Transaction.objects.create(
                content_object=new_withdraw,
                transaction_type=transaction_type,
                datetime=timestamp,
                account=account,
                amount=-amount,
                balance_after_transaction=account.balance
            )
            new_withdraw.status = WITHDRAW_STATUS['FINISHED']
            new_withdraw.save()

    @classmethod
    def mock_on_payment_unfreeze(cls, platform_account_id, payment, time_str):
        with transaction.atomic():

            timestamp = TimeUtil.format_time(time_str)
            payment = Payment.objects.select_for_update().select_related('coupon').get(
                serial_number=payment.serial_number)

            if payment.status != PAYMENT_STATUS.FROZEN:
                raise Exception("payment's status is invalid")

            is_wechat_pay = True if payment.pay_channel == PAY_CHANNELS['WECHAT'] else False

            if payment.coupon:  # 使用了优惠券的情况
                merchant_account_id = payment.merchant.account_id
                originator_account_id = payment.coupon.originator_merchant.account_id
                inviter_account_id = payment.merchant.inviter.account_id

                accounts = Account.objects.select_for_update().filter(id__in=(
                    platform_account_id, merchant_account_id, originator_account_id,
                    inviter_account_id))

                accounts = {a.id: a for a in accounts}
                if len(accounts) != 4:
                    raise Account.DoesNotExist()

                platform_account = accounts[platform_account_id]
                merchant_account = accounts[merchant_account_id]
                originator_account = accounts[originator_account_id]
                inviter_account = accounts[inviter_account_id]

                if is_wechat_pay:
                    platform_account.balance -= payment.originator_share + payment.inviter_share
                    originator_account.balance += payment.originator_share
                    originator_account.withdrawable_balance += payment.originator_share
                    inviter_account.balance += payment.inviter_share
                    inviter_account.withdrawable_balance += payment.inviter_share
                    merchant_account.withdrawable_balance += payment.order_price - payment.coupon.discount - sum(
                        (payment.platform_share,
                         payment.originator_share,
                         payment.inviter_share))
                else:
                    platform_account.alipay_balance -= payment.originator_share + payment.inviter_share
                    originator_account.alipay_balance += payment.originator_share
                    originator_account.alipay_withdrawable_balance += payment.originator_share
                    inviter_account.alipay_balance += payment.inviter_share
                    inviter_account.alipay_withdrawable_balance += payment.inviter_share
                    merchant_account.alipay_withdrawable_balance += payment.order_price - payment.coupon.discount - sum(
                        (payment.platform_share,
                         payment.originator_share,
                         payment.inviter_share))

                platform_account.save()
                originator_account.save()
                inviter_account.save()
                merchant_account.save()

                payment.status = PAYMENT_STATUS.FINISHED
                payment.save()


                # 记录Transaction
                Transaction.objects.bulk_create([
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_SHARE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-payment.originator_share,
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) + payment.inviter_share
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MARKETER_SHARE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-payment.inviter_share,
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_PLATFORM_SHARE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=-payment.platform_share,
                        balance_after_transaction=(platform_account.balance if is_wechat_pay
                                                   else platform_account.alipay_balance) - payment.platform_share
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['PLATFORM_SHARE'],
                        datetime=timestamp,
                        account=platform_account,
                        amount=payment.platform_share,
                        balance_after_transaction=platform_account.balance if is_wechat_pay else platform_account.alipay_balance
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'],
                        datetime=timestamp,
                        account=originator_account,
                        amount=payment.originator_share,
                        balance_after_transaction=originator_account.balance if is_wechat_pay else originator_account.alipay_balance
                    ),
                    Transaction(
                        content_object=payment,
                        transaction_type=TRANSACTION_TYPE['MARKETER_SHARE'],
                        datetime=timestamp,
                        account=inviter_account,
                        amount=payment.inviter_share,
                        balance_after_transaction=inviter_account.balance if is_wechat_pay else inviter_account.alipay_balance
                    )
                ])

            else:  # 没有使用优惠券的情况
                merchant_account_id = payment.merchant.account_id
                merchant_account = Account.objects.select_for_update().get(id=merchant_account_id)

                payment.status = PAYMENT_STATUS.FINISHED
                payment.save()

                if is_wechat_pay:
                    merchant_account.withdrawable_balance += payment.order_price
                else:
                    merchant_account.alipay_withdrawable_balance += payment.order_price
                merchant_account.save()

