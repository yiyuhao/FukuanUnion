# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import viewsets, status
from rest_framework.response import Response

from config import(
    SUBSCRIPTION_ACCOUNT_REPLY_STATUS,
    SUBSCRIPTION_ACCOUNT_REPLY_RULE,
    SUBSCRIPTION_ACCOUNT_REPLY_TYPE,
    SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT
)
from common.models import SubscriptionAccountReply
from padmin.serializers import SubscriptionAccountReplySerializer
from padmin.auth import DefaultAuthMixin
from padmin.paginations import ResultsSetPagination


class KeyWordReplyManageView(DefaultAuthMixin, viewsets.GenericViewSet):
    """ 关键字回复 """

    queryset = SubscriptionAccountReply.objects.exclude(
        status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE']
    ).order_by('-create_time')
    serializer_class = SubscriptionAccountReplySerializer
    pagination_class = ResultsSetPagination

    def list(self, request, *args, **kwargs):
        """ 关键字回复规则 """
        queryset = self.queryset.exclude(reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'])
        reply_account = self.request.query_params.get('reply_account')
        if reply_account:
            queryset = queryset.filter(reply_account=reply_account)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """ 更新关键字回复 """

        key_word_reply = SubscriptionAccountReply.objects.get(pk=kwargs['pk'])
        serializer = self.serializer_class(key_word_reply, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """ 新建关键字回复 """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update_status(self, request, *args, **kwargs):
        """ 删除关键字回复 """
        message_reply = SubscriptionAccountReply.objects.get(pk=kwargs['pk'])
        message_reply.status = SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE']
        message_reply.save()
        serializer = self.get_serializer(message_reply)
        return Response(serializer.data)


class MessageAndAttentionReplyViewManager(DefaultAuthMixin, viewsets.GenericViewSet):
    """  关注回复或消息回复 """
    queryset = SubscriptionAccountReply.objects.exclude(
        status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE']
    ).filter(
        reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
    ).order_by('-create_time')
    serializer_class = SubscriptionAccountReplySerializer
    pagination_class = ResultsSetPagination

    def retrieve(self, request, *args, **kwargs):
        """
            检索关注回复或消息回复
        """
        queryset = self.queryset.filter(reply_type=kwargs['reply_type'])
        reply_account = self.request.query_params.get('reply_account')
        if reply_account:
            queryset = queryset.filter(reply_account=reply_account)
        if queryset.first() is None:
            return Response(dict(data=None))
        else:
            serializer = self.get_serializer(queryset.first())
            return Response(dict(data=serializer.data))

    def create_or_update(self, request, *args, **kwargs):
        """ 新建关注回复或消息回复 """
        data = request.data
        if data.get("id"):
            # update
            message_reply = SubscriptionAccountReply.objects.get(pk=data['id'])
            message_reply.reply_text = data['reply_text']
            message_reply.save()
            serializer = self.get_serializer(message_reply)
            return Response(serializer.data)

        new_reply = dict(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
            reply_type=kwargs['reply_type'],
            reply_account=data['reply_account'],
            reply_text=data['reply_text'],
        )
        serializer = self.get_serializer(data=new_reply)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update_status(self, request, *args, **kwargs):
        """ 删除关注回复或消息回复 """
        data = request.data
        if data.get("id"):
            # update
            message_reply = SubscriptionAccountReply.objects.get(pk=data['id'])
            message_reply.status = SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE']
            message_reply.save()
            serializer = self.get_serializer(message_reply)
            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)


reply_key_word_list = KeyWordReplyManageView.as_view({
    'get': 'list',
    'post': 'create'
})
reply_key_word_detail = KeyWordReplyManageView.as_view({
    'patch': 'partial_update',
    'delete': 'update_status',
})

reply_message = MessageAndAttentionReplyViewManager.as_view({
    'get': 'retrieve',
    'post': 'create_or_update',
    'delete': 'update_status'
})

reply_attention = MessageAndAttentionReplyViewManager.as_view({
    'get': 'retrieve',
    'post': 'create_or_update',
    'delete': 'update_status'
})

