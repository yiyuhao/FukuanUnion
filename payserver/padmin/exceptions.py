# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class SettlementDuplicateException(Exception):
    """ 结算重复异常"""
    pass


class SettlementAbnormalBalanceException(Exception):
    """ 结算时余额异常"""
    pass

    

