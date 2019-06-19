#      File: permissions.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/18
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from functools import wraps

from rest_framework.permissions import BasePermission

from config import MERCHANT_ADMIN_TYPES, MERCHANT_STATUS, SYSTEM_USER_STATUS
from common.error_handler import MerchantError


class NotDisabled(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.status == SYSTEM_USER_STATUS['DISABLED']:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


def is_merchant_admin(func):
    def permission_denied(view_set, request, *args, **kwargs):
        view_set.permission_denied(request, message=MerchantError.not_merchant_admin['detail'])

    @wraps(func)
    def wrapper(view_set, request, *args, **kwargs):
        # check is admin
        if request.user.merchant_admin_type == MERCHANT_ADMIN_TYPES['ADMIN']:
            return func(view_set, request, *args, **kwargs)
        # reject cashier
        else:
            return permission_denied(view_set, request, *args, **kwargs)

    return wrapper


def merchant_is_using(func):
    """审核已通过"""

    def permission_denied(view_set, request, *args, **kwargs):
        view_set.permission_denied(request, message=MerchantError.invalid_status['detail'])

    @wraps(func)
    def wrapper(view_set, request, *args, **kwargs):
        # check is admin
        if request.user.work_merchant.status == MERCHANT_STATUS['USING']:
            return func(view_set, request, *args, **kwargs)
        # reject cashier
        else:
            return permission_denied(view_set, request, *args, **kwargs)

    return wrapper


def merchant_is_rejected(func):
    """审核已拒绝(才可修改商户信息)"""

    def permission_denied(view_set, request, *args, **kwargs):
        view_set.permission_denied(request, message=MerchantError.invalid_status['detail'])

    @wraps(func)
    def wrapper(view_set, request, *args, **kwargs):
        # check is admin
        if request.user.work_merchant.status == MERCHANT_STATUS['REJECTED']:
            return func(view_set, request, *args, **kwargs)
        # reject cashier
        else:
            return permission_denied(view_set, request, *args, **kwargs)

    return wrapper


def merchant_is_using_or_rejected(func):
    """审核已通过或审核拒绝需重新修改商铺信息"""

    def permission_denied(view_set, request, *args, **kwargs):
        view_set.permission_denied(request, message=MerchantError.invalid_status['detail'])

    @wraps(func)
    def wrapper(view_set, request, *args, **kwargs):
        # check is admin
        if request.user.work_merchant.status in (MERCHANT_STATUS['USING'], MERCHANT_STATUS['REJECTED']):
            return func(view_set, request, *args, **kwargs)
        # reject cashier
        else:
            return permission_denied(view_set, request, *args, **kwargs)

    return wrapper
