#      File: serializers.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import json
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from common.auth.wechat.login import LoginError, MerchantLoginHandler
from common.error_handler import MerchantError
from common.model_manager.utils import set_amount, get_amount, get_bank_name
from common.models import CouponRule, Payment, Account, Merchant, Area, MerchantAdmin
from config import TRANSACTION_TYPE, VALID_STRATEGY, MIN_WITHDRAW_AMOUNT, \
    WECHAT_MAX_WITHDRAW_AMOUNT, \
    ALIPAY_MAX_WITHDRAW_AMOUNT, MERCHANT_ADMIN_TYPES, SYSTEM_USER_STATUS, MERCHANT_STATUS, \
    PAY_CHANNELS


class UpdateSlugRelatedField(serializers.SlugRelatedField):
    default_error_messages = MerchantError.to_error_msg()

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            self.fail(MerchantError.area_not_exist['error_code'])
        except (TypeError, ValueError):
            self.fail('invalid')


class MerchantSerializer(serializers.ModelSerializer):
    area = UpdateSlugRelatedField(many=False, queryset=Area.objects.all(), slug_field='adcode')
    alipay_user_name = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()
    bank_card_number = serializers.SerializerMethodField()
    bank = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()

    default_error_messages = MerchantError.to_error_msg()

    class Meta:
        model = Merchant
        fields = (
            'id', 'status', 'name', 'category', 'photo_url', 'description', 'contact_phone', 'avatar_url',
            'location_lon', 'location_lat', 'address', 'id_card_front_url', 'id_card_back_url', 'license_url',
            'area', 'alipay_user_name', 'real_name', 'bank_card_number', 'bank', 'bank_name',
        )
        read_only_fields = ('status', 'alipay_user_name', 'real_name', 'bank_card_number', 'bank', 'bank_name',)

    def get_alipay_user_name(self, obj):
        return obj.admins.filter(
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN).first().alipay_user_name

    def get_real_name(self, obj):
        return obj.account.real_name

    def get_bank_card_number(self, obj):
        return obj.account.bank_card_number

    def get_bank(self, obj):
        return get_bank_name(obj.account.bank_name) if obj.account.bank_name else None

    def get_bank_name(self, obj):
        return obj.account.bank_name

    def validate(self, attrs):
        if 'id_card_front_url' in attrs or 'id_card_back_url' in attrs:
            # 身份证图片必须同时上传
            if 'id_card_front_url' not in attrs or 'id_card_back_url' not in attrs:
                self.fail(MerchantError.must_upload_both_front_and_back_id_card_url['error_code'])
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('MerchantSerializer cannot be used to create')

    def update(self, instance, validated_data):
        instance.status = MERCHANT_STATUS['REVIEWING']
        instance.update_datetime = timezone.now()
        instance = super(MerchantSerializer, self).update(instance, validated_data)
        return instance


class MerchantAuthSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)

    def create(self, validated_data):
        raise NotImplementedError('MerchantAuthSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantAuthSerializer cannot be used to update')


class MerchantDayBeginMinuteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ('day_begin_minute',)

    def update(self, instance, validated_data):
        value = validated_data.get('day_begin_minute')
        if value is not None and value != instance.day_begin_minute:
            instance.day_begin_minute = value
            instance.save()
        return instance

    def create(self, validated_data):
        raise NotImplementedError('MerchantDayBeginMinuteSerializer cannot be used to create')


