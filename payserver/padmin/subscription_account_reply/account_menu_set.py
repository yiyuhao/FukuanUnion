# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


"""
    设置公众号菜单
"""

import json

import requests
import redis

from padmin.subscription_account_reply.const import WEChAT_MINI_PROGRAM
from common.utils import RedisUtil


class MenuSetApi(object):

    def __init__(self, access_token):
        self.CREATE_URL = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token={}".format(access_token)
        self.DELETE_URL = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token={}".format(access_token)
        self.GET_URL = "https://api.weixin.qq.com/cgi-bin/menu/get?access_token={}".format(access_token)

    def create_menu(self, menu_params):
        url = self.CREATE_URL
        resp = requests.post(url, data=menu_params)
        resp_json = resp.json()
        return resp_json

    def delete_menu(self):
        url = self.DELETE_URL
        resp = requests.get(url)
        resp_json = resp.json()
        return resp_json

    def get_menu(self):
        url = self.GET_URL
        resp = requests.get(url)
        resp_json = resp.json()
        return resp_json


class AccountMenuSet(object):
    menu_set_api = MenuSetApi

    def __init__(self, account_type):
        key = "subscription_account_access_token_{}".format(account_type)
        access_token = RedisUtil.get_access_token(key)
        self.menu_setter = self.menu_set_api(access_token)

    def create_menu(self, menu_params):
        menu_params = json.dumps(menu_params, ensure_ascii=False).encode("utf-8").decode('unicode-escape')
        return self.menu_setter.create_menu(menu_params)

    def delete_menu(self):
        return self.menu_setter.delete_menu()

    def get_menu(self):
        return self.menu_setter.get_menu()


# 设置公众号菜单
def set_merchant_menu():
    menu_setter = AccountMenuSet("merchant")
    menu_params = {
        "button": [
            {
                "name": "联盟资讯",
                "sub_button": [
                    {"name": "联盟介绍", "type": "click", "key": "union_introduce"},
                    {"name": "活动推荐", "type": "click", "key": "activity_recommendation"},
                ]
            },
            {
                "name": "商户管家",
                "type": "miniprogram",
                "url": "http://shanghu.com",  # TODO 设置url
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": "/page/index"  # TODO 设置小程序路径

            },
            {
                "name": "专属服务",
                "sub_button": [
                    {
                        "name": "昨日账单",
                        "type": "miniprogram",
                        "url": "http://shanghu.com",  # TODO 设置url
                        "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                        "pagepath": "/page/index?time=yesterday"  # TODO 设置小程序路径
                    },
                    {
                        "name": "月度账单",
                        "type": "miniprogram",
                        "url": "http://shanghu.com",  # TODO 设置url
                        "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                        "pagepath": "/page/index?time=last_month"  # TODO 设置小程序路径
                    },
                    {
                        "name": "联系客服",
                        "type": "click",
                        "key": "contact_service"
                    }
                ]
            }
        ]
    }
    return menu_setter.create_menu(menu_params)


def set_user_menu():
    menu_setter = AccountMenuSet("user")
    menu_params = {
        "button": [
            {
                "name": "免费领券",
                "type": "miniprogram",
                "url": "http://shanghu.com",  # TODO 设置url
                "appid": WEChAT_MINI_PROGRAM['user']['app_id'],
                "pagepath": "pages/lunar/index"  # TODO 设置小程序路径
            },
            {
                "name": "我的优惠券",
                "type": "miniprogram",
                "url": "http://shanghu.com",  # TODO 设置url
                "appid": WEChAT_MINI_PROGRAM['user']['app_id'],
                "pagepath": "pages/lunar/index"  # TODO 设置小程序路径
            },
            {
                "name": "活动推荐",
                "type": "click",
                "key": "activity_recommendation"
            }
        ]
    }
    return menu_setter.create_menu(menu_params)


def set_marketer_menu():
    menu_setter = AccountMenuSet("marketer")
    menu_params = {
        "button": [
            {
                "name": "免费领券",
                "type": "miniprogram",
                "url": "http://shanghu.com",  # TODO 设置url
                "appid": WEChAT_MINI_PROGRAM['marketer']['app_id'],
                "pagepath": "pages/lunar/index"  # TODO 设置小程序路径
            },
        ]
    }
    return menu_setter.create_menu(menu_params)


if __name__ == "__main__":
    # print(set_marketer_menu())
    # print(set_merchant_menu())
    # print(set_user_menu())
    pass