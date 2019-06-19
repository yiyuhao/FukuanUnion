#      File: merchant_admin.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/22
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from config import SYSTEM_USER_STATUS
from common.models import MerchantAdmin
from .base import ModelObjectManagerBase, ModelManagerBase
from .merchant_manager import MerchantManager


class MerchantAdminManager(ModelObjectManagerBase):
    """self.obj = merchant_admin_model_instance"""

    def __init__(self, *args, **kwargs):
        super(MerchantAdminManager, self).__init__(*args, **kwargs)

    @property
    def work_merchant(self):
        return MerchantManager(self.obj.work_merchant)

    @property
    def insensitive_alipay_user_name(self):
        """张大三 --> **三"""
        name = self.obj.alipay_user_name
        return f'{"*" * (len(name) - 1)}{name[-1]}'


class MerchantAdminModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(MerchantAdminModelManager, self).__init__(*args, **kwargs)
        self.model = MerchantAdmin

    def get_merchant_admin(self, wechat_unionid):
        merchant_admin = self.model.objects.filter(
            wechat_unionid=wechat_unionid
        ).select_related(
            'work_merchant'
        ).first()
        return merchant_admin

    @staticmethod
    def remove_cashier(cashier):
        """删除收银员"""
        cashier.status = SYSTEM_USER_STATUS['DISABLED']
        cashier.save()
