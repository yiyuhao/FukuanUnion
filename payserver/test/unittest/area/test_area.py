#      File: test_area.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/18
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.test import TestCase

from common.model_manager.area_manager import AreaModelManager
from test.unittest.fake_factory import PayunionFactory


class TestAreaModelManager(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.manager = AreaModelManager()

    def test_list_areas(self):
        for p in range(4):
            parent = self.factory.create_area(name='市{}'.format(p))
            for c in range(4):
                child = self.factory.create_area(parent=parent, name='{}_区{}'.format(parent.name, c))
                for cc in range(4):
                    self.factory.create_area(parent=child, name='{}_区{}_街道{}'.format(parent.name, c, cc))
        areas = self.manager.list_areas()

        for p, area in enumerate(areas):
            if 'children' in area:
                self.assertEqual(area['name'], '市{}'.format(p))
                for c, child in enumerate(area['children']):
                    self.assertEqual(child['name'], '{}_区{}'.format(area['name'], c))
                    self.assertNotIn('children', child)
                    # 只陈列区级以上区域
                    # for cc, c_child in enumerate(child['children']):
                    #     self.assertEqual(c_child['name'], '{}_区{}_街道{}'.format(area['name'], c, cc))
