# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from decimal import Decimal
from datetime import datetime, timedelta


class TimeStampUtil(object):
    @staticmethod
    def format_start_timestamp_microsecond(datetime_string):
        if datetime_string:
            date = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
            return date
        return None

    @staticmethod
    def format_end_timestamp_microsecond(datetime_string):
        if datetime_string:
            date = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
            end_date = date.replace(microsecond=999999)
            return end_date
        return None
    
    @staticmethod
    def get_yesterday(datetime_obj):
        return datetime_obj + timedelta(days=-1)
    

def money_fmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    # digits = map(str, digits)
    digits = [str(d) for d in digits]
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))


def fen_to_yuan_fixed_2(fen):
    """
    
    :param fen: 分， 整型 int or decimal
    :return: str: 两位小数的元
    """
    if fen is None:
        return '0.00'

    return money_fmt(Decimal(fen) / Decimal(100))