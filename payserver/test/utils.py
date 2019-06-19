#      File: utils.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/25
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from datetime import datetime

from common.model_manager.utils import get_amount


def render(field_data):
    """
    :param field_data: django field data
    :return: rendered data
    >>> render(datetime(2018, 1, 1, 0, 0, 0))
    >>> '2018-01-01 00:00'
    >>> render(30010)
    >>> 300.1
    """
    if isinstance(field_data, datetime):
        return field_data.strftime('%Y-%m-%d %H:%M')
    elif isinstance(field_data, int):
        return get_amount(field_data)
    else:
        return field_data


class NonFieldError:
    def __new__(cls, error_dict):
        return {'non_field_errors': [error_dict['detail']], 'error_code': error_dict['error_code']}
