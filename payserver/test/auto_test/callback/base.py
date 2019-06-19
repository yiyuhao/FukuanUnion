# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class BaseCallback(object):
    def __init__(self, validate=None):
        self.validate = validate


def call_validate(fun):
    def wrap(self, request=None, context=None):
        if self.validate:
            assert self.validate(request)
        return fun(self, request, context)

    return wrap
