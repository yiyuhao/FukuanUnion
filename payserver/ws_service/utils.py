import json

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your views here.


class PublishToRedisChannel(object):
    """ 发布消息到redis频道 """

    @classmethod
    def publish_to_channel(cls, data):
        # 发布消息到特定channel
        channel_key = data['channel_key']
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            channel_key,
            {
                "type": "channel.message",
                "message": json.dumps(data),
            },
        )

        return {'code': 0, "message": 'success'}
