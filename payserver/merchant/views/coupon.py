#      File: coupon.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from common.models import CouponRule
from common.model_manager.coupon_rule_manager import CouponRuleModelManager, CouponRuleManager
from merchant.auth import MerchantAdminAuthentication
from merchant.paginators import MerchantTransactionPagination
from merchant.permissions import NotDisabled, merchant_is_using
from merchant.serializers import CouponRuleSerializer


logger = logging.getLogger(__name__)


class CouponViewSet(GenericViewSet, CreateModelMixin):
    queryset = CouponRule.objects.all()
    authentication_classes = [MerchantAdminAuthentication]
    pagination_class = MerchantTransactionPagination
    serializer_class = CouponRuleSerializer
    permission_classes = [NotDisabled]

    @merchant_is_using
    def list(self, request):
        """优惠券列表"""
        merchant = request.user.work_merchant
        manager = CouponRuleModelManager()
        coupons = manager.list_merchant_coupon_rule(merchant)

        return Response(
            status=status.HTTP_200_OK,
            data=coupons
        )

    @merchant_is_using
    def retrieve(self, request, pk=None):
        """优惠券详情"""
        merchant = request.user.work_merchant
        coupon_rule = self.get_object()

        if coupon_rule.merchant != merchant:
            raise Http404

        manager = CouponRuleManager(coupon_rule)
        detail = manager.detail()
        return Response(
            status=status.HTTP_200_OK,
            data=detail
        )

    @merchant_is_using
    def create(self, request, *args, **kwargs):
        merchant = request.user.work_merchant

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(merchant=merchant)
        headers = self.get_success_headers(serializer.data)

        logger.info(f'merchant({merchant.id}, {merchant.name}) created a coupon_rule({serializer.data})')

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @merchant_is_using
    def update(self, request, *args, **kwargs):
        """下架或修改库存"""
        merchant = request.user.work_merchant
        coupon_rule = self.get_object()
        old_stock = coupon_rule.stock

        if coupon_rule.merchant != merchant:
            raise Http404

        serializer = self.get_serializer(coupon_rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'merchant({merchant.id}, {merchant.name}) '
                    f'modified stock of a coupon_rule({coupon_rule.id}) '
                    f'from {old_stock} to {coupon_rule.stock}')

        return Response(serializer.data)

    @action(detail=True)
    @merchant_is_using
    def payments(self, request, *args, **kwargs):
        """使用优惠券的账单列表"""
        merchant = request.user.work_merchant
        coupon_rule = self.get_object()

        if coupon_rule.merchant != merchant:
            raise Http404

        manager = CouponRuleManager(coupon_rule)
        payments = manager.relative_payment()

        paged_payments = self.paginate_queryset(payments)
        page_data = manager.serialize_relative_payment(paged_payments)
        return self.get_paginated_response(page_data)
