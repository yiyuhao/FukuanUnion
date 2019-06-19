#      File: exceptions.py
#   Project: payunion
#    Author: Xie Wangyi
#    Create: 2018/7/2
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


class ApiCallException(Exception):
    pass


class ApiRequestError(ApiCallException):
    """不能正常拿到Response时抛出"""

    def __init__(self, request_exce, *args, **kwargs):
        super().__init__(args, kwargs)
        self.request_exce = request_exce

    def __str__(self):
        return "ApiRequestError:\r\n" + (str(self.request_exce) if self.request_exce else '')

    def __repr__(self):
        return f"ApiRequestError({repr(self.request_exce)})"


class ApiReturnedError(ApiCallException):
    """能正常拿到Response, 但是状态码不是成功的时候抛出"""

    def __init__(self, return_code, resp, *args, **kwargs):
        super().__init__(args, kwargs)
        self.return_code = return_code
        self.resp = resp

    def __str__(self):
        return f"ApiReturnedError: \r\n" \
               f"return_code:{str(self.return_code)} \r\n" \
               f"resp:{str(self.resp)}"

    def __repr__(self):
        return f'ApiReturnedError({repr(self.return_code)},{repr(self.resp)})'


class SignError(Exception):
    pass


class ApiStatusCodeError(ApiCallException):
    """ 请求状态码错误 """

    def __init__(self, status_code, *args, **kwargs):
        super().__init__(args, kwargs)
        self.status_code = status_code

    def __str__(self):
        return f"ApiStatusCodeError: \r\n" \
               f"status_code:{str(self.status_code)} \r\n"

    def __repr__(self):
        return f'ApiReturnedError({repr(self.status_code)})'
