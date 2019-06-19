#      File: wechat.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django import db
from django.db import transaction
from django.db.models import OuterRef, Exists
from django.utils import timezone
from dynaconf import settings as dynasettings

from common.doclink.exceptions import SignError, ApiRequestError, ApiReturnedError
from common.doclink.wechat_pay_apis import WechatPayApis
from common.models import Payment, Account, Transaction, Refund, Withdraw, Merchant, Marketer, \
    Coupon
from common.payment.base import PaymentBaseUseCases
from common.payment.exceptions import InvalidStatusError, BalanceInsufficient
from common.payment.util import generate_serial_number
from config import PAY_CHANNELS, PAYMENT_STATUS, PLATFORM_SHARE_RATE, TRANSACTION_TYPE, \
    REFUND_STATUS, WITHDRAW_STATUS, INVITER_SHARE_RATE, ORIGINATOR_SHARE_RATE, MERCHANT_ADMIN_TYPES, \
    COUPON_STATUS, WITHDRAW_TYPE


class WechatPaymentUseCases(PaymentBaseUseCases):
    api_cls = WechatPayApis

    def __init__(self):
        self.api_instance_without_cert = self.api_cls(dynasettings.CLIENT_MINI_APP_ID,
                                                      dynasettings.WECHAT_MERCHANT_ID,
                                                      dynasettings.WECHAT_MERCHANT_API_KEY,
                                                      dynasettings.WECHAT_PUBLIC_KEY)

        self.api_instance_with_cert = self.api_cls(dynasettings.CLIENT_MINI_APP_ID,
                                                   dynasettings.WECHAT_MERCHANT_ID,
                                                   dynasettings.WECHAT_MERCHANT_API_KEY,
                                                   dynasettings.WECHAT_PUBLIC_KEY,
                                                   dynasettings.WECHAT_MERCHANT_CERT,
                                                   dynasettings.WECHAT_MERCHANT_CERT_KEY)

    def parse_and_validate_xml_message(self, xml_message):
        """
        Parse and validate the sign of the message.
        :param xml_message:
        :return:
        :raises: xml.etree.ElementTree.ParseError, SignError
        """
        params = self.api_instance_without_cert.parse_xml_message(xml_message)
        if 'sign_type' in params:
            sign_type = params.pop('sign_type')
        else:
            sign_type = 'MD5'

        actual_sign = params.pop('sign')
        self.api_instance_without_cert.sign_message(params, sign_type)
        recalculated_sign = params['sign']

        if actual_sign != recalculated_sign:
            raise SignError('The sign is invalid')
        return params

    def place_order(self, client, merchant, coupon, order_price, client_ip, notify_url):
        """
        Place an pre-payment order.
        :param client: client instance, required
        :param merchant: merchant instance, required
        :param coupon: coupon instance, optional
        :param order_price:
        :param client_ip:
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
                pay_channel=PAY_CHANNELS['WECHAT'],
                status=PAYMENT_STATUS['UNPAID'],
                merchant=merchant,
                client=client,
                coupon=coupon,
                order_price=order_price,
                platform_share=round(max(0, paid_price) * PLATFORM_SHARE_RATE) if coupon else 0,
                inviter_share=round(max(0, paid_price) * INVITER_SHARE_RATE) if coupon else 0,
                originator_share=round(max(0, paid_price) * ORIGINATOR_SHARE_RATE) if coupon else 0,
            )

            result = self.api_instance_without_cert.place_order(
                order_title=merchant.name,
                payment_serial_number=new_payment.serial_number,
                total_fee=order_price - coupon.discount if coupon else order_price,
                spbill_create_ip=client_ip,
                notify_url=notify_url,
                openid=client.openid
            )

            return dict(
                client_payment_params=self.api_instance_without_cert.generate_client_payment_params(
                    result['prepay_id']),
                payment_serial_number=new_payment.serial_number
            )

    def request_refund(self, payment, notify_url):
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
            result = self.api_instance_with_cert.refund(
                payment_serial_number=payment.serial_number,
                refund_serial_number=new_refund.serial_number,
                total_fee=paid_price,
                refund_fee=paid_price,
                notify_url=notify_url
            )
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

            self.api_instance_without_cert.cancel(payment.serial_number)

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

    def withdraw(self, account, amount, client_ip, app_id=None):
        """
        :param account:
        :param amount:
        :param client_ip:
        :param app_id:
        :return:
        :raise: BalanceInsufficient, ApiRequestError, ApiReturnedError
        """
        try:
            self._try_withdraw(account, amount, client_ip, app_id)
        except (BalanceInsufficient, ApiRequestError, ApiReturnedError) as e:
            timestamp = timezone.now()

            Withdraw.objects.create(
                serial_number=generate_serial_number(),
                status=WITHDRAW_STATUS['FAILED'],
                withdraw_type=WITHDRAW_TYPE.WECHAT,
                datetime=timestamp,
                account=account,
                amount=amount
            )
            raise e

    def _try_withdraw(self, account, amount, client_ip, app_id=None):
        """
        :param account:
        :param amount:
        :param client_ip:
        :param app_id:
        :return:
        :raise: BalanceInsufficient, ApiRequestError, ApiReturnedError
        """

        with transaction.atomic():
            timestamp = timezone.now()
            account = Account.objects.select_for_update().annotate(
                has_merchant=Exists(Merchant.objects.filter(
                    account=OuterRef('id')
                ))).annotate(
                has_marketer=Exists(Marketer.objects.filter(
                    account=OuterRef('id')
                ))).get(id=account.id)

            if account.withdrawable_balance < amount:
                raise BalanceInsufficient()

            new_withdraw = Withdraw.objects.create(
                serial_number=generate_serial_number(),
                status=WITHDRAW_STATUS['FINISHED'],
                withdraw_type=WITHDRAW_TYPE.WECHAT,
                datetime=timestamp,
                account=account,
                amount=amount
            )

            if account.has_merchant:
                openid = account.merchant.admins.get(
                    merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN).wechat_openid
                transaction_type = TRANSACTION_TYPE.MERCHANT_WITHDRAW
            elif account.has_marketer:
                openid = account.marketer.wechat_openid
                transaction_type = TRANSACTION_TYPE.MARKETER_WITHDRAW
            else:
                raise db.DatabaseError("Don't know the owner of the account.")

            result = self.api_instance_with_cert.pay_to_wechat(
                partner_trade_no=new_withdraw.serial_number,
                openid=openid,
                amount=amount,
                desc="付款联盟提现",
                spbill_create_ip=client_ip,
                app_id=app_id or dynasettings.CLIENT_MINI_APP_ID
            )

            account.withdrawable_balance = account.withdrawable_balance - amount
            account.balance = account.balance - amount
            account.save()

            Transaction.objects.create(
                content_object=new_withdraw,
                transaction_type=transaction_type,
                datetime=timestamp,
                account=account,
                amount=-amount,
                balance_after_transaction=account.balance
            )

            return result