class MerchantWithdrawSerializer(serializers.ModelSerializer):
    channel = serializers.IntegerField(min_value=PAY_CHANNELS.WECHAT, max_value=PAY_CHANNELS.ALIPAY)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2,
                                      min_value=MIN_WITHDRAW_AMOUNT,
                                      max_value=ALIPAY_MAX_WITHDRAW_AMOUNT)

    class Meta:
        model = Account
        fields = ('channel', 'amount')

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        channel = attrs.get('channel')
        amount = attrs.get('amount')

        if channel == PAY_CHANNELS.WECHAT and WECHAT_MAX_WITHDRAW_AMOUNT < amount:
            self.fail(MerchantError.exceeding_the_wechat_maximum_withdrawal_balance['error_code'])

        # 可提现余额不足
        if (channel == PAY_CHANNELS.WECHAT and self.instance.withdrawable_balance < set_amount(
                amount)) \
                or (
                channel == PAY_CHANNELS.ALIPAY and self.instance.alipay_withdrawable_balance < set_amount(
            amount)):
            self.fail(MerchantError.withdrawable_balance_not_sufficient['error_code'])

        return attrs

    def create(self, validated_data):
        raise NotImplementedError('MerchantWithdrawSerializer cannot be used to create')


class LoginSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

    default_error_messages = MerchantError.to_error_msg()

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.token = None
        self.user = None

    def _authenticate(self, code):
        login_handler = MerchantLoginHandler()
        try:
            self.token = login_handler.login(code)
            self.user = login_handler.user
        except LoginError as e:
            self.fail(e.message)

    def validate(self, attrs):
        self._authenticate(code=attrs.get('code'))
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to update')


