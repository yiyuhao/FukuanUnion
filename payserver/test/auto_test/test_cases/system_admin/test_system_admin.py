# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from rest_framework.test import APITestCase

import config
from test.unittest.fake_factory.fake_factory import PayunionFactory
from test.auto_test.steps.system_admin import LoginStep, ChangeInviterToMarketerStep, FinancialQueryStep
from common.password_backend import make_password
from common.models import *


class SystemAdminTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        from test.unittest.system_admin.base_data import create_base_data
        create_base_data()
        cls.fake_factory = PayunionFactory()
        cls.fake_factory.create_system_admin(username='张三',
                                             is_super=True,
                                             password=make_password('abcde'),
                                             status=config.SYSTEM_USER_STATUS.USING)
        cls.inviter = cls.fake_factory.create_marketer(inviter_type=config.MARKETER_TYPES.MARKETER,
                                                       status=config.SYSTEM_USER_STATUS.USING,
                                                       account=cls.fake_factory.create_account())
        
    def test_system_admin(self):
        stepper = LoginStep(self)
        resp = stepper.login("张三", 'abcde')
        print(resp)
        print(resp.json())
        
        stepper = FinancialQueryStep(self)
        resp = stepper.get_overview_data()
        print(resp)
        print(resp.json())

        resp = stepper.get_sharing_details()
        print(resp)
        print(resp.json())

        resp = stepper.get_transaction_details()
        print(resp)
        print(resp.json())

        resp = stepper.get_withdraw_record()
        print(resp)
        print(resp.json())

        stepper = ChangeInviterToMarketerStep(self)

        resp = stepper.inviter_list()
        print(resp)
        print(resp.json())

        new_work_ids = [area.id for area in Area.objects.filter(parent__name='新都区')]
        resp = stepper.change_inviter_to_marketer(self.inviter.id, work_areas_ids=new_work_ids, worker_number='123456')
        print(resp)
        print(resp.json())


