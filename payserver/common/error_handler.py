import inspect

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if not response:
        return response

    if 'error_code' in response.data:
        return response

    for value in response.data.values():
        if isinstance(value, list):
            response.data['error_code'] = getattr(value[0], 'code', None)
            break

    if 'error_code' not in response.data:
        response.data['error_code'] = getattr(exc, 'code', None) \
                                      or getattr(exc, 'default_code', None) \
                                      or getattr(response.data.get('detail'), 'code', None)

    return response


def raise_with_code(exc, code):
    assert isinstance(exc, APIException)

    exc.code = code
    raise exc


class ErrorDict:
    def __new__(cls, error_code, detail):
        return dict(error_code=error_code, detail=detail)


class BaseServerError:
    get_openid_error = ErrorDict(
        'test login code error',
        '微信登录验证, 获取openid失败')

    withdraw_api_error = ErrorDict(
        'withdraw api request error',
        '提现失败')

    withdrawable_balance_not_sufficient = ErrorDict(
        'withdrawable balance is not sufficient',
        '可提现余额不足')

    exceeding_the_wechat_maximum_withdrawal_balance = ErrorDict(
        'exceeding the wechat maximum withdrawal balance',
        '超过微信最大可提现余额')

    xunfei_api_error = ErrorDict(
        'xunfei api return error',
        '讯飞api返回错误')

    @classmethod
    def to_error_msg(cls):
        """
        >>> BaseServerError.to_error_msg()
        >>> {
        >>>    'Coupon rule does not belong to the currently logged in merchant': '指定的优惠券不属于当前商户',
        >>>    'end_date must be greater than(or equal to) start_date when valid_strategy is DATE_RANGE': '结束日期必须大于等于开始日期',
        >>>    'Date format is invalid, format is:2018-01-01': '日期格式不正确',
        >>>    '...' : '...',
        >>> }
        """
        attributes = inspect.getmembers(cls, lambda attr: not (inspect.isroutine(attr)))
        error_msg = {a[1]['error_code']: a[1]['detail']
                     for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))}
        return error_msg


class MerchantError(BaseServerError):
    invalid_date_format = ErrorDict(
        'Date format is invalid, format is:2018-01-01',
        '日期格式不正确')
    invalid_transaction_type = ErrorDict(
        'query params <type> must be all, turnover, originator_earning, or withdraw',
        '参数type不正确, 需为all, turnover, originator_earning, or withdraw')
    end_date_must_greater_than_start_date = ErrorDict(
        'end_date must be greater than(or equal to) start_date when valid_strategy is DATE_RANGE',
        '结束日期必须大于等于开始日期')
    min_charge_range_error = ErrorDict(
        'min charge range error',
        '最低消费金额设置不正确'
    )
    discount_range_error = ErrorDict(
        'discount range error',
        '减免金额设置不正确'
    )
    start_date_must_be_in_1_year = ErrorDict(
        'start date must be in 1 year',
        '开始时间必须在一年内'
    )
    start_date_must_be_in_1_year_from_start_date = ErrorDict(
        'start date must be in 1 year from start date',
        '结束时间必须在开始时间后一年内'
    )
    invalid_expiration_days = ErrorDict(
        'invalid expiration days',
        '过期天数设置不正确'
    )
    min_charge_must_greater_than_discount = ErrorDict(
        'min_charge must be greater than discount when valid_strategy is DATE_RANGE',
        '最低消费必须大于优惠金额')
    must_have_param_start_date_and_end_date = ErrorDict(
        'must have param start_date and end_date when valid_strategy is DATE_RANGE',
        '当valid_strategy为指定日期区间时必须含有参数start_date与end_date')
    must_have_param_expiration_days = ErrorDict(
        'must have param expiration_days when valid_strategy is EXPIRATION',
        '当valid_strategy为指定有效天数时必须含有参数expiration_days')
    unsupported_transaction_type = ErrorDict(
        'invalid transaction type',
        '不支持查看该类型的订单')
    must_upload_both_front_and_back_id_card_url = ErrorDict(
        'must upload both front and back id card url',
        '身份证正反面图片必须同时上传')
    cashier_does_not_exist = ErrorDict(
        'cashier does not exist',
        '不存在该收银员')
    area_not_exist = ErrorDict(
        'adcode does not exist in areas',
        '找不到adcode对应的街道')
    refund_request_error = ErrorDict(
        'refund network error',
        '无法发起退款(未正常拿到支付宝或微信的响应)')
    refund_result_error = ErrorDict(
        'refund result error',
        '退款失败(发起了退款但结果未成功)')
    not_frozen_payment = ErrorDict(
        'payment is not in frozen status',
        '只有冻结期订单才可退款')
    cashier_already_worked_in_another_merchant = ErrorDict(
        'cashier already worked in another merchant',
        '该收银员已绑定其他商铺')
    cashier_already_has_been_added = ErrorDict(
        'cashier already has been added',
        '已添加该收银员')
    cashier_is_merchant_admin = ErrorDict(
        'merchant admin is not allowed to be a cashier',
        '商户管理员无法成为收银员')

    # login error
    no_token = ErrorDict(
        'authentication_failed',
        'can not find Token or HTTP_TOKEN in headers')
    invalid_token = ErrorDict(
        'authentication_failed',
        'invalid token')  # 登录过期
    invalid_user = ErrorDict(
        'authentication_failed',
        'invalid user(may not merchant admin)')
    disabled_user = ErrorDict(
        'authentication_failed',
        'user status is disabled')

    user_is_not_a_merchant_admin = ErrorDict(
        'user is not a merchant admin or cashier',
        '该用户不是商户管理员或收银员')

    # permission
    not_merchant_admin = ErrorDict(
        'permission_denied',
        'only for merchant admin')
    invalid_status = ErrorDict(
        'permission_denied',
        'no permission to access this API while in current merchant status')


class MarketerError(BaseServerError):
    """ 邀请人服务端错误 """
    transfer_api_error = ErrorDict(
        'transfer api request error',
        '转账失败'
    )

    invalid_channel_format = ErrorDict(
        'channel must be wechat or alipay',
        'channel必须为wechat或alipay')

    platform_balance_not_sufficient = ErrorDict(
        'platform balance is not sufficient',
        '平台余额不足')
