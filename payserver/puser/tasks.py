#
#      File: tasks.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from __future__ import absolute_import, unicode_literals

import json

from celery import shared_task
from celery.utils.log import get_task_logger

from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.model_manager.refund_manager import RefundManager
from common.models import Refund
from common.payment.wechat import WechatPaymentUseCases

logger = get_task_logger(__name__)


@shared_task
def wechat_refund_status_sync(refund_serial_number):
    use_cases = WechatPaymentUseCases()
    try:
        refund_info = use_cases.api_instance_without_cert.refund_query(
            refund_serial_number=refund_serial_number)
    except (ApiRequestError, ApiReturnedError) as e:
        logger.error('wechat_refund_status_sync: Call refund query error:')
        logger.error(e)
        return

    logger.debug('refund_info:' + json.dumps(refund_info))
    if 'refund_status_0' not in refund_info or 'out_refund_no_0' not in refund_info \
            or 'refund_fee_0' not in refund_info:
        logger.error("wechat_refund_status_sync: 'refund_status_0' not in refund_info "
                     "or 'out_refund_no_0' not in refund_info "
                     "or 'refund_fee_0' not in refund_info")
        logger.error(json.dumps(refund_info))
        return

    if refund_serial_number != refund_info['out_refund_no_0']:
        logger.error(f'wechat_refund_status_sync: out_refund_no_0 mismatch: '
                     f'refund_serial_number:{refund_serial_number} '
                     f'out_refund_no_0:{refund_info["out_refund_no_0"]}')
        return

    # get the payment from DB
    try:
        refund = Refund.objects.get(serial_number=refund_info['out_refund_no_0'])
    except Refund.DoesNotExist:
        logger.error(f'wechat_refund_status_sync: '
                     f'cannot find refund in DB: {refund_info["out_refund_no_0"]}')
        return

    if refund_info['refund_status_0'] == 'PROCESSING':  # 处理中，等待下一次轮询
        return

    if refund_info['refund_status_0'] != 'SUCCESS':  # 退款失败
        use_cases.on_refund_fail(refund)

        # send wechat message to merchant
        refund_manager = RefundManager(refund)
        refund_manager.send_refund_fail_message()
        return

    # 退款成功
    payment = refund.payment
    paid_price = payment.order_price - payment.coupon.discount \
        if payment.coupon else payment.order_price

    # check the price
    if paid_price != int(refund_info['refund_fee_0']):
        logger.error('wechat_refund_status_sync: refund_fee_0 mismatch')
        return

    use_cases.on_refund_success(refund)

    # send wechat message to merchant
    refund_manager = RefundManager(refund)
    refund_manager.send_refund_success_message()
