# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import csv
import codecs
import calendar

from datetime import datetime, timedelta
from django.db import connection
from django.db.models import Q, Sum, Case, When, F
from django.utils import timezone
from django.http import HttpResponse
from django.utils.encoding import escape_uri_path
from dynaconf import settings as dynasettings

from common.encryption import AESCipher
from common.models import (
    Merchant,
    Marketer,
    Client,
    Coupon,
    Payment,
)
from config import (
    MERCHANT_STATUS,
    SYSTEM_USER_STATUS,
    PAYMENT_STATUS,
    PAY_CHANNELS,
    WITHDRAW_STATUS,
    WITHDRAW_TYPE,
    WECHAT_PAY_BROKERAGE,
    ALIPAY_PAY_BROKERAGE,
    COUPON_STATUS,
    TRANSACTION_TYPE
)

def fen_to_yuan(fen):
    if fen is None:
        return 0
    return fen / 100.0

def format_yuan(float_yuan):

    return round(float_yuan, 2)

class CsvResponseFactory(object):
    @staticmethod
    def transaction_details_csv_response(result_data):
        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path("资金账单.csv"))
        csv_response.write(codecs.BOM_UTF8)
        writer = csv.writer(csv_response)
        head_list = [
            '时间',
            "有效交易笔数",
            '订单总额（元）',
            '交易总额（元）',
            '手续费（元）',
            '普通账单金额（元）',
            '优惠账单金额（元）',
        ]
        writer.writerow(head_list)
        for row in result_data['data']:
            row_list = [
                row['datetime'],
                row['tran_count'],
                row['order_price'],
                "{}\n支付宝：{} | 微信：{}".format(row['paid_price'], row['paid_price_alipay'], row['paid_price_wechat']),
                "{}\n支付宝：{} | 微信：{}".format(row['brokerage'], row['brokerage_alipay'], row['brokerage_wechat']),
                "{}\n支付宝：{} | 微信：{}".format(row['ordinary'], row['ordinary_alipay'], row['ordinary_wechat']),
                "{}\n支付宝：{} | 微信：{}".format(row['preferential'], row['preferential_alipay'],
                                            row['preferential_wechat']),
            ]
            writer.writerow(row_list)
        result = result_data['result']
        result_list = [
            "总计",
            result['all_tran_count'],
            result['all_order_price'],
            result['all_paid_price'],
            result['all_brokerage'],
            result['all_ordinary'],
            result['all_preferential'],
        ]
        writer.writerow(result_list)
        return csv_response

    @staticmethod
    def sharing_details_csv_response(result_data):
        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path("资金分成.csv"))
        csv_response.write(codecs.BOM_UTF8)
        writer = csv.writer(csv_response)
        head_list = [
            '时间',
            '优惠账单交易总额（元）',
            '总抽成（元）',
            '引流商户提成（元）',
            '邀请人提成（元）',
            '平台分成（元）',
        ]
        writer.writerow(head_list)
        for row in result_data['data']:
            row_list = [
                row['datetime'],
                row['paid_price'],
                row['share_all'],
                row['share_originator'],
                row['share_inviter'],
                row['share_platform'],
            ]
            writer.writerow(row_list)
        result = result_data['result']
        result_list = [
            "总计",
            result['all_paid_price'],
            result['all_share_all'],
            result['all_share_originator'],
            result['all_share_inviter'],
            result['all_share_platform'],
        ]
        writer.writerow(result_list)
        return csv_response

    @staticmethod
    def withdraw_record_csv_response(result_data):
        csv_response = HttpResponse(content_type='text/csv')
        csv_response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path("提现申请记录表.csv"))
        csv_response.write(codecs.BOM_UTF8)
        writer = csv.writer(csv_response)
        head_list = [
            '申请时间',
            '提现商户/个人',
            '标志',
            '交易单号',
            '提现类型',
            '提现金额（元）',
            '状态',
        ]
        writer.writerow(head_list)
        for row in result_data['data']:
            row_list = [
                row['datetime'],
                row['name'],
                row['is_merchant'],
                f"'{row['serial_number']}",
                row['withdraw_type'],
                row['with_draw_money'],
                row['status'],
            ]
            writer.writerow(row_list)
        result = result_data['result']
        result_list = [
            "总计提现成功金额: {}".format(result['with_draw_total_money']),
        ]
        writer.writerow(result_list)
        return csv_response


