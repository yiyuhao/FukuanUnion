# -*- coding: utf-8 -*-
#       File: sms_send.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-24
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import base64
import hashlib
import json
import random
import re
import time

import requests
from redis import StrictRedis
from requests.exceptions import RequestException

from .config import (ACCOUNT_SID,
                     APP_ID,
                     AUTH_TOKEN,
                     BASE_URL,
                     VERIFY_CODE_EXPIRES_IN,
                     RECORD_EXPIRES_IN,
                     TEMPLATE_ID,
                     CODE_RANGE,
                     redis_pool,
                     ERROR_MSG)


class SendMessageApi(object):
    """
    发送短信的接口
    """
    def __init__(self, phone, wechat_unionid):
        self.phone = phone
        self.wechat_unionid = wechat_unionid
        self.redis_cli = StrictRedis(connection_pool=redis_pool)

    def message_send(self):
        # 发送短信入口
        if not (self.phone and self._verify_phone_num(self.phone)):
            return {'code': -1, 'message': ERROR_MSG['PHONEERR']}

        if not self._verify_last_send_time():
            return {'code': -2, 'message': ERROR_MSG['FREQUENTLY']}

        time_stamp = self._gen_timestamp()
        sign = self._gen_params(time_stamp)
        url = self._gen_url(BASE_URL, ACCOUNT_SID, sign)
        data = {
            'to': self.phone,
            'appId': APP_ID,
            'templateId': TEMPLATE_ID,
            "datas": [self._gen_verify_code(), VERIFY_CODE_EXPIRES_IN]
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length': '{}'.format(len(json.dumps(data))),
            'Authorization': self._gen_auth(time_stamp)
        }

        count = 2
        while count > 0:
            resp_json = self._send_msg(url=url, data=data, headers=headers)
            status_code = resp_json.get('statusCode') or 'DEFAULT'
            if status_code == "000000":
                self._record_last_send_time()
                return {'code': 0, 'message': ERROR_MSG[status_code]}
            else:
                error_msg = resp_json.get('statusMsg')
                if error_msg:
                    return {'code': -1, 'message': error_msg}
                elif status_code in ERROR_MSG:
                    return {'code': -1, 'message': ERROR_MSG[status_code]}
            count -= 1
            time.sleep(2)

        return {'code': -1, 'message': ERROR_MSG['DEFAULT']}

    def _gen_url(self, base_url, account_sid, sig_parameter):
        url = (f'{base_url}/2013-12-26/Accounts/{account_sid}/'
               f'SMS/TemplateSMS?sig={sig_parameter}')
        return url

    def _gen_timestamp(self, fmt='%Y%m%d%H%M%S'):
        # 生成时间戳
        return time.strftime(fmt)

    def _gen_params(self, time_stamp):
        # 生成加密参数
        m = hashlib.md5()
        org_str = '{}{}{}'.format(ACCOUNT_SID, AUTH_TOKEN, time_stamp)
        m.update(org_str.encode('utf-8'))
        return m.hexdigest().upper()

    def _gen_auth(self, time_stamp):
        # 生成authorization
        org_str = f'{ACCOUNT_SID}:{time_stamp}'
        return base64.b64encode(org_str.encode('utf-8'))

    def _gen_verify_code(self):
        # 生成短信验证码
        verify_code = random.randint(CODE_RANGE[0], CODE_RANGE[1])
        self.redis_cli.set(name=self.phone, value=verify_code,
                           ex=VERIFY_CODE_EXPIRES_IN * 60)
        return verify_code

    def _verify_phone_num(self, phone):
        # 验证电话号码是否合法
        self.pattern = "^(?=\d{11}$)^1(?:3\d|4[57]|5[^4\D]|66|7[^249\D]|8\d|9[89])\d{8}$"
        res = re.match(self.pattern, phone)
        if res and res.group(0):
            return True

    def _send_msg(self, url, data, headers):
        # 发送请求到容联云
        resp = requests.post(url=url, json=data, headers=headers)
        try:
            resp_json = resp.json()
        except (ValueError, RequestException):
            resp_json = {}
        return resp_json

    def _record_last_send_time(self):
        # 记录该unionid上次发短信的时间
        send_time = time.time()
        self.redis_cli.set(name=f'last_send_time_{self.wechat_unionid}',
                           value=send_time, ex=RECORD_EXPIRES_IN * 60)

    def _verify_last_send_time(self):
        # 验证该unionid上次发送短信时间
        now = time.time()
        last_time = self.redis_cli.get(
            name=f'last_send_time_{self.wechat_unionid}') or "0.0".encode('utf8')
        if now - float(last_time.decode('utf8')) > 60:
            return True
        return False


class VerifySmsCode(object):
    """ 验证短信验证码是否正确 """
    def __init__(self, phone, verify_code):
        self.phone = phone
        self.verify_code = verify_code

    def verify(self, delete_cache=False):
        redis_cli = StrictRedis(connection_pool=redis_pool)
        code = redis_cli.get(name=self.phone) or b''
        if code.decode('utf8') != self.verify_code:
            return False
        if delete_cache:
            redis_cli.delete(self.phone)
        return True