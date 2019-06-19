# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

"""
微信服务器发送过来的各类消息

"""
import xml.etree.ElementTree as ET

class Msg(object):
    def __init__(self, xml_data):
        self.ToUserName = xml_data.find('ToUserName').text
        self.FromUserName = xml_data.find('FromUserName').text
        self.CreateTime = xml_data.find('CreateTime').text
        self.MsgType = xml_data.find('MsgType').text


class TextMsg(Msg):
    def __init__(self, xml_data):
        super(TextMsg, self).__init__(xml_data)
        self.Content = xml_data.find('Content').text
        self.MsgId = xml_data.find('MsgId').text


class EventMsg(Msg):
    def __init__(self, xml_data):
        super(EventMsg, self).__init__(xml_data)
        self.Event = xml_data.find('Event').text


class EventSubscribeMsg(EventMsg):
    """ 关注事件消息 """
    def __init__(self, xml_data):
        super(EventSubscribeMsg, self).__init__(xml_data)


class EventClickMsg(EventMsg):
    """ 菜单点击事件消息 """
    def __init__(self, xml_data):
        super(EventClickMsg, self).__init__(xml_data)
        self.EventKey = xml_data.find('EventKey').text


class EventViewMsg(EventMsg):
    """ 菜单浏览事件消息 """
    def __init__(self, xml_data):
        super(EventViewMsg, self).__init__(xml_data)
        self.EventKey = xml_data.find('EventKey').text
        self.MenuId = xml_data.find('MenuId').text


class MsgFactory(object):
    @staticmethod
    def parse_xml_string_to_msg(xml_string):
        if len(xml_string) == 0:
            return None
        xml_data = ET.fromstring(xml_string)
        msg_type = xml_data.find('MsgType').text
        if msg_type == 'text':
            return TextMsg(xml_data)
        elif msg_type == 'event':
            event_msg = EventMsg(xml_data)
            if event_msg.Event == 'subscribe':  # 订阅事件消息
                return EventSubscribeMsg(xml_data)
            elif event_msg.Event == 'CLICK':  # 点击菜单事件
                return EventClickMsg(xml_data)
            elif event_msg.Event == "VIEW": # 菜单浏览事件
                return EventViewMsg(xml_data)

        return None
