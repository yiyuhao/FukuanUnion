# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import random

from datetime import datetime, timedelta
from django.utils import timezone

from common.models import *
from config import *

from .base_data import create_base_data
from .mock_util import TimeUtil, MoneyUtil, MockProcessUtil

# 用户故事：
# 测试场景：
#
# 商户1： m1火锅店  A, B, C 卡券
#  A: 30张  满 11 减 2
#  B: 30张  满 15 减 3.3
#  C: 40张  满 19 减 4.7


# 商户2： m2火锅店  D, E, F 卡券
#  D: 10张  满 20 减 3
#  E: 20张  满 30 减 5.5
#  F: 20张  满 40 减 6.5

# 商户3： m3火锅店  X, Y, Z 卡券
#  X: 200张  满 50 减 10
#  Y: 200张  满 70 减 15
#  Z: 100张  满 100 减 25
#

# 商户4： m4火锅店  R, S, T 卡券
#  R: 15张  满 5 减 0.5
#  S: 25张  满 7 减 1
#  T: 35张  满 9 减 1.5

#
# 用户 u1, u2, u3, u4, u5, u6,
#
#
# 开始时间：2018-7-1
#
# 2018-7-2: 注册邀请人 i1, i2, i3
# 2018-7-2: 注册业务员 i1, i2, i3
# 2018-7-3： i1 -> m1， i2->m2, i2->m3, i3->m4 入住
#
# 2018-7-4 16:20:43 商户m1投放卡券
# 2018-7-5 16:20:43 商户m2投放卡券
# 2018-7-6 16:20:43 商户m3投放卡券
# 2018-7-7 16:20:43 商户m4投放卡券


# 2018-7-8  9:23:44  u1 在 m1 消费 10.37元, 获得 m2_D, m3_X, m4_R
# 2018-7-8 10:56:31  u2 在 m2 消费 17.88元, 获得 m1_A, m3_Y, m4_S
# 2018-7-8 11:30:22  u3 在 m3 消费 32.45元, 获得 m1_B, m2_E, m4_T
# 2018-7-8 12:40:22  u4 在 m4 消费 32.45元, 获得 m1_C, m2_F, m3_Z
# 2018-7-8 15:34:20  u5 在 m2 消费 32.45元, 获得 m1_A, m3_X, m4_R
# 2018-7-8 17:28:26  u6 在 m3 消费 32.45元, 获得 m1_B, m2_D, m4_S


# 2018-7-9 14:10:47  u1在 m2 使用 m2_D 消费 21.37 元
# 2018-7-9 16:45:23  u1在 m3 使用 m3_X 消费 52.66 元
# 2018-7-9 17:30:08  u1在 m3 退款消费 52.66 元
# 2018-7-9 18:25:32  u1在 m4 使用 m4_R 消费 7.16 元


# 2018-7-10 9:30:10  u2 在 m1 使用 m1_A 消费 13.47 元
# 2018-7-10 10:04:32 u2 在 m3 使用 m3_Y 消费 121.3 元
# 2018-7-10 10:48:21 u2 在 m4 使用 m4_S 消费 10.12 元

# 2018-7-11 10:21:56 u3 在 m1 使用 m1_B 消费 15.7 元
# 2017-7-11 13:13:30 u3 在 m2 使用 m2_E 消费 44.2 元
# 2018-7-11 14:20:18 u3 在 m4 使用 m4_T 消费 9.7 元

# 2018-7-15 10:21:56 u4 在 m1 使用 m1_C 消费 22.7 元
# 2018-7-15 13:13:30 u4 在 m2 使用 m2_F 消费 43.1 元
# 2018-7-15 13:20:54 u4 在 m2 退款消费 43.1
# 2018-7-15 14:20:18 u4 在 m3 使用 m3_Z 消费 152.7 元

# 2018-7-16 9:30:10  u5 在 m1 使用 m1_A 消费 12.47 元
# 2018-7-16 10:48:21 u5 在 m3 使用 m3_X 消费 51.3 元
# 2018-7-16 19:04:32 u5 在 m4 使用 m4_R 消费 8.12 元

# 2018-7-17 10:25:32  u6在 m1 使用 m1_B 消费 20.16 元
# 2018-7-17 14:10:47  u6在 m2 使用 m2_D 消费 21.37 元
# 2018-7-17 16:45:23  u6在 m4 使用 m4_S 消费 7.66 元


