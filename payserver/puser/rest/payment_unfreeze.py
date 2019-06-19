# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import views
from rest_framework.response import Response

import config
from common.auth.internal.auth import InternalAuthentication
from common.models import Payment
from common.payment.base import PaymentBaseUseCases
from common.payment.exceptions import InvalidStatusError

logger = logging.getLogger(__name__)


class PaymentUnfreezeView(views.APIView):
    authentication_classes = [InternalAuthentication]

    def post(self, request):
        frozen_payments = Payment.objects.filter(
            status=config.PAYMENT_STATUS.FROZEN,
            datetime__lte=timezone.now() - timedelta(seconds=config.PAYMENT_FROZEN_TIME)
        )
        for p in frozen_payments:
            try:
                PaymentBaseUseCases.on_payment_unfreeze(p)
                logger.info(f'unfreeze payment:{p.serial_number}')
            except InvalidStatusError as e:
                logger.warning(f'InvalidStatusError in PaymentUnfreezeView:{e}')

        return Response(data='OK')
