# -*- coding: utf-8 -*-
#       File: consumers.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-16
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


logger = logging.getLogger(__name__)


class WeChatAuthConsumer(WebsocketConsumer):
    def connect(self):
        self.channel_key = self.scope['url_route']['kwargs']['channel_key']

        # Join channel_key group
        async_to_sync(self.channel_layer.group_add)(
            self.channel_key,
            self.channel_name   # 为每个链接自动生成的一个唯一标识
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave channel_key group
        async_to_sync(self.channel_layer.group_discard)(
            self.channel_key,
            self.channel_name
        )

    # Receive message channel_key WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to channel_key group
        async_to_sync(self.channel_layer.group_send)(
            self.channel_key,
            {
                'type': 'channel_message',
                'message': message
            }
        )

    # Receive message from channel_key group
    def channel_message(self, event):
        message = event['message']

        logger.info(f"Send message: {message} to font channel: {self.channel_key}")

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))
