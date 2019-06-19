# -*- coding: utf-8 -*-
#       File: wechat_msg_send.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-7-26
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging

from common.models import MerchantAdmin
from config import SYSTEM_USER_STATUS
from padmin.subscription_account_reply.util import push_template_message

logger = logging.getLogger(__name__)


class MerchantMessageSender:
    """send wechat message to all merchant_admins"""

    def __init__(self, merchant):
        self.merchant_admins = MerchantAdmin.objects.filter(
            work_merchant=merchant,
            status=SYSTEM_USER_STATUS['USING'],
        )

    def on_refund_success(self, refund_amount, refund_datetime, refund_serial_number):
        for user in self.merchant_admins:
            params = {
                "account_type": 'merchant',
                "openid": user.wechat_openid,
                "content": {
                    'first': '账单已成功退款至用户',
                    'keyword1': refund_amount,
                    'keyword2': '已完成',
                    'keyword3': refund_datetime.strftime('%Y年%m月%d日 %H:%M'),
                    'remark': f'订单编号：{refund_serial_number}',
                    'serial_number': refund_serial_number
                },
                "template_type": 'merchant_refund_success'  # 消息类型"
            }
            push_template_message(params)

    def on_refund_fail(self, refund_amount, refund_datetime, refund_serial_number):
        for user in self.merchant_admins:
            params = {
                "account_type": 'merchant',
                "openid": user.wechat_openid,
                "content": {
                    'first': '退款失败，请在小程序重新操作，或联系客服',
                    'keyword1': refund_serial_number,
                    'keyword2': refund_amount,
                    'keyword3': '失败',
                    'keyword4': refund_datetime.strftime('%Y年%m月%d日 %H:%M'),
                },
                "template_type": 'merchant_refund_fail'  # 消息类型"
            }
            push_template_message(params)

    def on_pay_success(self, merchant_receive, payment_type, datetime, pay_serial_number):
        for user in self.merchant_admins:
            params = {
                "account_type": 'merchant',
                "openid": user.wechat_openid,
                "content": {
                    'first': '收款已到帐，可进入小程序查看详情',
                    'keyword1': payment_type,
                    'keyword2': merchant_receive,
                    'keyword3': datetime.strftime('%Y年%m月%d日 %H:%M'),
                    'serial_number': pay_serial_number,
                },
                "template_type": 'merchant_receive'
            }
            push_template_message(params)


class MerchantAdminMessageSender:

    def __init__(self, merchant_admin):
        self.merchant_admin = merchant_admin

    def wait_to_be_audit(self, merchant_name, commit_time):
        params = {
            "account_type": 'merchant',
            "openid": self.merchant_admin.wechat_openid,
            "content": {
                'merchant_name': merchant_name,
                'commit_time': commit_time.strftime('%Y年%m月%d日 %H:%M'),
            },
            "template_type": 'merchant_commit_info'  # 商户新增、信息修改"
        }
        push_template_message(params)

    def audited_success(self, audited_date):
        params = {
            "account_type": 'merchant',
            "openid": self.merchant_admin.wechat_openid,
            "content": {
                'pass_time': audited_date.strftime('%Y年%m月%d日 %H:%M'),
            },
            "template_type": 'merchant_be_approved'  # 被审核通过"
        }
        push_template_message(params)

    def audited_fail(self, reason, audited_date):
        params = {
            "account_type": 'merchant',
            "openid": self.merchant_admin.wechat_openid,
            "content": {
                'reason': f"{reason}"
            },
            "template_type": 'merchant_not_be_approved'  # 审核不通过"
        }
        push_template_message(params)


class MarketerMessageSender:
    def __init__(self, merchant):
        self.merchant = merchant

    def salesman_marchant_audit(self, marketer_openid, apply_date):
        params = {
            "account_type": 'marketer',
            "openid": marketer_openid,
            "content": {
                'applicant': self.merchant.name,
                'apply_time': apply_date.strftime('%Y年%m月%d日 %H:%M'),
            },
            "template_type": 'marketer_audit_merchant'  # 新的商户需要被审核"
        }
        push_template_message(params)

    def inviter_marchant_audited(self, marketer_openid, audited_date):
        params = {
            "account_type": 'marketer',
            "openid": marketer_openid,
            "content": {
                'merchant_name': self.merchant.name,
                'pass_time': audited_date.strftime('%Y年%m月%d日 %H:%M'),
            },
            "template_type": 'inviter_invite_merchant_pass'  # 邀请的商户被审核通过"
        }
        push_template_message(params)
