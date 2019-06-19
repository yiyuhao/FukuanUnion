from rest_framework import serializers

from common.error_handler import MarketerError
from common.model_manager.utils import set_amount
from common.models import Account
from config import WECHAT_MAX_WITHDRAW_AMOUNT, ALIPAY_MAX_WITHDRAW_AMOUNT, MIN_WITHDRAW_AMOUNT, PAY_CHANNELS


class MarketerWithdrawSerializer(serializers.ModelSerializer):
    channel = serializers.IntegerField(min_value=PAY_CHANNELS.WECHAT, max_value=PAY_CHANNELS.ALIPAY)
    amount = serializers.DecimalField(max_digits=20,
                                      decimal_places=2,
                                      min_value=MIN_WITHDRAW_AMOUNT,
                                      max_value=ALIPAY_MAX_WITHDRAW_AMOUNT)

    class Meta:
        model = Account
        fields = ('channel', 'amount')

    default_error_messages = MarketerError.to_error_msg()

    def validate(self, attrs):
        channel = attrs.get('channel')
        amount = attrs.get('amount')

        if channel == PAY_CHANNELS.WECHAT and WECHAT_MAX_WITHDRAW_AMOUNT < amount:
            self.fail(MarketerError.exceeding_the_wechat_maximum_withdrawal_balance['error_code'])

        # 可提现余额不足
        if (channel == PAY_CHANNELS.WECHAT and self.instance.withdrawable_balance < set_amount(amount)) \
                or (channel == PAY_CHANNELS.ALIPAY and self.instance.alipay_withdrawable_balance < set_amount(amount)):
            self.fail(MarketerError.withdrawable_balance_not_sufficient['error_code'])

        return attrs

    def create(self, validated_data):
        raise NotImplementedError('MerchantWithdrawSerializer cannot be used to create')


class MerchantCreateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            'bank_name',
            'bank_card_number',
            'real_name'
        )

    def create(self, validate_data):
        raise NotImplementedError('`MerchantCreateAccountSerializer` cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('`MerchantCreateAccountSerializer` cannot be used to update')


class VerifyAccountSerializer(serializers.Serializer):
    acctName = serializers.CharField(max_length=128)
    bankName = serializers.CharField(max_length=128)
    cardno = serializers.RegexField(regex='^\d+$', max_length=128)

    def create(self, validate_data):
        raise NotImplementedError('VerifyAccountSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('VerifyAccountSerializer cannot be used to update')

