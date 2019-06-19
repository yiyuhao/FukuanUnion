#      File: test_merchant_category.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/13
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

#      File: test_transaction_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/29
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from common.model_manager.merchant_category_manager import MerchantCategoryModelManager
from test.unittest.fake_factory import PayunionFactory


class TestTransactionModelManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.manager = MerchantCategoryModelManager()

    def test_list_categories(self):
        for p in range(4):
            parent = self.factory.create_merchant_category(name='parent{}'.format(p))
            for c in range(4):
                self.factory.create_merchant_category(parent=parent, name='{}_child{}'.format(parent.name, c))

        categories = self.manager.list_categories()

        for category in categories:
            for i, child in enumerate(category['children']):
                self.assertEqual(child['name'], '{}_child{}'.format(category['name'], i))
