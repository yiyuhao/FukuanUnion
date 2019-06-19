#      File: test_cashier_view_set.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/17
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from faker import Faker
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.error_handler import MerchantError
from common.models import MerchantAdmin
from config import SYSTEM_USER_STATUS, MERCHANT_ADMIN_TYPES, MERCHANT_STATUS
from test.api_test.merchant.utils import MerchantLoginedMixin
from test.unittest.fake_factory import PayunionFactory

fake = Faker('zh_CN')


class TestCashierViewSet(MerchantLoginedMixin, APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()

        cls.merchant = cls.factory.create_merchant(status=MERCHANT_STATUS['USING'])
        cls.merchant_admin = cls.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['ADMIN'],
            work_merchant=cls.merchant
        )

        # create cashiers

        cls.merchant_cashier = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.normal_cashier_b = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.other_merchant_cashier = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['USING'],
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )

        cls.disabled_cashier = cls.factory.create_merchant_admin(
            status=SYSTEM_USER_STATUS['DISABLED'],
            work_merchant=cls.merchant,
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER']
        )
        # 创建token并缓存, 绕过登录
        super(TestCashierViewSet, cls).setUpTestData()

    def test_remove(self):

        not_exist_id = 100000

        # success
        url = reverse('cashier-remove', kwargs=dict(pk=self.normal_cashier_b.id))
        response = self.client.get(url, Token=self.token)
        result = response.json()
        self.assertEqual(result, {})

        # fail
        url = reverse('cashier-remove', kwargs=dict(pk=self.other_merchant_cashier.id))
        response = self.client.get(url, Token=self.token)
        result = response.json()
        self.assertEqual(result, MerchantError.cashier_does_not_exist)

        url = reverse('cashier-remove', kwargs=dict(pk=self.disabled_cashier.id))
        response = self.client.get(url, Token=self.token)
        result = response.json()
        self.assertEqual(result, MerchantError.cashier_does_not_exist)

        url = reverse('cashier-remove', kwargs=dict(pk=not_exist_id))
        response = self.client.get(url, Token=self.token)
        result = response.json()
        self.assertEqual(result, MerchantError.cashier_does_not_exist)

        # check permission: only for merchant admin
        response = self.client.get(url, Token=self.cashier_token)  # auth by token
        detail = response.json()
        self.assertEqual(detail, MerchantError.not_merchant_admin)

        # restore test env
        self.normal_cashier_b.status = SYSTEM_USER_STATUS['USING']
        self.normal_cashier_b.save()

    def test_list(self):
        url = reverse('cashier-list')
        response = self.client.get(url, Token=self.token)
        cashiers = response.json()
        self.assertEqual(len(cashiers), 2)
        for cashier in cashiers:
            get_cashier_object = {
                self.merchant_cashier.id: self.merchant_cashier,
                self.normal_cashier_b.id: self.normal_cashier_b,
            }
            ins = get_cashier_object[cashier['id']]
            self.assertEqual(cashier['id'], ins.id)
            self.assertEqual(cashier['wechat_openid'], ins.wechat_openid)
            self.assertEqual(cashier['wechat_unionid'], ins.wechat_unionid)
            self.assertEqual(cashier['wechat_avatar_url'], ins.wechat_avatar_url)
            self.assertEqual(cashier['wechat_nickname'], ins.wechat_nickname)

    def test_create(self):
        new_cashier = dict(
            wechat_openid='new cashier wechat_openid',
            wechat_unionid='new cashier wechat_unionid',
            wechat_avatar_url='new cashier wechat_avatar_url',
            wechat_nickname='new cashier wechat_nickname',
        )
        url = reverse('cashier-list')
        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        created_cashier = response.json()
        new_cashier['id'] = created_cashier['id']
        self.assertEqual(created_cashier, new_cashier)

        # check database
        cashier_ins = MerchantAdmin.objects.get(pk=created_cashier['id'])
        for attr, value in created_cashier.items():
            self.assertEqual(getattr(cashier_ins, attr), value)

        del created_cashier['id']

        # 已删除的收银员再次添加, 需更新收银员资料
        cashier_ins.wechat_nickname = 'modified nickname'
        cashier_ins.status = SYSTEM_USER_STATUS['DISABLED']
        cashier_ins.save()

        new_cashier['wechat_nickname'] = 'modified nickname'
        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        created_cashier = response.json()
        new_cashier['id'] = created_cashier['id']
        self.assertEqual(created_cashier, new_cashier)

        # check database
        cashier_ins.refresh_from_db()
        for attr, value in created_cashier.items():
            self.assertEqual(getattr(cashier_ins, attr), value)

        del created_cashier['id']

        # 已添加该收银员
        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.cashier_already_has_been_added)

        # 收银员已绑定其他商铺
        cashier_ins.work_merchant = self.factory.create_merchant()
        cashier_ins.save()
        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.cashier_already_worked_in_another_merchant)

        # 商户管理员无法成为收银员
        cashier_ins.merchant_admin_type = MERCHANT_ADMIN_TYPES['ADMIN']
        cashier_ins.save()

        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, MerchantError.cashier_is_merchant_admin)

        # 其他店的收银员为删除状态时 可成为该店收银员
        deleted_cashier = self.factory.create_merchant_admin(
            merchant_admin_type=MERCHANT_ADMIN_TYPES['CASHIER'],
            status=SYSTEM_USER_STATUS['DISABLED']
        )
        new_cashier = dict(
            wechat_openid=deleted_cashier.wechat_openid,
            wechat_unionid=deleted_cashier.wechat_unionid,
            wechat_avatar_url=deleted_cashier.wechat_avatar_url,
            wechat_nickname=deleted_cashier.wechat_nickname,
        )

        response = self.client.post(url, data=new_cashier, Token=self.token, format='json')
        created_cashier = response.json()
        new_cashier['id'] = created_cashier['id']
        self.assertEqual(created_cashier, new_cashier)

        # check database
        cashier_ins = MerchantAdmin.objects.get(pk=created_cashier['id'])
        for attr, value in created_cashier.items():
            self.assertEqual(getattr(cashier_ins, attr), value)
        self.assertEqual(cashier_ins.work_merchant, self.merchant)
