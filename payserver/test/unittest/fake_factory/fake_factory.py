#      File: fake_factory.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/21
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from random import randint, choice

from faker import Faker

from common.models import LoginStats, SystemAdmin, MerchantAdmin, Marketer, Client, City, Area, MerchantCategory, \
    PaymentQRCode, Merchant, CouponRule, Coupon, Account, Payment, Refund, Withdraw, Transaction, \
    MerchantMarketerShip, TransferRecord, Settlement

from common.model_manager.utils import set_amount
from config import MERCHANT_STATUS, MARKETER_TYPES, MERCHANT_ADMIN_TYPES, VALID_STRATEGY, COUPON_STATUS, \
    WITHDRAW_STATUS, PAYMENT_STATUS, REFUND_STATUS, PAY_CHANNELS, TRANSACTION_TYPE, SYSTEM_USER_STATUS, \
    WITHDRAW_TYPE, TRANSFER_STATUS, SETTLEMENT_STATUS

fake = Faker('zh_CN')


class Config:
    default_number = 1
    many_to_many_num = 5
    merchant_categories = ('美食', '饮品', '足浴', '珠宝', '健身运动', '电影', '酒店住宿', '密室逃脱', '酒吧', 'KTV',
                           '手机维修', '开锁', '宠物', '超市/生鲜', '鲜花')
    image_urls = (
        'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.GFOwACkadFdDe15e3b97da58527dc8aee94f917354a3.png',
        'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.vXbifX6t4GBJ12b9f3ceaa2b26674b022d4148a894b3.png',
        'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.66AMmUizMaOYcc06e6e74ba8b05925979ce561b0e7ed.png',
        'https://ss1.mvpalpha.muchbo.com//tmp/wxde4cd9477fb1b7cc.o6zAJs_2J1MEva4MSZJ3mD_HZxGs.nvTz6UJsNa5K3690ad76c046f3192363a782eda7fae4.png',
    )
    discount = (5, 10, 12, 15, 20, 30, 40, 50, 55, 59)
    min_charge = (60, 66, 88, 80, 99, 100, 101, 110, 120, 300)
    bank_name = ('交通银行北京长虹桥支行', '中国银行上海市紫竹高新区支行', '工商银行北京学院路支行', '建设银行成都光华支行')

    @staticmethod
    def banlance(min_balance=1, max_balance=10000000):
        return set_amount(randint(min_balance, max_balance))


