#
#      File: paginators.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework.pagination import PageNumberPagination


class MerchantTransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
