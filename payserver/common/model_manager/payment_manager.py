#      File: payment_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/25
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.error_handler import MerchantError
from common.model_manager.base import ModelObjectManagerBase, ModelManagerBase
from common.model_manager.refund_manager import RefundManager
from common.model_manager.utils import get_amount
from common.models import Refund, Payment
from common.payment.alipay import AlipayUseCases
from common.payment.exceptions import InvalidStatusError
from common.payment.wechat import WechatPaymentUseCases
from common.voice_synthesis.xunfei import XunfeiApi
from config import PAY_CHANNELS, PAYMENT_STATUS

logger = logging.getLogger(__name__)

wechat_payment = WechatPaymentUseCases()
alipay_payment = AlipayUseCases()


class PaymentManager(ModelObjectManagerBase):
    """self.obj = payment_model_instance"""

    def __init__(self, *args, **kwargs):
        super(PaymentManager, self).__init__(*args, **kwargs)
        self.refund_error = None

    @property
    def _refund(self):
        refund = Refund.objects.filter(payment=self.obj).first()
        return refund

    @property
    def paid_price(self):
        """用户实付金额"""
        if not self.obj.coupon:
            paid_price = self.obj.order_price
        else:
            paid_price = self.obj.order_price - self.obj.coupon.discount  # 订单金额 - 减免
        return paid_price

    def refund(self, notify_url):

        def send_wechat_message(success=True):
            """send a refund wechat message to merchant admin"""
            refund = self._refund

            if refund is None:
                logger.error(f'payment({self.obj.id}) has not create refund yet')
                return

            refund_manager = RefundManager(refund)
            refund_manager.send_refund_success_message() if success else refund_manager.send_refund_fail_message()

        # only in frozen status
        if self.obj.status not in (PAYMENT_STATUS['FROZEN'], PAYMENT_STATUS['REFUND_FAILED']):
            self.refund_error = MerchantError.not_frozen_payment
            return

        try:
            if self.obj.pay_channel == PAY_CHANNELS['WECHAT']:
                wechat_payment.request_refund(self.obj, notify_url)
            elif self.obj.pay_channel == PAY_CHANNELS['ALIPAY']:
                alipay_payment.request_refund(self.obj)
                send_wechat_message(success=True)

        except ApiRequestError:
            send_wechat_message(success=False)
            self.refund_error = MerchantError.refund_request_error

        except ApiReturnedError:
            send_wechat_message(success=False)
            self.refund_error = MerchantError.refund_result_error

        except InvalidStatusError:
            send_wechat_message(success=False)
            self.refund_error = MerchantError.not_frozen_payment

    @property
    def voice_text(self):
        pay_channel_name = PAY_CHANNELS.number_name_dict()[self.obj.pay_channel]  # '微信', '支付宝'
        price = get_amount(self.paid_price)

        return f'{pay_channel_name}到帐: {price}元。'

    @property
    def voice(self):
        """
            request Xunfei and download voice of this payment
            :return (iterable bytes)
        """
        return XunfeiApi().request_voice(self.voice_text)


class PaymentModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(PaymentModelManager, self).__init__(*args, **kwargs)
        self.model = Payment

    def search(self, serial_number, merchant):
        return self.model.objects.filter(serial_number=serial_number, merchant=merchant).first()
