import random

import config
from test.unittest.fake_factory.fake_factory import PayunionFactory, Config, fake
from common.models import Marketer, Area, Merchant, MerchantCategory
from test.generate_area_info import main as generate_area


class MarketerFactory(PayunionFactory):
    def create_merchant(
            self,
            number=Config.default_number,
            status=None,
            name=None,
            account=None,
            inviter=None,
            payment_qr_code=None,
            category=None,
            contact_phone=None,
            area=None,
            address=None,
            location_lon=None,
            location_lat=None,
            description=None,
            avatar_url=None,
            photo_url=None,
            license_url=None,
            id_card_front_url=None,
            id_card_back_url=None,
            create_datetime=None,
            day_begin_minute=None,
    ):
        for _ in range(number):
            e = Merchant.objects.create(
                status=self.random_choice(config.MERCHANT_STATUS) if status is None else status,
                name=fake.company() if name is None else name,
                account=self.create_account() if account is None else account,
                payment_qr_code=self.create_payment_qrcode() if payment_qr_code is None else payment_qr_code,
                category=self.create_merchant_category() if category is None else category,
                contact_phone=fake.phone_number() if contact_phone is None else contact_phone,
                area=self.create_area() if area is None else area,
                address=fake.address() if address is None else address,
                location_lon=float(fake.longitude()) if location_lon is None else location_lon,
                location_lat=float(fake.latitude()) if location_lat is None else location_lat,
                description=fake.text(max_nb_chars=300, ext_word_list=None) if description is None else description,
                avatar_url=random.choice(Config.image_urls) if avatar_url is None else avatar_url,
                photo_url=random.choice(Config.image_urls) if photo_url is None else photo_url,
                create_datetime=fake.date_time_this_year(
                    before_now=True) if create_datetime is None else create_datetime,
            )
            if inviter is not None:
                e.inviter = self.create_marketer() if inviter is True else inviter
            if license_url is not None:
                e.license_url = random.choice(Config.image_urls) if license_url is True else license_url
            if id_card_front_url is not None:
                e.id_card_front_url = random.choice(
                    Config.image_urls) if id_card_front_url is True else id_card_front_url
            if id_card_back_url is not None:
                e.id_card_back_url = random.choice(Config.image_urls) if id_card_back_url is True else id_card_back_url
            if day_begin_minute is not None:
                e.day_begin_minute = day_begin_minute
            e.save()
            self.create_merchant_admin(merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
                                       status=config.SYSTEM_USER_STATUS.USING,
                                       work_merchant=e)
        return e


class GenerateMarketerData:
    _f = MarketerFactory()
    categories = {
        '娱乐': ('电玩', '健身游泳', '彩票', '网吧', '按摩', '足浴'),
        '农林牧渔': ('兽医兽药', '农药', '化肥', '养殖', '种植', '园林景观'),
        '旅游住宿': ('旅游', '宾馆酒店', '交通票务'),
        '日用百货': ('文具', '服装', '纺织原料', '箱包', '饰品', '日化用品', '化妆品', '美容', '家具', '家纺家饰',
                 '餐具厨具', '大型家电', '成人用品'),
        '餐饮': ('饮料饮品', '中餐', '牛排', '零食', '冰淇淋', '火锅', '咖啡'),
    }

    def __init__(self, marketer_id=None):
        self.marketer = Marketer.objects.get(id=marketer_id) if marketer_id else None

    @classmethod
    def generate_category_info(cls):
        for root, subs in cls.categories.items():
            root_category = MerchantCategory.objects.create(name=root)
            for sub in subs:
                MerchantCategory.objects.create(name=sub, parent=root_category)

    @classmethod
    def generate_area(cls):
        generate_area(write_db=True)

    def create_platform_account(self):
        self._f.create_account(
            id=1,
            real_name='平台账户',
            balance=100000000,
            withdrawable_balance=100000000,
            alipay_balance=100000000,
            alipay_withdrawable_balance=100000000
        )

    def init_marketer(self, marketer_id):
        self.marketer = Marketer.objects.get(id=marketer_id)

    def create_marketer(self, marketer_info=None):
        marketer_info = marketer_info or dict(unionid='oYpKH1Cvof7wewQ4e6WJcokIOIr8',
                                              openid='JxyKtZeqCDUxDbI1FgkRLs78Im8g0oPgWyXVfseUl5w=')
        return self._f.create_marketer(
            wechat_openid=marketer_info['openid'],
            wechat_unionid=marketer_info['unionid'],
            wechat_nickname='张继华',
            alipay_id='cyvkaa2286@sandbox.com',
            inviter_type=config.MARKETER_TYPES.SALESMAN,
            status=config.SYSTEM_USER_STATUS.USING,
            name='沙箱环境',
            phone='13730897717',
        ).id

    def update_marketer_type(self):
        self.marketer.inviter_type = config.MARKETER_TYPES.SALESMAN
        self.marketer.save()

    def add_working_area(self, adcode):
        area = Area.objects.get(adcode=adcode)
        self.marketer.working_areas.add(area)

    def create_merchant(self):
        area = self.marketer.working_areas.all().first()
        self._f.create_merchant(number=10, status=config.MERCHANT_STATUS.USING, inviter=self.marketer, area=area)
        self._f.create_merchant(number=5, status=config.MERCHANT_STATUS.REVIEWING, inviter=self.marketer, area=area)
        self._f.create_merchant(number=3, status=config.MERCHANT_STATUS.REJECTED, inviter=self.marketer, area=area)

    def create_transaction(self):
        for i in range(10):
            merchant = self.marketer.invited_merchants.all().order_by('?').first()
            coupon = self._f.create_coupon(discount=100, originator_merchant=merchant)
            withdraw = self._f.create_withdraw(amount=random.randint(100, 10000),
                                               withdraw_type=random.choice([config.WITHDRAW_TYPE.WECHAT,
                                                                            config.WITHDRAW_TYPE.ALIPAY]))

            payment = self._f.create_payment(inviter_share=random.randint(100, 10000),
                                             coupon=coupon,
                                             merchant=merchant,
                                             status=config.PAYMENT_STATUS.FINISHED,
                                             pay_channel=random.choice([config.PAY_CHANNELS.WECHAT,
                                                                        config.PAY_CHANNELS.ALIPAY])
                                             )
            self._f.create_transaction(
                account=self.marketer.account,
                content_object=withdraw
            )
            self._f.create_transaction(
                account=self.marketer.account,
                content_object=payment
            )

    def init_local_db(self):
        self.create_platform_account()
        self.generate_category_info()
        self.generate_area()


def go():
    GenerateMarketerData().init_local_db()
