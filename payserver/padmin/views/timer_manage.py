# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from rest_framework.decorators import api_view, authentication_classes
from django.http import JsonResponse

from common.auth.internal.auth import InternalAuthentication
from padmin.query_manage.settlement_query import SettlementQuery, SettlementUseCase
from padmin.exceptions import SettlementDuplicateException, SettlementAbnormalBalanceException

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([InternalAuthentication, ])
def timer_generate_settlement_bill(request):
    """ 定时生成结算账单"""

    bill_list = SettlementQuery.query_enterprise_merchant_pure_profit_by_day()
    for bill in bill_list:
        if bill['total_wechat'] == 0 and bill['total_alipay'] == 0:
            continue
        try:
            SettlementUseCase.settlement(bill['merchant'],
                                         bill['total_wechat'],
                                         bill['total_alipay']
                                         )
        except (SettlementDuplicateException, SettlementAbnormalBalanceException) as e:
            logger.error(repr(e))
            
    return JsonResponse(dict(result='OK'))
