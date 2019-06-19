#      File: transaction.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from django.http import Http404, StreamingHttpResponse, HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.error_handler import MerchantError
from common.models import Transaction
from common.model_manager.transaction_manager import TransactionModelManager, TransactionManager
from common.model_manager.payment_manager import PaymentManager, PaymentModelManager
from common.voice_synthesis import xunfei
from common.voice_synthesis.xunfei import XunfeiApi, XunfeiApiReturnError
from merchant.paginators import MerchantTransactionPagination
from merchant.auth import MerchantAdminAuthentication
from merchant.permissions import NotDisabled, merchant_is_using
from merchant.serializers import TransactionTypeSerializer, TransactionListInputSerializer, PaymentSerializer

logger = logging.getLogger(__name__)


class TransactionViewSet(GenericViewSet):
    queryset = Transaction.objects.all()
    authentication_classes = [MerchantAdminAuthentication]
    pagination_class = MerchantTransactionPagination
    serializer_class = PaymentSerializer
    permission_classes = [NotDisabled]

    @merchant_is_using
    def list(self, request):
        """账单列表"""
        merchant = request.user.work_merchant
        transaction_type = request.GET.get('type', 'all')
        serializer = TransactionListInputSerializer(data=dict(transaction_type=transaction_type))
        serializer.is_valid(raise_exception=True)

        transaction_manager = TransactionModelManager()
        transactions = transaction_manager.list_merchant_transaction(merchant, transaction_type)

        page_data = self.paginate_queryset(transactions)
        page_data = transaction_manager.serialize(transactions=page_data)
        return self.get_paginated_response(page_data)

    @merchant_is_using
    def retrieve(self, request, pk=None):
        """账单详情 pk为两种类型:transaction.id or payment.serial_number"""

        merchant = request.user.work_merchant
        manager = TransactionModelManager()
        transaction = manager.get(pk=pk, merchant=merchant)
        if transaction is None:
            raise Http404

        type_check = TransactionTypeSerializer(data=dict(transaction_type=transaction.transaction_type))
        type_check.is_valid(raise_exception=True)

        transaction = TransactionManager(transaction)
        detail = transaction.detail

        return Response(
            status=status.HTTP_200_OK,
            data=detail
        )

    @merchant_is_using
    def update(self, request, pk=None):
        """修改支付账单备注"""
        merchant = request.user.work_merchant

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'requested a payment note updating(transaction id={pk})'
                    f'data: ({request.data})')

        manager = TransactionModelManager()
        transaction = manager.get(pk=pk, is_payment=True, merchant=merchant)
        if transaction is None:
            raise Http404

        serializer = self.get_serializer(transaction.content_object, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @merchant_is_using
    @action(detail=True, url_name='refund')
    def refund(self, request, pk=None):
        """退款"""
        merchant = request.user.work_merchant

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'requested a refund(id={pk})')

        manager = TransactionModelManager()
        transaction = manager.get(pk=pk, is_payment=True, merchant=merchant)
        if transaction is None:
            raise Http404

        notify_url = request.build_absolute_uri('/').strip("/") + reverse('wechat_refund_callback')

        payment = PaymentManager(transaction.content_object)
        payment.refund(notify_url=notify_url)

        status_ = status.HTTP_200_OK if payment.refund_error is None else status.HTTP_400_BAD_REQUEST

        return Response(
            status=status_,
            data=payment.refund_error or {}
        )

