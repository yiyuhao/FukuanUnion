#      File: test_merchant_view_set.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/26
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from contextlib import contextmanager

from django.core.cache import cache
from django.utils import timezone
from django.utils.timezone import timedelta
from faker import Faker
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.error_handler import MerchantError
from common.model_manager.utils import set_amount
from common.models import Merchant
from config import TRANSACTION_TYPE, COUPON_STATUS, MERCHANT_STATUS, MERCHANT_ADMIN_TYPES, PAYMENT_STATUS, \
    SYSTEM_USER_STATUS, REFUND_STATUS, PAY_CHANNELS, WECHAT_MAX_WITHDRAW_AMOUNT, ALIPAY_MAX_WITHDRAW_AMOUNT
from test.api_test.merchant.utils import MerchantLoginedMixin
from test.unittest.fake_factory import PayunionFactory
from test.utils import NonFieldError

fake = Faker('zh_CN')


class TestMerchantViewSet(MerchantLoginedMixin, APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

        # 商户分类
        cls.merchant_category = None
        for p in range(4):
            parent = cls.factory.create_merchant_category(name='parent{}'.format(p))
            for c in range(4):
                cls.merchant_category = cls.factory.create_merchant_category(
                    parent=parent,
                    name='{}_child{}'.format(parent.name, c))

        # 商户街道
        for p in range(4):
            parent = cls.factory.create_area(name='市{}'.format(p))
            for c in range(4):
                child = cls.factory.create_area(parent=parent, name='{}_区{}'.format(parent.name, c))
                for cc in range(4):
                    cls.area = cls.factory.create_area(parent=child, name='{}_区{}_街道{}'.format(parent.name, c, cc))

        cls.account = cls.factory.create_account(
            balance=set_amount(1000.00),
            withdrawable_balance=set_amount('500.05'),
            alipay_balance=set_amount(2000),
            alipay_withdrawable_balance=set_amount('1000.05'),
            real_name='张三',
            bank_card_number='1234567890123',
            bank_name='中国招商银行成都玉林路支行'
        )

        cls.merchant = cls.factory.create_merchant(
            name='就是这个公司',
            status=MERCHANT_STATUS['USING'],
            account=cls.account,
            area=cls.area,
            category=cls.merchant_category,
            avatar_url='https://merchant_avatar.jpg',
            photo_url='https://merchant_photo.jpg',
            id_card_back_url=True,
            id_card_front_url=True,
            day_begin_minute=8 * 60,  # 商户订单日结时间设置为08:00
        )
        cls.merchant_admin = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN'],
            work_merchant=cls.merchant,
            wechat_nickname='张微信',
            alipay_user_name='张付宝',
            voice_on=True
        )
        cls.merchant_cashier = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            work_merchant=cls.merchant
        )

        # 创建token并缓存, 绕过登录
        super(TestMerchantViewSet, cls).setUpTestData()

    @contextmanager
    def merchant_status(self, status_='using'):
        old_status = self.merchant.status
        self.merchant.status = MERCHANT_STATUS[status_.upper()]
        self.merchant.save()
        yield
        self.merchant.refresh_from_db()
        self.merchant.status = old_status
        self.merchant.save()

    @contextmanager
    def merchant_admin_status(self, status_='using'):
        old_status = self.merchant_admin.status
        self.merchant_admin.status = SYSTEM_USER_STATUS[status_.upper()]
        self.merchant_admin.save()
        yield
        self.merchant_admin.refresh_from_db()
        self.merchant_admin.status = old_status
        self.merchant_admin.save()

    @contextmanager
    def not_change_account(self):
        old_balance = self.account.balance
        old_withdrawable_balance = self.account.withdrawable_balance
        old_alipay_balance = self.account.alipay_balance
        old_alipay_withdrawable_balance = self.account.alipay_withdrawable_balance
        yield
        self.account.balance = old_balance
        self.account.withdrawable_balance = old_withdrawable_balance
        self.account.alipay_balance = old_alipay_balance
        self.account.alipay_withdrawable_balance = old_alipay_withdrawable_balance
        self.account.save()

    def test_statistics(self):

        yesterday = timezone.now().replace(hour=1)
        today = timezone.now().replace(hour=9)

        # 1. 今日创建一笔退款订单
        refund_payment = self.factory.create_payment(
            datetime=today,
            merchant=self.merchant,
            order_price=set_amount(100),
            status=PAYMENT_STATUS.REFUND
        )

        # 退款订单
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
            datetime=today,
            account=self.account,
            amount=set_amount(100),
            content_object=refund_payment
        )
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_REFUND,
            datetime=today,
            account=self.account,
            amount=-set_amount(100),
            content_object=self.factory.create_refund(
                datetime=today, status=REFUND_STATUS.FINISHED, payment=refund_payment)
        )

        # 2. 昨日今日分别创建一笔未支付订单, 一笔优惠订单, 一笔普通订单, 一笔引流收益
        for datetime_ in (yesterday, today):
            # 未支付订单
            self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.UNPAID,
                merchant=self.merchant,
                order_price=set_amount(100),
            )

            # 优惠券订单
            coupon = self.factory.create_coupon(
                discount=set_amount(10),
                min_charge=set_amount(100),
                status=COUPON_STATUS.USED,
                use_datetime=datetime_,
            )
            use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(110),
                coupon=coupon,
                platform_share=set_amount(3),
                originator_share=set_amount(1),
                inviter_share=set_amount(1)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(95),
                content_object=use_coupon_payment,
            )

            # 普通订单
            not_use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(100),
                platform_share=set_amount(0),
                originator_share=set_amount(0),
                inviter_share=set_amount(0)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(100),
                content_object=not_use_coupon_payment,
            )

            # 引流收益
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(1),
            )

        url = reverse('merchant-statistics')
        response = self.client.get(url, Token=self.token)
        statistics = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            statistics,
            {'name': '就是这个公司',
             'status': self.merchant.status,
             'avatar_url': self.merchant.avatar_url,
             'wechat_balance': 1000,
             'alipay_balance': 2000,
             'turnover': 200,
             'originator_expenditure': 5,
             'originator_earning': 1,
             'payment': {'use_coupon': 1, 'not_use_coupon': 2}})  # 订单数要计算退款订单

    def test_list_earning(self):

        the_day_before_yesterday = timezone.now() - timedelta(days=2)
        yesterday = timezone.now() - timedelta(days=1)

        # 1. 昨日创建一笔退款订单
        refund_payment = self.factory.create_payment(
            datetime=yesterday,
            merchant=self.merchant,
            order_price=set_amount(100),
            status=PAYMENT_STATUS.REFUND
        )

        # 退款订单
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
            datetime=yesterday,
            account=self.account,
            amount=set_amount(100),
            content_object=refund_payment
        )
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_REFUND,
            datetime=yesterday,
            account=self.account,
            amount=-set_amount(100),
            content_object=self.factory.create_refund(
                datetime=yesterday, status=REFUND_STATUS.FINISHED, payment=refund_payment)
        )

        # 2. 前天昨天分别创建一笔未支付订单, 一笔优惠订单, 一笔普通订单, 一笔引流收益
        for datetime_ in (the_day_before_yesterday, yesterday):
            # 未支付订单
            self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.UNPAID,
                merchant=self.merchant,
                order_price=set_amount(100),
            )

            # 优惠券订单
            coupon = self.factory.create_coupon(
                discount=set_amount(10),
                min_charge=set_amount(100),
                status=COUPON_STATUS.USED,
                use_datetime=datetime_,
            )
            use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(110),
                coupon=coupon,
                platform_share=set_amount(3),
                originator_share=set_amount(1),
                inviter_share=set_amount(1)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(95),
                content_object=use_coupon_payment,
            )

            # 普通订单
            not_use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(100),
                platform_share=set_amount(0),
                originator_share=set_amount(0),
                inviter_share=set_amount(0)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(100),
                content_object=not_use_coupon_payment,
            )

            # 引流收益
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(1),
            )

        url = reverse('merchant-list_earning')
        start_date = timezone.now().date().replace(year=timezone.now().year - 1, day=1)
        response = self.client.get(url, dict(start_date=start_date), Token=self.token)
        statistics = response.json()
        for earning in statistics:
            date, amount = earning['date'], earning['amount']
            if date in (the_day_before_yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')):
                self.assertEqual(amount, 95 + 100 + 1)
            else:
                self.assertEqual(amount, 0)

    def test_info(self):
        url = reverse('merchant-info')
        response = self.client.get(url, Token=self.token)
        info = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(info['name'], '就是这个公司')
        self.assertEqual(info['avatar_url'], 'https://merchant_avatar.jpg')
        self.assertEqual(info['employer_num'], 2)
        self.assertEqual(info['day_begin_minute'], self.merchant.day_begin_minute)

        # 增加员工
        self.factory.create_merchant_admin(number=2, work_merchant=self.merchant)
        self.factory.create_merchant_admin(4)
        response = self.client.get(url, Token=self.token)
        info = response.json()
        self.assertEqual(info['employer_num'], 4)

    def test_day_begin_minute(self):
        url = reverse('merchant-day-begin-minute')
        response = self.client.put(url, data={'day_begin_minute': 481}, Token=self.token,
                                   format='json')
        self.assertEqual(response.json()['day_begin_minute'], 481)
        # 验证数据库修改成功
        self.merchant.refresh_from_db()
        self.assertEqual(self.merchant.day_begin_minute, 481)
        self.merchant.day_begin_minute = 8 * 60
        self.merchant.save()

    def test_business_report(self):
        first_day = timezone.now().replace(year=2018, month=1, day=1, hour=9)
        second_day = timezone.now().replace(year=2018, month=1, day=2, hour=9)

        # 1. 创建一笔退款订单
        refund_payment = self.factory.create_payment(
            datetime=second_day,
            merchant=self.merchant,
            order_price=set_amount(100),
            status=PAYMENT_STATUS.REFUND
        )

        # 退款订单
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
            datetime=second_day,
            account=self.account,
            amount=set_amount(100),
            content_object=refund_payment
        )
        self.factory.create_transaction(
            transaction_type=TRANSACTION_TYPE.MERCHANT_REFUND,
            datetime=second_day,
            account=self.account,
            amount=-set_amount(100),
            content_object=self.factory.create_refund(
                datetime=second_day, status=REFUND_STATUS.FINISHED, payment=refund_payment)
        )

        # 2. 两天分别创建一笔未支付订单, 一笔优惠订单, 一笔普通订单, 一笔引流收益
        for datetime_ in (first_day, second_day):
            # 未支付订单
            self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.UNPAID,
                merchant=self.merchant,
                order_price=set_amount(100),
            )

            # 优惠券订单
            coupon = self.factory.create_coupon(
                discount=set_amount(10),
                min_charge=set_amount(100),
                status=COUPON_STATUS.USED,
                use_datetime=datetime_,
            )
            use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(110),
                coupon=coupon,
                platform_share=set_amount(3),
                originator_share=set_amount(1),
                inviter_share=set_amount(1)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(95),
                content_object=use_coupon_payment,
            )

            # 普通订单
            not_use_coupon_payment = self.factory.create_payment(
                datetime=datetime_,
                status=PAYMENT_STATUS.FINISHED,
                merchant=self.merchant,
                order_price=set_amount(100),
                platform_share=set_amount(0),
                originator_share=set_amount(0),
                inviter_share=set_amount(0)
            )
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_RECEIVE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(100),
                content_object=not_use_coupon_payment,
            )

            # 引流收益
            self.factory.create_transaction(
                transaction_type=TRANSACTION_TYPE.MERCHANT_SHARE,
                datetime=datetime_,
                account=self.account,
                amount=set_amount(1),
            )

        url = reverse('merchant-business_report')

        # 第一日数据
        response = self.client.get(url, dict(start_date=first_day.strftime('%Y-%m-%d'),
                                             end_date=first_day.strftime('%Y-%m-%d')),
                                   Token=self.token, format='json')
        result = response.json()
        self.assertEqual(
            result,
            {'turnover': 200,
             'originator_expenditure': 5,
             'originator_earning': 1,
             'payment': {'use_coupon': 1, 'not_use_coupon': 1}}
        )

        # 第二日数据
        response = self.client.get(url, dict(start_date=second_day.strftime('%Y-%m-%d'),
                                             end_date=second_day.strftime('%Y-%m-%d')),
                                   Token=self.token, format='json')
        result = response.json()
        self.assertEqual(
            result,
            {'turnover': 200,
             'originator_expenditure': 5,
             'originator_earning': 1,
             'payment': {'use_coupon': 1, 'not_use_coupon': 2}}
        )

        # 第1-10日数据
        response = self.client.get(url, dict(start_date=first_day.strftime('%Y-%m-%d'),
                                             end_date=(first_day + timedelta(days=9)).strftime('%Y-%m-%d')),
                                   Token=self.token, format='json')
        result = response.json()
        self.assertEqual(
            result,
            {'turnover': 400,
             'originator_expenditure': 10,
             'originator_earning': 2,
             'payment': {'use_coupon': 2, 'not_use_coupon': 3}}
        )

    def test_category(self):
        url = reverse('merchant-category')
        response = self.client.get(url, Token=self.token)
        categories = response.json()
        for category in categories:
            for i, child in enumerate(category['children']):
                self.assertEqual(child['name'], '{}_child{}'.format(category['name'], i))

    def test_area(self):

        url = reverse('merchant-area')
        response = self.client.get(url, Token=self.token)
        areas = response.json()

        for p, area in enumerate(areas):
            if 'children' in area:
                self.assertEqual(area['name'], '市{}'.format(p))
                for c, child in enumerate(area['children']):
                    self.assertEqual(child['name'], '{}_区{}'.format(area['name'], c))
                    self.assertNotIn('children', child)
                    # 只陈列区级以上区域
                    # for cc, c_child in enumerate(child['children']):
                    #     self.assertEqual(c_child['name'], '{}_区{}_街道{}'.format(area['name'], c, cc))

        # permission
        with self.merchant_status('rejected'):
            response = self.client.get(url, Token=self.token)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            info = response.json()
            self.assertEqual(info, MerchantError.invalid_status)

        with self.merchant_status('reviewing'):
            response = self.client.get(url, Token=self.token)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            info = response.json()
            self.assertEqual(info, MerchantError.invalid_status)

        with self.merchant_status('disabled'):
            response = self.client.get(url, Token=self.token)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            info = response.json()
            self.assertEqual(info, MerchantError.invalid_status)

    def test_withdraw_exception(self):

        # 超过微信最大可提现金额
        url = reverse('merchant-withdraw')
        response = self.client.put(url, data=dict(
            channel=PAY_CHANNELS.ALIPAY,
            amount=ALIPAY_MAX_WITHDRAW_AMOUNT + 1,
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'amount': ['请确保该值小于或者等于 50000。'], 'error_code': 'max_value'})

        # 超过微信最大可提现金额
        url = reverse('merchant-withdraw')
        response = self.client.put(url, data=dict(
            channel=PAY_CHANNELS.WECHAT,
            amount=WECHAT_MAX_WITHDRAW_AMOUNT + 1,
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MerchantError.exceeding_the_wechat_maximum_withdrawal_balance))

        # 提现类型不正确
        response = self.client.put(url, data=dict(
            channel=-1,
            amount=100,
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'channel': ['请确保该值大于或者等于 0。'], 'error_code': 'min_value'})

        # 微信可提现余额不足
        response = self.client.put(url, data=dict(
            channel=PAY_CHANNELS.WECHAT,
            amount=500.11,
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MerchantError.withdrawable_balance_not_sufficient))

        # 支付宝可提现余额不足
        response = self.client.put(url, data=dict(
            channel=PAY_CHANNELS.ALIPAY,
            amount=1000.11
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MerchantError.withdrawable_balance_not_sufficient))

        # 未达可提现金额
        response = self.client.put(url, data=dict(
            channel=PAY_CHANNELS.ALIPAY,
            amount='0.99'
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'amount': ['请确保该值大于或者等于 1。'], 'error_code': 'min_value'})

    def test_balance(self):
        url = reverse('merchant-balance')
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, dict(
            wechat_balance=1000,
            wechat_withdrawable_balance=500.05,
            alipay_balance=2000,
            alipay_withdrawable_balance=1000.05,
            wechat_nickname=self.merchant_admin.wechat_nickname,
            alipay_user_name=self.merchant_admin.alipay_user_name,
        ))

        with self.not_change_account():
            # 更改可提现余额为0.99
            self.account.withdrawable_balance = set_amount(0.99)
            self.account.alipay_withdrawable_balance = set_amount(0.99)
            self.account.save()
            # 检查可提现金额显示为0.99(前端显示为0)
            response = self.client.get(url, Token=self.token)
            resp_json = response.json()
            self.assertEqual(resp_json, dict(
                wechat_balance=1000,
                wechat_withdrawable_balance=0.99,
                alipay_balance=2000,
                alipay_withdrawable_balance=0.99,
                wechat_nickname=self.merchant_admin.wechat_nickname,
                alipay_user_name=self.merchant_admin.alipay_user_name,
            ))

    def test_me(self):
        for merchant_status in MERCHANT_STATUS.values():
            # 检查商户状态对应的访问权限
            url = reverse('merchant-me')
            if merchant_status['code'] in ('USING', 'REJECTED'):
                with self.merchant_status(merchant_status['code']):
                    response = self.client.get(url, Token=self.token)
                    detail = response.json()
                    self.assertEqual(detail['id'], self.merchant.id)
                    self.assertEqual(detail['status'], self.merchant.status)
                    self.assertEqual(detail['name'], self.merchant.name)
                    self.assertEqual(detail['category'], self.merchant.category_id)
                    self.assertEqual(detail['avatar_url'], self.merchant.avatar_url)
                    self.assertEqual(detail['photo_url'], self.merchant.photo_url)
                    self.assertEqual(detail['description'], self.merchant.description)
                    self.assertEqual(detail['contact_phone'], self.merchant.contact_phone)
                    self.assertEqual(detail['location_lon'], self.merchant.location_lon)
                    self.assertEqual(detail['location_lat'], self.merchant.location_lat)
                    self.assertEqual(detail['address'], self.merchant.address)
                    self.assertEqual(detail['id_card_back_url'], self.merchant.id_card_back_url)
                    self.assertEqual(detail['id_card_front_url'], self.merchant.id_card_front_url)
                    self.assertEqual(detail['license_url'], self.merchant.license_url)
                    self.assertEqual(detail['alipay_user_name'], self.merchant_admin.alipay_user_name)
                    self.assertEqual(detail['real_name'], self.account.real_name)
                    self.assertEqual(detail['bank_name'], self.account.bank_name)
                    self.assertEqual(detail['bank_card_number'], self.account.bank_card_number)
                    self.assertEqual(detail['bank'], '中国招商银行')

                    # check permission: only for merchant admin
                    response = self.client.get(url, Token=self.cashier_token)
                    detail = response.json()
                    self.assertEqual(detail, MerchantError.not_merchant_admin)

            else:
                with self.merchant_status(merchant_status['code']):
                    response = self.client.get(url, Token=self.token)
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                    info = response.json()
                    self.assertEqual(info, MerchantError.invalid_status)

    def test_update(self):
        # 只有审核不通过才可修改商户具体信息
        with self.merchant_status('rejected'):
            # 不存在的优惠券
            url = reverse('merchant-modify')
            new_attrs = dict(
                area=self.area.adcode,
                name='new name',
                category=self.factory.create_merchant_category().id,
                avatar_url='new avatar_url',
                photo_url='new photo_url',
                description='new description',
                contact_phone='new contact_phone',
                location_lon=float(fake.longitude()),
                location_lat=float(fake.latitude()),
                address='new address',
                license_url='new license_url',
            )

            not_allowed_to_modify = dict(
                status=MERCHANT_STATUS.USING,
                alipay_user_name='李四',
            )

            for attr, value in new_attrs.items():

                old_update_datetime = self.merchant.update_datetime

                response = self.client.put(url, data={attr: value}, Token=self.token, format='json')
                resp_json = response.json()

                # 验证response正确
                self.assertEqual(resp_json[attr], value)

                # 验证修改了商户状态为审核中
                merchant = Merchant.objects.get(pk=self.merchant.id)
                self.assertEqual(MERCHANT_STATUS['REVIEWING'], merchant.status)

                # 验证数据库修改成功
                if attr == 'category':
                    self.assertEqual(merchant.category_id, value)
                elif attr == 'area':
                    self.assertEqual(merchant.area.adcode, value)
                else:
                    self.assertEqual(getattr(merchant, attr), value)

                # 刷新update_time
                self.assertGreater(merchant.update_datetime, old_update_datetime)

                # 恢复状态为审核拒绝
                merchant.status = MERCHANT_STATUS['REJECTED']
                merchant.save()

            # do nothing
            response = self.client.put(url, data={}, Token=self.token, format='json')
            resp_json = response.json()
            # 验证response正确
            self.assertEqual(resp_json['license_url'], new_attrs['license_url'])

        with self.merchant_status('rejected'):

            # 身份证正反面必须同时上传
            response = self.client.put(url, data={'id_card_back_url': 'wrong'}, Token=self.token, format='json')
            resp_json = response.json()
            # 验证response正确
            self.assertEqual(resp_json, {
                'non_field_errors': ['身份证正反面图片必须同时上传'],
                'error_code': 'must upload both front and back id card url'})

            # invalid area
            ad_code = 'invalid adcode'
            response = self.client.put(url, data={'area': ad_code}, Token=self.token, format='json')
            resp_json = response.json()
            self.assertEqual(resp_json, {'area': ['找不到adcode对应的街道'], 'error_code': 'adcode does not exist in areas'})

            # check permission: only for merchant admin
            response = self.client.put(url, data={}, Token=self.cashier_token, format='json')
            detail = response.json()
            self.assertEqual(detail, MerchantError.not_merchant_admin)

            for attr, value in not_allowed_to_modify.items():
                response = self.client.put(url, data={attr: value}, Token=self.token, format='json')
                resp_json = response.json()

                # 验证未修改成功
                self.assertNotEqual(resp_json.get(attr), value)

        with self.merchant_status('using'):
            response = self.client.put(url, data={}, Token=self.token, format='json')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            info = response.json()
            self.assertEqual(info, MerchantError.invalid_status)

    def test_auth(self):
        url = reverse('merchant-auth')
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json, {'name': '就是这个公司'})

        # merchant_admin status is DISABLED
        with self.merchant_admin_status('disabled'):
            response = self.client.get(url, Token=self.token)
            resp_json = response.json()
            self.assertEqual(resp_json, MerchantError.disabled_user)

        # with no token
        response = self.client.get(url)
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.no_token)

        # invalid token
        response = self.client.get(url, Token='invalid token')
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.invalid_token)

        # other user like marketer login merchant app
        marketer_token = 'marketer_token'
        cache.set(marketer_token, dict(
            openid='marketer openid',
            unionid='marketer unionid',
            session_key='session key'), 300)

        response = self.client.get(url, Token=marketer_token)
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.invalid_user)

    def test_login_code_error(self):
        url = reverse('merchant-admin-login')
        data = {'code': 'wrong login code'}
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        resp_json = response.json()

        self.assertEqual(resp_json, NonFieldError(MerchantError.get_openid_error))

    def test_voice_on(self):
        url = reverse('merchant-voice-on')
        response = self.client.put(url, data={'voice_on': False}, Token=self.token, format='json')
        self.assertEqual(response.json()['voice_on'], False)

        # 验证数据库修改成功
        self.merchant_admin.refresh_from_db()
        self.assertEqual(self.merchant_admin.voice_on, False)
