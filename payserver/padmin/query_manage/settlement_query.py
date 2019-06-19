# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

#   账单结算查询
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Sum, Case, When, F, Count
from django.utils import timezone
from rest_framework import status

from common.models import (
    Merchant,
    Payment,
    Account,
    Settlement,
    MerchantAdmin,
    Transaction
)
from django.core.paginator import Paginator
from config import (
    SETTLEMENT_STATUS,
    TRANSACTION_TYPE,
    PAYMENT_STATUS,
    MERCHANT_TYPE,
    PAY_CHANNELS,
    MERCHANT_STATUS,
    MERCHANT_ADMIN_TYPES,
)
from padmin.query_manage.query_until import fen_to_yuan_fixed_2, TimeStampUtil
from padmin.paginations import PAGE_SIZE
from padmin.exceptions import SettlementDuplicateException, SettlementAbnormalBalanceException
from padmin.subscription_account_reply.util import push_template_message
from common.payment.util import generate_serial_number


class SettlementUseCase:
    """ 商户结算 """
    
    @staticmethod
    def settlement(merchant_id, wechat_amount, alipay_amount):
        assert merchant_id is not None
        assert wechat_amount is not None
        assert alipay_amount is not None
        
        with transaction.atomic():
            now_timestamp = timezone.now()
            
            merchant_account_id = Merchant.objects.get(pk=merchant_id).account_id
            merchant_account = Account.objects.select_for_update().get(id=merchant_account_id)

            # 最近一条结算账单记账日期必须小于当前记账时间，避免重复结算
            latest_settlement = Settlement.objects.filter(account__id=merchant_account_id)\
                            .filter(status=SETTLEMENT_STATUS['PROCESSING']).order_by('-datetime').first()
            if latest_settlement and latest_settlement.datetime.date() >= now_timestamp.date():
                raise SettlementDuplicateException(
                    f"{now_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')} occur duplicate settlement"
                    f",merchant's account's id is {merchant_account_id},"
                    f" wechat_amount is {wechat_amount} fen, alipay_amount is {alipay_amount} fen")
            
            # 校验金额
            if merchant_account.balance < wechat_amount or \
                    merchant_account.withdrawable_balance < wechat_amount or \
                    merchant_account.alipay_balance < alipay_amount or \
                    merchant_account.alipay_withdrawable_balance < alipay_amount:
                raise SettlementAbnormalBalanceException(
                    f"{now_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')} occur abnormal balance settlement"
                    f",merchant's account's id is {merchant_account_id},"
                    f" wechat_amount is {wechat_amount} fen, alipay_amount is {alipay_amount} fen")
            
            # 账户扣钱
            if wechat_amount > 0:
                merchant_account.balance = merchant_account.balance - wechat_amount
                merchant_account.withdrawable_balance = merchant_account.withdrawable_balance - wechat_amount
            if alipay_amount > 0:
                merchant_account.alipay_balance = merchant_account.alipay_balance - alipay_amount
                merchant_account.alipay_withdrawable_balance = merchant_account.alipay_withdrawable_balance - alipay_amount
            merchant_account.save()
            
            new_settlement = Settlement.objects.create(
                serial_number=generate_serial_number(),
                datetime=now_timestamp,
                finished_datetime=None,
                status=SETTLEMENT_STATUS['PROCESSING'],
                account=merchant_account,
                wechat_amount=wechat_amount,
                alipay_amount=alipay_amount,
            )
            
            Transaction.objects.bulk_create([
                Transaction(
                    content_object=new_settlement,
                    transaction_type=TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'],
                    datetime=now_timestamp,
                    account=merchant_account,
                    amount=-wechat_amount,
                    balance_after_transaction=merchant_account.balance
                ),
                Transaction(
                    content_object=new_settlement,
                    transaction_type=TRANSACTION_TYPE['MERCHANT_ALIPAY_SETTLEMENT'],
                    datetime=now_timestamp,
                    account=merchant_account,
                    amount=-alipay_amount,
                    balance_after_transaction=merchant_account.alipay_balance
                )
            ])
            

