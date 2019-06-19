#
#      File: tasks.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from __future__ import absolute_import, unicode_literals

import json

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from requests.exceptions import RequestException

from common.utils import RedisUtil
from padmin.subscription_account_reply.reply_msg import ReplyMessageFactory

logger = get_task_logger(__name__)


@shared_task
def async_push_template_message(params):
    account_type = params.get('account_type')  # user, merchant, marketer
    open_id = params.get('openid')
    content = params.get('content')
    message_template_type = params.get('template_type')  # 消息类型
    if not (account_type and open_id and content and message_template_type):
        return {"detail": "push_failed", "errmsg": 'invalid_params'}

    key = "subscription_account_access_token_{}".format(account_type)
    access_token = RedisUtil.get_access_token(key)

    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}". \
        format(access_token)
    template_message = ReplyMessageFactory.get_template_message(message_template_type,
                                                                open_id,
                                                                content)
    if template_message is None:
        return {"detail": "push_failed", "errmsg": 'no_template_of_this_account_type'}

    json_body = template_message.get_msg_body()
    try:
        resp = requests.post(url=url,
                             data=json.dumps(json_body, ensure_ascii=False)
                             .encode("utf-8")
                             .decode('unicode-escape'))
        resp_json = resp.json()

        logger.info(f'send wechat message: ({json_body}), the wechat response: ({resp_json})')

        if resp_json.get('errmsg') == 'ok' and resp_json.get('errcode') == 0:
            return {"detail": "push_ok", "errmsg": ""}

        else:
            logger.error('send wechat message failed')
            return {"detail": "push_failed", "errmsg": resp_json.get('errmsg')}

    except (RequestException, KeyError) as e:
        return {"detail": "push_failed", "errmsg": repr(e)}
