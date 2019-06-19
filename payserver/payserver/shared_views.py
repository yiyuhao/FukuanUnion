# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.http import JsonResponse

from config import API_VERSION


def api_version_not_found(request, api_category, api_version):
    current_version = 'v%d.%d.%d' % API_VERSION.get(api_category.upper())
    return JsonResponse(status=404,
                        data=dict(
                            error='api_version_not_found',
                            message=f'api {api_version} does not exist, '
                                    f'current version is {current_version}'
                        ))
