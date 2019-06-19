# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import viewsets, mixins, response

from padmin.auth import DefaultAuthMixin
from common.models import MerchantCategory


class MerchantCategoryView(DefaultAuthMixin, viewsets.GenericViewSet):
    queryset = MerchantCategory.objects.filter(parent__isnull=True)
    pagination_class = None

    def list(self, request, *args, **kwargs):
        result_list = []

        for parent in self.queryset:
            item = {'id': parent.id, 'name': parent.name}
            child_queryset = MerchantCategory.objects.filter(parent=parent.id)
            if len(child_queryset) != 0:
                child_list = []
                for child in child_queryset:
                    children = {'id': child.id, 'name': child.name}
                    child_list.append(children)
                item['children'] = child_list
            result_list.append(item)
        return response.Response(result_list)


merchant_category_list = MerchantCategoryView.as_view({
    'get': 'list',
})

