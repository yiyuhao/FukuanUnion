#      File: merchant_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncDate, Coalesce
from django.utils.timezone import timedelta, now

from common.model_manager.base import ModelObjectManagerBase
from common.model_manager.utils import get_amount
from common.models import Transaction, MerchantAdmin, Payment
from config import TRANSACTION_TYPE, MERCHANT_ADMIN_TYPES, SYSTEM_USER_STATUS, PAYMENT_STATUS


class MerchantManager(ModelObjectManagerBase):
    """self.obj = merchant_model_instance"""

    def __init__(self, *args, **kwargs):
        super(MerchantManager, self).__init__(*args, **kwargs)

    @property
    def merchant_admin(self):
        return MerchantAdmin.objects.get(
            work_merchant=self.obj,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN']
        )

    @property
    def account_wechat_balance(self):
        """商户账户微信余额"""
        return get_amount(self.obj.account.balance)

    @property
    def account_wechat_withdraw_balance(self):
        """商户账户微信可提现金额"""
        amount = get_amount(self.obj.account.withdrawable_balance)

        # 不足微信最小可提现余额时, 可提现余额前端显示为0
        return amount

    @property
    def account_alipay_balance(self):
        """商户账户支付宝余额"""
        return get_amount(self.obj.account.alipay_balance)

    @property
    def account_alipay_withdraw_balance(self):
        """商户账户支付宝可提现金额"""
        amount = get_amount(self.obj.account.alipay_withdrawable_balance)

        # 不足支付宝最小可提现余额时, 可提现余额前端显示为0
        return amount

    def today_business_report(self):
        # 加上营业开始时间
        now_ = now()
        today_begin = now_.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=self.day_begin_minute)

        if now_ < today_begin:  # 未到今日营业开始时间， 当前时间归于昨日账单结算
            today_begin -= timedelta(days=1)

        return self.merchant_business_report(
            datetime_start=today_begin,
            datetime_end=now_,
        )

    def merchant_business_report(self, datetime_start, datetime_end) -> dict:
        """
        经营报表数据 (营业额, 收款单数, 引流支出, 引流收益)
        :return {
                    "turnover": 1000.1,
                    "payment": {
                        "use_coupon": 1,
                        "not_use_coupon": 10
                    },
                    "originator_earning": 10.01,
                    "originator_expenditure": 1
                }
        """
        not_refund_status = [PAYMENT_STATUS.FROZEN, PAYMENT_STATUS.REFUND_REQUESTED,
                             PAYMENT_STATUS.REFUND_FAILED, PAYMENT_STATUS.FINISHED]

        result = Payment.objects.filter(
            merchant=self.obj,
        ).exclude(
            status__in=(PAYMENT_STATUS.UNPAID, PAYMENT_STATUS.CANCELLED),
        ).filter(
            Q(datetime__gte=datetime_start),
            Q(datetime__lt=datetime_end),
        ).aggregate(
            # 所有账单总金额 - 优惠券总减免金额
            turnover=Sum(
                'order_price', filter=Q(status__in=not_refund_status)) - Coalesce(
                Sum('coupon__discount', filter=Q(coupon__isnull=False, status__in=not_refund_status)), 0),
            originator_expenditure=Sum(
                'platform_share', filter=Q(status__in=not_refund_status)) + Sum(
                'inviter_share', filter=Q(status__in=not_refund_status)) + Sum(
                'originator_share', filter=Q(status__in=not_refund_status)),
            use_coupon=Count('pk', filter=Q(coupon__isnull=False)),
            not_use_coupon=Count('pk', filter=Q(coupon__isnull=True))
        )

        originator_earning = Transaction.objects.filter(
            account__merchant=self.obj,
        ).filter(
            Q(datetime__gte=datetime_start),
            Q(datetime__lt=datetime_end),
        ).aggregate(
            originator_earning=Sum('amount', filter=Q(transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE)),
        )

        result.update(originator_earning)
        result['turnover'] = get_amount(result['turnover'] or 0)
        result['originator_expenditure'] = get_amount(result['originator_expenditure'] or 0)
        result['originator_earning'] = get_amount(result['originator_earning'] or 0)
        result['payment'] = dict(use_coupon=result['use_coupon'], not_use_coupon=result['not_use_coupon'])
        del result['use_coupon']
        del result['not_use_coupon']

        return result

    @property
    def employer_num(self):
        """收银员数量"""
        num = MerchantAdmin.objects.filter(
            work_merchant=self.obj,
            status=SYSTEM_USER_STATUS['USING'],
        ).aggregate(
            num=Count('wechat_unionid'))['num'] or 0
        return num

    @property
    def day_begin_minute(self):
        return self.obj.day_begin_minute

    def merchant_earning_list_by_day(self, date_start=None, date_end=None):
        """
        一段时间内 各日净利润
        :param date_start: (date)  开始日期 默认为去年此月的第一日
        :param date_end: (date)    截止日期
        :return:
        """

        # 默认为去年该月的1号 至 今日
        today = now().date()
        date_start = date_start or today.replace(year=today.year - 1, day=1)
        date_end = date_end + timedelta(days=1) if date_end else today

        # turnover = <QuerySet [{'date': datetime.date(2018, 1, 1), 'amount': 19500},
        #             {'date': datetime.date(2018, 1, 2), 'amount': 19500},
        #             {'date': datetime.date(2018, 1, 4), 'amount': 19500}]>
        turnover = Payment.objects.filter(
            merchant=self.obj,
        ).exclude(
            status__in=(PAYMENT_STATUS.UNPAID, PAYMENT_STATUS.CANCELLED, PAYMENT_STATUS.REFUND),
        ).filter(
            Q(datetime__gte=date_start),
            Q(datetime__lt=date_end),
        ).annotate(
            date=TruncDate('datetime')
        ).values('date').annotate(
            amount=Sum('order_price') - Coalesce(Sum(  # 所有账单总金额 - 优惠券总减免金额 - 分成
                'coupon__discount', filter=Q(coupon__isnull=False)), 0) - Sum(
                'platform_share') - Sum(
                'inviter_share') - Sum(
                'originator_share')
        ).order_by('date')

        originator_earning = Transaction.objects.filter(
            account__merchant=self.obj,
        ).filter(
            Q(datetime__gte=date_start),
            Q(datetime__lt=date_end),
        ).annotate(
            date=TruncDate('datetime')
        ).values('date').annotate(
            amount=Sum('amount', filter=Q(transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE)),
        ).order_by('date')

        def list_every_day(queryset):
            lst = []
            day_p = date_start  # date pointer
            # date = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            # turnover有2种情况:
            # data = [      2, 3,       6             ]
            # data = []
            for data in queryset:
                while day_p < data['date']:
                    lst.append(dict(date=day_p.strftime('%Y-%m-%d'), amount=0))
                    day_p = day_p + timedelta(days=1)
                lst.append(dict(date=day_p.strftime('%Y-%m-%d'), amount=get_amount(data['amount'] or 0)))
                day_p = day_p + timedelta(days=1)

            # 补全日期数据(7-10 or 0-10)
            while day_p < date_end:
                lst.append(dict(date=day_p.strftime('%Y-%m-%d'), amount=0))
                day_p = day_p + timedelta(days=1)

            return lst

        turnover = list_every_day(turnover)
        originator_earning = list_every_day(originator_earning)

        result = []
        for e in zip(turnover, originator_earning):
            date = e[0]['date']
            amount = e[0]['amount'] + e[1]['amount']
            result.append(dict(date=date, amount=amount))

        return result

    def get_cashier(self, cashier_id):
        cashier = MerchantAdmin.objects.filter(
            id=cashier_id,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=self.obj
        ).first()

        return cashier

    @property
    def cashiers(self):
        cashiers = MerchantAdmin.objects.filter(
            work_merchant=self.obj,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            status=SYSTEM_USER_STATUS['USING'],
        )
        return cashiers