class TimeTransform(object):
    @staticmethod
    def date_string_to_start_date(data_string):
        if data_string:
            date = datetime.strptime(data_string, "%Y-%m-%d")
            return date
        return None

    @staticmethod
    def date_string_to_end_date(data_string):
        if data_string:
            date = datetime.strptime(data_string, "%Y-%m-%d")
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return end_date
        return None


class FinancialQuery(object):
    @classmethod
    def data_overview(cls):
        merchant_all = Merchant.objects.filter(~Q(status=MERCHANT_STATUS['DISABLED'])).count()
        inviter_all = Marketer.objects.filter(status=SYSTEM_USER_STATUS['USING']).count()
        client_all = Client.objects.filter(Q(status=SYSTEM_USER_STATUS['USING'])).count()
        coupon_all = Coupon.objects.filter(~Q(status=COUPON_STATUS['DESTROYED'])).count()
        coupon_used = Coupon.objects.filter(status=COUPON_STATUS['USED']).count()
        payment_query = Payment.objects.filter(status__in=(PAYMENT_STATUS['FROZEN'], PAYMENT_STATUS['REFUND_REQUESTED'],
                                           PAYMENT_STATUS['REFUND_FAILED'], PAYMENT_STATUS['FINISHED']
                                           )).select_related('coupon').values('pay_channel').\
            annotate(paid_price = Sum(Case(When(coupon__isnull=True, then='order_price'),
                                           default=(F('order_price')-F('coupon__discount')))))
        payment_all = {
            "wechat": 0,
            "alipay": 0,
            "total": 0,
        }
        for item in payment_query:
            payment_all['total'] += item['paid_price']
            if item['pay_channel'] == PAY_CHANNELS['WECHAT']:
                payment_all['wechat'] = item['paid_price']
            elif item['pay_channel'] == PAY_CHANNELS['ALIPAY']:
                payment_all['alipay'] = item['paid_price']
        payment_all = {
            "wechat": fen_to_yuan(payment_all['wechat']),
            "alipay": fen_to_yuan(payment_all['alipay']),
            "total": fen_to_yuan(payment_all['total']),
        }
        return dict(
            merchant=merchant_all,  # 商户总数
            inviter=inviter_all,  # 邀请人数
            client=client_all,  # 用户数
            coupon=coupon_all,  # 优惠券数
            coupon_used=coupon_used,  # 已使用优惠券数
            payment=payment_all  # 入账金额
        )

    @classmethod
    def transaction_details(cls, start_date=None, end_date=None):
        # 除开退款的payment
        query_sql_start = f"""
            select 
                (DATE_FORMAT(datetime, '%%Y-%%m-%%d')) as time_str,
                cast( sum(p.order_price) as SIGNED) as order_price ,
                cast( sum((case when p.coupon_id is null then p.order_price else p.order_price - c.discount end)) as SIGNED)as paid_price ,
                cast( sum((case when p.pay_channel = {PAY_CHANNELS['WECHAT']} then (case when p.coupon_id is null then p.order_price else p.order_price - c.discount end)  else 0 end)) as SIGNED)as paid_price_wechat ,
                cast( sum((case when p.pay_channel = {PAY_CHANNELS['ALIPAY']} then (case when p.coupon_id is null then p.order_price else p.order_price - c.discount end)  else 0 end)) as SIGNED)as paid_price_alipay ,
                cast( sum((case when p.coupon_id is null then p.order_price else 0 end)) as SIGNED)as ordinary,
                cast( sum((case when p.coupon_id is null and p.pay_channel = {PAY_CHANNELS['WECHAT']} then p.order_price else 0 end)) as SIGNED)as ordinary_wechat,
                cast( sum((case when p.coupon_id is null and p.pay_channel = {PAY_CHANNELS['ALIPAY']} then p.order_price else 0 end)) as SIGNED)as ordinary_alipay,
                cast( sum((case when p.coupon_id is not null then p.order_price - c.discount else 0 end)) as SIGNED)as preferential,
                cast( sum((case when p.coupon_id is not null and p.pay_channel = {PAY_CHANNELS['WECHAT']} then p.order_price - c.discount else 0 end)) as SIGNED)as preferential_wechat,
                cast( sum((case when p.coupon_id is not null and p.pay_channel = {PAY_CHANNELS['ALIPAY']} then p.order_price - c.discount else 0 end)) as SIGNED)as preferential_alipay,
                cast( sum((case when p.pay_channel = {PAY_CHANNELS['WECHAT']} then (case when p.coupon_id is null then cast( round(p.order_price/100*{WECHAT_PAY_BROKERAGE}, 2)*100 as SIGNED) else cast( round((p.order_price - c.discount)/100 * {WECHAT_PAY_BROKERAGE}, 2)*100 as SIGNED) end) else 0 end) ) as SIGNED) as paid_price_wechat_brokerage ,
                cast( sum((case when p.pay_channel = {PAY_CHANNELS['ALIPAY']} then (case when p.coupon_id is null then cast( round(p.order_price/100*{ALIPAY_PAY_BROKERAGE}, 2)*100 as SIGNED) else cast( round((p.order_price - c.discount)/100 * {ALIPAY_PAY_BROKERAGE}, 2)*100 as SIGNED) end)  else 0 end) ) as SIGNED )as paid_price_alipay_brokerage,
                count(*) as tran_count
            from common_payment as p LEFT JOIN common_coupon as c 
            on p.coupon_id = c.id 
            where p.status in ({PAYMENT_STATUS['FROZEN']}, {PAYMENT_STATUS['REFUND_REQUESTED']},{PAYMENT_STATUS['REFUND_FAILED']},{PAYMENT_STATUS['FINISHED']}) and 1 = %s
            """
        query_sql_condition = ""
        query_params = [1]
        query_sql_end = "group by time_str order by time_str desc"

        if start_date:
            query_sql_condition = query_sql_condition + " and p.datetime >= %s "
            query_params.append(start_date.strftime('%Y-%m-%d %H:%M:%S.%f'))
        if end_date:
            query_sql_condition = query_sql_condition + " and p.datetime <= %s "
            query_params.append(end_date.strftime('%Y-%m-%d %H:%M:%S.%f'))

        query_sql = query_sql_start + query_sql_end
        if query_sql_condition != "" and len(query_params) != 1:
            query_sql = query_sql_start + query_sql_condition + query_sql_end

        all_order_price = 0
        all_paid_price = 0
        all_paid_price_wechat = 0
        all_paid_price_alipay = 0
        all_ordinary = 0
        all_ordinary_wechat = 0
        all_ordinary_alipay = 0
        all_preferential = 0
        all_preferential_wechat = 0
        all_preferential_alipay = 0
        all_brokerage = 0
        all_brokerage_wechat = 0
        all_brokerate_alipay = 0
        all_tran_count = 0
        with connection.cursor() as cursor:
            cursor.execute(query_sql, query_params)
            row_list = []
            for row in cursor.fetchall():
                all_order_price += row[1]
                all_paid_price += row[2]
                all_paid_price_wechat += row[3]
                all_paid_price_alipay += row[4]
                all_ordinary += row[5]
                all_ordinary_wechat += row[6]
                all_ordinary_alipay += row[7]
                all_preferential += row[8]
                all_preferential_wechat += row[9]
                all_preferential_alipay += row[10]
                all_brokerage_wechat += row[11]
                all_brokerate_alipay += row[12]
                all_brokerage += row[11] + row[12]  # 手续费
                all_tran_count += row[13] # 有效交易

                row_dict = {
                    "datetime": row[0],
                    "order_price": fen_to_yuan(row[1]),
                    "paid_price": fen_to_yuan(row[2]),
                    "paid_price_wechat": fen_to_yuan(row[3]),
                    "paid_price_alipay": fen_to_yuan(row[4]),
                    "ordinary": fen_to_yuan(row[5]),
                    "ordinary_wechat": fen_to_yuan(row[6]),
                    "ordinary_alipay": fen_to_yuan(row[7]),
                    "preferential": fen_to_yuan(row[8]),
                    "preferential_wechat": fen_to_yuan(row[9]),
                    "preferential_alipay": fen_to_yuan(row[10]),
                    "brokerage": fen_to_yuan(row[11] + row[12]),
                    "brokerage_wechat": fen_to_yuan(row[11]),
                    "brokerage_alipay": fen_to_yuan(row[12]),
                    "tran_count": row[13],
                }
                row_list.append(row_dict)
        result = {
            "result": {
                "all_brokerage": format_yuan(fen_to_yuan(all_brokerage)),
                "all_brokerage_wechat": format_yuan(fen_to_yuan(all_brokerage_wechat)),
                "all_brokerate_alipay": format_yuan(fen_to_yuan(all_brokerate_alipay)),
                "all_order_price": format_yuan(fen_to_yuan(all_order_price)),
                "all_paid_price": format_yuan(fen_to_yuan(all_paid_price)),
                "all_paid_price_wechat": format_yuan(fen_to_yuan(all_paid_price_wechat)),
                "all_paid_price_alipay": format_yuan(fen_to_yuan(all_paid_price_alipay)),
                "all_ordinary": format_yuan(fen_to_yuan(all_ordinary)),
                "all_ordinary_alipay": format_yuan(fen_to_yuan(all_ordinary_alipay)),
                "all_ordinary_wechat": format_yuan(fen_to_yuan(all_ordinary_wechat)),
                "all_preferential": format_yuan(fen_to_yuan(all_preferential)),
                "all_preferential_alipay": format_yuan(fen_to_yuan(all_preferential_alipay)),
                "all_preferential_wechat": format_yuan(fen_to_yuan(all_preferential_wechat)),
                "all_tran_count": all_tran_count,
            },
            "data": row_list,
        }
        return result

    @classmethod
    def sharing_details(cls, start_date=None, end_date=None):
        # 除开退款的以及没有使用优惠券的payment
        query = Payment.objects.filter(Q(status__in=(PAYMENT_STATUS['FROZEN'], PAYMENT_STATUS['REFUND_REQUESTED'],
                       PAYMENT_STATUS['REFUND_FAILED'], PAYMENT_STATUS['FINISHED']
                       )), Q(coupon__isnull=False))
        if start_date:
            query = query.filter(datetime__gte=start_date)
        if end_date:
            query = query.filter(datetime__lte=end_date)

        query = query.select_related('coupon').extra(
            select={'datetime': "DATE_FORMAT(datetime, %s)"},
            select_params=("%Y-%m-%d", ), ) \
            .values("datetime") \
            .annotate(
            paid_price=Sum(F('order_price') - F('coupon__discount')),
            share_platform=Sum('platform_share'),
            share_inviter=Sum('inviter_share'),
            share_originator=Sum('originator_share'),
            share_all = Sum(F('platform_share') + F('inviter_share') + F('originator_share')),
        ).order_by("-datetime")

        query_set = list(query)
        all_paid_price = 0
        all_share_all = 0
        all_share_platform = 0
        all_share_inviter = 0
        all_share_originator = 0
        for item in query_set:
            item['paid_price'] = format_yuan(fen_to_yuan(item['paid_price']))
            item['share_platform'] = format_yuan(fen_to_yuan(item['share_platform']))
            item['share_inviter'] = format_yuan(fen_to_yuan(item['share_inviter'] ))
            item['share_originator'] = format_yuan(fen_to_yuan(item['share_originator'] ))
            item['share_all'] = format_yuan(fen_to_yuan(item['share_all'] ))

            all_paid_price = all_paid_price + item['paid_price']
            all_share_all = all_share_all + item['share_all']
            all_share_originator = all_share_originator + item['share_originator']
            all_share_inviter = all_share_inviter + item['share_inviter']
            all_share_platform = all_share_platform + item['share_platform']


        result = {
            "result": {
                "all_paid_price": format_yuan(all_paid_price),
                "all_share_all": format_yuan(all_share_all),
                "all_share_platform": format_yuan(all_share_platform),
                "all_share_inviter": format_yuan(all_share_inviter),
                "all_share_originator": format_yuan(all_share_originator),
            },
            "data": query_set
        }
        return result

    @classmethod
    def withdraw_record(cls, status=None, start_date=None, end_date=None):
        sql_start = """
            select 
                a.datetime,
                a.status,
                a.amount,
                (case when a.merchant_name is null then a.inviter_name else a.merchant_name end) as p_name,
                (case when a.merchant_phone is null then a.inviter_phone else a.merchant_phone end ) as p_phone,
                a.serial_number,
                (case when a.merchant_name is null then 0 else 1 end) as is_merchant,
                a.withdraw_type
                from (
                    select * 
                    from common_withdraw w  LEFT JOIN  ( select account_id as merchant_account_id, name as merchant_name, contact_phone as merchant_phone from common_merchant ) merchant 
                    on  w.account_id = merchant.merchant_account_id
                    left join ( select account_id as inviter_account_id, name as inviter_name, phone as inviter_phone from common_marketer) inviter
                    on w.account_id = inviter.inviter_account_id
                    where 1 = %s """
        sql_condition = ""
        sql_end = """ ) a order by a.datetime desc """
        sql_params = [1]

        if status:
            try:
                status = int(status)
            except ValueError:
                pass
            else:
                sql_condition = sql_condition + " and status = %s "
                sql_params.append(status)
        if start_date:
            sql_condition = sql_condition + " and datetime >= %s "
            sql_params.append(start_date.strftime('%Y-%m-%d %H:%M:%S.%f'))
        if end_date:
            sql_condition = sql_condition + " and datetime <= %s "
            sql_params.append(end_date.strftime('%Y-%m-%d %H:%M:%S.%f'))

        all_withdraw_money = 0
        list_data = []
        query_sql = sql_start + sql_condition + sql_end
        with connection.cursor() as cursor:
            cursor.execute(query_sql, sql_params)
            for row in cursor.fetchall():
                if row[1] == WITHDRAW_STATUS['FINISHED']:
                    all_withdraw_money += row[2]
                list_data.append({
                    'datetime': row[0].strftime("%Y-%m-%d %H:%M:%S"),
                    'name': row[3],
                    'serial_number': row[5],
                    'is_merchant': "个体商户" if row[6] == 1 else "邀请人",
                    'withdraw_type': "微信零钱" if row[7] == WITHDRAW_TYPE['WECHAT'] else "支付宝余额",
                    'with_draw_money': fen_to_yuan(row[2]),
                    'status': WITHDRAW_STATUS[row[1]]['name'],
                    'note': ""
                })
        result = {
            "result": {
                "with_draw_records": len(list_data),
                "with_draw_total_money": format_yuan(fen_to_yuan(all_withdraw_money)),
            },
            "data": list_data
        }


        return result

    @classmethod
    def query_merchant_month_bill(cls):
        """ 查询所有商户月账单 """
        # 根据当前时间求出上个月的第一天和最后一天时间
        curr_time = timezone.now()
        curr_month_first_day = curr_time.replace(day=1,hour=0, minute=0, second=0, microsecond=0)
        end_time = curr_month_first_day - timedelta(days = 1)
        month_days = calendar.monthrange(end_time.year, end_time.month)[1]
        start_time = curr_month_first_day - timedelta(days=month_days)
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')

        query_sql =f"""
        select a.wechat_openid, b.turnover, b.sharing_earning from (
                select 
                    m.account_id, 
                    admin.wechat_openid
                from common_merchant m INNER JOIN common_merchantadmin admin 
                on m.id = admin.work_merchant_id 
                where m.status = {MERCHANT_STATUS['USING']}
          ) a left join (
                select account_id,
                    cast( sum( (case when transaction_type in ({TRANSACTION_TYPE['MERCHANT_RECEIVE']},{TRANSACTION_TYPE['MERCHANT_REFUND']}) then amount else 0 end)) as SIGNED) as turnover,
                    cast( sum( (case when transaction_type = {TRANSACTION_TYPE['MERCHANT_SHARE']} then amount else 0 end)) as SIGNED) as sharing_earning
                from common_transaction 
                where datetime >= %s and datetime <= %s and account_id in (select account_id from common_merchant where status = {MERCHANT_STATUS['USING']})
                group by account_id
        ) b
        on a.account_id = b.account_id
        """
        sql_params = [start_time_str, end_time_str]
        result_list = []
        aes = AESCipher(dynasettings.OPENID_AES_KEY)
        with connection.cursor() as cursor:
            cursor.execute(query_sql, sql_params)
            for row in cursor.fetchall():
                result_list.append(
                    {
                        "open_id": aes.decrypt(row[0]),
                        "bill": {
                            "turnover": format_yuan(fen_to_yuan(row[1])),
                            "sharing_earning": format_yuan(fen_to_yuan(row[2])),
                        }
                    })
        return start_time.year,  start_time.month, result_list
