# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
import hashlib

from common.tasks import async_push_template_message
from padmin.subscription_account_reply.const import WEChAT_REPLY_CONFIG
from padmin.subscription_account_reply.wechat_msg import (
    TextMsg,
    EventSubscribeMsg,
    EventClickMsg,
    EventViewMsg,
    MsgFactory,
)
from padmin.subscription_account_reply.reply_msg import ReplyMessageFactory
from padmin.subscription_account_reply.replyer import ReplyerFactory

logger = logging.getLogger(__name__)


def validate_from_wechat(data, reply_account_type):
    """ 验证微信请求签名  """
    signature = data['signature']
    timestamp = data['timestamp']
    nonce = data['nonce']
    echostr = data['echostr']
    token = WEChAT_REPLY_CONFIG[reply_account_type]['token']  # 公众号基本配置-服务器配置token

    param_list = [token, timestamp, nonce]
    param_list.sort()
    sha1 = hashlib.sha1()

    sha1.update("".join(param_list).encode('utf-8'))
    hashcode = sha1.hexdigest()
    if hashcode == signature:
        return echostr
    else:
        return ""


class MsgHandler(object):
    msg_factory = MsgFactory
    replyer_factory = ReplyerFactory
    reply_message_factory = ReplyMessageFactory

    def __init__(self, xml_string, reply_account_type):
        self.msg = self.msg_factory.parse_xml_string_to_msg(xml_string)
        self.replyer = self.replyer_factory.get_replyer(reply_account_type)
        self.reply_account_type = reply_account_type

    def get_reply_xml_string(self):
        if self.msg is None:
            return "success"

        # 关注事件回复或者发消息回复
        if isinstance(self.msg, EventSubscribeMsg) or isinstance(self.msg, TextMsg):
            reply_content = self.replyer.reply(self.msg)
            if reply_content is None:
                return "success"

            reply_xml_string = self.reply_message_factory.get_text_message(from_user_name=self.msg.ToUserName,
                                                                           to_user_name=self.msg.FromUserName,
                                                                           content=reply_content).get_msg_body()
            return reply_xml_string

        # 菜单的点击事件消息
        elif isinstance(self.msg, EventClickMsg):
            reply_content = "点击测试，该功能正在上线的路上"

            # TODO 点击具体的菜单消息
            if self.reply_account_type == "user":
                if self.msg.EventKey == "activity_recommendation":
                    reply_content = "活动推荐，该功能正在上线的路上"

            elif self.reply_account_type == "merchant":
                if self.msg.EventKey == "union_introduce":
                    reply_content = "联盟介绍，该功能正在上线的路上"
                elif self.msg.EventKey == "activity_recommendation":
                    reply_content = "活动推荐，该功能正在上线的路上"
                elif self.msg.EventKey == "contact_service":
                    reply_content = "联系客服，该功能正在上线的路上"

            elif self.reply_account_type == "marketer":
                pass

            reply_xml_string = self.reply_message_factory.get_text_message(from_user_name=self.msg.ToUserName,
                                                                           to_user_name=self.msg.FromUserName,
                                                                           content=reply_content).get_msg_body()
            return reply_xml_string
        # 菜单的浏览事件消息
        elif isinstance(self.msg, EventViewMsg):
            pass

        return "success"


def push_template_message(params):

    logger.info(f'push wechat template message({params})')

    return async_push_template_message.delay(params)
