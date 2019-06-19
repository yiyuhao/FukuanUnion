# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from decimal import Decimal

from padmin.query_manage.query_until import TimeStampUtil, money_fmt, fen_to_yuan_fixed_2

from django.test import TestCase


class TestQueryUtil(TestCase):
    
    def test_timestamp_util(self):
        timestamp_string = "2018-11-05 09:47:01"
        start_date = TimeStampUtil.format_start_timestamp_microsecond(timestamp_string)
        end_date = TimeStampUtil.format_end_timestamp_microsecond(timestamp_string)
        
        self.assertEqual(start_date.strftime('%Y-%m-%d %H:%M:%S.%f'), '2018-11-05 09:47:01.000000')
        self.assertEqual(end_date.strftime('%Y-%m-%d %H:%M:%S.%f'), '2018-11-05 09:47:01.999999')
    
    def test_money_fmt(self):
        d = Decimal('-1234567.8901')
        self.assertEqual(money_fmt(d, curr='$'), '-$1,234,567.89')
        self.assertEqual(money_fmt(d, places=0, sep='.', dp='', neg='', trailneg='-'), '1.234.568-')
        self.assertEqual(money_fmt(d, curr='$', neg='(', trailneg=')'), '($1,234,567.89)')
        self.assertEqual(money_fmt(Decimal(123456789), sep=' '), '123 456 789.00')
        self.assertEqual(money_fmt(Decimal('-0.02'), neg='<', trailneg='>'), '<0.02>')

    def test_fen_to_yuan_fixed_2(self):
        self.assertEqual(fen_to_yuan_fixed_2(None), "0.00")
        self.assertEqual(fen_to_yuan_fixed_2(0), "0.00")
        self.assertEqual(fen_to_yuan_fixed_2(1), "0.01")
        self.assertEqual(fen_to_yuan_fixed_2(3), "0.03")
        self.assertEqual(fen_to_yuan_fixed_2(399), "3.99")
        self.assertEqual(fen_to_yuan_fixed_2(100000), "1,000.00")
        self.assertEqual(fen_to_yuan_fixed_2(5900), "59.00")
