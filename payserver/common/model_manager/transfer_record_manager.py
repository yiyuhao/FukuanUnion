#!/usr/bin/python3
#
#   Project: payunion
#    Author: Tian Xu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.error_handler import MarketerError
from common.models import TransferRecord
from common.payment.alipay import AlipayUseCases
from common.payment.exceptions import BalanceInsufficient
from config import TRANSFER_STATUS

alipay_payment = AlipayUseCases()


class TransferRecordManager:
    """ 支付宝转账记录 """

    @staticmethod
    def check_transfer_success(unionid, account_number=None, account_name=None):
        """
        查询针对该用户名和账号转账成功记录
        :param unionid:
        :param account_number:
        :param account_name:
        :return:
        """
        filter_params = dict(
            wechat_unionid=unionid, status=TRANSFER_STATUS.FINISHED)
        if account_number and account_name:
            filter_params.update(
                account_number=account_number, account_name=account_name)

        success_record = TransferRecord.objects.filter(**filter_params).first()

        data = dict(exist=False, record={})
        if success_record:
            data = dict(exist=True, record=dict(
                account_name=success_record.account_name,
                account_number=success_record.account_number
            ))

        return data

    @staticmethod
    def transfer_to_account(unionid, account_number, account_name, amount):
        """
        转账到单个支付宝账户
        :param unionid:  微信unionid
        :param account_number:  支付宝账号(一般是手机、邮箱)
        :param account_name:  支付宝用户真实姓名
        :param amount:  转账金额
        :return:
        """
        try:
            alipay_payment.transfer(unionid, account_number, account_name, amount)
        except BalanceInsufficient:
            return MarketerError.platform_balance_not_sufficient['detail']
        except (ApiRequestError, ApiReturnedError):
            return MarketerError.transfer_api_error['detail']

        return None



