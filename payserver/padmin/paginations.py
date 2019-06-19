# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework.pagination import PageNumberPagination

PAGE_SIZE = 10


class ResultsSetPagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'page_size'