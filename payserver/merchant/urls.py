#      File: urls.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.conf.urls import url, include
from rest_framework import routers

from merchant.views.coupon import CouponViewSet
from merchant.views.merchant import MerchantLoginViewSet, MerchantViewSet
from merchant.views.transaction import TransactionViewSet
from merchant.views.cashier import CashierViewSet
from merchant.views.wechat_auth_redirect import AddCashierCRCodeViewSet

router = routers.DefaultRouter()
router.register(r'merchant', MerchantViewSet)
router.register(r'transaction', TransactionViewSet, base_name='transaction')
router.register(r'coupon', CouponViewSet, base_name='coupon')
router.register(r'cashier', CashierViewSet, base_name='cashier')
router.register(r'add_cashier', AddCashierCRCodeViewSet, base_name='add_cashier')

urlpatterns = [
    url(r'^login/$', MerchantLoginViewSet.as_view(), name='merchant-admin-login'),
    url(r'^', include(router.urls)),
]
