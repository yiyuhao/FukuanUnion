import json

from rest_framework import serializers

import config
from common.model_manager.marketer_manager import MarketerModelManager
from common.models import Marketer
from common.msg_service.sms_send import VerifySmsCode
from marketer.model_manager import CreateMarketerManager
from marketer.utils.redis_utils import RedisUtil


class CreateMarketerBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marketer
        fields = ('name', 'alipay_id', 'phone', 'id_card_front_url', 'id_card_back_url', 'id', 'verify_code')

    verify_code = serializers.CharField(write_only=True)
    id = serializers.IntegerField(read_only=True)

    def validate_phone(self, phone):
        manager = MarketerModelManager()
        if manager.check_phone_exist(phone):
            raise serializers.ValidationError('电话号码已被其他邀请人或业务员绑定')
        return phone

    def validate(self, attrs):
        verify_instace = VerifySmsCode(phone=attrs.get('phone'), verify_code=attrs.get('verify_code'))
        if not verify_instace.verify(delete_cache=True):
            raise serializers.ValidationError('验证码错误')
        attrs.pop('verify_code')
        return attrs

    def create(self, validated_data):
        manager = CreateMarketerManager()
        unionid = self.context['request'].user.get('unionid')
        wechat_info = json.loads(RedisUtil.load_data(unionid))
        extra_data = dict(
            wechat_openid=wechat_info['openid'],
            wechat_unionid=unionid,
            wechat_avatar_url=wechat_info['headimgurl'],
            wechat_nickname=wechat_info['nickname'],
            inviter_type=config.MARKETER_TYPES.MARKETER,
            status=config.SYSTEM_USER_STATUS.USING,
        )
        validated_data.update(extra_data)
        return manager.create(validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('CreateMarketerBaseSerializer cannot be used for updating')


class UpdateMarketerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marketer
        fields = (
            'phone',
            'verify_code'
        )

    verify_code = serializers.CharField(write_only=True)

    def validate_phone(self, phone):
        manager = MarketerModelManager()
        if manager.check_phone_exist(phone):
            raise serializers.ValidationError('电话号码已被其他邀请人或业务员绑定')
        return phone

    def validate(self, attrs):
        if attrs.get('phone'):
            verify_instace = VerifySmsCode(phone=attrs.get('phone'), verify_code=attrs.get('verify_code'))
            if not verify_instace.verify(delete_cache=True):
                raise serializers.ValidationError('验证码错误')
            attrs.pop('verify_code')
        return attrs

    def create(self, validated_data):
        raise NotImplementedError('UpdateMarketerSerializer cannot be used for updating')
