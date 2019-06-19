# -*- coding: utf-8 -*-


def login_user(request, user):
    request._request.session['admin'] = user


def logout_user(request):
    del request._request.session['admin']


