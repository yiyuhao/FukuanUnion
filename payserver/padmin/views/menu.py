# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import views
from rest_framework.response import Response

from padmin.auth import DefaultAuthMixin
from config import NOT_SUPER_MENU, SUPER_EXTRA_MENU


class MenuView(DefaultAuthMixin, views.APIView):
    def get(self, request):
        menu_list = NOT_SUPER_MENU
        if request._request.session['admin'].is_super:
            menu_list = NOT_SUPER_MENU + SUPER_EXTRA_MENU
        return Response(menu_list)




