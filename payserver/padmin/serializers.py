import json

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common import password_backend
from common.models import (
    SystemAdmin,
    LoginStats,
    Merchant,
    Marketer,
    City,
    Area,
    Account,
    MerchantAdmin,
    MerchantMarketerShip,
    Message,
    SubscriptionAccountReply,
)
from common.password_backend import make_password
from config import SYSTEM_USER_STATUS


class LoginStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginStats
        fields = ('id', 'last_success_login', 'last_success_ip',
                  'last_failed_login', 'last_failed_ip', 'failed_login_count')

    def create(self, validated_data):
        raise NotImplementedError('LoginStatsSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginStatsSerializer cannot be used to update')


class SystemAdminSerializer(serializers.ModelSerializer):
    login_stats = LoginStatsSerializer(read_only=True)

    class Meta:
        model = SystemAdmin
        fields = (
            'id', 'username', 'password', 'name', 'status', 'login_stats', 'permissions')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        with transaction.atomic():
            validated_data['login_stats'] = LoginStats.objects.create()
            validated_data['password'] = make_password(validated_data['password'])
            return super().create(validated_data)

    def update(self, instance, validated_data):

        instance.name = validated_data.get('name', instance.name)
        instance.permissions = validated_data.get('permissions', instance.permissions)
        instance.username = validated_data.get('username', instance.username)
        instance.status = validated_data.get('status', instance.status)
        password = validated_data.get('password', None)
        if password is not None:
            password = make_password(password)
            instance.password = password
        instance.save()

        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, style={'input_type': 'password'})

    default_error_messages = {
        'invalid_username_or_password': '用户名或密码错误',
        'user_disabled': '用户已经被禁用'
    }

    def __init__(self, client_ip=None, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.client_ip = client_ip
        self.user = None

    def validate(self, attrs):
        self.user = self._authenticate(
            username=attrs.get('username'),
            password=attrs.get('password')
        )

        return attrs

    def _authenticate(self, username, password):
        try:
            admin = SystemAdmin.objects.get(username=username)
        except SystemAdmin.DoesNotExist:
            raise self.fail('invalid_username_or_password')

        if admin.status == SYSTEM_USER_STATUS['DISABLED']:
            raise self.fail('user_disabled')

        is_password_ok = password_backend.check_password(password, admin.password)
        if not is_password_ok:
            admin.login_stats.last_failed_login = timezone.now()
            admin.login_stats.last_failed_ip = self.client_ip
            admin.login_stats.failed_login_count = F('failed_login_count') + 1
            admin.login_stats.save()
            admin.save()
            raise self.fail('invalid_username_or_password')

        admin.login_stats.last_success_login = timezone.now()
        admin.login_stats.last_success_ip = self.client_ip
        admin.login_stats.failed_login_count = 0
        admin.login_stats.save()
        admin.save()

        return admin

    def create(self, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to update')


class MerchantAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantAdmin
        fields = ('id', 'wechat_openid', 'merchant_admin_type', 'status', 'wechat_unionid',
                  'wechat_nickname', 'alipay_user_name', 'phone')


class MerchantSerializer(serializers.ModelSerializer):
    admins = MerchantAdminSerializer(many=True)

    class Meta:
        model = Merchant
        fields = '__all__'

        read_only_fields = ('account',)

    def update(self, instance, validated_data):

        instance.status = validated_data.get('status', instance.status)
        instance.name = validated_data.get('name', instance.name)
        instance.contact_phone = validated_data.get('contact_phone', instance.contact_phone)
        instance.description = validated_data.get('description', instance.description)
        instance.avatar_url = validated_data.get('avatar_url', instance.avatar_url)
        instance.license_url = validated_data.get('license_url', instance.license_url)
        instance.id_card_front_url = validated_data.get('id_card_front_url', instance.id_card_front_url)
        instance.id_card_back_url = validated_data.get('id_card_back_url', instance.id_card_back_url)
        instance.category = validated_data.get('category', instance.category)
        instance.save()

        return instance


class JsonField(serializers.Field):
    def to_representation(self, obj):
        return json.loads(obj)

    def to_internal_value(self, data):
        return data


class MessageSerializer(serializers.ModelSerializer):
    extra_data = JsonField(required=False)

    class Meta:
        model = Message
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

    def create(self, validated_data):
        raise NotImplementedError('MessageSerializer cannot be used to create')


class SubscriptionAccountReplySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionAccountReply
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.rule_name = validated_data.get('rule_name', instance.rule_name)
        instance.question_text = validated_data.get('question_text', instance.question_text)
        instance.reply_rule = validated_data.get('reply_rule', instance.reply_rule)
        instance.reply_text = validated_data.get('reply_text', instance.reply_text)
        instance.save()

        return instance


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name',)

    def create(self, validated_data):
        raise NotImplementedError('CitySerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to update')


class AreaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    city = CitySerializer(required=False, read_only=True)
    name = serializers.CharField(required=False, read_only=True)
    parent = serializers.CharField(required=False, read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('AreaSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to update')


AreaSerializer.parent = AreaSerializer(required=False, read_only=True)
AreaSerializer._declared_fields['parent'] = AreaSerializer.parent


class AccountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    balance = serializers.IntegerField(read_only=True)
    alipay_balance = serializers.IntegerField(read_only=True)
    bank_card_number = serializers.CharField(read_only=True)

    class Meta:
        model = Account
        fields = ('id', 'bank_name', 'bank_card_number', 'real_name',
                  'balance', 'alipay_balance')

    def create(self, validated_data):
        raise NotImplementedError('AccountSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('AccountSerializer cannot be used to update')


class InviterSerializer(serializers.ModelSerializer):
    account = AccountSerializer()

    class Meta:
        model = Marketer
        fields = (
            'id', 'inviter_type', 'status', 'name',
            'phone', 'id_card_front_url', 'id_card_back_url', 'account', 'alipay_id'
        )

    default_error_messages = {
        'data_error': '获取数据包中字段错误',
    }

    def create(self, validated_data):
        raise NotImplementedError('InviterSerializer cannot be used to create')

    def _update_fields(self, instance, data):
        for field in data:
            if hasattr(instance, field) and getattr(instance, field) != data[field]:
                setattr(instance, field, data[field])
        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            account_data = validated_data.pop('account', {})
            if account_data:
                account_data = {k: v for k, v in account_data.items()
                                if 'balance' not in k}
                try:
                    account_id = account_data.get('id', -1)
                    account = Account.objects.get(id=account_id)
                    account = self._update_fields(account, account_data)
                    account.save()
                    instance.account = account
                except Account.DoesNotExist:
                    raise self.fail('data_error')

            instance = self._update_fields(instance, validated_data)
            instance.save()
            return instance


class SalesmanSerializer(serializers.ModelSerializer):
    inviter_type = serializers.CharField()
    account = AccountSerializer(required=False)
    working_areas = AreaSerializer(many=True, required=False)

    class Meta:
        model = Marketer
        fields = (
            'id', 'name', 'status', 'phone', 'account', 'working_areas', 'worker_number',
            'inviter_type', 'id_card_front_url', 'id_card_back_url', 'alipay_id'
        )
        read_only_fields = ('alipay_id',)

    default_error_messages = {
        'invalid_work_area': '无效的工作区域'
    }

    def create(self, validated_data):
        raise NotImplementedError('SalesmanSerializer cannot be used to create')

    def update(self, instance, validated_data):
        new_working_areas = self._get_working_areas_objs(validated_data)
        with transaction.atomic():
            instance = self._update_fields(validated_data, instance)
            old_working_areas = instance.working_areas.all()
            instance = self._map_many_to_many(instance, new_working_areas, old_working_areas)
            instance.save()
            return instance

    def _get_working_areas_objs(self, validated_data):
        """ 根据传回的 area_id 字典组成的列表生成地点对象集 """
        working_areas = validated_data.get('working_areas', [])
        allow_working_areas = Area.objects.filter(~Q(parent_id=None))
        if len(working_areas) > allow_working_areas.count():
            raise self.fail('invalid_work_area')
        working_areas_objs = allow_working_areas.filter(id__in=working_areas)
        if allow_working_areas.count() < len(working_areas):
            raise self.fail('invalid_work_area')
        return working_areas_objs

    def _map_many_to_many(self, obj, new_working_areas, old_working_areas):
        """ 验证是否需要更新 / 添加多对多关系 """
        if not new_working_areas.exists():
            obj.working_areas.clear()
            return obj
        if old_working_areas:
            query_set = new_working_areas | old_working_areas
            if new_working_areas.count() == old_working_areas.count() == query_set.count():
                return obj
            obj.working_areas.clear()

        obj.working_areas.add(*new_working_areas)
        return obj

    def _check_update(self, instance, data):
        """ 检查是否更新　"""
        for field in data:
            if hasattr(instance, field) and getattr(instance, field) != data[field]:
                return True

    def _update_fields(self, data, instance):
        """ 添加 属性 """
        _ = data.pop('working_areas', None)
        account_data = data.pop('account', {})
        _ = account_data.pop('id', None)
        account_data = {k: v for k, v in account_data.items()
                        if 'balance' not in k}
        if self._check_update(instance.account, account_data):
            Account.objects.filter(id=instance.account_id).update(**account_data)
        instance.account = Account.objects.get(id=instance.account_id)
        for field in data:
            if hasattr(instance, field) and getattr(instance, field) != data[field]:
                setattr(instance, field, data[field])
        return instance


class MerchantMarketerShipSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantMarketerShip
        fields = ('id', 'marketer', 'merchant', 'audit_datetime',)

    def create(self, validated_data):
        raise NotImplementedError('MerchantMarketerShipSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantMarketerShipSerializer cannot be used to update')


class MarketerMerchantSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    avatar_url = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    address = serializers.SerializerMethodField()
    status = serializers.IntegerField(read_only=True)
    last_audited_time = serializers.CharField(read_only=True)
    audited_num = serializers.IntegerField(read_only=True)

    def get_address(self, obj):
        area_id = obj['area_id']
        area_res = Area.objects.select_related('parent').select_related('city').get(pk=area_id)
        return f'{area_res.city.name}{area_res.parent.name if area_res.parent else ""}{area_res.name}{obj["address"]}'

    def create(self, validated_data):
        raise NotImplementedError('AreaSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('LoginSerializer cannot be used to update')
