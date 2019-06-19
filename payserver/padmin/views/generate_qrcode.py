# -*- coding: utf-8 -*-
#       File: generate_qrcode.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-9
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import time
from hashlib import sha1
from urllib import parse

import requests
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from rest_framework import viewsets, status
from dynaconf import settings as dynasettings

from common.models import PaymentQRCode
from config import QRCODE_ENVS, QINIU_IMAGE_SERVERS, IO_BUFF_SIZE
from padmin.auth import DefaultAuthMixin
from padmin.errors import GenerateQrCodeZipError

SERVICE_NAME = QRCODE_ENVS[dynasettings.ENV]


class GenerateQrCodeView(DefaultAuthMixin, viewsets.ViewSet):
    """ 管理后台批量生成二维码 """

    def _gen_qrcode_zip_bytes(self, uuids, url):
        """ 流式下载压缩包　"""

        aliyun_func_api = (f'https://1034036495131009.cn-hangzhou.fc.aliyuncs.com/'  # noqa
                           f'2016-08-15/proxy/{SERVICE_NAME}/generate_qrcode/')
        salt = 9999
        sh = sha1()
        timestamp = int(time.time())
        sh.update(bytes(str(timestamp + salt), 'utf8'))

        json_data = {
            'uuids': uuids,
            'url': url,
            'timestamp': timestamp,
            'signature': sh.hexdigest()
        }

        with requests.post(url=aliyun_func_api, json=json_data,
                           stream=True) as resp:
            if resp.status_code not in (200, 201):
                raise GenerateQrCodeZipError(f"批量生成收款二维码出错,状态码: {resp.status_code}")  # noqa

            for chunk in resp.iter_content(IO_BUFF_SIZE):
                yield chunk

    def gen_qrcode(self, request):
        """ 管理后台批量生成二维码 """
        qrcode_image_url = request.GET.get('qrcode_image_url', '')
        qrcode_num = int(request.GET.get('qrcode_num', 0))
        qrcode_num = qrcode_num if 0 < qrcode_num < 51 else 50
        uuids = []
        pay_qr_objs = []
        for i in range(qrcode_num):
            pay_qr_obj = PaymentQRCode()
            pay_qr_objs.append(pay_qr_obj)
            uuids.append(pay_qr_obj.uuid)
        PaymentQRCode.objects.bulk_create(pay_qr_objs)

        created_objs = PaymentQRCode.objects.filter(uuid__in=uuids)
        uuids = [(obj.id, str(obj.uuid)) for obj in created_objs]
        bytes_generator = self._gen_qrcode_zip_bytes(uuids=uuids,
                                                     url=qrcode_image_url)

        response = StreamingHttpResponse(bytes_generator)
        response["Content-Disposition"] = "attachment; filename=qrcode.zip"
        return response


class GenerateSignQrCodeView(DefaultAuthMixin, viewsets.ViewSet):
    """ 管理后台生成指定商户二维码 """

    def gen_sign_qrcode_redirect(self, request):
        """
        重定向生成单个收款二维码
        """
        qid = request.query_params.get('qid')
        uuid = request.query_params.get('uuid')

        image_host = QINIU_IMAGE_SERVERS[dynasettings.ENV]

        func_api = (f'https://{image_host}/2016-08-15/proxy/'
                    f'{SERVICE_NAME}/generate_signal_qrcode/')

        params = {
            'uuid': uuid,
            'id': qid,
        }
        url = f'{func_api}%3f{parse.urlencode(params)}'
        return HttpResponseRedirect(url)


generate_qrcode = GenerateQrCodeView.as_view({
    'get': 'gen_qrcode'
})
generate_sign_qrcode = GenerateSignQrCodeView.as_view({
    'get': 'gen_sign_qrcode_redirect'
})
