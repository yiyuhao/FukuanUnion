# -*- coding: utf-8 -*-
#       File: redis_utils.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-8-16
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import logging
import time

from dynaconf import settings as dynasettings
from redis import ConnectionPool, StrictRedis

REDIS_URL = 'redis://{0}{1}:{2}/{3}'.format(
    ':%s@' % dynasettings.REDIS_PASSWORD if dynasettings.REDIS_PASSWORD else '',  # noqa
    dynasettings.REDIS_HOST,
    dynasettings.as_int('REDIS_PORT'),
    4
)

redis_pool = ConnectionPool.from_url(REDIS_URL)
logger = logging.getLogger(__file__)


class ValueNotExistsError(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg


class RedisUtil(object):
    """ 缓存数据"""
    redis_cli = StrictRedis(connection_pool=redis_pool)

    @classmethod
    def cache_data(cls, key, value, data_type='wechat_info'):
        """ 缓存网页授权部分数据 """
        res = cls.redis_cli.hset(f'{data_type}[unionid]', key=key, value=value)
        if res in (0, 1):
            return True

    @classmethod
    def load_data(cls, key, data_type='wechat_info'):
        """ 获取缓存的网页授权部分数据 """
        openid = cls.redis_cli.hget(f'{data_type}[unionid]', key=key)
        if not openid:
            logger.info(f'redis缓存{data_type}中不存在该unionid: {key}')
            raise ValueNotExistsError("该unionid在redis中对应的{data_type}不存在")
        return openid.decode('utf8')

    @classmethod
    def cache_request_time(cls, unionid, time):
        """ 缓存单个unionid访问的时间 返回插入后的长度 """
        return cls.redis_cli.rpush(unionid, time)

    @classmethod
    def get_request_time_len(cls, unionid):
        """ 当前unionid访问的时间列表的长度 """
        return cls.redis_cli.llen(unionid)

    @classmethod
    def get_oldest_item(cls, unionid, pop_item=False):
        """ 获取[删除]左边的第一个元素 """
        if pop_item:
            return cls.redis_cli.lpop(unionid).decode('utf8')
        return cls.redis_cli.lindex(unionid, 0).decode('utf8')

    @classmethod
    def record_request_one_day(cls, key, num_incr=False):
        """ 每天请求的次数 num_incr为True，自增1 """
        name = f'request_record_{key}'
        current_num = cls.redis_cli.get(name)  # 不存在返回None
        if current_num is None:
            cls.redis_cli.set(name, '1', ex=24 * 60 * 60 + 1)  # 防止在incr之前过期
            current_num = b'1'
        if num_incr:
            return cls.redis_cli.incr(name)
        return int(current_num.decode('utf8'))


def unionid_add_prefix_deco(func):
    def wrapper(cls, unionid, *args, **kwargs):
        unionid = f'verify_account_{unionid}'
        return func(cls, unionid, *args, **kwargs)

    return wrapper


class VerifyAccountLimitRecord(RedisUtil):
    @classmethod
    @unionid_add_prefix_deco
    def cache_request_time(cls, unionid, time):
        return super().cache_request_time(unionid, time)

    @classmethod
    @unionid_add_prefix_deco
    def get_request_time_len(cls, unionid):
        return super().get_request_time_len(unionid)

    @classmethod
    @unionid_add_prefix_deco
    def delete_record(cls, unionid):
        return cls.redis_cli.delete(unionid)

    @classmethod
    @unionid_add_prefix_deco
    def record_request_an_hour(cls, unionid):
        ex = int(3600 - (time.time() % 3600))
        if cls.redis_cli.set(unionid, '0', nx=True, ex=ex):
            return 0
        return cls.redis_cli.incr(unionid)

    @classmethod
    @unionid_add_prefix_deco
    def decr_record_request(cls, unionid):
        record_num = cls.redis_cli.decr(unionid) or 0
        if record_num < 0:
            cls.redis_cli.incr(unionid)
