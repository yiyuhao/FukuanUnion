import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from common.models import (
    City,
    Area,
    MerchantCategory,
    PaymentQRCode,
    Merchant,
    CouponRule,
    Coupon,
    Marketer,
    Account,
    Client)
import config


class Command(BaseCommand):
    help = 'Populate datas for client test'

    @transaction.atomic
    def handle(self, *args, **options):
        # 城市
        cd = City(name='成都')
        bj = City(name='北京')

        cd.save()
        bj.save()

        # 区域
        area_smq = Area(
            city=cd,
            name='驷马桥')

        area_wks = Area(
            city=cd,
            name='五块石')

        area_smq.save()
        area_wks.save()

        # 商户类型
        merchant_category_yinshi = MerchantCategory(
            name='饮食')
        merchant_category_yule = MerchantCategory(
            name='娱乐')

        merchant_category_yinshi.save()
        merchant_category_yule.save()

        # 付款码
        pay_code = PaymentQRCode(uuid=uuid.uuid4())
        pay_code.save()

        # account
        merchant_account = Account(
            bank_name='招商银行成都分行高新支行',
            bank_card_number='7678442831579099123',
            bank_account_name='陈冠希',
            balance=10000,
            withdrawable_balance=8000)
        merchant_account.save()

        marketer_account = Account(
            bank_name='招商银行成都分行高新支行',
            bank_card_number='7678442831579099145',
            bank_account_name='流川枫',
            balance=10000,
            withdrawable_balance=8000)
        marketer_account.save()

        # 业务员
        marketer = Marketer(
            wechat_openid='saxsdadf00xx',
            wechat_unionid='xx456asdfnn',
            inviter_type=config.MARKETER_TYPES.SALESMAN,
            status=config.SYSTEM_USER_STATUS.USING,
            name='流川枫',
            phone='18109045756',
            account=marketer_account,
            worker_number='tnt001')
        marketer.save()
        marketer.working_areas.add(area_wks)

        # 商户
        merchant = Merchant(
            status=config.MERCHANT_STATUS.USING,
            name='生如夏花泰式火锅（鹭洲里店）',
            account=merchant_account,
            payment_qr_code=pay_code,
            category=merchant_category_yinshi,
            contact_phone='18945236754',
            area=area_wks,
            address='成都市五块石北城天街98号',
            location_lon=10,
            location_lat=10,
            description='纯正泰式火锅，家门口的泰式美食旅行',
            avatar_url='https://img.meituan.net/msmerchant/96814ff238209b8b9ecc8144338f9c09253790.jpg',  # noqa
            photo_url='https://img.meituan.net/msmerchant/96814ff238209b8b9ecc8144338f9c09253790.jpg',  # noqa
            license_url='https://img.meituan.net/msmerchant/96814ff238209b8b9ecc8144338f9c09253790.jpg', # noqa
            id_card_front_url='http://img.wenzhangba.com/userup/883/1P4020F057-35O-0.jpg',
            id_card_back_url='http://image2.sina.com.cn/dy/c/2004-03-29/U48P1T1D3073262F23DT20040329135445.jpg',  # noqa
            create_datetime=timezone.now())
        merchant.save()
        merchant.auditors.add(marketer)

        # 用户
        client = Client(
            openid='oUkVN5WSmOYbYSgR74rRPamWmoAM',
            openid_channel=config.PAY_CHANNELS.WECHAT)
        client.save()

        # 优惠券rule
        coupon_rule = CouponRule(
            merchant=merchant,
            discount=10,
            min_charge=50,
            valid_strategy=config.VALID_STRATEGY.EXPIRATION,
            expiration_days=15,
            stock=30,
            photo_url='https://img.meituan.net/msmerchant/96814ff238209b8b9ecc8144338f9c09253790.jpg')  # noqa
        coupon_rule.save()

        coupon = Coupon(
            rule=coupon_rule,
            client=client,
            discount=10,
            min_charge=50,
            originator_merchant=merchant,
            status=config.COUPON_STATUS.NOT_USED,
            obtain_datetime=timezone.now())
        coupon.save()
