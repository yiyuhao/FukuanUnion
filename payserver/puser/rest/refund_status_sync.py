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
from common.models import Refund
from puser.tasks import wechat_refund_status_sync

logger = logging.getLogger(__name__)


class RefundStatusSyncView(views.APIView):
    authentication_classes = [InternalAuthentication]

    def post(self, request):
        in_process_refunds = Refund.objects.filter(
            status=config.REFUND_STATUS.REQUESTED,
            datetime__gte=timezone.now() - timedelta(seconds=config.REFUND_STATUS_SYNC_TIME_WINDOW)
        )
        for r in in_process_refunds:
            wechat_refund_status_sync.delay(r.serial_number)
            logger.info(f'submitted refund status sync task:{r.serial_number}')

        return Response(data='OK')
