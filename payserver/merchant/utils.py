#
#      File: utils.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from common.model_manager.payment_manager import PaymentManager
from common.model_manager.utils import get_amount
from common.msg_service.wechat_msg_send import MerchantMessageSender
from common.voice_synthesis.baidu import get_baidu_token
from ws_service.utils import PublishToRedisChannel


def send_pay_success_wechat_message(payment):
    """付款成功微信消息推送"""

    payment = PaymentManager(payment)

    message_sender = MerchantMessageSender(payment.merchant)
    message_sender.on_pay_success(
        merchant_receive='%.2f' % get_amount(payment.paid_price),
        payment_type='普通订单' if not payment.coupon else '优惠券订单',
        datetime=payment.datetime,
        pay_serial_number=payment.serial_number,
    )


def send_voice_message_to_merchant_app(payment):
    """send payment pk to app through websocket, and then app request server a voice by the pk."""

    payment = PaymentManager(payment)

    token, error_msg = get_baidu_token()
    data = dict(
        channel_key=f'merchant_{payment.merchant_id}_new_payment',
        voice_text=payment.voice_text,
        baidu_token=token,
        error_msg=error_msg
    )

    PublishToRedisChannel.publish_to_channel(data=data)
