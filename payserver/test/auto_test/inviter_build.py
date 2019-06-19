# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from .inviter import Inviter


class InviterBuilder(object):
    
    @classmethod
    def build(cls, info=None):
        inveter = Inviter()
        inveter.entry_mini_program()
        inveter.click_button_to_register_become_inviter()
        inveter.set_info(info)
        inveter.send_message()
        inveter.register()
        
        return inveter
