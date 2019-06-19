# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import generics
from rest_framework import serializers

from common.models import Coupon
from common.models import CouponRule
from common.models import Merchant
from puser.core import coupon, auth


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = (
            'location_lon',
            'location_lat',
            'name',
            'category',
            'avatar_url',
            'address')

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class CouponRuleSerializer(serializers.ModelSerializer):
    merchant = MerchantSerializer()

    class Meta:
        model = CouponRule
        fields = (
            'merchant',
            'valid_strategy',
            'start_date',
            'end_date',
            'expiration_days',
            'photo_url',
            'note')

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class CouponSerializer(serializers.ModelSerializer):
    originator_merchant = serializers.SlugRelatedField(slug_field='name', read_only=True)
    rule = CouponRuleSerializer(read_only=True)

    class Meta:
        model = Coupon
        fields = (
            'id',
            'rule',
            'discount',
            'min_charge',
            'originator_merchant',
            'obtain_datetime')

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class CouponList(auth.BasicTokenAuthMixin, generics.ListAPIView):
    serializer_class = CouponSerializer
    pagination_class = None

    def get_queryset(self):
        client = self.request.user
        qr_code_uuid = self.request.query_params.get('uuid', None)

        if qr_code_uuid:
            # 有qr_code_uuid，说明是在支付的时候。
            # 这时需要返回当前支付能使用的优惠券，不包含未来可用的优惠券
            qs = coupon.DbManager.get_user_coupons_for_payment(client.id, qr_code_uuid)
        else:
            # 没有qr_code_uuid，说明是在用户端列表页。这时需要返回所有优惠券，包括未来能使用的优惠券
            qs = coupon.DbManager.get_user_coupons_not_expired_and_not_used(client.id)
        return qs
