#      File: transaction_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/28
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import collections

from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.utils.timezone import timedelta

from .base import ModelManagerBase, ModelObjectManagerBase
from .utils import get_amount
from config import TRANSACTION_TYPE, PAYMENT_STATUS, WITHDRAW_STATUS, PAY_CHANNELS, WITHDRAW_TYPE, SETTLEMENT_STATUS
from common.models import Transaction, Payment


class TransactionManager(ModelObjectManagerBase):
    """self.obj = merchant_model_instance"""

    def __init__(self, *args, **kwargs):
        super(TransactionManager, self).__init__(*args, **kwargs)
        self.transaction_detail = dict()

    def _receive_detail(self):
        """
        营业订单(payment)
        普通订单:    付款方式 微信/支付宝 | 账单分类 普通/优惠/余额提现/引流收益 | 创建时间    备注
        优惠券订单：  + 订单原价 378.00元  |  优惠减免 30.00元  |  抽成  20%  |  优惠券名称
        """
        payment = self.obj.content_object

        self.transaction_detail.update(
            pay_channel=payment.pay_channel,
            create_datetime=payment.datetime.strftime('%Y-%m-%d %H:%M'),
            note=payment.note,
            status=payment.status,
        )

        if payment.coupon is None:  # 普通订单
            self.transaction_detail.update(transaction_type='普通')
        else:
            total_share = payment.platform_share + payment.inviter_share + payment.originator_share
            discount = payment.coupon.discount
            self.transaction_detail.update(
                transaction_type='优惠',
                order_price=get_amount(payment.order_price),
                discount=get_amount(payment.coupon.discount),
                total_share='{}%'.format(
                    # 总分成 / 减免后金额
                    int((total_share / (payment.order_price - discount) * 100) * 100) / 100  # 最多显示两位小数
                ),
                coupon='[满{}减{}优惠券]'.format(
                    get_amount(payment.coupon.min_charge), get_amount(payment.coupon.discount)),
                coupon_rule_id=payment.coupon.rule_id
            )

    def _originator_earning_detail(self):
        """
        引流收益:    账单分类  | 交易总金额 358.00元  | 提成  10.00%  | 创建时间  | 到帐时间
        """
        payment = self.obj.content_object

        order_price_after_discount = payment.order_price - payment.coupon.discount \
            if payment.coupon else payment.order_price
        self.transaction_detail.update(
            transaction_type='引流收益',
            status=payment.status,
            merchant_name=payment.merchant.name,
            price_after_discount=get_amount(order_price_after_discount),
            merchant_share='{}%'.format(
                int((payment.originator_share / order_price_after_discount * 100) * 100) / 100  # 最多显示两位xiaoshu
            ),
            create_datetime=payment.datetime.strftime('%Y-%m-%d %H:%M'),
            receive_datetime=self.obj.datetime.strftime('%Y-%m-%d %H:%M'),
        )

    def _withdraw_detail(self):
        """
        提现:        账单分类  | 创建时间 |  处理进度  到帐成功  |  提现到  招商银行(6481) 张三
        """
        withdraw = self.obj.content_object

        self.transaction_detail.update(
            transaction_type='余额提现',
            withdraw_type=withdraw.withdraw_type,
            status=withdraw.status,
            amount=-self.transaction_detail['amount'],
            create_datetime=withdraw.datetime.strftime('%Y-%m-%d %H:%M'),
        )

    def _settlement_detail(self):
        settlement = self.obj.content_object

        self.transaction_detail.update(
            transaction_type='结算账单',
            status=settlement.status,
            create_datetime=settlement.datetime.strftime('%Y-%m-%d %H:%M'),
            receive_datetime=settlement.finished_datetime.strftime('%Y-%m-%d %H:%M'),
        )

    @property
    def detail(self):
        is_settlement = self.obj.transaction_type in (TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'],
                                                      TRANSACTION_TYPE['MERCHANT_ALIPAY_SETTLEMENT'])
        self.transaction_detail.update(
            id=self.obj.id,
            amount=get_amount((self.obj.content_object.wechat_amount +
                               self.obj.content_object.alipay_amount) if is_settlement else self.obj.amount),
            serial_number=self.obj.content_object.serial_number
        )
        if self.obj.transaction_type == TRANSACTION_TYPE['MERCHANT_RECEIVE']:  # 营业额
            self._receive_detail()
        elif self.obj.transaction_type == TRANSACTION_TYPE['MERCHANT_SHARE']:  # 引流收益
            self._originator_earning_detail()
        elif self.obj.transaction_type == TRANSACTION_TYPE['MERCHANT_WITHDRAW']:  # 提现
            self._withdraw_detail()
        elif is_settlement:  # 企业商户结算账单
            self._settlement_detail()
        return self.transaction_detail


class TransactionModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(TransactionModelManager, self).__init__(*args, **kwargs)
        self.model = Transaction

    def get(self, pk, is_payment=False, merchant=None):

        # get transaction by id
        query_set = self.model.objects.filter(id=pk) if pk.isdigit() else None

        # get transaction by payment.serial_number
        if query_set is None or query_set.first() is None:
            payment = Payment.objects.filter(serial_number=pk).first()
            if payment is None:
                return None
            payment_type = ContentType.objects.get_for_model(payment)
            query_set = Transaction.objects.filter(
                content_type_id=payment_type.id,
                object_id=payment.serial_number,
            )

        if merchant:
            query_set = query_set.filter(account__merchant=merchant)
        if is_payment:
            query_set = query_set.filter(transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])
        return query_set.first()

    def serialize(self, transactions):
        """
        :param transactions: <QuerySet>, <List>, result of self.list_merchant_transaction()
        :return: e.g.
        [
            {'turnover': 200.2,
             'originator_earning': 2.02,
             'withdraw': 180,
             'cur_page_transactions': [
                 {'id': 1, 'title': 'client name', 'desc': '[普通]',
                  'datetime': datetime.datetime(2018, 5, 10, 0, 0), 'amount': 100.1, 'status': ''},
                 {'id': 2, 'title': '引流到达的商户', 'desc': '[其他]',
                  'datetime': datetime.datetime(2018, 5, 8, 0, 0), 'amount': 1.01, 'status': ''},
                 {'id': 3, 'title': '余额提现', 'desc': '[其他]',
                  'datetime': datetime.datetime(2018, 5, 6, 0, 0), 'amount': 90, 'status': '处理中'},
                 {'id': 4, 'title': 'client name', 'desc': '[满300减100优惠券]',
                  'datetime': datetime.datetime(2018, 5, 3, 0, 0), 'amount': 100.1, 'status': ''}
             ],
             'month': '2018/05'},

            {'turnover': 0, 'originator_earning': 0, 'withdraw': 0, 'cur_page_transactions': [], 'month': '2018/04'}
        ]
        """
        if not transactions:
            return []

        merchant = None
        data_group_by_month = dict()  # key: datetime of every month begins, value: info

        for transaction in transactions:
            if merchant is None:
                merchant = transaction.account.merchant
            date = transaction.datetime
            month = date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if month not in data_group_by_month:
                data_group_by_month[month] = dict(
                    turnover=0, originator_earning=0, withdraw=0, cur_page_transactions=[]
                )

            # 用户付款订单(营业额)
            if transaction.transaction_type == TRANSACTION_TYPE['MERCHANT_RECEIVE']:
                payment = transaction.content_object
                pay_channels = {PAY_CHANNELS['WECHAT']: '微信支付', PAY_CHANNELS['ALIPAY']: '支付宝支付'}
                use_coupon = payment.coupon is not None
                data_group_by_month[month]['cur_page_transactions'].append(dict(
                    id=transaction.id,
                    title='{}{}'.format(pay_channels[payment.pay_channel], ' - 优惠账单' if use_coupon else ''),
                    desc='[普通]' if not use_coupon else '[满{}减{}优惠券]'.format(
                        get_amount(payment.coupon.min_charge), get_amount(payment.coupon.discount)),
                    datetime=payment.datetime.strftime('%m-%d %H:%M'),
                    amount=get_amount(transaction.amount),
                    status={
                        PAYMENT_STATUS['REFUND']: '已退款',
                        PAYMENT_STATUS['REFUND_REQUESTED']: '退款中',
                        PAYMENT_STATUS['REFUND_FAILED']: '退款失败',
                    }.get(payment.status, ''),
                    transaction_type='discount' if use_coupon else 'normal',
                ))

            # 商户提现
            elif transaction.transaction_type == TRANSACTION_TYPE['MERCHANT_WITHDRAW']:
                withdraw = transaction.content_object
                data_group_by_month[month]['cur_page_transactions'].append(dict(
                    id=transaction.id,
                    title='余额提现 - 到微信零钱' if withdraw.withdraw_type == WITHDRAW_TYPE.WECHAT else '余额提现 - 到支付宝余额',
                    desc='[其他]',
                    datetime=withdraw.datetime.strftime('%m-%d %H:%M'),
                    amount=get_amount(withdraw.amount),
                    status=WITHDRAW_STATUS.get(withdraw.status)['name'],
                    transaction_type='withdraw',
                ))

            # 企业商户结算账单
            elif transaction.transaction_type == TRANSACTION_TYPE.MERCHANT_WECHAT_SETTLEMENT:
                settlement = transaction.content_object
                data_group_by_month[month]['cur_page_transactions'].append(dict(
                    id=transaction.id,
                    title='账单结算',
                    desc='[其他]',
                    datetime=settlement.finished_datetime.strftime('%m-%d %H:%M'),
                    amount=get_amount(settlement.wechat_amount + settlement.alipay_amount),
                    status=SETTLEMENT_STATUS.get(settlement.status)['name'],
                    transaction_type='withdraw',
                ))

            # 引流收益
            elif transaction.transaction_type == TRANSACTION_TYPE['MERCHANT_SHARE']:
                payment = transaction.content_object
                data_group_by_month[month]['cur_page_transactions'].append(dict(
                    id=transaction.id,
                    title=payment.merchant.name,
                    desc='[其他]',
                    datetime=transaction.datetime.strftime('%m-%d %H:%M'),  # 需要为分成时间而非payment.datetime
                    amount=get_amount(transaction.amount),
                    status='',
                    transaction_type='original_earning',
                ))

        # 补充没有transaction的月份数据
        datetime_start = min(data_group_by_month.items(), key=lambda x: x[0])[0]
        month_end = max(data_group_by_month.items(), key=lambda x: x[0])[0]
        month_p = datetime_start  # pointer
        while month_p <= month_end:
            if month_p not in data_group_by_month:
                data_group_by_month[month_p] = dict(
                    turnover=0, originator_earning=0, withdraw=0, cur_page_transactions=[],
                    month=month_p.strftime('%Y/%m')
                )
            month_p = (month_p + timedelta(days=32)).replace(day=1)  # month_p += 1
        # 按月份排序
        data_group_by_month = collections.OrderedDict(sorted(data_group_by_month.items(), reverse=True))

        # 获取该月营业额/引流收益/提现总金额
        serialized_data = []

        datetime_end = (month_end + timedelta(days=32)).replace(day=1)  # last month end datetime
        # 每月营业额/引流收益/提现总金额
        query = Transaction.objects.filter(
            account__merchant=merchant,
            transaction_type__in=(
                TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                TRANSACTION_TYPE['MERCHANT_REFUND'],
                TRANSACTION_TYPE['MERCHANT_SHARE'],
                TRANSACTION_TYPE['MERCHANT_WITHDRAW'],
            )
        ).filter(
            Q(datetime__gte=datetime_start),
            Q(datetime__lt=datetime_end),
        ).annotate(month=TruncMonth('datetime')).values('month').annotate(
            turnover=Sum('amount', filter=Q(transaction_type__in=(
                TRANSACTION_TYPE['MERCHANT_RECEIVE'],
                TRANSACTION_TYPE['MERCHANT_REFUND']))),
            refund=Sum('amount', filter=Q(transaction_type=TRANSACTION_TYPE['MERCHANT_REFUND'])),
            withdraw=Sum('amount', filter=Q(transaction_type__in=(
                TRANSACTION_TYPE['MERCHANT_WITHDRAW'],
                TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'],
                TRANSACTION_TYPE['MERCHANT_ALIPAY_SETTLEMENT']))),
            originator_earning=Sum('amount', filter=Q(transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])),
        )

        for q in query:
            data = data_group_by_month[q['month']]
            data['month'] = q['month'].strftime('%Y/%m')
            data['turnover'] = get_amount(q.get('turnover') or 0)
            data['withdraw'] = -get_amount(q.get('withdraw') or 0)  # 负数 -> 正数
            data['originator_earning'] = get_amount(q.get('originator_earning') or 0)

        for data in data_group_by_month.values():
            serialized_data.append(data)

        return serialized_data

    def list_merchant_transaction(self, merchant, transaction_type=None):
        """
        获取商户账单列表
        :param merchant: merchant model instance
        :param transaction_type: must be None, 'turnover', 'originator_earning', or 'withdraw'
        :return:
        """
        types = dict(
            turnover=TRANSACTION_TYPE['MERCHANT_RECEIVE'],
            originator_earning=TRANSACTION_TYPE['MERCHANT_SHARE'],
            withdraw=TRANSACTION_TYPE['MERCHANT_WITHDRAW'],
            settlement=TRANSACTION_TYPE['MERCHANT_WECHAT_SETTLEMENT'],
        )

        if transaction_type is None or transaction_type == 'all':
            return self.model.objects.filter(
                account__merchant=merchant,
                transaction_type__in=tuple(types.values())
            ).order_by('-datetime')
        else:
            return self.model.objects.filter(
                account__merchant=merchant,
                transaction_type=types[transaction_type]
            ).order_by('-datetime')
