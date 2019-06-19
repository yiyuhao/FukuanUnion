#      File: cashier.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/17
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES
from common.error_handler import MerchantError
from common.model_manager.merchant_manager import MerchantManager
from common.model_manager.merchant_admin_manager import MerchantAdminModelManager
from merchant.auth import MerchantAdminAuthentication
from merchant.permissions import NotDisabled, is_merchant_admin, merchant_is_using
from merchant.serializers import CashierSerializer


logger = logging.getLogger(__name__)


class CashierViewSet(GenericViewSet):
    authentication_classes = [MerchantAdminAuthentication]
    serializer_class = CashierSerializer
    permission_classes = [NotDisabled]

    @action(detail=True, url_name='remove')
    @is_merchant_admin
    @merchant_is_using
    def remove(self, request, pk=None):
        """删除收银员"""

        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        cashier = merchant.get_cashier(cashier_id=pk)
        if cashier is None:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data=MerchantError.cashier_does_not_exist
            )

        merchant_admin = MerchantAdminModelManager()
        merchant_admin.remove_cashier(cashier)

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'removed a cashier({cashier.id, cashier.wechat_nickname}))')

        return Response(
            status=status.HTTP_200_OK,
            data=dict()
        )

    @is_merchant_admin
    @merchant_is_using
    def list(self, request):
        """展示收银员列表"""
        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        cashiers = merchant.cashiers
        serializer = CashierSerializer(cashiers, many=True)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )

    @is_merchant_admin
    @merchant_is_using
    def create(self, request):

        logger.info(f'try create a cashier, request.data is ({request.data})')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merchant = request.user.work_merchant
        manager = MerchantAdminModelManager()
        cashier = manager.get_merchant_admin(serializer.validated_data['wechat_unionid'])

        if cashier:
            # 商户管理员无法成为收银员
            if cashier.merchant_admin_type == MERCHANT_ADMIN_TYPES['ADMIN']:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=MerchantError.cashier_is_merchant_admin
                )
            # 该收银员已绑定其他商铺(DISABLED的收银员可加入其他店铺)
            if cashier.work_merchant != merchant and cashier.status == SYSTEM_USER_STATUS['USING']:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=MerchantError.cashier_already_worked_in_another_merchant
                )
            # 已添加该收银员
            if cashier.work_merchant == merchant and cashier.status == SYSTEM_USER_STATUS['USING']:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=MerchantError.cashier_already_has_been_added
                )
        serializer.save(work_merchant=merchant)
        headers = self.get_success_headers(serializer.data)

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'added a cashier({serializer.data}))')

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @staticmethod
    def get_success_headers(data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}
