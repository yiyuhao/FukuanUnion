# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from unittest import TestCase

from common.utils import degree_to_metre, metre_to_degree, distance


class UtilsTestCase(TestCase):
    def test_degree_to_metre(self):
        metre = degree_to_metre(1)
        assert round(metre * 10) == 1111949

    def test_metre_to_degree(self):
        deg = metre_to_degree(111194.9)
        assert round(deg * 1000000) == 1000000

    def test_distance(self):
        dist = distance(100, 200, 101, 200)
        assert round(dist * 10) == 1111949

    def test_distance1(self):
        dist = distance(100, 200, 100, 201)
        assert round(dist * 10) == 1111949

    def test_distance2(self):
        dist = distance(100, 200, 101, 201)
        assert round(dist * 10) == 1572554