# 2018-7-18 10:10:10 m1 提现10元
# 2018-7-19 10:10:10 m2 提现10元
# 2018-7-19 10:12:10 m3 提现10元
# 2018-7-20 10:10:10 m4 提现10元
# 2018-7-21 10:10:10 i1 提现0.15元
# 2018-7-22 10:10:10 i2 提现0.15元
# 2018-7-23 10:12:10 i3 提现0.15元

class CreateData(object):

    @classmethod
    def initial_base_date(cls):
        # 创建城市和区域
        create_base_data()

    @classmethod
    def initial_mock_data(cls):
        # 商户分类
        category = MerchantCategory.objects.filter(name='进口食品').first()
        platform_account = Account.objects.get(real_name="平台账户")

        # 注册邀请人
        i1_data = dict(
            wechat_openid='i1_openid',
            wechat_unionid='i1_unionid',
            inviter_type=MARKETER_TYPES['MARKETER'],
            status=SYSTEM_USER_STATUS['USING'],
            name='i1i1',
            phone='13100000001',
            id_card_front_url='',
            id_card_back_url='',
            account=Account.objects.create(
                        bank_name="中国银行",
                        bank_card_number="9999888877776666401",
                        real_name="inviter1账户",
                        balance=0,
                        withdrawable_balance=0,
                        alipay_balance=0,
                        alipay_withdrawable_balance=0
                    ),
        )
        i2_data = dict(
            wechat_openid='i2_openid',
            wechat_unionid='i2_unionid',
            inviter_type=MARKETER_TYPES['MARKETER'],
            status=SYSTEM_USER_STATUS['USING'],
            name='i2i2',
            phone='13100000002',
            id_card_front_url='',
            id_card_back_url='',
            account=Account.objects.create(
                bank_name="中国银行",
                bank_card_number="9999888877776666402",
                real_name="inviter2账户",
                balance=0,
                withdrawable_balance=0,
                alipay_balance=0,
                alipay_withdrawable_balance=0
            ),
        )
        i3_data = dict(
            wechat_openid='i3_openid',
            wechat_unionid='i3_unionid',
            inviter_type=MARKETER_TYPES['MARKETER'],
            status=SYSTEM_USER_STATUS['USING'],
            name='i3i3',
            phone='13100000003',
            id_card_front_url='',
            id_card_back_url='',
            account=Account.objects.create(
                bank_name="中国银行",
                bank_card_number="9999888877776666403",
                real_name="inviter3账户",
                balance=0,
                withdrawable_balance=0,
                alipay_balance=0,
                alipay_withdrawable_balance=0
            ),
        )
        i1 = Marketer.objects.create(**i1_data)
        i2 = Marketer.objects.create(**i2_data)
        i3 = Marketer.objects.create(**i3_data)

        # 邀请人变为业务员
        jingjia_qu = Area.objects.filter(parent=Area.objects.get(adcode='510104000000'))
        wuhou_qu = Area.objects.filter(parent=Area.objects.get(adcode='510107000000'))
        qingyang_qu = Area.objects.filter(parent=Area.objects.get(adcode='510105000000'))
        # i1 -> 成都市锦江区 下所有街道
        i1.inviter_type = MARKETER_TYPES.SALESMAN
        i1.worker_number = 'inviter_001'
        for area in jingjia_qu:
            i1.working_areas.add(area)
        i1.save()
        # i2 -> 成都市武侯区 下所有街道
        i2.inviter_type = MARKETER_TYPES.SALESMAN
        i2.worker_number = 'inviter_002'
        for area in wuhou_qu:
            i2.working_areas.add(area)
        i2.save()
        # i3 -> 成都市青羊区 下所有街道
        i3.inviter_type = MARKETER_TYPES.SALESMAN
        i3.worker_number = 'inviter_003'
        for area in qingyang_qu:
            i3.working_areas.add(area)
        i3.save()


        # 2018-7-3： i1 -> m1， i2->m2, i2->m3 i3->m4入住
        # m1-> # 商户所在区域-> 锦江区春熙路街道
        # m2-> # 商户所在区域-> 武侯区浆洗街街道
        # m3-> # 商户所在区域-> 武侯区桂溪街道
        # m4-> # 商户所在区域-> 青羊区西御河街道
        m1 = Merchant.objects.create(
            status = MERCHANT_STATUS.REVIEWING,  # 商户状态
            name ="m1火锅店",  # 商户名称
            account =  Account.objects.create(
                        bank_name="中国银行",
                        bank_card_number="9999888877776666201",
                        real_name="merchant1账户",
                        balance=0,
                        withdrawable_balance=0,
                        alipay_balance=0,
                        alipay_withdrawable_balance=0
                      ),  # 商户账户
            inviter = i1,
            payment_qr_code = PaymentQRCode.objects.create(),  # 付款码
            category = category,  # 商户业务分类
            contact_phone = "13977770201",  # 联系电话
            area = Area.objects.get(adcode='510104022000'),  # 商户所在区域-> 春熙路街道
            address = "春熙路街道总府路2号",  # 商户地址
            location_lon = 20,  # 商户位置经度
            location_lat = 20,  # 商户位置纬度
            description = '', # 商户介绍
            avatar_url = '',  # 商户头像
            photo_url = '',  # 商户照片
            license_url = '',  # 营业执照照片
            id_card_front_url = '',  # 法人身份证正面
            id_card_back_url = '',  # 法人身份证反面
            create_datetime = TimeUtil.format_time('2018-7-3 14:00:00'), # 入驻时间
            day_begin_minute = 480  # 账单日结开始时间(延后day_begin_minute分钟) 8点
        )
        m1_admin = MerchantAdmin.objects.create(
            wechat_openid='m1_admin_openid',  # 微信openid
            wechat_unionid='m1_wechat_unionid',  # 微信unionid
            wechat_avatar_url='',  # 收银员微信头像(商户管理员为空)
            wechat_nickname='m1_admin',  # 收银员微信昵称(商户管理员为空)
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,  # 类型：管理员/收银员
            status=SYSTEM_USER_STATUS.USING,  # 用户状态
            work_merchant = m1,  # 所属店铺
        )

        m2 = Merchant.objects.create(
            status=MERCHANT_STATUS.REVIEWING,  # 商户状态
            name="m2火锅店",  # 商户名称
            account=Account.objects.create(
                bank_name="中国银行",
                bank_card_number="9999888877776666202",
                real_name="merchant2账户",
                balance=0,
                withdrawable_balance=0,
                alipay_balance=0,
                alipay_withdrawable_balance=0
            ),  # 商户账户
            inviter=i2,
            payment_qr_code=PaymentQRCode.objects.create(),  # 付款码
            category=category,  # 商户业务分类
            contact_phone="13977770202",  # 联系电话
            area=Area.objects.get(adcode='510107001000'),  # 商户所在区域-> 武侯区浆洗街街道
            address="武侯区浆洗街12号附1号",  # 商户地址
            location_lon=20,  # 商户位置经度
            location_lat=20,  # 商户位置纬度
            description='',  # 商户介绍
            avatar_url='',  # 商户头像
            photo_url='',  # 商户照片
            license_url='',  # 营业执照照片
            id_card_front_url='',  # 法人身份证正面
            id_card_back_url='',  # 法人身份证反面
            create_datetime=TimeUtil.format_time('2018-7-3 14:00:00'),  # 入驻时间
            day_begin_minute=480  # 账单日结开始时间(延后day_begin_minute分钟) 8点
        )
        m2_admin = MerchantAdmin.objects.create(
            wechat_openid='m2_admin_openid',  # 微信openid
            wechat_unionid='m2_wechat_unionid',  # 微信unionid
            wechat_avatar_url='',  # 收银员微信头像(商户管理员为空)
            wechat_nickname='m2_admin',  # 收银员微信昵称(商户管理员为空)
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,  # 类型：管理员/收银员
            status=SYSTEM_USER_STATUS.USING,  # 用户状态
            work_merchant=m2,  # 所属店铺
        )

        m3 = Merchant.objects.create(
            status=MERCHANT_STATUS.REVIEWING,  # 商户状态
            name="m3火锅店",  # 商户名称
            account=Account.objects.create(
                bank_name="中国银行",
                bank_card_number="9999888877776666203",
                real_name="merchant3账户",
                balance=0,
                withdrawable_balance=0,
                alipay_balance=0,
                alipay_withdrawable_balance=0
            ),  # 商户账户
            inviter=i2,
            payment_qr_code=PaymentQRCode.objects.create(),  # 付款码
            category=category,  # 商户业务分类
            contact_phone="13977770203",  # 联系电话
            area=Area.objects.get(adcode='510116064000'),  # 商户所在区域-> 武侯区浆桂溪街街道
            address="武侯区桂溪街道天久北巷8号",  # 商户地址
            location_lon=20,  # 商户位置经度
            location_lat=20,  # 商户位置纬度
            description='',  # 商户介绍
            avatar_url='',  # 商户头像
            photo_url='',  # 商户照片
            license_url='',  # 营业执照照片
            id_card_front_url='',  # 法人身份证正面
            id_card_back_url='',  # 法人身份证反面
            create_datetime=TimeUtil.format_time('2018-7-3 14:00:00'),  # 入驻时间
            day_begin_minute=480  # 账单日结开始时间(延后day_begin_minute分钟) 8点
        )
        m3_admin = MerchantAdmin.objects.create(
            wechat_openid='m3_admin_openid',  # 微信openid
            wechat_unionid='m3_wechat_unionid',  # 微信unionid
            wechat_avatar_url='',  # 收银员微信头像(商户管理员为空)
            wechat_nickname='m3_admin',  # 收银员微信昵称(商户管理员为空)
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,  # 类型：管理员/收银员
            status=SYSTEM_USER_STATUS.USING,  # 用户状态
            work_merchant=m3,  # 所属店铺
        )
        m4 = Merchant.objects.create(
            status=MERCHANT_STATUS.REVIEWING,  # 商户状态
            name="m4火锅店",  # 商户名称
            account=Account.objects.create(
                bank_name="中国银行",
                bank_card_number="9999888877776666204",
                real_name="merchant4账户",
                balance=0,
                withdrawable_balance=0,
                alipay_balance=0,
                alipay_withdrawable_balance=0
            ),  # 商户账户
            inviter=i3,
            payment_qr_code=PaymentQRCode.objects.create(),  # 付款码
            category=category,  # 商户业务分类
            contact_phone="13977770204",  # 联系电话
            area=Area.objects.get(adcode='510105003000'),  # 商户所在区域-> 青羊区西御河街道
            address="青羊区西御河街道小西巷16号",  # 商户地址
            location_lon=20,  # 商户位置经度
            location_lat=20,  # 商户位置纬度
            description='',  # 商户介绍
            avatar_url='',  # 商户头像
            photo_url='',  # 商户照片
            license_url='',  # 营业执照照片
            id_card_front_url='',  # 法人身份证正面
            id_card_back_url='',  # 法人身份证反面
            create_datetime=TimeUtil.format_time('2018-7-3 14:00:00'),  # 入驻时间
            day_begin_minute=480  # 账单日结开始时间(延后day_begin_minute分钟) 8点
        )
        m4_admin = MerchantAdmin.objects.create(
            wechat_openid='m4_admin_openid',  # 微信openid
            wechat_unionid='m4_wechat_unionid',  # 微信unionid
            wechat_avatar_url='',  # 收银员微信头像(商户管理员为空)
            wechat_nickname='m4_admin',  # 收银员微信昵称(商户管理员为空)
            merchant_admin_type=MERCHANT_ADMIN_TYPES.ADMIN,  # 类型：管理员/收银员
            status=SYSTEM_USER_STATUS.USING,  # 用户状态
            work_merchant=m4,  # 所属店铺
        )


        # i1 审核 m1 通过
        # i2 审核 m2 通过
        # i2 审核 m3 通过
        # i3 审核 m4 通过
        def mock_audit_merchant_pass(merchant, marketer, time_str):
            merchant.status = MERCHANT_STATUS.USING
            merchant.save()
            MerchantMarketerShip.objects.create(
                merchant=merchant,
                marketer=marketer,
                audit_datetime=TimeUtil.format_time(time_str),  # 商户被审核时间
            )

        mock_audit_merchant_pass(m1, i1, '2018-7-3 18:30:00')
        mock_audit_merchant_pass(m2, i2, '2018-7-3 18:40:00')
        mock_audit_merchant_pass(m3, i2, '2018-7-3 18:50:00')
        mock_audit_merchant_pass(m4, i3, '2018-7-3 18:52:00')



        # 商户投放卡券
        # 2018-7-4 16:20:43 商户m1投放卡券
        # 2018-7-5 16:20:43 商户m2投放卡券
        # 2018-7-6 16:20:43 商户m3投放卡券
        # 2018-7-7 16:20:43 商户m4投放卡券
        # 商户1： m1火锅店  A, B, C 卡券
        #  A: 30张  满 11 减 2
        #  B: 30张  满 15 减 3.3
        #  C: 40张  满 19 减 4.7

        # 商户2： m2火锅店  D, E, F 卡券
        #  D: 10张  满 20 减 3
        #  E: 20张  满 30 减 5.5
        #  F: 20张  满 40 减 6.5

        # 商户3： m3火锅店  X, Y, Z 卡券
        #  X: 200张  满 50 减 10
        #  Y: 200张  满 70 减 15
        #  Z: 100张  满 100 减 25

        # 商户4： m4火锅店  R, S, T 卡券
        #  R: 15张  满 5 减 0.5
        #  S: 25张  满 7 减 1
        #  T: 35张  满 9 减 1.5

        def mock_crate_coupon_rule(merchant, discount, min_charge, stock, create_time_str):
            rule = CouponRule.objects.create(
                merchant=merchant,  # 所属商户
                discount=MoneyUtil.yuan_to_fen(discount),  # 优惠金额
                min_charge=MoneyUtil.yuan_to_fen(min_charge),  # 最低消费
                valid_strategy=VALID_STRATEGY.DATE_RANGE,  # 有效期策略
                start_date=TimeUtil.format_time('2018-7-3 0:0:0'),  # 开始日期
                end_date=TimeUtil.format_time('2019-7-3 0:0:0'),  # 结束日期
                expiration_days=300,  # 有效期天数
                stock=stock,  # 库存
                photo_url='',  # 照片地址2：1， min-width 380
                note='',  # 使用说明
                datetime=TimeUtil.format_time(create_time_str),  # 创建时间
                update_datetime=TimeUtil.format_time(create_time_str),  # 更新时间
            )

            return rule

        rule_m1_a = mock_crate_coupon_rule(m1, 2, 11, 30, '2018-7-4 16:20:43')
        rule_m1_b = mock_crate_coupon_rule(m1, 3.3, 15, 30, '2018-7-4 16:20:43')
        rule_m1_c = mock_crate_coupon_rule(m1, 4.7, 19, 40, '2018-7-4 16:20:43')
        rule_m2_d = mock_crate_coupon_rule(m2, 3, 20, 10, '2018-7-5 16:20:43')
        rule_m2_e = mock_crate_coupon_rule(m2, 5.5, 30, 20, '2018-7-5 16:20:43')
        rule_m2_f = mock_crate_coupon_rule(m2, 6.5, 40, 10, '2018-7-5 16:20:43')
        rule_m3_x = mock_crate_coupon_rule(m3, 10, 50, 200, '2018-7-6 16:20:43')
        rule_m3_y = mock_crate_coupon_rule(m3, 15, 70, 200, '2018-7-6 16:20:43')
        rule_m3_z = mock_crate_coupon_rule(m3, 25, 100, 100, '2018-7-6 16:20:43')
        rule_m4_r = mock_crate_coupon_rule(m4, 0.5, 5, 15, '2018-7-7 16:20:43')
        rule_m4_s = mock_crate_coupon_rule(m4, 1, 7, 25, '2018-7-7 16:20:43')
        rule_m4_t = mock_crate_coupon_rule(m4, 1.5, 9, 35, '2018-7-7 16:20:43')


        # 用户 u1, u2, u3, u4, u5, u6
        def mock_create_client(openid, unionid, openid_channel):
            client = Client.objects.create(
                openid=openid,  # openid,可能是微信或支付宝
                wechat_unionid = unionid,  # 微信unionid
                openid_channel = openid_channel,  # openid渠道
                phone = None,  # 手机号
                status = SYSTEM_USER_STATUS['USING'],  # 状态
                avatar_url = ''  # 消费者头像
            )
            return client
        u1 = mock_create_client('u1_openid', 'u1_unionid', PAY_CHANNELS['WECHAT'])
        u2 = mock_create_client('u2_openid', 'u2_unionid', PAY_CHANNELS['WECHAT'])
        u3 = mock_create_client('u3_openid', 'u3_unionid', PAY_CHANNELS['WECHAT'])
        u4 = mock_create_client('u4_openid', 'u4_unionid', PAY_CHANNELS['ALIPAY'])
        u5 = mock_create_client('u5_openid', 'u5_unionid', PAY_CHANNELS['ALIPAY'])
        u6 = mock_create_client('u6_openid', 'u6_unionid', PAY_CHANNELS['ALIPAY'])

        sharing_details = {
            'all_paid_price': 0,
            'all_share_all': 0,
            'all_share_platform': 0,
            'all_share_inviter': 0,
            'all_share_originator': 0,
        }

        def charge_up(order_price, coupon):
            order_price_fen = MoneyUtil.yuan_to_fen(order_price)
            paid_price_fen = order_price_fen - coupon.discount
            platform_share = round(max(0, paid_price_fen) * PLATFORM_SHARE_RATE)
            inviter_share = round(max(0, paid_price_fen) * INVITER_SHARE_RATE)
            originator_share = round(max(0, paid_price_fen) * ORIGINATOR_SHARE_RATE)
            sharing_details['all_paid_price'] += paid_price_fen
            sharing_details['all_share_all'] += (platform_share + inviter_share + originator_share)
            sharing_details['all_share_platform'] += platform_share
            sharing_details['all_share_inviter'] += inviter_share
            sharing_details['all_share_originator'] += originator_share

        # 2018-7-8  9:23:44  u1 在 m1 消费 10.37元, 获得 m2_D, m3_X, m4_R
        # 2018-7-8 10:56:31  u2 在 m2 消费 17.88元, 获得 m1_A, m3_Y, m4_S
        # 2018-7-8 11:30:22  u3 在 m3 消费 32.45元, 获得 m1_B, m2_E, m4_T
        # 2018-7-8 12:40:22  u4 在 m4 消费 32.45元, 获得 m1_C, m2_F, m3_Z
        # 2018-7-8 15:34:20  u5 在 m2 消费 32.45元, 获得 m1_A, m3_X, m4_R
        # 2018-7-8 17:28:26  u6 在 m3 消费 32.45元, 获得 m1_B, m2_D, m4_S

        def mock_pay_with_no_coupon(client, merchant, order_price, time_str, pay_way, coupon_rule_list):
            coupon_list = []
            new_payment = MockProcessUtil.mock_request_payment(client.id, merchant.id, None,
                            MoneyUtil.yuan_to_fen(order_price), time_str, pay_way)
            for coupon_rule in coupon_rule_list:
                new_coupon = MockProcessUtil.mock_get_coupon(client, coupon_rule, time_str, merchant)
                coupon_list.append(new_coupon)
            MockProcessUtil.mock_on_payment_success(platform_account.id, new_payment, time_str)
            MockProcessUtil.mock_on_payment_unfreeze(platform_account.id, new_payment, time_str)
            return coupon_list

        u1_coupon_list = mock_pay_with_no_coupon(u1, m1, 10.37, '2018-7-8 9:23:44', PAY_CHANNELS['WECHAT'],[rule_m2_d, rule_m3_x, rule_m4_r])
        u2_coupon_list = mock_pay_with_no_coupon(u2, m2, 17.88, '2018-7-8 10:56:31', PAY_CHANNELS['WECHAT'],[rule_m1_a, rule_m3_y, rule_m4_s])
        u3_coupon_list = mock_pay_with_no_coupon(u3, m3, 32.45, '2018-7-8 11:30:22', PAY_CHANNELS['WECHAT'],[rule_m1_b, rule_m2_e, rule_m4_t])
        u4_coupon_list = mock_pay_with_no_coupon(u4, m4, 32.45, '2018-7-8 12:40:22', PAY_CHANNELS['ALIPAY'],[rule_m1_c, rule_m2_f, rule_m3_z])
        u5_coupon_list = mock_pay_with_no_coupon(u5, m2, 32.45, '2018-7-8 15:34:20', PAY_CHANNELS['ALIPAY'],[rule_m1_a, rule_m3_x, rule_m4_r])
        u6_coupon_list = mock_pay_with_no_coupon(u6, m3, 32.45, '2018-7-8 17:28:26', PAY_CHANNELS['ALIPAY'],[rule_m1_b, rule_m2_d, rule_m4_s])
        # new_payment = MockProcessUtil.mock_request_payment(u1.id, m1.id, None, MoneyUtil.yuan_to_fen(10.37),
        #                                      '2018-7-8 9:23:44', PAY_CHANNELS['WECHAT'])
        # MockProcessUtil.mock_on_payment_success(platform_account.id, new_payment, '2018-7-8 9:23:44')
        # MockProcessUtil.mock_get_coupon(u1, rule_m2_d, '2018-7-8 9:23:44')
        # MockProcessUtil.mock_get_coupon(u1, rule_m2_d, '2018-7-8 9:23:44')
        # MockProcessUtil.mock_get_coupon(u1, rule_m2_d, '2018-7-8 9:23:44')
        # MockProcessUtil.mock_on_payment_unfreeze(platform_account.id, new_payment, '2018-7-8 9:24:44')

        # 2018-7-9 14:10:47  u1在 m2 使用 m2_D 消费 21.37 元
        # 2018-7-9 16:45:23  u1在 m3 使用 m3_X 消费 52.66 元
        # 2018-7-9 17:30:08  u1在 m3 退款消费 52.66 元
        # 2018-7-9 18:25:32  u1在 m4 使用 m4_R 消费 7.16 元
        def mock_pay_with_no_coupon(client, merchant, coupon, order_price, pay_time_str, pay_way, is_refund, refund_time_str):
            new_payment = MockProcessUtil.mock_request_payment(client.id, merchant.id, coupon.id, MoneyUtil.yuan_to_fen(order_price),
                                                               pay_time_str, pay_way)
            MockProcessUtil.mock_on_payment_success(platform_account.id, new_payment, pay_time_str)
            if is_refund:
                new_refund = MockProcessUtil.mock_request_refund(new_payment, refund_time_str)
                MockProcessUtil.mock_on_refund_success(platform_account.id, new_refund, refund_time_str)
            else:
                charge_up(order_price, coupon)
                MockProcessUtil.mock_on_payment_unfreeze(platform_account.id, new_payment, pay_time_str)

        # 2018-7-9 14:10:47  u1在 m2 使用 m2_D 消费 21.37 元
        # 2018-7-9 16:45:23  u1在 m3 使用 m3_X 消费 52.66 元
        # 2018-7-9 17:30:08  u1在 m3 退款消费 52.66 元
        # 2018-7-9 18:25:32  u1在 m4 使用 m4_R 消费 7.16 元
        mock_pay_with_no_coupon(u1, m2, u1_coupon_list[0], 21.37, '2018-7-9 14:10:47', PAY_CHANNELS['WECHAT'], False, None)
        mock_pay_with_no_coupon(u1, m3, u1_coupon_list[1], 52.66, '2018-7-9 16:45:23', PAY_CHANNELS['WECHAT'], True, '2018-7-9 17:30:08')
        mock_pay_with_no_coupon(u1, m4, u1_coupon_list[2], 7.16, '2018-7-9 18:25:32', PAY_CHANNELS['WECHAT'], False, None)

        # 2018-7-10 9:30:10  u2 在 m1 使用 m1_A 消费 13.47 元
        # 2018-7-10 10:04:32 u2 在 m3 使用 m3_Y 消费 121.3 元
        # 2018-7-10 10:48:21 u2 在 m4 使用 m4_S 消费 10.12 元
        mock_pay_with_no_coupon(u2, m1, u2_coupon_list[0], 13.47, '2018-7-10 9:30:10', PAY_CHANNELS['WECHAT'], False, None)
        mock_pay_with_no_coupon(u2, m3, u2_coupon_list[1], 121.3, '2018-7-10 10:04:32', PAY_CHANNELS['WECHAT'], False, None)
        mock_pay_with_no_coupon(u2, m4, u2_coupon_list[2], 10.12, '2018-7-10 10:48:21', PAY_CHANNELS['WECHAT'], False, None)

        # 2018-7-11 10:21:56 u3 在 m1 使用 m1_B 消费 15.7 元
        # 2018-7-11 13:13:30 u3 在 m2 使用 m2_E 消费 44.2 元
        # 2018-7-11 14:20:18 u3 在 m4 使用 m4_T 消费 9.7 元
        mock_pay_with_no_coupon(u3, m1, u3_coupon_list[0], 15.7, '2018-7-11 10:21:56', PAY_CHANNELS['WECHAT'], False, None)
        mock_pay_with_no_coupon(u3, m2, u3_coupon_list[1], 44.2, '2018-7-11 13:13:30', PAY_CHANNELS['WECHAT'], False, None)
        mock_pay_with_no_coupon(u3, m4, u3_coupon_list[2], 9.7, '2018-7-11 14:20:18', PAY_CHANNELS['WECHAT'], False, None)

        # 2018-7-15 10:21:56 u4 在 m1 使用 m1_C 消费 22.7 元
        # 2018-7-15 13:13:30 u4 在 m2 使用 m2_F 消费 43.1 元
        # 2018-7-15 13:20:54 u4 在 m2 退款消费 43.1
        # 2018-7-15 14:20:18 u4 在 m3 使用 m3_Z 消费 152.7 元
        mock_pay_with_no_coupon(u4, m1, u4_coupon_list[0], 22.7, '2018-7-15 10:21:56', PAY_CHANNELS['ALIPAY'], False, None)
        mock_pay_with_no_coupon(u4, m2, u4_coupon_list[1], 43.1, '2018-7-15 13:13:30', PAY_CHANNELS['ALIPAY'], True, '2018-7-15 13:20:54')
        mock_pay_with_no_coupon(u4, m3, u4_coupon_list[2], 152.7, '2018-7-15 14:20:18', PAY_CHANNELS['ALIPAY'], False, None)

        # 2018-7-16 9:30:10  u5 在 m1 使用 m1_A 消费 12.47 元
        # 2018-7-16 10:48:21 u5 在 m3 使用 m3_X 消费 51.3 元
        # 2018-7-16 19:04:32 u5 在 m4 使用 m4_R 消费 8.12 元
        mock_pay_with_no_coupon(u5, m1, u5_coupon_list[0], 12.47, '2018-7-16 9:30:10', PAY_CHANNELS['ALIPAY'], False, None)
        mock_pay_with_no_coupon(u5, m3, u5_coupon_list[1], 51.3, '2018-7-16 10:48:21', PAY_CHANNELS['ALIPAY'], False, None)
        mock_pay_with_no_coupon(u5, m4, u5_coupon_list[2], 8.12, '2018-7-16 19:04:32', PAY_CHANNELS['ALIPAY'], False, None)

        # 2018-7-17 10:25:32  u6在 m1 使用 m1_B 消费 20.16 元
        # 2018-7-17 14:10:47  u6在 m2 使用 m2_D 消费 21.37 元
        # 2018-7-17 16:45:23  u6在 m4 使用 m4_S 消费 7.66 元
        mock_pay_with_no_coupon(u6, m1, u6_coupon_list[0], 20.16, '2018-7-17 10:25:32', PAY_CHANNELS['ALIPAY'], False, None)
        mock_pay_with_no_coupon(u6, m2, u6_coupon_list[1], 21.37, '2018-7-17 14:10:47', PAY_CHANNELS['ALIPAY'], False, None)
        mock_pay_with_no_coupon(u6, m4, u6_coupon_list[2], 7.66, '2018-7-17 16:45:23', PAY_CHANNELS['ALIPAY'], False, None)


        # 2018-7-18 10:10:10 m1 提现10元
        # 2018-7-19 10:10:10 m2 提现10元
        # 2018-7-19 10:12:10 m3 提现10元
        # 2018-7-20 10:10:10 m4 提现10元
        MockProcessUtil.mock_withdraw(m1.account, MoneyUtil.yuan_to_fen(10), '2018-7-18 10:10:10', WITHDRAW_TYPE['WECHAT'])
        MockProcessUtil.mock_withdraw(m2.account, MoneyUtil.yuan_to_fen(10), '2018-7-19 10:10:10', WITHDRAW_TYPE['WECHAT'])
        MockProcessUtil.mock_withdraw(m3.account, MoneyUtil.yuan_to_fen(10), '2018-7-19 10:12:10', WITHDRAW_TYPE['ALIPAY'])
        MockProcessUtil.mock_withdraw(m4.account, MoneyUtil.yuan_to_fen(10), '2018-7-20 10:10:10', WITHDRAW_TYPE['ALIPAY'])
        # 2018-7-21 10:10:10 i1 提现0.1元
        # 2018-7-22 10:10:10 i2 提现0.1元
        # 2018-7-23 10:12:10 i3 提现0.1元
        MockProcessUtil.mock_withdraw(i1.account, MoneyUtil.yuan_to_fen(0.1), '2018-7-21 10:10:10', WITHDRAW_TYPE['WECHAT'])
        MockProcessUtil.mock_withdraw(i2.account, MoneyUtil.yuan_to_fen(0.1), '2018-7-22 10:10:10', WITHDRAW_TYPE['WECHAT'])
        MockProcessUtil.mock_withdraw(i3.account, MoneyUtil.yuan_to_fen(0.1), '2018-7-23 10:10:10', WITHDRAW_TYPE['WECHAT'])

        def fen_to_yuan(fen):
            if fen is None:
                return 0
            return round(fen / 100.0, 2)
        sharing_details['all_paid_price'] = fen_to_yuan(sharing_details['all_paid_price'])
        sharing_details['all_share_all'] = fen_to_yuan(sharing_details['all_share_all'])
        sharing_details['all_share_platform'] = fen_to_yuan(sharing_details['all_share_platform'])
        sharing_details['all_share_inviter'] = fen_to_yuan(sharing_details['all_share_inviter'])
        sharing_details['all_share_originator'] = fen_to_yuan(sharing_details['all_share_originator'])

        return sharing_details
