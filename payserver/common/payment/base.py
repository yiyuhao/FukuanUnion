#      File: base.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging

from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone

import config
from common.model_manager.account_proxy import AccountProxy
from common.models import Payment, Transaction, Refund, CouponRule, Coupon
from common.payment.exceptions import InvalidStatusError
from common.payment.util import PayChannelContext
from common.utils import distance, metre_to_degree
from config import COUPON_STATUS, PAYMENT_STATUS, PLATFORM_ACCOUNT_ID, TRANSACTION_TYPE, \
    REFUND_STATUS

logger = logging.getLogger(__name__)


class PaymentBaseUseCases(object):
    @classmethod
    def on_payment_success(cls, payment):
        """
        :param payment:
        :return:
        """
        with PayChannelContext(payment.pay_channel):
            with transaction.atomic():
                timestamp = timezone.now()

                platform_account = AccountProxy.objects.select_for_update().get(
                    id=PLATFORM_ACCOUNT_ID)
                merchant_account = AccountProxy.objects.select_for_update().get(
                    id=payment.merchant.account.id)
                payment = Payment.objects.select_for_update().get(
                    serial_number=payment.serial_number)

                if payment.status != PAYMENT_STATUS['UNPAID']:
                    raise InvalidStatusError()  # Duplicated callback
                payment.status = PAYMENT_STATUS['FROZEN']
                payment.save()

                if not payment.coupon:  # 没有使用优惠券的情况
                    merchant_account.channel_balance = merchant_account.channel_balance + payment.order_price
                    merchant_account.save()

                    Transaction.objects.bulk_create([
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_RECEIVE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=payment.order_price,
                            balance_after_transaction=platform_account.channel_balance + payment.order_price
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_RECEIVE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-payment.order_price,
                            balance_after_transaction=platform_account.channel_balance
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                            datetime=timestamp,
                            account=merchant_account,
                            amount=payment.order_price,
                            balance_after_transaction=merchant_account.channel_balance
                        )
                    ])
                else:  # 使用了优惠券的情况
                    paid_price = payment.order_price - payment.coupon.discount
                    total_share = payment.platform_share + payment.inviter_share + payment.originator_share

                    platform_account.channel_balance = platform_account.channel_balance + total_share
                    platform_account.save()
                    merchant_account.channel_balance = merchant_account.channel_balance + paid_price - total_share
                    merchant_account.save()

                    Transaction.objects.bulk_create([
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_RECEIVE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=paid_price,
                            balance_after_transaction=platform_account.channel_balance + paid_price - total_share
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_RECEIVE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-(paid_price - total_share),
                            balance_after_transaction=platform_account.channel_balance
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                            datetime=timestamp,
                            account=merchant_account,
                            amount=paid_price - total_share,
                            balance_after_transaction=merchant_account.channel_balance
                        )
                    ])

    @classmethod
    def on_refund_success(cls, refund):

        with transaction.atomic():
            timestamp = timezone.now()

            platform_account = AccountProxy.objects.select_for_update().get(
                id=PLATFORM_ACCOUNT_ID)
            merchant_account = AccountProxy.objects.select_for_update().get(
                id=refund.payment.merchant.account.id)

            coupon = refund.payment.coupon
            if coupon:
                coupon = Coupon.objects.select_for_update().get(id=coupon.id)

            payment = Payment.objects.select_for_update().get(
                serial_number=refund.payment.serial_number)
            refund = Refund.objects.select_for_update().get(serial_number=refund.serial_number)

            with PayChannelContext(payment.pay_channel):
                if refund.status != REFUND_STATUS['REQUESTED'] \
                        or payment.status != PAYMENT_STATUS['REFUND_REQUESTED']:
                    raise InvalidStatusError()

                refund.status = REFUND_STATUS['FINISHED']
                refund.save()

                payment.status = PAYMENT_STATUS['REFUND']
                payment.save()

                if not coupon:  # 没有使用优惠券
                    merchant_account.channel_balance = merchant_account.channel_balance - payment.order_price
                    merchant_account.save()

                    Transaction.objects.bulk_create([
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'],
                            datetime=timestamp,
                            account=merchant_account,
                            amount=-payment.order_price,
                            balance_after_transaction=merchant_account.channel_balance
                        ),
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EARNING_MERCHANT_REFUND'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=payment.order_price,
                            balance_after_transaction=platform_account.channel_balance + payment.order_price
                        ),
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_REFUND'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-payment.order_price,
                            balance_after_transaction=platform_account.channel_balance
                        )
                    ])
                else:  # 有使用优惠券的情况
                    paid_price = payment.order_price - payment.coupon.discount
                    total_share = payment.platform_share + payment.inviter_share + payment.originator_share

                    merchant_account.channel_balance = merchant_account.channel_balance - (
                            paid_price - total_share)
                    merchant_account.save()

                    platform_account.channel_balance = platform_account.channel_balance - total_share
                    platform_account.save()

                    Transaction.objects.bulk_create([
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'],
                            datetime=timestamp,
                            account=merchant_account,
                            amount=-(paid_price - total_share),
                            balance_after_transaction=merchant_account.channel_balance
                        ),
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EARNING_MERCHANT_REFUND'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=(paid_price - total_share),
                            balance_after_transaction=platform_account.channel_balance + paid_price
                        ),
                        Transaction(
                            content_object=refund,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_REFUND'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-paid_price,
                            balance_after_transaction=platform_account.channel_balance
                        )
                    ])

                    # 设置原优惠券为销毁状态，并退给用户一张新的优惠券
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

    @classmethod
    def on_refund_fail(cls, refund):
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                serial_number=refund.payment.serial_number)
            refund = Refund.objects.select_for_update().get(serial_number=refund.serial_number)

            if refund.status != REFUND_STATUS['REQUESTED'] \
                    or payment.status != PAYMENT_STATUS['REFUND_REQUESTED']:
                raise InvalidStatusError()

            refund.status = REFUND_STATUS['FAILED']
            refund.save()

            payment.status = PAYMENT_STATUS['REFUND_FAILED']
            payment.save()

    @classmethod
    def grant_coupons(cls, payment, longitude, latitude, accuracy):
        if not all([longitude, latitude, accuracy]):  # 如果没有定到位，则使用商户位置
            longitude = payment.merchant.location_lon
            latitude = payment.merchant.location_lat
            accuracy = 0

        updated = Payment.objects.filter(serial_number=payment.serial_number,
                                         status=config.PAYMENT_STATUS.FROZEN,
                                         coupon_granted=False
                                         ).update(coupon_granted=True)
        if not updated:
            return []

        if accuracy > config.GRANT_COUPON_DISTANCE:  # accuracy too low
            return []

        now = timezone.now()
        now_date = now.date()

        selected_rules = CouponRule.objects.filter(
            merchant__location_lon__gte=longitude - metre_to_degree(config.GRANT_COUPON_DISTANCE),
            merchant__location_lon__lte=longitude + metre_to_degree(config.GRANT_COUPON_DISTANCE),
            merchant__location_lat__gte=latitude - metre_to_degree(config.GRANT_COUPON_DISTANCE),
            merchant__location_lat__lte=latitude + metre_to_degree(config.GRANT_COUPON_DISTANCE),
            merchant__status=config.MERCHANT_STATUS.USING,
            stock__gt=0,
        ).exclude(merchant_id=payment.merchant_id).filter(
            Q(valid_strategy=config.VALID_STRATEGY.EXPIRATION) | Q(
                end_date__gte=now_date)).order_by('?')

        result = []
        for rule in selected_rules:
            if len(result) >= 3:
                return result
            if distance(rule.merchant.location_lon, rule.merchant.location_lat, longitude,
                        latitude) > config.GRANT_COUPON_DISTANCE:  # 前面是初步筛选，这里精确筛选
                continue
            updated = CouponRule.objects.filter(id=rule.id, stock__gt=0).update(
                stock=F('stock') - 1)
            if updated:
                coupon = Coupon.objects.create(
                    rule=rule,
                    client=payment.client,
                    discount=rule.discount,
                    min_charge=rule.min_charge,
                    originator_merchant=payment.merchant,
                    status=config.COUPON_STATUS.NOT_USED
                )

                result.append(coupon)
        else:
            return result

    @classmethod
    def on_payment_unfreeze(cls, payment):
        """
        unfreeze payment.
        :param payment:
        :return:
        :raise: InvalidStatusError
        """
        with PayChannelContext(payment.pay_channel):
            with transaction.atomic():
                timestamp = timezone.now()
                accounts = None
                merchant_account = None

                if payment.coupon:  # 使用了优惠券的情况
                    merchant_account_id = payment.merchant.account_id
                    originator_account_id = payment.coupon.originator_merchant.account_id
                    inviter_account_id = payment.merchant.inviter.account_id

                    accounts = AccountProxy.objects.select_for_update().filter(id__in=(
                        PLATFORM_ACCOUNT_ID, merchant_account_id, originator_account_id,
                        inviter_account_id))
                else:
                    merchant_account_id = payment.merchant.account_id
                    merchant_account = AccountProxy.objects.select_for_update().get(
                        id=merchant_account_id)

                payment = Payment.objects.select_for_update().select_related('coupon').get(
                    serial_number=payment.serial_number)

                if payment.status != PAYMENT_STATUS.FROZEN:
                    raise InvalidStatusError()

                if payment.coupon:  # 使用了优惠券的情况
                    accounts = {a.id: a for a in accounts}
                    if len(accounts) != 4:
                        logger.error('Cannot find all the accounts:{}'.format(repr((
                            PLATFORM_ACCOUNT_ID, merchant_account_id, originator_account_id,
                            inviter_account_id))))
                        raise AccountProxy.DoesNotExist()

                    platform_account = accounts[PLATFORM_ACCOUNT_ID]
                    merchant_account = accounts[merchant_account_id]
                    originator_account = accounts[originator_account_id]
                    inviter_account = accounts[inviter_account_id]

                    platform_account.channel_balance -= payment.originator_share + payment.inviter_share
                    platform_account.save()

                    originator_account.channel_balance += payment.originator_share
                    originator_account.channel_withdrawable_balance += payment.originator_share
                    originator_account.save()

                    inviter_account.channel_balance += payment.inviter_share
                    inviter_account.channel_withdrawable_balance += payment.inviter_share
                    inviter_account.save()

                    payment.status = PAYMENT_STATUS.FINISHED
                    payment.save()

                    merchant_account.channel_withdrawable_balance += payment.order_price - payment.coupon.discount - sum(
                        (payment.platform_share,
                         payment.originator_share,
                         payment.inviter_share))
                    merchant_account.save()

                    # 记录Transaction
                    Transaction.objects.bulk_create([
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MERCHANT_SHARE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-payment.originator_share,
                            balance_after_transaction=platform_account.channel_balance + payment.inviter_share
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_MARKETER_SHARE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-payment.inviter_share,
                            balance_after_transaction=platform_account.channel_balance
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_EXPEND_PLATFORM_SHARE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=-payment.platform_share,
                            balance_after_transaction=platform_account.channel_balance - payment.platform_share
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['PLATFORM_SHARE'],
                            datetime=timestamp,
                            account=platform_account,
                            amount=payment.platform_share,
                            balance_after_transaction=platform_account.channel_balance
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'],
                            datetime=timestamp,
                            account=originator_account,
                            amount=payment.originator_share,
                            balance_after_transaction=originator_account.channel_balance
                        ),
                        Transaction(
                            content_object=payment,
                            transaction_type=TRANSACTION_TYPE['MARKETER_SHARE'],
                            datetime=timestamp,
                            account=inviter_account,
                            amount=payment.inviter_share,
                            balance_after_transaction=inviter_account.channel_balance
                        )
                    ])

                else:  # 没有使用优惠券的情况
                    payment.status = PAYMENT_STATUS.FINISHED
                    payment.save()

                    merchant_account.channel_withdrawable_balance += payment.order_price
                    merchant_account.save()
