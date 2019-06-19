# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import uuid
import random
from faker import Faker

fake = Faker('zh_CN')


class WechatPerson(object):
    def __init__(self, *args, **kwargs):
        self.unionid = kwargs.get('unionid', None) or str(uuid.uuid4().hex)
        self.mini_openid = kwargs.get('mini_openid', None) or str(uuid.uuid4().hex)
        self.mini_session_key = kwargs.get('mini_session_key', None) or str(uuid.uuid4().hex)
        self.subscription_openid = kwargs.get('subscription_openid', None) or str(uuid.uuid4().hex)
        
        self.user_info = dict(
            openid=self.subscription_openid,
            nickname=kwargs.get('nickname', None) or fake.name(),
            sex=kwargs.get('sex', None) or random.choice('12'),
            province=kwargs.get('province', None) or fake.province(),
            city=kwargs.get('city', None) or fake.city_suffix(),
            country=kwargs.get('country', None) or fake.country(),
            headimgurl=kwargs.get('headimgurl', None) or fake.image_url(),
            privilege=kwargs.get('privilege', None) or ["PRIVILEGE1", "PRIVILEGE2"],
            unionid=self.unionid,
        )
        
        
class AliPayPerson(object):
    def __init__(self, *args, **kwargs):
        self.user_info = dict(
            user_id=kwargs.get('user_id', None) or str(uuid.uuid4().hex),
            avatar=kwargs.get('avatar', None) or fake.image_url(),
            province=kwargs.get('province', None) or fake.province(),
            city=kwargs.get('city', None) or fake.city_suffix(),
            nick_name=kwargs.get('nickname', None) or fake.name(),
            is_student_certified=kwargs.get('is_student_certified', None) or random.choice('TF'),
            user_type=kwargs.get('user_type', None) or random.choice('12'),
            user_status=kwargs.get('user_status', None) or random.choice('QTBW'),
            is_certified=kwargs.get('is_certified', None) or random.choice('TF'),
            gender=kwargs.get('user_type', None) or random.choice('FM'),
        )
