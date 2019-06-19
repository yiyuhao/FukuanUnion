# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from django.db.models import F, When, Case, BooleanField
from django.db.models.functions import Now
from django.utils import timezone

import config
from common.models import Coupon


class DbManager:

    @classmethod
    def get_coupons_merchant_valid(cls):
        return Coupon.objects.select_related('rule__merchant', 'originator_merchant').filter(
            payment=None,
            rule__merchant__status=config.MERCHANT_STATUS.USING)

    @classmethod
    def get_coupons_not_expired(cls, include_not_started_coupons=True):
        now = timezone.now()
        now_date = now.date()

        return cls.get_coupons_merchant_valid().annotate(
            not_expired=Case(
                When(rule__valid_strategy=config.VALID_STRATEGY.DATE_RANGE,
                     rule__start_date__lte=now_date if not include_not_started_coupons else timezone.datetime.max,
                     rule__end_date__gte=now_date,
                     then=True),
                When(rule__valid_strategy=config.VALID_STRATEGY.EXPIRATION,
                     rule__expiration_days__gt=(Now() - F('obtain_datetime')) / (
                             3600 * 24 * 1000 * 1000),  # noqa
                     then=True),
                default=False,
                output_field=BooleanField())).filter(not_expired=True)

    @classmethod
    def get_user_coupons_for_payment(cls, client_id, qr_code_uuid):
        return cls.get_coupons_not_expired(include_not_started_coupons=False).filter(
            client_id=client_id,
            rule__merchant__payment_qr_code__uuid=qr_code_uuid,
            status=config.COUPON_STATUS.NOT_USED)

    @classmethod
    def get_user_coupons_not_expired_and_not_used(cls, client_id):
        return cls.get_coupons_not_expired(include_not_started_coupons=True).filter(
            client_id=client_id,
            status=config.COUPON_STATUS.NOT_USED)