class PayunionFactory:
    """
        factory = PayunionFactory()
        factory.create_merchant_admin(number=100)  # 将自动生成依赖的model数据
    """

    @staticmethod
    def random_choice(types):
        """
        随机选择属性
        :param types: (tuple)  e.g. config.MERCHANT_ADMIN_TYPES
        :return:
        """
        return choice(list(types.model_choices()))[0]

    def create_login_status(
            self,
            number=Config.default_number,
            last_success_login=None,
            last_success_ip=None,
            last_failed_login=None,
            last_failed_ip=None,
            failed_login_count=None
    ):
        for _ in range(number):
            e = LoginStats.objects.create(
                last_success_login=fake.date_time_this_year(
                    before_now=True) if last_success_login is None else last_success_login,
                last_success_ip=fake.ipv4_public(network=False,
                                                 address_class=None) if last_success_ip is None else last_success_ip,
                last_failed_login=fake.date_time_this_year(
                    before_now=True) if last_failed_login is None else last_failed_login,
                last_failed_ip=fake.ipv4_public(network=False,
                                                address_class=None) if last_failed_ip is None else last_failed_ip,
                failed_login_count=randint(1, 100) if failed_login_count is None else failed_login_count
            )
        return e

    def create_system_admin(
            self,
            number=Config.default_number,
            username=None,
            password=None,
            name=None,
            status=None,
            is_super=None,
            permissions=None,
            login_stats=None
    ):
        for _ in range(number):
            e = SystemAdmin.objects.filter(username=username).first()
            if not e:
                e = SystemAdmin.objects.create(
                    username=fake.email() if username is None else username,
                    password=fake.password() if password is None else password,
                    name=fake.name() if name is None else name,
                    status=self.random_choice(SYSTEM_USER_STATUS) if status is None else status,
                    is_super=fake.boolean() if is_super is None else is_super,
                    permissions='some permission' if permissions is None else permissions,
                    login_stats=self.create_login_status() if login_stats is None else login_stats
                )
                e.save()
        return e

    def create_merchant_admin(
            self,
            number=Config.default_number,
            wechat_openid=None,
            wechat_unionid=None,
            wechat_avatar_url=None,
            wechat_nickname=None,
            alipay_userid=None,
            alipay_user_name=None,
            merchant_admin_type=None,
            status=None,
            voice_on=None,
            work_merchant=None,
    ):
        for _ in range(number):
            e = MerchantAdmin.objects.create(
                wechat_openid=fake.uuid4() if wechat_openid is None else wechat_openid,
                wechat_unionid=fake.uuid4() if wechat_unionid is None else wechat_unionid,
                wechat_avatar_url=choice(Config.image_urls) if wechat_avatar_url is None else wechat_avatar_url,
                wechat_nickname=fake.name() if wechat_nickname is None else wechat_nickname,
                alipay_userid=fake.uuid4() if alipay_userid is None else alipay_userid,
                alipay_user_name=fake.name() if alipay_user_name is None else alipay_user_name,
                merchant_admin_type=self.random_choice(
                    MERCHANT_ADMIN_TYPES) if merchant_admin_type is None else merchant_admin_type,
                status=SYSTEM_USER_STATUS['USING'] if status is None else status,
                voice_on=True if voice_on is None else voice_on,
                work_merchant=self.create_merchant() if work_merchant is None else work_merchant,
            )
            e.save()
        return e

    def create_marketer(
            self,
            number=Config.default_number,
            wechat_openid=None,
            wechat_unionid=None,
            wechat_avatar_url=None,
            wechat_nickname=None,
            alipay_id=None,
            inviter_type=None,
            status=None,
            name=None,
            phone=None,
            id_card_front_url=None,
            id_card_back_url=None,
            account=None,
            worker_number=None,
            working_areas_name=None,
    ):
        for _ in range(number):
            e = Marketer.objects.create(
                wechat_openid=fake.uuid4() if wechat_openid is None else wechat_openid,
                wechat_unionid=fake.uuid4() if wechat_unionid is None else wechat_unionid,
                wechat_avatar_url=choice(Config.image_urls) if wechat_avatar_url is None else wechat_avatar_url,
                wechat_nickname=fake.name() if wechat_nickname is None else wechat_nickname,
                inviter_type=self.random_choice(MARKETER_TYPES) if inviter_type is None else inviter_type,
                status=self.random_choice(SYSTEM_USER_STATUS) if status is None else status,
                name=fake.name() if name is None else name,
                phone=fake.phone_number() if phone is None else phone,
                alipay_id=fake.phone_number() if alipay_id is None else alipay_id,
                id_card_front_url=choice(Config.image_urls) if id_card_front_url is None else id_card_front_url,
                id_card_back_url=choice(Config.image_urls) if id_card_back_url is None else id_card_back_url,
                account=self.create_account() if account is None else account,
                worker_number=fake.uuid4() if worker_number is None else worker_number,
            )
            if e.status == SYSTEM_USER_STATUS['USING']:
                if e.status == SYSTEM_USER_STATUS['USING'] and e.inviter_type == MARKETER_TYPES['SALESMAN']:
                    if working_areas_name:
                        for working_area_name in working_areas_name:
                            e.working_areas.add(self.create_area(name=working_area_name))
                    elif working_areas_name is True:
                        for _ in range(Config.many_to_many_num):
                            e.working_areas.add(self.create_area())
                e.save()
        return e

    def create_client(
            self,
            number=Config.default_number,
            openid=None,
            openid_channel=None,
            phone=None,
            status=None
    ):
        for _ in range(number):
            e = Client.objects.create(
                openid=fake.uuid4() if openid is None else openid,
                openid_channel=self.random_choice(PAY_CHANNELS) if openid_channel is None else openid_channel,
                phone=fake.phone_number() if phone is None else phone,
                status=self.random_choice(SYSTEM_USER_STATUS) if status is None else status
            )
            e.save()
        return e

    def create_city(
            self,
            number=Config.default_number,
            name=None
    ):
        for _ in range(number):
            name_ = fake.city_name() if name is None else name
            e = City.objects.filter(name=name_).first()
            if not e:
                e = City.objects.create(name=name_)
                e.save()
        return e

    def create_area(
            self,
            number=Config.default_number,
            city=None,
            name=None,
            parent=None,
            adcode=None,
    ):
        for _ in range(number):
            name_ = fake.address() if name is None else name
            e = Area.objects.filter(name=name_).first()
            if not e:
                e = Area.objects.create(
                    city=self.create_city() if city is None else city,
                    name=name_,
                )
                if parent is not None:
                    e.parent = parent
                e.adcode = str(e.id) if adcode is None else adcode
                e.save()

        return e

    def create_merchant_category(self, number=Config.default_number, name=None, parent=None):
        for _ in range(number):
            e = MerchantCategory.objects.create(
                name=choice(Config.merchant_categories) if name is None else name
            )
            if parent is not None:
                e.parent = parent
            e.save()
        return e

    def create_payment_qrcode(self, number=Config.default_number, uuid=None):
        for _ in range(number):
            e = PaymentQRCode.objects.create(
                uuid=fake.uuid4() if uuid is None else uuid
            )
            e.save()
        return e

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
                status=self.random_choice(MERCHANT_STATUS) if status is None else status,
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
                avatar_url=choice(Config.image_urls) if avatar_url is None else avatar_url,
                photo_url=choice(Config.image_urls) if photo_url is None else photo_url,
                create_datetime=fake.date_time_this_year(
                    before_now=True) if create_datetime is None else create_datetime,
            )
            if inviter is not None:
                e.inviter = self.create_marketer() if inviter is True else inviter
            if license_url is not None:
                e.license_url = choice(Config.image_urls) if license_url is True else license_url
            if id_card_front_url is not None:
                e.id_card_front_url = choice(Config.image_urls) if id_card_front_url is True else id_card_front_url
            if id_card_back_url is not None:
                e.id_card_back_url = choice(Config.image_urls) if id_card_back_url is True else id_card_back_url
            if day_begin_minute is not None:
                e.day_begin_minute = day_begin_minute
            e.save()
        return e

    def create_coupon_rule(
            self,
            number=Config.default_number,
            merchant=None,
            discount=None,
            min_charge=None,
            valid_strategy=None,
            start_date=None,
            end_date=None,
            expiration_days=None,
            stock=None,
            photo_url=None,
            note=None,
            datetime=None,
            update_datetime=None,
    ):
        for _ in range(number):
            e = CouponRule.objects.create(
                merchant=self.create_merchant() if merchant is None else merchant,
                discount=set_amount(choice(Config.discount)) if discount is None else discount,
                min_charge=set_amount(choice(Config.min_charge)) if min_charge is None else min_charge,
                valid_strategy=self.random_choice(VALID_STRATEGY) if valid_strategy is None else valid_strategy,
                start_date=fake.date_time_this_year(before_now=True) if start_date is None else start_date,
                end_date=fake.future_datetime(end_date="+90d", tzinfo=None) if end_date is None else end_date,
                expiration_days=randint(30, 90) if expiration_days is None else expiration_days,
                stock=randint(0, 100) if stock is None else stock,
                photo_url=choice(Config.image_urls) if photo_url is None else photo_url,
                note=fake.text(max_nb_chars=300, ext_word_list=None) if note is None else note,
            )
            if datetime:
                e.datetime = fake.date_time_this_year(before_now=True) if datetime is True else datetime
            if update_datetime:
                e.update_datetime = fake.date_time_this_year(
                    before_now=True) if update_datetime is True else update_datetime
            e.save()
        return e

    def create_coupon(
            self,
            number=Config.default_number,
            rule=None,
            client=None,
            discount=None,
            min_charge=None,
            originator_merchant=None,
            status=None,
            obtain_datetime=None,
            use_datetime=None,
    ):
        for _ in range(number):
            coupon_rule = self.create_coupon_rule() if rule is None else rule

            status_ = self.random_choice(COUPON_STATUS) if status is None else status
            e = Coupon.objects.create(
                rule=coupon_rule,
                client=self.create_client() if client is None else client,
                discount=coupon_rule.discount if discount is None else discount,
                min_charge=coupon_rule.min_charge if min_charge is None else min_charge,
                originator_merchant=self.create_merchant() if originator_merchant is None else originator_merchant,
                status=status_,
                obtain_datetime=fake.date_time_this_year(
                    before_now=True) if obtain_datetime is None else obtain_datetime,
                use_datetime=(fake.date_time_this_year(before_now=True) if status_ == COUPON_STATUS[
                    'NOT_USED'] else None) if use_datetime is True else use_datetime
            )
            e.save()
        return e

    def create_account(
            self,
            id=None,
            number=Config.default_number,
            bank_name=None,
            bank_card_number=None,
            real_name=None,
            balance=None,
            withdrawable_balance=None,
            alipay_balance=None,
            alipay_withdrawable_balance=None
    ):
        for _ in range(number):
            e = Account.objects.create(
                id=id,
                bank_name=choice(Config.bank_name) if bank_name is None else bank_name,
                bank_card_number=fake.ean(length=13) if bank_card_number is None else bank_card_number,
                real_name=fake.name() if real_name is None else real_name,
                balance=Config.banlance(8000, 100000) if balance is None else balance,
                withdrawable_balance=Config.banlance(5000,
                                                     7000) if withdrawable_balance is None else withdrawable_balance,
                alipay_balance=Config.banlance(8000, 100000) if alipay_balance is None else alipay_balance,
                alipay_withdrawable_balance=Config.banlance(5000,
                                                            7000) if alipay_withdrawable_balance is None else alipay_withdrawable_balance,

            )
            e.save()
        return e

    def create_payment(
            self,
            number=Config.default_number,
            serial_number=None,
            datetime=None,
            pay_channel=None,
            status=None,
            merchant=None,
            client=None,
            order_price=None,
            coupon=None,  # coupon=True  auto create a coupon
            platform_share=None,
            inviter_share=None,
            originator_share=None,
            note=None,
            coupon_granted=False
    ):
        for _ in range(number):
            e = Payment.objects.create(
                serial_number=fake.md5() if serial_number is None else serial_number,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime,
                pay_channel=self.random_choice(PAY_CHANNELS) if pay_channel is None else pay_channel,
                status=self.random_choice(PAYMENT_STATUS) if status is None else status,
                merchant=self.create_merchant() if merchant is None else merchant,
                client=self.create_client() if client is None else client,
                order_price=Config.banlance(20, 1000) if order_price is None else order_price,
                platform_share=Config.banlance(1, 2) if platform_share is None else platform_share,
                inviter_share=Config.banlance(1, 2) if inviter_share is None else inviter_share,
                originator_share=Config.banlance(1, 2) if originator_share is None else originator_share,
                note=fake.text(max_nb_chars=300, ext_word_list=None) if note is None else note,
                coupon=self.create_coupon() if coupon is True else coupon,
                coupon_granted=coupon_granted
            )
            e.save()
        return e

    def create_refund(
            self,
            number=Config.default_number,
            serial_number=None,
            datetime=None,
            status=None,
            payment=None,
    ):
        for _ in range(number):
            if payment:
                datetime = payment.datetime
            else:
                payment = self.create_payment()

            e = Refund.objects.create(
                serial_number=fake.md5() if serial_number is None else serial_number,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime,
                status=self.random_choice(REFUND_STATUS) if status is None else status,
                payment=payment,
            )
            e.save()
        return e

    def create_withdraw(
            self,
            number=Config.default_number,
            withdraw_type=None,
            serial_number=None,
            datetime=None,
            status=None,
            account=None,
            amount=None,
    ):
        for _ in range(number):
            e = Withdraw.objects.create(
                withdraw_type=WITHDRAW_TYPE.WECHAT if withdraw_type is None else withdraw_type,
                serial_number=fake.md5() if serial_number is None else serial_number,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime,
                status=self.random_choice(WITHDRAW_STATUS) if status is None else status,
                account=self.create_account() if account is None else account,
                amount=Config.banlance(100, 2000) if amount is None else amount,
            )
            e.save()
        return e

    def create_settlement(
            self,
            number=Config.default_number,
            serial_number=None,
            datetime=None,
            finished_datetime=None,
            status=None,
            account=None,
            wechat_amount=None,
            alipay_amount=None,
    ):
        for _ in range(number):
            e = Settlement.objects.create(
                serial_number=fake.md5() if serial_number is None else serial_number,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime,
                finished_datetime=fake.date_time_this_year(before_now=True) if finished_datetime is None else finished_datetime,
                status=self.random_choice(SETTLEMENT_STATUS) if status is None else status,
                account=self.create_account() if account is None else account,
                wechat_amount=Config.banlance(100, 2000) if wechat_amount is None else wechat_amount,
                alipay_amount=Config.banlance(100, 2000) if alipay_amount is None else alipay_amount,
            )
            e.save()
        return e

    def create_transaction(
            self,
            number=Config.default_number,
            transaction_type=None,
            datetime=None,
            account=None,
            amount=None,
            balance_after_transaction=None,
            content_object=None,
    ):

        for _ in range(number):
            e = Transaction.objects.create(
                transaction_type=self.random_choice(TRANSACTION_TYPE) if transaction_type is None else transaction_type,
                account=self.create_account() if account is None else account,
                amount=Config.banlance(20, 1000) if amount is None else amount,
                balance_after_transaction=Config.banlance(20,
                                                          1000) if balance_after_transaction is None else balance_after_transaction,
                content_object=self.create_payment() if content_object is None else content_object,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime
            )
            if datetime is True:
                e.datetime = fake.date_time_this_year(before_now=True)
            elif datetime is not None:
                e.datetime = datetime
            e.save()
        return e

    def create_merchant_marketer_ship(
            self,
            number=Config.default_number,
            merchant=None,
            marketer=None,
            audit_datetime=None,
            audit_info=None
    ):
        for _ in range(number):
            e = MerchantMarketerShip.objects.create(
                marketer=self.create_marketer() if marketer is None else marketer,
                merchant=self.create_merchant() if merchant is None else merchant,
                audit_datetime=fake.date_time_this_year(before_now=True) if audit_datetime is None else audit_datetime,
                audit_info=fake.text(max_nb_chars=100, ext_word_list=None) if audit_info is None else audit_info
            )
            e.save()
        return e

    def create_transfer_record(
            self,
            number=Config.default_number,
            serial_number=None,
            account_number=None,
            account_name=None,
            wechat_unionid=None,
            status=None,
            amount=None,
            datetime=None
    ):

        for _ in range(number):
            e = TransferRecord.objects.create(
                serial_number=fake.md5() if serial_number is None else serial_number,
                account_number=account_number,
                account_name=account_name,
                wechat_unionid=wechat_unionid,
                status=self.random_choice(TRANSFER_STATUS) if status is None else status,
                amount=Config.banlance(1, 1) if amount is None else amount,
                datetime=fake.date_time_this_year(before_now=True) if datetime is None else datetime
            )
            if datetime is True:
                e.datetime = fake.date_time_this_year(before_now=True)
            elif datetime is not None:
                e.datetime = datetime
            e.save()
        return e
