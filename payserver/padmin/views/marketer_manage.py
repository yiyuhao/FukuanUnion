# -*- coding: utf-8 -*-
#       File: fake_factory.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 2018/6/20
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.db.models import Q, Max, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response

from padmin.auth import DefaultAuthMixin
from padmin.serializers import (
    SalesmanSerializer,
    InviterSerializer,
    AreaSerializer,
    MarketerMerchantSerializer,
    MerchantMarketerShipSerializer,
)
from padmin.paginations import ResultsSetPagination
from padmin.query_manage.marketer_query import MarketerQeuryManager
from common.models import Marketer, Merchant, MerchantMarketerShip
from config import MARKETER_TYPES


class InviterViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = Marketer.objects.select_related('account')
    serializer_class = InviterSerializer
    pagination_class = ResultsSetPagination

    def filter_queryset(self, queryset):
        name_or_id = self.request.query_params.get('name')
        status = self.request.query_params.get('status', 'default')
        queryset = queryset.filter(inviter_type=MARKETER_TYPES.MARKETER)
        if name_or_id:
            queryset = queryset.filter(Q(pk__icontains=name_or_id) |
                                       Q(name__icontains=name_or_id))
        if status != 'default':
            queryset = queryset.filter(status=status)
        return queryset.order_by('-id')


class SalesmanViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = MarketerQeuryManager.marketer_selected()
    serializer_class = SalesmanSerializer
    pagination_class = ResultsSetPagination

    def filter_queryset(self, queryset):
        name_or_id = self.request.query_params.get('name')
        status = self.request.query_params.get('status', 'default')
        change_inviter = self.request.query_params.get('change_inviter', False)
        if change_inviter:
            queryset = queryset.filter(inviter_type=MARKETER_TYPES.MARKETER)
        else:
            queryset = queryset.filter(inviter_type=MARKETER_TYPES.SALESMAN)
        if name_or_id:
            queryset = queryset.filter(Q(worker_number__icontains=name_or_id) |
                                       Q(name__icontains=name_or_id))
        if status != 'default':
            queryset = queryset.filter(status=status)
        return queryset.order_by('-id')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        working_areas = serializer.initial_data.pop('working_areas', {})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, working_areas)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(
            self.get_serializer(self.queryset.get(id=instance.id)).data)

    def perform_update(self, serializer, working_areas):
        serializer.save(working_areas=working_areas)


class SalesmanAreaViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = MarketerQeuryManager.area_selected()
    serializer_class = AreaSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MarketerMerchantViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = Merchant.objects.prefetch_related('auditors')
    serializer_class = MarketerMerchantSerializer
    pagination_class = ResultsSetPagination

    def filter_queryset(self, queryset):
        uid = self.request.query_params.get('uid')
        audit = self.request.query_params.get('audit', False)
        start_date = self.request.query_params.get('start_date', '')
        end_date = self.request.query_params.get('end_date', '')
        if audit:
            try:
                marketer = Marketer.objects.get(id=uid)
            except Marketer.DoesNotExist:
                return queryset.none()
            if start_date and end_date:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d') + \
                           timezone.timedelta(days=1)
                queryset = marketer.audited_merchants.filter(
                    merchantmarketership__audit_datetime__range=[start_date,
                                                                 end_date])
            else:
                queryset = marketer.audited_merchants.all()
        else:
            queryset = queryset.filter(inviter_id=uid)
        return queryset.values(
            'id', 'name', 'avatar_url', 'address', 'status', 'area_id',
            last_audited_time=Max('merchantmarketership__audit_datetime'),
            audited_num=Count('id')
        ).order_by('-last_audited_time')


class MarketerMerchantShipViewSet(DefaultAuthMixin, viewsets.ModelViewSet):
    queryset = MerchantMarketerShip.objects.select_related('merchant')
    serializer_class = MerchantMarketerShipSerializer
    pagination_class = ResultsSetPagination

    def filter_queryset(self, queryset):
        uid = self.request.query_params.get('uid', '')
        start_date = self.request.query_params.get('start_date', '')
        end_date = self.request.query_params.get('end_date', '')
        queryset = queryset.filter(marketer_id=uid)
        if start_date and end_date:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d') + \
                       timezone.timedelta(days=1)
            queryset = queryset.filter(audit_datetime__range=[start_date,
                                                              end_date])
        return queryset


inviter_list = InviterViewSet.as_view({
    'get': 'list',
})

inviter_detail = InviterViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

salesman_list = SalesmanViewSet.as_view({
    'get': 'list',
})

salesman_detail = SalesmanViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update'
})

areas_list = SalesmanAreaViewSet.as_view({
    'get': 'list'
})

marketer_merchant_list = MarketerMerchantViewSet.as_view({
    'get': 'list'
})

marketer_merchant_ship_list = MarketerMerchantShipViewSet.as_view({
    'get': 'list'
})
