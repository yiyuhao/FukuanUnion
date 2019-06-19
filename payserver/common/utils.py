# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import math

import redis

from config import SUBSCRIPT_REDIS_POOL

EARTH_RADIUS = 6371000
METRE_PER_DEGREE = EARTH_RADIUS / 180.0 * math.pi


class RedisUtil(object):
    @classmethod
    def get_redis_conn(cls):
        redis_conn = redis.Redis(connection_pool=SUBSCRIPT_REDIS_POOL)
        return redis_conn

    @classmethod
    def set_access_token(cls, key, value, ex=None):
        cls.get_redis_conn().set(key, value, ex)

    @classmethod
    def get_access_token(cls, key):
        return cls.get_redis_conn().get(key)


def degree_to_metre(degree):
    return degree * METRE_PER_DEGREE


def metre_to_degree(metre):
    return metre / METRE_PER_DEGREE


def distance(lon1, lat1, lon2, lat2):
    lon_deg = abs(lon1 - lon2) / 180.0 * math.pi
    lat_deg = abs(lat1 - lat2) / 180.0 * math.pi
    lon_line_dist = EARTH_RADIUS * math.sin(lon_deg / 2) * 2
    lat_line_dist = EARTH_RADIUS * math.sin(lat_deg / 2) * 2
    line_dist = math.sqrt(lon_line_dist * lon_line_dist + lat_line_dist * lat_line_dist)
    deg = math.asin(line_dist / 2 / EARTH_RADIUS) * 2
    return deg * EARTH_RADIUS
