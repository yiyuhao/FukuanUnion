# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


"""
回复公众号消息
"""
import functools

from rest_framework.decorators import api_view, authentication_classes
from django.http import HttpResponse, JsonResponse

from common.utils import RedisUtil
from common.auth.internal.auth import InternalAuthentication
from padmin.subscription_account_reply.util import (
    validate_from_wechat,
    MsgHandler,
    push_template_message,
)
from padmin.query_manage.financial_query import FinancialQuery
from padmin.subscription_account_reply.access_token import RefreshTokenUtil

def reply(reply_account_type):
    def wrap_reply(func):
        @functools.wraps(func)
        def wrapper(request):
            if request.method == 'GET':  # 微信验证
                data = request.query_params
                response_string = validate_from_wechat(data, reply_account_type)
                return HttpResponse(response_string)

            # POST被动回复消息
            receive_xml_message = request.body.decode("utf-8")
            msg_handler = MsgHandler(receive_xml_message, reply_account_type)
            xml_response_data = msg_handler.get_reply_xml_string()
            return HttpResponse(xml_response_data)
        return wrapper
    return wrap_reply


@api_view(['GET', 'POST'])
@reply("user")
def reply_user(request):
    """被动回复用户公众号"""
    pass


@api_view(['GET', 'POST'])
@reply("merchant")
def reply_merchant(request):
    """被动回复商户公众号"""
    pass


@api_view(['GET', 'POST'])
@reply("marketer")
def reply_marketer(request):
    """被动回复业务员公众号"""
    pass


@api_view(['POST'])
@authentication_classes([InternalAuthentication,])
def push_merchant_month_bill(request):
    year, month, bill_list = FinancialQuery.query_merchant_month_bill()
    time_str = f'{year}年{month}月'
    for merchant_bill in bill_list:
        merchant_bill['bill'].update({'bill_month': time_str, 'month': month})
        temp_params = dict(
            account_type='merchant',  # user, merchant, marketer
            openid=merchant_bill['open_id'],
            content=merchant_bill['bill'],
            template_type='merchant_month_bill',  # 消息类型
        )
        push_template_message(temp_params)
    return JsonResponse({'result': 'OK'})


@api_view(['POST'])
@authentication_classes([InternalAuthentication,])
def refresh_access_token(request):
    """ 刷新access_token """

    params = request.data
    response_data = RefreshTokenUtil.refresh_token(params)
    return JsonResponse(response_data)


@api_view(['POST'])
@authentication_classes([InternalAuthentication,])
def obtain_access_token(request):
    token_data = {
        "merchant": RedisUtil.get_access_token("subscription_account_access_token_merchant"),
        "marketer": RedisUtil.get_access_token("subscription_account_access_token_marketer"),
        "user": RedisUtil.get_access_token("subscription_account_access_token_user")
    }
    return JsonResponse(token_data)




