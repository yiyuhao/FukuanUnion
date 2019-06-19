# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import config
from common.password_backend import make_password
from test.auto_test.test_cases.merchant.merchant_clinet_test_base import MerchantClientTestBase
from test.unittest.fake_factory import PayunionFactory
from test.auto_test.steps.common_object import WechatPerson, fake
from test.auto_test.steps.merchant import CashierManagerStep, MerchantStep
from test.auto_test.steps.system_admin import MerchantManageStep, LoginStep


class TestInfoManage(MerchantClientTestBase):
    """ 商户端-信息管理测试"""
    
    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        
        # 5个微信号和两个商铺
        cls.wechat_person_A = WechatPerson()
        cls.wechat_person_B = WechatPerson()
        cls.wechat_person_C = WechatPerson()
        cls.wechat_person_D = WechatPerson()
        cls.wechat_person_E = WechatPerson()
        
        # 创建商户a 并设管理员为A
        cls.merchatn_a = cls.factory.create_merchant(status=config.MERCHANT_STATUS['USING'])
        cls.factory.create_merchant_admin(
            wechat_openid=cls.wechat_person_A.subscription_openid,
            wechat_unionid=cls.wechat_person_A.unionid,
            wechat_avatar_url=cls.wechat_person_A.user_info['headimgurl'],
            wechat_nickname=cls.wechat_person_A.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchatn_a
        )

        # 创建商户b 并设管理员为D, 收银员为E
        cls.merchatn_b = cls.factory.create_merchant(status=config.MERCHANT_STATUS['USING'])
        cls.factory.create_merchant_admin(
            wechat_openid=cls.wechat_person_D.subscription_openid,
            wechat_unionid=cls.wechat_person_D.unionid,
            wechat_avatar_url=cls.wechat_person_D.user_info['headimgurl'],
            wechat_nickname=cls.wechat_person_D.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchatn_b
        )
        cls.factory.create_merchant_admin(
            wechat_openid=cls.wechat_person_E.subscription_openid,
            wechat_unionid=cls.wechat_person_E.unionid,
            wechat_avatar_url=cls.wechat_person_E.user_info['headimgurl'],
            wechat_nickname=cls.wechat_person_E.user_info['nickname'],
            merchant_admin_type=config.MERCHANT_ADMIN_TYPES['CASHIER'],
            status=config.SYSTEM_USER_STATUS['USING'],
            work_merchant=cls.merchatn_b
        )
    
    def test_add_cashier(self):
        """ 添加收银员 """

        # a商户管理员A登陆成功
        wechat_person_A_token = self.mock_merchant_admin_or_cashier_login_success(self.wechat_person_A)

        cashier_manager_step = CashierManagerStep(self)
        # 管理员A添加收银员，B扫码 --> 添加B为收银员成功
        resp_data = cashier_manager_step.add_cashier(wechat_person_A_token, self.wechat_person_B.user_info)
        cashier_scan_code_resp = resp_data['cashier_scan_code_resp']
        socket_message_info = resp_data['socket_message_info']
        merchant_add_cashier_resp = resp_data['merchant_add_cashier_resp']
        resp_context = cashier_scan_code_resp.content.decode('utf-8')
        self.assertIn("已接受邀请!", resp_context)
        self.assertIn("你已成为该店铺的收银员:", resp_context)
        socket_message_info.pop('channel_key')
        self.assertEqual(socket_message_info, self.wechat_person_B.user_info)
        merchant_add_cashier_resp_json = merchant_add_cashier_resp.json()
        self.assertEqual(merchant_add_cashier_resp_json['wechat_openid'], self.wechat_person_B.user_info['openid'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_unionid'], self.wechat_person_B.user_info['unionid'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_avatar_url'],
                         self.wechat_person_B.user_info['headimgurl'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_nickname'], self.wechat_person_B.user_info['nickname'])

        # 管理员A添加收银员，C扫码 --> 添加C为收银员成功
        resp_data = cashier_manager_step.add_cashier(wechat_person_A_token, self.wechat_person_C.user_info)
        cashier_scan_code_resp = resp_data['cashier_scan_code_resp']
        socket_message_info = resp_data['socket_message_info']
        merchant_add_cashier_resp = resp_data['merchant_add_cashier_resp']
        resp_context = cashier_scan_code_resp.content.decode('utf-8')
        self.assertIn("已接受邀请!", resp_context)
        self.assertIn("你已成为该店铺的收银员:", resp_context)
        socket_message_info.pop('channel_key')
        self.assertEqual(socket_message_info, self.wechat_person_C.user_info)
        merchant_add_cashier_resp_json = merchant_add_cashier_resp.json()
        self.assertEqual(merchant_add_cashier_resp_json['wechat_openid'], self.wechat_person_C.user_info['openid'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_unionid'], self.wechat_person_C.user_info['unionid'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_avatar_url'],
                         self.wechat_person_C.user_info['headimgurl'])
        self.assertEqual(merchant_add_cashier_resp_json['wechat_nickname'], self.wechat_person_C.user_info['nickname'])

        # 获取收银员列表
        resp = cashier_manager_step.get_all_cashiers(wechat_person_A_token)
        resp_json = resp.json()
        self.assertEqual(len(resp_json), 2)  # 两个收银员
        self.assertEqual(resp_json[0]['wechat_openid'], self.wechat_person_B.user_info['openid'])
        self.assertEqual(resp_json[0]['wechat_unionid'], self.wechat_person_B.user_info['unionid'])
        self.assertEqual(resp_json[1]['wechat_openid'], self.wechat_person_C.user_info['openid'])
        self.assertEqual(resp_json[1]['wechat_unionid'], self.wechat_person_C.user_info['unionid'])

        # 管理员A添加收银员，D扫码 --> A收到绑定失败，D收到绑定失败
        resp_data = cashier_manager_step.add_cashier(wechat_person_A_token, self.wechat_person_D.user_info)
        cashier_scan_code_resp = resp_data['cashier_scan_code_resp']
        socket_message_info = resp_data['socket_message_info']
        merchant_add_cashier_resp = resp_data['merchant_add_cashier_resp']
        resp_context = cashier_scan_code_resp.content.decode('utf-8')
        self.assertIn("授权失败", resp_context)
        self.assertIn("商户管理员无法成为收银员", resp_context)
        socket_message_info.pop('channel_key')
        self.assertEqual(socket_message_info, self.wechat_person_D.user_info)
        self.assertEqual(merchant_add_cashier_resp.json(),
                         {'error_code': 'merchant admin is not allowed to be a cashier',
                          'detail': '商户管理员无法成为收银员'}
                         )

        # 管理员A添加收银员，E扫码 --> A收到绑定失败，E收到绑定失败
        resp_data = cashier_manager_step.add_cashier(wechat_person_A_token, self.wechat_person_E.user_info)
        cashier_scan_code_resp = resp_data['cashier_scan_code_resp']
        socket_message_info = resp_data['socket_message_info']
        merchant_add_cashier_resp = resp_data['merchant_add_cashier_resp']
        resp_context = cashier_scan_code_resp.content.decode('utf-8')
        self.assertIn("授权失败", resp_context)
        self.assertIn("已添加该收银员或该收银员已绑定其他商铺", resp_context)
        socket_message_info.pop('channel_key')
        self.assertEqual(socket_message_info, self.wechat_person_E.user_info)
        self.assertEqual(merchant_add_cashier_resp.json(),
                         {'error_code': 'cashier already worked in another merchant',
                          'detail': '该收银员已绑定其他商铺'}
                         )

    def test_delete_cashier(self):
        """ 删除收银员 """
        # b商户管理员D登陆
        wechat_person_D_token = self.mock_merchant_admin_or_cashier_login_success(self.wechat_person_D)

        cashier_manager_step = CashierManagerStep(self)
        # 获取收银员列表
        resp = cashier_manager_step.get_all_cashiers(wechat_person_D_token)
        resp_json = resp.json()
        self.assertEqual(len(resp_json), 1)
        self.assertEqual(resp_json[0]['wechat_openid'], self.wechat_person_E.user_info['openid'])
        self.assertEqual(resp_json[0]['wechat_unionid'], self.wechat_person_E.user_info['unionid'])
        cashier_e_id = resp_json[0]['id']
        #  b商户管理员D删除收银员E
        resp = cashier_manager_step.remove_cashier(wechat_person_D_token, cashier_e_id)
        self.assertEqual(resp.json(), {})
        resp = cashier_manager_step.get_all_cashiers(wechat_person_D_token)
        self.assertEqual(resp.json(), [])

    def test_modify_do_business_time(self):
        """ 修改营业时间 """
        wechat_person_D_token = self.mock_merchant_admin_or_cashier_login_success(self.wechat_person_D)
        wechat_person_D_merchant_step = MerchantStep(self, wechat_person_D_token)

        self.assertEqual(self.merchatn_b.day_begin_minute, 0)
        resp = wechat_person_D_merchant_step.day_begin_minute(12 * 60)
        self.merchatn_b.refresh_from_db()
        self.assertEqual(self.merchatn_b.day_begin_minute, 12 * 60)

        wechat_person_E_token = self.mock_merchant_admin_or_cashier_login_success(self.wechat_person_E, is_chashier=True)
        wechat_person_D_merchant_step = MerchantStep(self, wechat_person_E_token)

        # TODO 收银员和商户管理员查看首页数据一致, 接口变动
        raise Exception("TODO 收银员和商户管理员查看首页数据一致, 接口变动")
    
    def test_look_through_merchant_info(self):
        """ 查看商户信息 """
        # 微信小程序获取商户信息
        wechat_person_D_token = self.mock_merchant_admin_or_cashier_login_success(self.wechat_person_D)
        wechat_person_D_merchant_step = MerchantStep(self, wechat_person_D_token)
        resp = wechat_person_D_merchant_step.me()
        mini_program_merchant_info = resp.json()
        # 后台管理员获取商户信息
        sysadmin_name = fake.name()
        sysadmin_password = fake.md5()
        self.factory.create_system_admin(username=sysadmin_name,
                                         is_super=True,
                                         password=make_password(sysadmin_password),
                                         status=config.SYSTEM_USER_STATUS.USING)
        sysadmin = LoginStep(self)
        sysadmin.login(username=sysadmin_name, password=sysadmin_password)
        sysadmin_merchant_manage_step = MerchantManageStep(self)
        resp = sysadmin_merchant_manage_step.get_merchant_info(self.merchatn_b.id)
        sysadmin_merchant_info = resp.json()
        self.assertEqual(mini_program_merchant_info['id'], sysadmin_merchant_info['id'])
        self.assertEqual(mini_program_merchant_info['status'], sysadmin_merchant_info['status'])
        self.assertEqual(mini_program_merchant_info['name'], sysadmin_merchant_info['name'])
        self.assertEqual(mini_program_merchant_info['area'], str(sysadmin_merchant_info['area']['id']))
        self.assertEqual(mini_program_merchant_info['category'], sysadmin_merchant_info['category']['id'])
        self.assertEqual(mini_program_merchant_info['photo_url'], sysadmin_merchant_info['photo_url'])
        self.assertEqual(mini_program_merchant_info['description'], sysadmin_merchant_info['description'])
        self.assertEqual(mini_program_merchant_info['contact_phone'], sysadmin_merchant_info['contact_phone'])
        self.assertEqual(mini_program_merchant_info['avatar_url'], sysadmin_merchant_info['avatar_url'])
        self.assertEqual(mini_program_merchant_info['location_lon'], sysadmin_merchant_info['location_lon'])
        self.assertEqual(mini_program_merchant_info['location_lat'], sysadmin_merchant_info['location_lat'])
        self.assertEqual(mini_program_merchant_info['address'], sysadmin_merchant_info['address'])
        self.assertEqual(mini_program_merchant_info['id_card_front_url'], sysadmin_merchant_info['id_card_front_url'])
        self.assertEqual(mini_program_merchant_info['id_card_back_url'], sysadmin_merchant_info['id_card_back_url'])
        self.assertEqual(mini_program_merchant_info['license_url'], sysadmin_merchant_info['license_url'])
        self.assertEqual(mini_program_merchant_info['photo_url'], sysadmin_merchant_info['photo_url'])

