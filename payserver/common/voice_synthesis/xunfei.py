#
#      File: xunfei.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


import base64
import hashlib
import json
import logging
import time

import requests

from config import XunfeiVoiceSynthesisConfig as Conf

logger = logging.getLogger(__name__)


class XunfeiApiReturnError(Exception):
    pass


class XunfeiApi:
    """
        科大讯飞 语音合成use case
        https://doc.xfyun.cn/rest_api/语音合成.html
    """

    def request_voice(self, text, auf=Conf.auf, aue=Conf.aue, voice_name=Conf.voice_name, speed=Conf.speed,
                volume=Conf.volume, pitch=Conf.pitch, engine_type=Conf.engine_type):

        """
            IOS中小程序无法播放transfer-encoding=chunked的音频，直接传输整个音频文件
            :param text: 语音内容
            :param auf: 音频采样率 可选值: 'audio/L16;rate=8000', 'audio/L16;rate=16000'
            :param aue: 音频编码, 可选值: raw(未压缩的pcm或wav格式) , lame(mp3格式)
            :param voice_name:  发音人, 可选值: 详见发音人列表(https://www.xfyun.cn/services/online_tts)
            :param speed: 语速, 可选值: [0-100], 默认为50
            :param volume: 音量, 可选值: [0-100], 默认为50
            :param pitch: 音高, 可选值: [0-100], 默认为50
            :param engine_type: 引擎类型, 可选值: aisound(普通效果) , intp65(中文) , intp65_en(英文)
            :return (bytes)
        """
        params = dict(
            auf=auf,
            aue=aue,
            voice_name=voice_name,
            speed=speed,
            volume=volume,
            pitch=pitch,
            engine_type=engine_type
        )

        # 配置参数编码为base64字符串, 过程: 字典→明文字符串→utf8编码→base64(bytes)→base64字符串
        param_utf8 = json.dumps(params).encode('utf8')  # utf8编码(bytes类型)
        param_base64 = base64.b64encode(param_utf8).decode('utf8')  # base64字符串

        # 构造HTTP请求的头部
        time_now = str(int(time.time()))
        checksum = (Conf.api_key + time_now + param_base64).encode('utf8')
        checksum_md5 = hashlib.md5(checksum).hexdigest()
        header = {
            "X-Appid": Conf.app_id,
            "X-CurTime": time_now,
            "X-Param": param_base64,
            "X-CheckSum": checksum_md5
        }

        # 发送HTTP POST请求
        with requests.post(Conf.api_url, data=dict(text=text), headers=header) as response:
            if response.headers['Content-Type'] != "audio/mpeg":
                logger.error(f'Xunfei api returned error: {response.text}')
                raise XunfeiApiReturnError(response.text)

            return response.content
