from django.test import TestCase
from django.utils import timezone

from marketer.config import MAX_VERIFY_ACCOUNT_REQUEST_AN_HOUR
from marketer.utils.redis_utils import VerifyAccountLimitRecord
from test.unittest.fake_factory import PayunionFactory
from common.model_manager.marketer_manager import MarketerModelManager
from marketer.model_manager import AreaModelManager, PaymentModelManager, CreateMarketerManager, CreateMerchantManager, \
    UserMerchantModelManager, UserTransactionModelManager
from config import SYSTEM_USER_STATUS, MARKETER_TYPES, MERCHANT_STATUS, PAYMENT_STATUS, TRANSACTION_TYPE, MERCHANT_TYPE


class TestMarketerManager(TestCase):
    factory = PayunionFactory()

    def test_has_area(self):
        manager = AreaModelManager()
        area = self.factory.create_area(adcode='110119110000')
        marketer = self.factory.create_marketer(status=SYSTEM_USER_STATUS.USING, inviter_type=MARKETER_TYPES.SALESMAN)
        marketer.working_areas.add(area)
        self.assertEqual(manager.has_marketer(adcode='110119110000'), True)

    def test_get_merchant_sharing(self):
        manager = PaymentModelManager()
        merchant = self.factory.create_merchant(name='this merchant')
        self.factory.create_payment(merchant=merchant, inviter_share=1989, number=10, status=PAYMENT_STATUS.FINISHED)
        sharing = manager.get_merchant_sharing(obj=merchant)
        self.assertEqual(sharing, 1989 * 10)

    def test_create_marketer(self):
        manager = CreateMarketerManager()
        data = dict(
            wechat_openid='this open id',
            wechat_unionid='this union id',
            inviter_type=MARKETER_TYPES.MARKETER,
            status=SYSTEM_USER_STATUS.USING,
            name='this marketer name',
            phone='this phone num',
            id_card_front_url='this id card front url',
            id_card_back_url='this id card back url'
        )
        marketer_instance = manager.create(data)
        self.assertEqual(marketer_instance.name, data.get('name'))

    def test_create_merchant(self):
        manager = CreateMerchantManager()
        merchant_data = dict(
            status=MERCHANT_STATUS.USING,
            name='this name',
            inviter=self.factory.create_marketer(),
            payment_qr_code=self.factory.create_payment_qrcode(),
            category=self.factory.create_merchant_category(),
            contact_phone='this phone number',
            area=self.factory.create_area(),
            address='this address',
            location_lon=123,
            location_lat=132,
            description='this description',
            avatar_url='this url',
            photo_url='this url',
            license_url='this url',
            id_card_front_url='',
            id_card_back_url='',
            create_datetime=timezone.now()
        )
        admin_data = dict(
            wechat_openid='this openid',
            wechat_unionid='this unionid',
            wechat_avatar_url='this url',
            wechat_nickname='this nickname'
        )
        merchant_acct_data = {
            'bank_name': 'bank name',
            'bank_card_number': '88888888888',
            'real_name': 'real name'
        }
        merchant = manager.create(merchant_data=merchant_data,
                                  merchant_admin_data=admin_data,
                                  merchant_acct_data=merchant_acct_data)
        pass

    def test_audit_merchant(self):
        marketer = self.factory.create_marketer(name='this marketer')
        to_using_merchant = self.factory.create_merchant(name='to_using_merchant', status=MERCHANT_STATUS.REVIEWING)
        to_reject_merchant = self.factory.create_merchant(name='to_reject_merchant', status=MERCHANT_STATUS.REVIEWING)
        manager = UserMerchantModelManager(user=marketer)
        to_using_merchant = manager.audit_merchant(merchant_instance=to_using_merchant, to_status=MERCHANT_STATUS.USING)
        to_reject_merchant = manager.audit_merchant(merchant_instance=to_reject_merchant,
                                                    to_status=MERCHANT_STATUS.REJECTED, audit_info='audit_info')
        audit_info = to_reject_merchant.merchantmarketership_set.all().order_by('-audit_datetime').first()
        pass

    def test_get_all_status_merchant_num(self):
        marketer = self.factory.create_marketer()
        self.factory.create_merchant(number=5, inviter=marketer, status=MERCHANT_STATUS.USING)
        self.factory.create_merchant(number=4, inviter=marketer, status=MERCHANT_STATUS.REVIEWING)
        self.factory.create_merchant(number=3, inviter=marketer, status=MERCHANT_STATUS.REJECTED)
        manager = UserMerchantModelManager(user=marketer)
        res = manager.get_invited_merchant_num()
        self.assertEqual(res.get('reviewing_merchants_num'), 4 + 3)
        self.assertEqual(res.get('using_merchants_num'), 5)

    def test_get_sharing(self):
        marketer = self.factory.create_marketer()
        manager = UserTransactionModelManager(user=marketer)
        merchant = self.factory.create_merchant(inviter=marketer)
        self.factory.create_transaction(account=marketer.account, transaction_type=TRANSACTION_TYPE.MARKETER_SHARE,
                                        amount=100, content_object=self.factory.create_payment(merchant=merchant))
        self.factory.create_transaction(account=marketer.account, transaction_type=TRANSACTION_TYPE.MARKETER_SHARE,
                                        amount=200, content_object=self.factory.create_payment(merchant=merchant))
        self.factory.create_transaction(account=marketer.account, transaction_type=TRANSACTION_TYPE.MARKETER_SHARE,
                                        amount=300, content_object=self.factory.create_payment(merchant=merchant))
        res = manager.get_sharing(merchant=merchant)
        self.assertEqual(res, 100 + 200 + 300)

    def test_get_auditor_merchant(self):

        # 创建地址
        area1 = self.factory.create_area()
        area2 = self.factory.create_area()
        area3 = self.factory.create_area()

        # 为管理员添加工作区域
        marketer = self.factory.create_marketer()
        marketer.working_areas.add(area1, area2)

        # 添加管理员非工作区域但审核过的商铺
        # using_merchant1 = self.factory.create_merchant(status=MERCHANT_STATUS.USING, area=area3)
        # using_merchant2 = self.factory.create_merchant(status=MERCHANT_STATUS.USING, area=area3)
        # using_merchant3 = self.factory.create_merchant(status=MERCHANT_STATUS.USING, area=area3)
        # self.factory.create_merchant_marketer_ship(marketer=marketer, merchant=using_merchant1)
        # self.factory.create_merchant_marketer_ship(marketer=marketer, merchant=using_merchant2)
        # self.factory.create_merchant_marketer_ship(marketer=marketer, merchant=using_merchant3)

        # 添加管理员工作区域待审核商铺
        reviewing_merchant1 = self.factory.create_merchant(status=MERCHANT_STATUS.REVIEWING, area=area1)
        reviewing_merchant2 = self.factory.create_merchant(status=MERCHANT_STATUS.REVIEWING, area=area2)

        # 添加非管理员工作区域商铺
        self.factory.create_merchant(area=area3)

        # 添加管理员工作区域已审核商铺
        using_merchant = self.factory.create_merchant(status=MERCHANT_STATUS.USING, area=area1)

        # 预期查询结果
        # merchant_set = {using_merchant1, using_merchant2, using_merchant3, reviewing_merchant1, reviewing_merchant2}
        merchant_set = {using_merchant, reviewing_merchant1, reviewing_merchant2}
        manager = UserMerchantModelManager(user=marketer)
        res = manager.get_auditor_merchants()

        # 实际查询结果
        res_set = set()
        for item in res:
            res_set.add(item)
        self.assertEqual(merchant_set, res_set)

    def test_check_phone(self):
        self.factory.create_marketer(phone='18888888888')
        mamager = MarketerModelManager()
        res = mamager.check_phone_exist('18888888888')
        self.assertEqual(res, True)

    def test_show_invited_merchants(self):
        marketer = self.factory.create_marketer(status=SYSTEM_USER_STATUS.USING)
        merchant = self.factory.create_merchant(inviter=marketer, status=MERCHANT_STATUS.USING)
        for i in range(10):
            payment = self.factory.create_payment(merchant=merchant, status=PAYMENT_STATUS.FINISHED, order_price=10000,
                                                  inviter_share=10000 * 0.005)
            self.factory.create_transaction(content_object=payment, transaction_type=TRANSACTION_TYPE.MARKETER_SHARE,
                                            amount=payment.inviter_share)
        manager = UserTransactionModelManager(user=marketer)
        res = manager.get_sharing(merchant)
        self.assertEqual(res, 500)

    def test_VerifyAccountLimitRecord(self):
        VerifyAccountLimitRecord.delete_record('test')
        record = 0
        for _ in range(11):
            record = VerifyAccountLimitRecord.record_request_an_hour('test')
        self.assertFalse(record < MAX_VERIFY_ACCOUNT_REQUEST_AN_HOUR)
        VerifyAccountLimitRecord.delete_record('test')
