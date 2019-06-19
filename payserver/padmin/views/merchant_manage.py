# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response

from common.models import Merchant
from padmin.serializers import MerchantSerializer
from padmin.auth import DefaultAuthMixin
from padmin.paginations import ResultsSetPagination


class MerchantManageListView(DefaultAuthMixin, viewsets.GenericViewSet):
    queryset = Merchant.objects.order_by('-payment_qr_code__id')
    serializer_class = MerchantSerializer
    pagination_class = ResultsSetPagination

    def list(self, request, *args, **kwargs):
        """
            条件状态分页查询商户
        """
        self.serializer_class.Meta.depth = 0
        queryset = self.queryset
        status = self.request.query_params.get('status')
        id_name = self.request.query_params.get('id_name')
        if status:
            queryset = queryset.filter(status=status)
        if id_name:
            queryset = queryset.filter(Q(payment_qr_code__id__contains=id_name) | Q(name__contains=id_name))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
            具体商户信息
        """
        self.serializer_class.Meta.depth = 10
        queryset = Merchant.objects.get(pk=pk)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
            更新商户信息
        """
        self.serializer_class.Meta.depth = 0
        merchant = Merchant.objects.get(pk=kwargs['pk'])
        serializer = self.serializer_class(merchant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


merchant_list = MerchantManageListView.as_view({'get': 'list'})
merchant_detail = MerchantManageListView.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
})
