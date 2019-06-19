from django.db.transaction import atomic

from .base import ModelManagerBase
from common.models import Marketer
from marketer.model_manager import UserMerchantModelManager, UserTransactionModelManager, UserAccountModelManager


class MarketerModelManager(ModelManagerBase):
    """
    marketer数据表查询
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = Marketer

    def has_unionid(self, unionid):
        marketer = self.model.objects.filter(wechat_unionid=unionid)
        return marketer.first()

    def get_inviting_info(self, unionid):
        user = self.has_unionid(unionid)
        if not user:
            return None
        merchant_manager = UserMerchantModelManager(user=user)
        invited_merchants = merchant_manager.get_invited_merchant_num()
        using_invited_merchants_num = invited_merchants.get('using_merchants_num')
        reviewing_invited_merchants_num = invited_merchants.get('reviewing_merchants_num')
        transaction_manager = UserTransactionModelManager(user=user)
        user_share_transactions = transaction_manager.get_user_transactions(content_type='payment')
        if user_share_transactions:
            total_bonus = sum([transaction.amount for transaction in user_share_transactions])
        else:
            total_bonus = 0
        account_manager = UserAccountModelManager(user=user)
        user_withdrawable_balance = account_manager.get_withdrawable_balance()
        return dict(
            user_name=user.name,
            user_phone=user.phone,
            user_type=user.inviter_type,
            using_invited_merchants_num=using_invited_merchants_num,
            reviewing_invited_merchants_num=reviewing_invited_merchants_num,
            total_bonus=total_bonus,
            user_withdrawable_balance=user_withdrawable_balance['wechat']['balance'] +
                                      user_withdrawable_balance['alipay']['balance'],
            alipay_withdraw_balance=user_withdrawable_balance['alipay']['balance'],
            wechat_withdraw_balance=user_withdrawable_balance['wechat']['balance'],
            alipay_id=user.alipay_id,
            avatar=user.wechat_avatar_url,
        )

    def get_user_info(self, unionid):
        info = self.get_inviting_info(unionid=unionid)
        if not info:
            return None
        if (not info['using_invited_merchants_num']) and (not info['reviewing_invited_merchants_num']):
            user_status = 'no_inviting'
        elif (not info['using_invited_merchants_num']) and info['reviewing_invited_merchants_num']:
            user_status = 'no_sharing'
        else:
            user_status = 'normal'
        info.update(user_status=user_status)
        return info

    @classmethod
    def check_marketer_exists(cls, unionid):
        """ 根据微信unionid验证当前业务员是否已经授权"""
        return Marketer.objects.filter(wechat_unionid=unionid).exists()

    def check_phone_exist(self, phone):
        return self.model.objects.filter(phone=phone).exists()
