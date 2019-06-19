# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from django.conf.urls import url
from django.http import HttpResponse

from puser.rest import (
    client,
    coupon,
    merchant,
    payment,
    payment_callback,
    payment_poll_result,
    payment_unfreeze,
    payment_cancel, refund_status_sync)

urlpatterns = [

    url('^health-check', lambda request: HttpResponse("I'ok"), name='health-check'),

    url(r'^clients/login$', client.Login.as_view(), name='client-login'),

    url(r'^me$', client.Me.as_view(), name='client-me'),

    url(r'^me/set_phone$', client.SetPhone.as_view(), name='client-set-phone'),

    url(r'^coupons/$', coupon.CouponList.as_view(), name='client-coupon-list'),
    url(r'^merchant_info$', merchant.GetMerchantInfo.as_view(), name='payment-merchant-info'),

    url(r'^orders/place', payment.PlaceOrder.as_view(), name='place_order'),

    url(r'^orders/cancel', payment_cancel.PaymentCancelView.as_view(), name='cancel_order'),

    url(r'^orders/poll_result', payment_poll_result.PaymentPollResultView.as_view(),
        name='orders_poll_result'),

    url(r'^payment_callback/wechat_payment_callback',
        payment_callback.WechatPaymentCallbackView.as_view(), name='wechat_payment_callback'),

    url(r'^payment_callback/alipay_payment_callback',
        payment_callback.AlipayPaymentCallbackView.as_view(), name='alipay_payment_callback'),

    url(r'^payment_callback/wechat_refund_callback',
        payment_callback.WechatRefundCallbackView.as_view(), name='wechat_refund_callback'),

    url(r'^payment/unfreeze', payment_unfreeze.PaymentUnfreezeView.as_view(),
        name='payment_unfreeze'),
    url(r'^refund/status_sync', refund_status_sync.RefundStatusSyncView.as_view(),
        name='refund_status_sync'),
]
