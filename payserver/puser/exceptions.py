# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import status
from rest_framework.exceptions import APIException


class WeixinLoginUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'weixin login service unavaliable'
    default_code = '503'


class AlipayLoginUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'alipay login service unavaliable'
    default_code = '503'


class DataNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'resource not found'
    default_code = '404'


class InvalidParameter(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'invalid parameter'
    default_code = '400'


class InvalidStatus(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'invalid status'
    default_code = '400'


class PlaceOrderError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'place order error'
    default_code = '500'
