# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import viewsets
from rest_framework.response import Response

from config import MESSAGE_STATUS, MESSAGE_TYPE
from common.models import Message
from padmin.auth import DefaultAuthMixin, admin_permissions
from padmin.serializers import MessageSerializer
from padmin.paginations import ResultsSetPagination


class MessageViewSet(DefaultAuthMixin, viewsets.GenericViewSet):
    queryset = Message.objects.exclude(status=MESSAGE_STATUS['DELETE']).order_by('-create_time')
    serializer_class = MessageSerializer
    permission_classes = (admin_permissions['PLATFORM_ADMIN'],)
    pagination_class = ResultsSetPagination

    def list(self, request, *args, **kwargs):
        """
            消息列表
        """
        queryset = self.queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
            更新消息状态
        """
        merchant = Message.objects.get(pk=kwargs['pk'])
        serializer = self.serializer_class(merchant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


message_list = MessageViewSet.as_view({
    'get': 'list',
})

message_detail = MessageViewSet.as_view({
    'patch': 'partial_update',
})