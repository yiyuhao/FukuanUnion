#      File: alipay.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from time import sleep

from django import db
from django.db import transaction
from django.db.models import OuterRef, Exists
from django.utils import timezone
from dynaconf import settings as dynasettings

from common.doclink.alipay_apis import AlipayApis
from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.models import Payment, Refund, Coupon, Withdraw, Account, Marketer, Merchant, \
    Transaction, TransferRecord
from common.payment.base import PaymentBaseUseCases
from common.payment.exceptions import InvalidStatusError, BalanceInsufficient
from common.payment.util import generate_serial_number
from config import PAY_CHANNELS, PAYMENT_STATUS, REFUND_STATUS, PLATFORM_SHARE_RATE, \
    INVITER_SHARE_RATE, ORIGINATOR_SHARE_RATE, COUPON_STATUS, WITHDRAW_STATUS, MERCHANT_ADMIN_TYPES, \
    TRANSACTION_TYPE, WITHDRAW_TYPE, TRANSFER_STATUS, PLATFORM_ACCOUNT_ID


class AlipayUseCases(PaymentBaseUseCases):
    api_cls = AlipayApis

    def __init__(self):
        self.api_instance = self.api_cls(
            app_id=dynasettings.ALIPAY_APP_ID,
            private_key=dynasettings.ALIPAY_APP_PRIVATE_KEY,
            alipay_public_key=dynasettings.ALIPAY_PUBLIC_KEY
        )

    def place_order(self,
                    client,
                    merchant,
                    coupon,
                    order_price,
                    notify_url):
        """
        Place a pre-payment order.
        :param client: client instance, required
        :param merchant: merchant instance, required
        :param coupon: coupon instance, optional
        :param order_price:
        :param notify_url:
        :return:
        :raises: db.DatabaseError, ApiRequestError, ApiReturnedError
        """
        paid_price = order_price - coupon.discount if coupon else order_price

        with transaction.atomic():
            # update coupon status
            if coupon:
                updated = Coupon.objects.filter(
                    id=coupon.id, status=COUPON_STATUS.NOT_USED
                ).update(status=COUPON_STATUS.USED, use_datetime=timezone.now())

                if not updated:
                    raise InvalidStatusError()

            # Create the payment record
            new_payment = Payment.objects.create(
                serial_number=generate_serial_number(),
                pay_channel=PAY_CHANNELS['ALIPAY'],
                status=PAYMENT_STATUS['UNPAID'],
                merchant=merchant,
                client=client,
                coupon=coupon,
                order_price=order_price,
                platform_share=round(max(0, paid_price) * PLATFORM_SHARE_RATE) if coupon else 0,
                inviter_share=round(max(0, paid_price) * INVITER_SHARE_RATE) if coupon else 0,
                originator_share=round(max(0, paid_price) * ORIGINATOR_SHARE_RATE) if coupon else 0,
            )

            try:
                result = self.api_instance.place_order(
                    notify_url=notify_url,
                    order_title=merchant.name,
                    payment_serial_number=new_payment.serial_number,
                    total_amount=paid_price,
                    buyer_id=client.openid
                )
            except (ApiRequestError, ApiReturnedError):
                # if error occurs, send a query request to check the order.
                sleep(1)
                result = self.api_instance.query_payment(new_payment.serial_number)

            return result

    def request_refund(self, payment):
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(serial_number=payment.serial_number)

            if payment.status == PAYMENT_STATUS['FROZEN']:
                new_refund = Refund.objects.create(
                    serial_number=generate_serial_number(),
                    status=REFUND_STATUS['REQUESTED'],
                    payment=payment
                )
            elif payment.status == PAYMENT_STATUS['REFUND_FAILED']:
                new_refund = Refund.objects.select_for_update().get(payment=payment)
                new_refund.status = REFUND_STATUS['REQUESTED']
                new_refund.save()
            else:
                raise InvalidStatusError()

            payment.status = PAYMENT_STATUS['REFUND_REQUESTED']
            payment.save()

            paid_price = payment.order_price - payment.coupon.discount if payment.coupon else payment.order_price

        try:
            result = self.api_instance.refund(
                payment_serial_number=payment.serial_number,
                refund_serial_number=new_refund.serial_number,
                refund_amount=paid_price
            )
            self.on_refund_success(new_refund)
            return result

        except (ApiRequestError, ApiReturnedError) as e:
            self.on_refund_fail(new_refund)
            raise e

    def cancel_order(self, payment):
        """
        Cancel the order
        :param payment:
        :return: InvalidStatusError, ApiRequestError, ApiReturnedError
        """
        with transaction.atomic():
            coupon = None
            if payment.coupon_id:
                coupon = Coupon.objects.select_for_update().get(id=payment.coupon_id)

            payment = Payment.objects.select_for_update().get(
                serial_number=payment.serial_number)

            if payment.status != PAYMENT_STATUS.UNPAID:
                raise InvalidStatusError()

            payment.status = PAYMENT_STATUS['CANCELLED']
            payment.save()

            self.api_instance.cancel(payment.serial_number)

            if coupon:  # 有使用优惠券的情况，设置原优惠券为销毁状态，并退给用户一张新的优惠券
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
                return new_coupon
            else:
                return None

    def withdraw(self, account, amount):
        """

        :param account:
        :param amount:
        :return:
        :raises: BalanceInsufficient, ApiRequestError, ApiReturnedError
        """
        try:
            self._try_withdraw(account, amount)
        except (BalanceInsufficient, ApiRequestError, ApiReturnedError) as e:
            timestamp = timezone.now()

            Withdraw.objects.create(
                serial_number=generate_serial_number(),
                status=WITHDRAW_STATUS['FAILED'],
                withdraw_type=WITHDRAW_TYPE.ALIPAY,
                datetime=timestamp,
                account=account,
                amount=amount
            )
            raise e

    def _try_withdraw(self, account, amount):
        with transaction.atomic():
            timestamp = timezone.now()
            account = Account.objects.select_for_update().annotate(
                has_merchant=Exists(Merchant.objects.filter(
                    account=OuterRef('id')
                ))).annotate(
                has_marketer=Exists(Marketer.objects.filter(
                    account=OuterRef('id')
                ))).get(id=account.id)

            if account.alipay_withdrawable_balance < amount:
                raise BalanceInsufficient()

            new_withdraw = Withdraw.objects.create(
                serial_number=generate_serial_number(),
                status=WITHDRAW_STATUS['FINISHED'],
                withdraw_type=WITHDRAW_TYPE.ALIPAY,
                datetime=timestamp,
                account=account,
                amount=amount
            )

            if account.has_merchant:
                merchant_admin = account.merchant.admins.get(
                    merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN)
                alipay_userid = merchant_admin.alipay_userid
                alipay_real_name = None
                transaction_type = TRANSACTION_TYPE.MERCHANT_WITHDRAW
            elif account.has_marketer:
                alipay_userid = account.marketer.alipay_id
                alipay_real_name = account.marketer.name
                transaction_type = TRANSACTION_TYPE.MARKETER_WITHDRAW
            else:
                raise db.DatabaseError("Don't know the owner of the account.")

            result = self.api_instance.pay_to_alipay(
                new_withdraw.serial_number,
                receiver_alipay_id=alipay_userid,
                amount=amount,
                desc="付款联盟提现",
                payee_type='ALIPAY_USERID' if account.has_merchant else 'ALIPAY_LOGONID',
                payee_real_name=alipay_real_name
            )

            account.alipay_withdrawable_balance = account.alipay_withdrawable_balance - amount
            account.alipay_balance = account.alipay_balance - amount
            account.save()

            Transaction.objects.create(
                content_object=new_withdraw,
                transaction_type=transaction_type,
                datetime=timestamp,
                account=account,
                amount=-amount,
                balance_after_transaction=account.alipay_balance
            )

            return result

    def transfer(self, unionid, account_number, account_name, amount):
        """
        check the alipay account
        :param unionid:
        :param account_number:
        :param account_name:
        :param amount:
        :return:
        :raises: BalanceInsufficient, ApiRequestError, ApiReturnedError
        """
        try:
            self._try_transfer(unionid, account_number, account_name, amount)
        except (BalanceInsufficient, ApiRequestError, ApiReturnedError) as e:
            timestamp = timezone.now()

            TransferRecord.objects.create(
                serial_number=generate_serial_number(),
                account_number=account_number,
                account_name=account_name,
                wechat_unionid=unionid,
                status=TRANSFER_STATUS['FAILED'],
                datetime=timestamp,
                amount=amount
            )

            raise e

    def _try_transfer(self, unionid, account_number, account_name, amount):
        with transaction.atomic():
            timestamp = timezone.now()

            account = Account.objects.select_for_update().get(id=PLATFORM_ACCOUNT_ID)
            if account.alipay_withdrawable_balance < amount:
                raise BalanceInsufficient()

            new_transfer_record = TransferRecord.objects.create(
                serial_number=generate_serial_number(),
                account_number=account_number,
                account_name=account_name,
                wechat_unionid=unionid,
                status=TRANSFER_STATUS['FINISHED'],
                datetime=timestamp,
                amount=amount
            )

            result = self.api_instance.pay_to_alipay(
                generate_serial_number(),
                receiver_alipay_id=account_number,
                payee_real_name=account_name,
                amount=amount,
                desc="付款联盟邀请人支付宝账号验证",
                payee_type='ALIPAY_LOGONID'
            )

            account.alipay_withdrawable_balance = account.alipay_withdrawable_balance - amount
            account.alipay_balance = account.alipay_balance - amount
            account.save()

            Transaction.objects.create(
                content_object=new_transfer_record,
                transaction_type=TRANSACTION_TYPE.MARKETER_ALIPAY_ACCOUNT_AUTH,
                datetime=timestamp,
                account=account,
                amount=-amount,
                balance_after_transaction=account.alipay_balance
            )

            return result
