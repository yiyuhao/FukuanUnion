# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from qiniu import Auth
from dynaconf import settings as dynasettings
from rest_framework.response import Response
from rest_framework.decorators import api_view


QINIU = {
    'ACCESS_KEY': dynasettings.QINIU_ACCESS_KEY,
    'SECRET_KEY': dynasettings.QINIU_SECRET_KEY,
    'BUCKET_NAME': dynasettings.QINIU_BUCKET_NAME,
    'BUCKET_DOMAIN': dynasettings.QINIU_BUCKET_DOMAIN
}


@api_view(['GET', 'POST'])
def qiniu_uptoken(request):
    if request.method == "OPTIONS":
        response = Response()
    else:
        q = Auth(QINIU['ACCESS_KEY'], QINIU['SECRET_KEY'])
        key = None
        token = q.upload_token(QINIU['BUCKET_NAME'], key, 7200, {})

        response = Response({"upload_token": token, 'bucket_domain': QINIU['BUCKET_DOMAIN']})
        response["Cache-Control"] = "max-age=0, private, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = 0
    return response
