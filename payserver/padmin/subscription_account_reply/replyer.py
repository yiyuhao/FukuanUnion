# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from common.models import SubscriptionAccountReply
from config import(
    SUBSCRIPTION_ACCOUNT_REPLY_STATUS,
    SUBSCRIPTION_ACCOUNT_REPLY_RULE,
    SUBSCRIPTION_ACCOUNT_REPLY_TYPE,
    SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT
)
from padmin.subscription_account_reply.wechat_msg import (
    TextMsg,
    EventSubscribeMsg,
)


class Replyer(object):
    def attention_reply(self):
        """ 关注回复 """

        query_set = SubscriptionAccountReply.objects.filter(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['BE_PAID_ATTENTION'],
            reply_account=self.reply_account
        ).order_by('-create_time')

        query_first = query_set.first()
        if query_first is not None:
            return query_first.reply_text

        return None

    def message_reply(self, question_text):
        """ 关键字及收到消息回复 """

        # 先查关键字全匹配的规则， 按创建时间逆序
        query_set = SubscriptionAccountReply.objects.filter(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['KEY_WORD'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['COMPLETE'],
            reply_account=self.reply_account,
            question_text=question_text
        ).order_by('-create_time')

        query_first = query_set.first()
        if query_first is not None:
            return query_first.reply_text


        # 半匹配的规则
        query_set = SubscriptionAccountReply.objects.filter(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['KEY_WORD'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['PARTIAL'],
            reply_account=self.reply_account,
        ).order_by('-create_time')

        if len(query_set) != 0:
            for reply in query_set:
                if reply.question_text in question_text:
                    return reply.reply_text

        # 消息回复规则
        query_set = SubscriptionAccountReply.objects.filter(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['RECEIVED'],
            reply_account=self.reply_account,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
        ).order_by('-create_time')

        query_first = query_set.first()
        if query_first is not None:
            return query_first.reply_text

        return None

    def reply(self, msg):
        if isinstance(msg, TextMsg):
            return self.message_reply(msg.Content)
        elif isinstance(msg, EventSubscribeMsg):
            return self.attention_reply()

        return None


class UserReplyer(Replyer):
    reply_account = SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT['USER']


class MerchantReplyer(Replyer):
    reply_account = SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT['MERCHANT']


class MarketerReplyer(Replyer):
    reply_account = SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT['MARKETER']


class ReplyerFactory(object):
    @staticmethod
    def get_replyer(replyer_type):
        if replyer_type == "user":
            return UserReplyer()
        elif replyer_type == "merchant":
            return MerchantReplyer()
        elif replyer_type == "marketer":
            return MarketerReplyer()