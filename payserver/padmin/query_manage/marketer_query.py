# -*- coding: utf-8 -*-
#       File: marketer_query.py
#    Project: payunion
#     Author: Tian Xu
#     Create: 18-8-9
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from django.db.models import Prefetch

from common.models import Marketer, Area


class MarketerQeuryManager(object):
    """
    管理后台marketer复杂的数据库查询
    """

    @classmethod
    def marketer_selected(cls):
        query_set = Marketer.objects.select_related('account').prefetch_related(Prefetch(
            'working_areas', queryset=Area.objects.select_related('city', 'parent', 'parent__city')
        ))
        return query_set

    @classmethod
    def area_selected(cls):
        query_set = Area.objects.select_related('city').prefetch_related(Prefetch(
            'parent', queryset=Area.objects.select_related('city', 'parent', 'parent__city')
        ))
        return query_set