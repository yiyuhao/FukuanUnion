#      File: coupon_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/4
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.db.models import Count, Q

from common.models import CouponRule, Coupon, Payment
from config import COUPON_STATUS, PAY_CHANNELS, PAYMENT_STATUS
from .base import ModelManagerBase, ModelObjectManagerBase
from .utils import get_amount


class CouponRuleModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(CouponRuleModelManager, self).__init__(*args, **kwargs)
        self.model = CouponRule

    def list_merchant_coupon_rule(self, merchant):
        query_set = self.model.objects.filter(merchant=merchant).order_by('-update_datetime')
        coupons = []
        for coupon_rule in query_set:
            coupons.append(dict(
                id=coupon_rule.id,
                discount=get_amount(coupon_rule.discount),
                min_charge=get_amount(coupon_rule.min_charge),
                valid_strategy=coupon_rule.valid_strategy,
                start_date=coupon_rule.start_date,
                end_date=coupon_rule.end_date,
                expiration_days=coupon_rule.expiration_days,
                stock=coupon_rule.stock,
            ))
        return coupons


class CouponRuleManager(ModelObjectManagerBase):

    def obtain_used_num(self):
        """领取数, 使用数"""
        count = Coupon.objects.filter(
            rule=self.obj
        ).aggregate(
            obtain_num=Count('pk', filter=~Q(status=COUPON_STATUS['DESTROYED'])),
            used_num=Count('pk', filter=Q(status=COUPON_STATUS['USED']))
        )
        return count

    def detail(self):
        detail = dict(
            merchant=self.obj.merchant.name,
            merchant_location_lon=self.obj.merchant.location_lon,
            merchant_location_lat=self.obj.merchant.location_lat,
            discount=get_amount(self.obj.discount),
            min_charge=get_amount(self.obj.min_charge),
            valid_strategy=self.obj.valid_strategy,
            start_date=self.obj.start_date,
            end_date=self.obj.end_date,
            expiration_days=self.obj.expiration_days,
            stock=self.obj.stock,
            photo_url=self.obj.photo_url,
            datetime=self.obj.datetime.date(),
        )
        # 领取数, 使用数
        detail.update(self.obtain_used_num())

        return detail

    def relative_payment(self):
        """使用了该优惠券的订单"""
        return Payment.objects.filter(
            coupon__rule=self.obj,
        ).exclude(
            status__in=(PAYMENT_STATUS['UNPAID'], PAYMENT_STATUS['CANCELLED']),
        ).order_by('-datetime')

    def serialize_relative_payment(self, payments):
        """
        :param payments: <QuerySet Payment>
        :return:
        """
        data_group_by_day = dict()
        for payment in payments:
            day = payment.datetime.strftime('%Y-%m-%d')
            if day not in data_group_by_day:
                data_group_by_day[day] = []
            pay_channels = {PAY_CHANNELS['WECHAT']: '微信支付', PAY_CHANNELS['ALIPAY']: '支付宝支付'}
            data_group_by_day[day].append(dict(
                id=payment.serial_number,
                title='{}'.format(pay_channels[payment.pay_channel]),
                desc='[满{}减{}优惠券]'.format(
                    get_amount(payment.coupon.min_charge), get_amount(payment.coupon.discount)),
                datetime=payment.datetime.strftime('%m-%d %H:%M'),
                amount=get_amount(payment.order_price - payment.coupon.discount),
                status={PAYMENT_STATUS['REFUND']: '已退款',
                        PAYMENT_STATUS['REFUND_REQUESTED']: '退款中'}.get(payment.status, ''),
                transaction_type='discount'
            ))

        results = []
        for date, data in data_group_by_day.items():
            results.append(dict(
                month=date,
                cur_page_transactions=data,
            ))
        return results
