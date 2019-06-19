#      File: account_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/12
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging

from dynaconf import settings as dynasettings

from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.error_handler import MerchantError
from common.model_manager.base import ModelObjectManagerBase
from common.model_manager.utils import set_amount
from common.payment.alipay import AlipayUseCases
from common.payment.exceptions import BalanceInsufficient
from common.payment.wechat import WechatPaymentUseCases

logger = logging.getLogger(__name__)
wechat_payment = WechatPaymentUseCases()
alipay_payment = AlipayUseCases()


class AccountManager(ModelObjectManagerBase):
    """self.obj = account_model_instance"""

    def __init__(self, *args, **kwargs):
        super(AccountManager, self).__init__(*args, **kwargs)

    def wechat_withdraw(self, amount, client_ip,
                        app_id=dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MERCHANT):
        """微信提现 amount为0时不进行任何操作"""
        if amount != 0:
            try:
                wechat_payment.withdraw(self.obj, set_amount(amount), client_ip, app_id)
            except BalanceInsufficient:
                return MerchantError.withdrawable_balance_not_sufficient
            except (ApiRequestError, ApiReturnedError):
                return MerchantError.withdraw_api_error

        return None

    def alipay_withdraw(self, amount):
        """支付宝提现 amount为0时不进行任何操作"""
        if amount != 0:
            try:
                alipay_payment.withdraw(self.obj, set_amount(amount))
            except BalanceInsufficient:
                return MerchantError.withdrawable_balance_not_sufficient
            except (ApiRequestError, ApiReturnedError):
                return MerchantError.withdraw_api_error

        return None