class TransactionListInputSerializer(serializers.Serializer):
    transaction_type = serializers.CharField()

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        if attrs.get('transaction_type') not in ('turnover', 'originator_earning', 'withdraw', 'settlement', 'all'):
            self.fail(MerchantError.unsupported_transaction_type['error_code'])
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('TransactionListInputSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('TransactionListInputSerializer cannot be used to update')


class TransactionTypeSerializer(serializers.Serializer):
    transaction_type = serializers.IntegerField(min_value=0,
                                                max_value=TRANSACTION_TYPE['MARKETER_WITHDRAW'])

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        if attrs.get('transaction_type') not in (
                TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                TRANSACTION_TYPE['MERCHANT_SHARE'],
                TRANSACTION_TYPE['MERCHANT_WITHDRAW'],
                TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'],
        ):
            self.fail('invalid transaction type')

        return attrs

    def create(self, validated_data):
        raise NotImplementedError('TransactionTypeSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('TransactionTypeSerializer cannot be used to update')


class MerchantDatetimeFilterSerializer(serializers.Serializer):
    start_date = serializers.CharField(min_length=10, max_length=10)
    end_date = serializers.CharField(min_length=10, max_length=10)

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        super(MerchantDatetimeFilterSerializer, self).validate(attrs)
        try:
            for k, v in attrs.items():
                attrs[k] = datetime.strptime(v, '%Y-%m-%d')
            # end_time 变为第二天0刻
            attrs['end_date'] = attrs['end_date'] + timedelta(days=1)
        except ValueError:
            self.fail(MerchantError.invalid_date_format['error_code'])
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('MerchantDatetimeFilterSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantDatetimeFilterSerializer cannot be used to update')


class MerchantListEarningSerializer(serializers.Serializer):
    start_date = serializers.CharField(min_length=10, max_length=10)

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        super(MerchantListEarningSerializer, self).validate(attrs)
        try:
            attrs['start_date'] = datetime.strptime(attrs['start_date'], '%Y-%m-%d').date()
        except ValueError:
            self.fail(MerchantError.invalid_date_format['error_code'])
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('MerchantDatetimeFilterSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantDatetimeFilterSerializer cannot be used to update')


class CouponRuleSerializer(serializers.Serializer):
    discount = serializers.DecimalField(min_value=0, max_value=99999, decimal_places=0,
                                        max_digits=7)
    min_charge = serializers.DecimalField(min_value=0, max_value=99999, decimal_places=0,
                                          max_digits=7)
    valid_strategy = serializers.IntegerField(min_value=VALID_STRATEGY['DATE_RANGE'],
                                              max_value=VALID_STRATEGY['EXPIRATION'])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    expiration_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    stock = serializers.IntegerField(min_value=0)
    photo_url = serializers.CharField(max_length=1024, required=False)
    note = serializers.CharField(max_length=300, required=False)

    default_error_messages = MerchantError.to_error_msg()

    def validate(self, attrs):
        now = timezone.now()
        # update CouponRule, only has param 'stock'
        if 'discount' not in attrs:
            return attrs

        # create CouponRule
        attrs['discount'] = set_amount(attrs['discount'])
        attrs['min_charge'] = set_amount(attrs['min_charge'])

        # 最低消费 > 优惠减免
        if not float(attrs['discount']) < float(attrs['min_charge']):
            self.fail(MerchantError.min_charge_must_greater_than_discount['error_code'])

        # 指定日期区间时
        if attrs['valid_strategy'] == VALID_STRATEGY['DATE_RANGE']:
            # 必须传入参数start_date与end_date
            if attrs.get('start_date') is None or attrs.get('end_date') is None:
                self.fail(MerchantError.must_have_param_start_date_and_end_date['error_code'])
            # 开始日期 <= 结束日期
            if not attrs['start_date'] <= attrs['end_date']:
                self.fail(MerchantError.end_date_must_greater_than_start_date['error_code'])

            # 时间段：开始时间可选择1年内
            if attrs['start_date'] > now.date().replace(year=now.year + 1):
                self.fail(MerchantError.start_date_must_be_in_1_year['error_code'])

            # 时间段：结束时间按开始时间起计算的1年内
            if attrs['end_date'] > attrs['start_date'].replace(year=now.year + 1):
                self.fail(MerchantError.start_date_must_be_in_1_year_from_start_date['error_code'])

        # 指定有效天数时
        if attrs['valid_strategy'] == VALID_STRATEGY['EXPIRATION']:
            if attrs.get('expiration_days') is None:
                self.fail(MerchantError.must_have_param_expiration_days['error_code'])

        return attrs

    def update(self, instance, validated_data):
        stock = validated_data.get('stock')
        if stock is not None and stock != instance.stock:
            instance.stock = stock
            instance.update_datetime = timezone.now()
            instance.save()
        return instance

    def create(self, validated_data):
        return CouponRule.objects.create(**validated_data)

    def to_representation(self, instance):
        """customize serializer.data"""
        ret = super(CouponRuleSerializer, self).to_representation(instance)
        ret = (json.loads(json.dumps(ret)))  # ret is immutable object, change it to dict
        ret['discount'] = get_amount(ret['discount'])
        ret['min_charge'] = get_amount(ret['min_charge'])
        return ret


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('note',)

    default_error_messages = MerchantError.to_error_msg()

    def update(self, instance, validated_data):
        note = validated_data.get('note') or ''
        if note != instance.note:
            instance.note = note
            instance.save()
        return instance

    def create(self, validated_data):
        raise NotImplementedError('PaymentSerializer cannot be used to create')


class CashierSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    wechat_openid = serializers.CharField(max_length=128)
    wechat_unionid = serializers.CharField(max_length=128, required=False)
    wechat_avatar_url = serializers.CharField(max_length=1024)
    wechat_nickname = serializers.CharField(max_length=128)

    def create(self, validated_data):
        # update cashier if he has been deleted.
        cashier = MerchantAdmin.objects.filter(
            wechat_unionid=validated_data['wechat_unionid']).first()
        if cashier:
            for attr, value in validated_data.items():
                setattr(cashier, attr, value)
            cashier.status = SYSTEM_USER_STATUS['USING']
            cashier.save()
            return cashier

        # else create
        return MerchantAdmin.objects.create(
            **validated_data,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            status=SYSTEM_USER_STATUS['USING'],
        )

    def update(self, instance, validated_data):
        raise NotImplementedError('CashierSerializer cannot be used to update')


class MerchantAdminVoiceOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantAdmin
        fields = ('voice_on',)

    def create(self, validated_data):
        raise NotImplementedError('MerchantDayBeginMinuteSerializer cannot be used to create')