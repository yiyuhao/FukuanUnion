#      File: create_demo_data.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/8/13
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.db.transaction import atomic
from django.utils import timezone
from django.utils.timezone import timedelta

from config import TRANSACTION_TYPE, COUPON_STATUS, MERCHANT_STATUS, MERCHANT_ADMIN_TYPES, SYSTEM_USER_STATUS, \
    MARKETER_TYPES, WITHDRAW_TYPE
from common.model_manager.utils import set_amount
from common.models import MerchantAdmin, Area
from common.password_backend import make_password
from test.generate_area_info import main as generate_area
from test.unittest.fake_factory import PayunionFactory


class DemoData:
    factory = PayunionFactory()

    class C:
        categories = {
            '娱乐': ('电玩', '健身游泳', '彩票', '网吧', '按摩', '足浴'),
            '农林牧渔': ('兽医兽药', '农药', '化肥', '养殖', '种植', '园林景观'),
            '旅游住宿': ('旅游', '宾馆酒店', '交通票务'),
            '日用百货': ('文具', '服装', '纺织原料', '箱包', '饰品', '日化用品', '化妆品', '美容', '家具', '家纺家饰',
                     '餐具厨具', '大型家电', '成人用品'),
            '餐饮': ('饮料饮品', '中餐', '牛排', '零食', '冰淇淋', '火锅', '咖啡'),
        }

        avatar_url = 'https://ss1.mvpalpha.muchbo.com/images/8c4d0e63-9d0d-4147-9c4c-bdfe0041d954_.jpg'
        photo_url = 'https://ss1.mvp.muchbo.com/default_avatar_v2/2.png'

        id_card_front_url = 'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.HCOsasOtDFiIfa0725dff5d321d4c45473bbb9a559a9.png'
        id_card_back_url = 'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.LQlXi3PiXc6Y514303d48605a6b93c6acd415b691055.png'

        merchant_admins = [
            dict(name='易宇豪', openid='ocBww1tzu48XhqoyLAAro_K5VjNU', unionid='oYpKH1FA1m_piWNL9RYF8Mi61iCU'),
            dict(name='陈秀梅', openid='1', unionid='oYpKH1NA7fnrBASmTz_61Wh-e3dA'),
            dict(name='代绪', openid='ocBww1oHcnOem9Uhterls3ItFx9o', unionid='oYpKH1BZdJeahn9sL46tsXM7vXqM',
                 qr_code_uuid='129d3209ad9f87771719df50347492d9'),
            dict(name='谢汪益', openid='ocBww1n_-2iKlWyp4lXBS73iWwAc', unionid='oYpKH1E0JUlHLfeGXed1nsCdavoE'),
        ]

        marketers = [
            dict(type='SALESMAN', name='谢汪益', openid='ocBww1n_-2iKlWyp4lXBS73iWwAc',
                 unionid='oYpKH1E0JUlHLfeGXed1nsCdavoE'),
            dict(type='MARKETER', name='刘琳', openid='ocBww1iGLaABtMiNJGgT0fK2mp1g',
                 unionid='oYpKH1BKU3Qdg9kPgCwTAJGgbBJI'),
            dict(type='MARKETER', name='唐田', openid='3',
                 unionid='oYpKH1Ebo1opV914_yj49vyB0Aa8'),
            dict(type='MARKETER', name='李姗', openid='ocBww1lbnnTT8fz84M8WX4mYz4ho',
                 unionid='oYpKH1FXke5DLi38tqZ-p8Sa1VEE'),
        ]

        withdraw = 90
        receive = 100.1
        share = 1.01

    @classmethod
    def already_created(cls):
        return MerchantAdmin.objects.first() is not None

    @classmethod
    def create_marketer(cls, user):
        account = cls.factory.create_account(
            balance=set_amount(10),
            withdrawable_balance=set_amount('0.50'),
            alipay_balance=set_amount('15006.50'),
            alipay_withdrawable_balance=set_amount('15006.50'),
            real_name=user['name']
        )
        cls.marketer = cls.factory.create_marketer(
            wechat_openid=user['openid'],
            wechat_unionid=user['unionid'],
            inviter_type=MARKETER_TYPES[user['type']],
            status=SYSTEM_USER_STATUS['USING'],
            name=user['name'],
            phone='13333333333',
            id_card_front_url=cls.C.id_card_front_url,
            id_card_back_url=cls.C.id_card_back_url,
            account=account,
        )

    @classmethod
    def create_merchant(cls, user):
        # 商户account
        account = cls.factory.create_account(
            balance=set_amount(10),
            withdrawable_balance=set_amount('0.50'),
            alipay_balance=set_amount('15006.50'),
            alipay_withdrawable_balance=set_amount('15006.50'),
            real_name=user['name']
        )

        # 付款二维码, 使用唯一可测试的code
        payment_qr_code = cls.factory.create_payment_qrcode(uuid='129d3209ad9f87771719df50347492d9') \
            if 'qr_code_uuid' in user else None

        # 商户
        merchant = cls.factory.create_merchant(
            name=f"一家咖啡店({user['name']}店)",
            status=MERCHANT_STATUS['USING'],
            location_lat=30.533743,
            location_lon=104.068197,
            account=account,
            area=cls.area,
            category=cls.merchant_category,
            inviter=cls.marketer,
            avatar_url=cls.C.avatar_url,
            photo_url=cls.C.photo_url,
            id_card_back_url=cls.C.id_card_back_url,
            id_card_front_url=cls.C.id_card_front_url,
            payment_qr_code=payment_qr_code
        )
        cls.factory.create_merchant_admin(
            wechat_openid=user['openid'],
            wechat_unionid=user['unionid'],
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN'],
            work_merchant=merchant,
            wechat_nickname=user['name']
        )

        # 创建投放完成的优惠券
        coupon_rule = cls.factory.create_coupon_rule(
            merchant=merchant,
            stock=0
        )

        share_merchant = cls.factory.create_merchant(
            name='通过发优惠券引流客户到达的商户',
            area=cls.area,
            category=cls.merchant_category,
            inviter=cls.marketer,
        )
        grant_coupon_merchant = cls.factory.create_merchant(
            name='发优惠券的商户',
            area=cls.area,
            category=cls.merchant_category,
            inviter=cls.marketer,
        )

        cls.factory.create_coupon(number=1, rule=coupon_rule, status=COUPON_STATUS['NOT_USED'],
                                  originator_merchant=grant_coupon_merchant, use_datetime=timezone.now())
        cls.factory.create_coupon(number=2, rule=coupon_rule, status=COUPON_STATUS['USED'],
                                  originator_merchant=grant_coupon_merchant, use_datetime=timezone.now())
        cls.factory.create_coupon(number=4, rule=coupon_rule, status=COUPON_STATUS['DESTROYED'],
                                  originator_merchant=grant_coupon_merchant, use_datetime=timezone.now())
        cls.factory.create_coupon(number=8, rule=coupon_rule, status=COUPON_STATUS['USED'],
                                  originator_merchant=grant_coupon_merchant,
                                  use_datetime=timezone.now().replace(
                                      hour=7, minute=59, second=59, microsecond=0))

        for day in range(10):
            withdraw = cls.factory.create_withdraw(account=account, amount=set_amount(cls.C.withdraw))
            cls.factory.create_transaction(
                content_object=withdraw,
                account=account,
                datetime=withdraw.datetime,
                transaction_type=TRANSACTION_TYPE['MERCHANT_WITHDRAW'])

            withdraw = cls.factory.create_withdraw(withdraw_type=WITHDRAW_TYPE.ALIPAY, account=account, amount=set_amount(cls.C.withdraw))
            cls.factory.create_transaction(
                content_object=withdraw,
                account=account,
                amount=-withdraw.amount,
                datetime=withdraw.datetime,
                transaction_type=TRANSACTION_TYPE['MERCHANT_WITHDRAW'])

            coupon_rule = cls.factory.create_coupon_rule(
                merchant=merchant,
                datetime=timezone.now(),
                end_date=timezone.now().replace(year=2019)
            )

            coupon = cls.factory.create_coupon(
                rule=coupon_rule, originator_merchant=grant_coupon_merchant,
                obtain_datetime=timezone.now() - timedelta(days=day),
                use_datetime=timezone.now() - timedelta(days=day),
            )
            payment = cls.factory.create_payment(
                merchant=merchant,
                coupon=coupon,
                datetime=timezone.now() - timedelta(days=day),
            )
            cls.factory.create_transaction(
                content_object=payment,
                account=account,
                datetime=payment.datetime,
                transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])

            without_coupon_payment = cls.factory.create_payment(
                merchant=merchant,
                datetime=timezone.now() - timedelta(days=day),
            )
            cls.factory.create_transaction(
                content_object=without_coupon_payment,
                account=account,
                datetime=without_coupon_payment.datetime,
                transaction_type=TRANSACTION_TYPE['MERCHANT_RECEIVE'])

            share = cls.factory.create_payment(
                coupon=cls.factory.create_coupon(rule=coupon_rule, originator_merchant=grant_coupon_merchant),
                datetime=timezone.now() - timedelta(days=day),
                merchant=share_merchant)
            cls.factory.create_transaction(
                content_object=share,
                account=account,
                datetime=share.datetime,
                transaction_type=TRANSACTION_TYPE['MERCHANT_SHARE'])

    @classmethod
    def create(cls):
        if cls.already_created():
            return

        with atomic():
            cls.area = Area.objects.order_by('-id').first()

            # 商户分类
            cls.merchant_category = None
            for p, children in cls.C.categories.items():
                parent = cls.factory.create_merchant_category(name=p)
                for c in children:
                    cls.merchant_category = cls.factory.create_merchant_category(
                        parent=parent,
                        name=c)

            # 创建业务员
            for user in cls.C.marketers:
                cls.create_marketer(user)

            # 创建商户
            for user in cls.C.merchant_admins:
                cls.create_merchant(user)

            # 后台管理员
            cls.factory.create_system_admin(
                username='test@mixadx.com',
                password=make_password('123456'),
                name='super',
                status=SYSTEM_USER_STATUS['USING'],
                is_super=True,
            )


def run():
    DemoData.create()
