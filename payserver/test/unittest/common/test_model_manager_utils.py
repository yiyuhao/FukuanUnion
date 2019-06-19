#      File: test_model_manager_utils.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/8/1
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from unittest import TestCase

from common.model_manager.utils import set_amount, get_amount


class TestModelManagerTestManager(TestCase):

    def test_get_amount(self):
        self.assertEqual(get_amount(0), 0)
        self.assertEqual(get_amount(1), 0.01)
        self.assertEqual(get_amount(30000), 300)
        self.assertEqual(get_amount(30030), 300.3)
        self.assertEqual(get_amount(30033), 300.33)

        self.assertEqual(get_amount('0'), 0)
        self.assertEqual(get_amount('1'), 0.01)
        self.assertEqual(get_amount('30000'), 300)
        self.assertEqual(get_amount('30030'), 300.3)
        self.assertEqual(get_amount('30033'), 300.33)

        self.assertEqual(get_amount('0.00'), 0)
        self.assertEqual(get_amount('1.0'), 0.01)
        self.assertEqual(get_amount('30000.00'), 300)
        self.assertEqual(get_amount('30030.00'), 300.3)
        self.assertEqual(get_amount('30033.00'), 300.33)

    def test_set_amount(self):
        self.assertEqual(set_amount(0), 0)
        self.assertEqual(set_amount(0.01), 1)
        self.assertEqual(set_amount(300), 30000)
        self.assertEqual(set_amount(300.3), 30030)
        self.assertEqual(set_amount(300.33), 30033)

        self.assertEqual(set_amount('0'), 0)
        self.assertEqual(set_amount('0.01'), 1)
        self.assertEqual(set_amount('300'), 30000)
        self.assertEqual(set_amount('300.00'), 30000)
        self.assertEqual(set_amount('300.3'), 30030)
        self.assertEqual(set_amount('300.30'), 30030)
        self.assertEqual(set_amount('300.33'), 30033)