class UpdateUnLiquidatedSettlementUseCase:
    @staticmethod
    def un_liquidated_settlement_update(serial_number):
        try:
            s = Settlement.objects.get(pk=serial_number)
            s.status = SETTLEMENT_STATUS['FINISHED']
            s.finished_datetime = timezone.now()
            s.save()
        except Settlement.DoesNotExist:
            return status.HTTP_400_BAD_REQUEST, {'detail': f'serial_number {serial_number} dose not exist'}

        merchant_admin = MerchantAdmin.objects.filter(merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN']) \
            .filter(work_merchant__account__id=s.account_id).first()
        if merchant_admin:
            params = {
                "account_type": 'merchant',
                "openid": merchant_admin.wechat_openid,
                "content": {
                    'first': (TimeStampUtil.get_yesterday(s.datetime)).strftime('%Y年%m月%d日'),
                    'keyword1': fen_to_yuan_fixed_2(s.wechat_amount + s.alipay_amount),
                    'keyword2': s.finished_datetime.strftime('%Y年%m月%d日 %H:%M'),
                },
                "template_type": 'merchant_settlement'  # 结算账单消息
            }
            push_template_message(params)
        return status.HTTP_200_OK, {'detail': 'ok'}


class LiquidatedSettlementQueryHelper:
    def __init__(self, start_date, end_date, merchant_name):
        self.start_date = start_date
        self.end_date = end_date
        self.merchant_name = merchant_name
        
    def get_queryset(self):
        queryset = Settlement.objects.select_related('account__merchant').filter(status=SETTLEMENT_STATUS['FINISHED'])
        
        if self.start_date:
            queryset = queryset.filter(finished_datetime__gte=self.start_date)
        
        if self.end_date:
            queryset = queryset.filter(finished_datetime__lte=self.end_date)

        if self.merchant_name:
            payment_qr_code = None
            try:
                payment_qr_code = int(self.merchant_name)
            except ValueError:
                queryset = queryset.filter(account__merchant__name=self.merchant_name)
            else:
                queryset = queryset.filter(Q(account__merchant__name=self.merchant_name)
                                           | Q(account__merchant__payment_qr_code=payment_qr_code))
        
        return queryset
        
    def count(self):
        queryset = self.get_queryset()
        result = queryset.aggregate(total_money=Sum(F('wechat_amount') + F('alipay_amount')), total=Count('serial_number'))
        return result['total'], fen_to_yuan_fixed_2(result['total_money'])

    def page_data(self, current_page, page_size):
        queryset = self.get_queryset()
    
        paginator = Paginator(queryset, page_size)
        total_page = paginator.num_pages
        page_data_list = []
    
        if 1 <= current_page <= total_page:
            page_obj = paginator.page(current_page)
            page_data_list = page_obj.object_list
    
        result_list = []
        for settlement in page_data_list:
            result_list.append({
                'serial_number': settlement.serial_number,
                'finished_datetime': settlement.finished_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'all_money': fen_to_yuan_fixed_2(settlement.wechat_amount+settlement.alipay_amount),
                'real_name': settlement.account.real_name,
                'bank_name': settlement.account.bank_name,
                'bank_card_number': settlement.account.bank_card_number,
                'merchant_name': f"{settlement.account.merchant.name}({settlement.account.merchant.payment_qr_code_id})",
            })
        return result_list
        

class SettlementQuery:
    @classmethod
    def query_liquidated_settlement_list(cls, query_params):
        """ 查询已结算账单 """
        current_page = query_params.get('page')
        try:
            current_page = int(current_page)
        except ValueError:
            current_page = 1
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        merchant_name = query_params.get('merchant_name')
        if start_date:
            start_date = TimeStampUtil.format_start_timestamp_microsecond(start_date)
        if end_date:
            end_date = TimeStampUtil.format_end_timestamp_microsecond(end_date)
        
        query_helper = LiquidatedSettlementQueryHelper(start_date, end_date, merchant_name)
        return current_page, query_helper
    
    @classmethod
    def query_un_liquidated_settlement_list(cls, query_params):
        current_page = query_params.get('page')
        try:
            current_page = int(current_page)
        except ValueError:
            current_page = 1
    
        q = Settlement.objects.select_related('account__merchant__payment_qr_code') \
            .filter(status=SETTLEMENT_STATUS['PROCESSING']).order_by('-datetime')
    
        paginator = Paginator(q, PAGE_SIZE)
        total_page = paginator.num_pages
        page_data_list = []
    
        if 1 <= current_page <= total_page:
            page_obj = paginator.page(current_page)
            page_data_list = page_obj.object_list
    
        result_list = []
        for settlement in page_data_list:
            result_list.append({
                'datetime': settlement.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'merchant_name': f"{settlement.account.merchant.name}"
                                 f"(M{settlement.account.merchant.payment_qr_code_id})",
                'account_name': settlement.account.real_name,
                'bank_name': settlement.account.bank_name,
                'bank_card_number': settlement.account.bank_card_number,
                'money': fen_to_yuan_fixed_2(settlement.alipay_amount + settlement.wechat_amount),
                'serial_number': settlement.serial_number,
            })

        return dict(
            page=current_page,
            total=paginator.count,
            data=result_list,
        )

    @classmethod
    def query_enterprise_merchant_pure_profit_by_day(cls):
    
        # 根据当前时间求出昨日 00:00:00:000000 - 23:59:59:999999
        curr_time = timezone.now()
        yesterday_start = curr_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = Payment.objects.filter(Q(status=PAYMENT_STATUS['FINISHED'])
                                       & Q(merchant__type=MERCHANT_TYPE['ENTERPRISE'])
                                       & Q(merchant__status=MERCHANT_STATUS['USING'])
                                       & Q(datetime__gte=yesterday_start)
                                       & Q(datetime__lte=yesterday_end)
                                       ) \
            .values('merchant') \
            .annotate(
            total_wechat=Sum(Case(When(coupon__isnull=True, pay_channel=PAY_CHANNELS['WECHAT'], then='order_price', ),
                                  default=0))
                         + Sum(Case(When(coupon__isnull=False, pay_channel=PAY_CHANNELS['WECHAT'],
                                         then=F('order_price') - F('coupon__discount') - F('platform_share') - F(
                                             'inviter_share')
                                              - F('originator_share'), ), default=0)
                               ),
            total_alipay=Sum(Case(When(coupon__isnull=True, pay_channel=PAY_CHANNELS['ALIPAY'], then='order_price', ),
                                  default=0))
                         + Sum(Case(When(coupon__isnull=False, pay_channel=PAY_CHANNELS['ALIPAY'],
                                         then=F('order_price') - F('coupon__discount') - F('platform_share') - F(
                                             'inviter_share')
                                              - F('originator_share'), ), default=0)
                               ),

        ).order_by('merchant')

        return list(query)
