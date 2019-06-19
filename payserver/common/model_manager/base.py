#      File: base.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class ModelObjectManagerBase:
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, item):
        return getattr(self.obj, item)


class ModelManagerBase:
    def __init__(self, model=None):
        # the concrete implementation class can set model
        self.model = model
