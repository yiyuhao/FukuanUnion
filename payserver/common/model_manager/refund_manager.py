#
#      File: refund_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.utils import timezone

from .base import ModelObjectManagerBase
from common.msg_service.wechat_msg_send import MerchantMessageSender
from common.model_manager.utils import get_amount


class RefundManager(ModelObjectManagerBase):
    """self.obj = payment_model_instance"""

    def __init__(self, *args, **kwargs):
        super(RefundManager, self).__init__(*args, **kwargs)

    def send_refund_success_message(self):
        payment = self.obj.payment
        paid_price = payment.order_price if not payment.coupon else payment.order_price - payment.coupon.discount

        message_sender = MerchantMessageSender(payment.merchant)
        message_sender.on_refund_success(
            refund_amount='%.2f' % get_amount(paid_price),
            refund_datetime=timezone.now(),
            refund_serial_number=payment.serial_number
        )

    def send_refund_fail_message(self):
        payment = self.obj.payment
        paid_price = payment.order_price if not payment.coupon else payment.order_price - payment.coupon.discount

        message_sender = MerchantMessageSender(payment.merchant)
        message_sender.on_refund_fail(
            refund_amount='%.2f' % get_amount(paid_price),
            refund_datetime=timezone.now(),
            refund_serial_number=payment.serial_number
        )
