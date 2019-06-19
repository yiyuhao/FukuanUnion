from rest_framework import serializers

from merchant.serializers import LoginSerializer
from marketer.utils.login import MarketerLoginHandler
from common.auth.wechat.login import LoginError
from common.models import Payment, Withdraw
import config


class MarketerLoginSerializer(LoginSerializer):
    """
    Serializer for marketer to login
    """

    def _authenticate(self, code):
        login_handler = MarketerLoginHandler()
        try:
            self.token = login_handler.login(code)
        except LoginError as e:
            self.fail(e.message)

    def create(self, validated_data):
        raise NotImplementedError('MarketerLoginSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MarketerLoginSerializer cannot be used to update')


class OperationDetailsSerializer(serializers.Serializer):
    object_id = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    amount = serializers.SerializerMethodField()
    detail_info = serializers.SerializerMethodField()
    channel = serializers.SerializerMethodField()
    transaction_type = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            return content_object.merchant.avatar_url
        else:
            return None

    def get_name(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            return content_object.merchant.name
        elif isinstance(content_object, Withdraw):
            code = content_object.withdraw_type
            name = config.WITHDRAW_TYPE[code]['name']
            return '提现到' + name + f'{"零钱" if code == config.WITHDRAW_TYPE.WECHAT else "钱包"}'
        else:
            return None

    def get_amount(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            return content_object.inviter_share
        elif isinstance(content_object, Withdraw):
            return content_object.amount

    def get_detail_info(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            return content_object.order_price
        elif isinstance(content_object, Withdraw):
            code = content_object.withdraw_type
            name = config.WITHDRAW_TYPE[code]['name']
            return name + f'{"零钱" if code == config.WITHDRAW_TYPE.WECHAT else "钱包"}'

    def get_channel(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            code = content_object.pay_channel
            return config.PAY_CHANNELS[code]['name'] + '支付'
        elif isinstance(content_object, Withdraw):
            code = content_object.withdraw_type
            marketer = obj.account.marketer
            return marketer.wechat_nickname if code == config.WITHDRAW_TYPE.WECHAT else marketer.alipay_id

    def get_transaction_type(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            return 'payment'
        if isinstance(content_object, Withdraw):
            return config.WITHDRAW_TYPE[content_object.withdraw_type]['code']

    def get_discount(self, obj):
        content_object = obj.content_object
        if isinstance(content_object, Payment):
            if not content_object.coupon:
                return None
            return content_object.coupon.discount
        return None

    def create(self, validated_data):
        raise NotImplementedError('OperationDetailsSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('OperationDetailsSerializer cannot be used to update')




