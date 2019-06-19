#      File: test_fake_factory.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/21
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from .fake_factory import PayunionFactory


class TestFakeFactory(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestFakeFactory, self).__init__(*args, **kwargs)
        self.factory = PayunionFactory()
        self.create_number = 20

    def test_create_login_status(self):
        self.factory.create_login_status(self.create_number)

    def test_create_system_admin(self):
        self.factory.create_system_admin(self.create_number)

    def test_create_merchant_admin(self):
        self.factory.create_merchant_admin(self.create_number)

    def test_create_marketer(self):
        self.factory.create_marketer(self.create_number)

    def test_create_client(self):
        self.factory.create_client(self.create_number)

    def test_create_city(self):
        self.factory.create_city(self.create_number)

    def test_create_area(self):
        self.factory.create_area(self.create_number)

    def test_create_merchant_category(self):
        self.factory.create_merchant_category(self.create_number)

    def test_create_payment_qrcode(self):
        self.factory.create_payment_qrcode(self.create_number)

    def test_create_merchant(self):
        self.factory.create_merchant(self.create_number)

    def test_create_coupon_rule(self):
        self.factory.create_coupon_rule(self.create_number)

    def test_create_coupon(self):
        self.factory.create_coupon(self.create_number)

    def test_create_account(self):
        self.factory.create_account(self.create_number)

    def test_create_payment(self):
        self.factory.create_payment(self.create_number)

    def test_create_withdraw(self):
        self.factory.create_withdraw(self.create_number)

    def test_create_settlement(self):
        self.factory.create_settlement(self.create_number)

    def test_create_transaction(self):
        self.factory.create_transaction(self.create_number)
