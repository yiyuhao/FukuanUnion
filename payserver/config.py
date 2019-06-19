# -*- coding: utf-8 -*-
from collections import UserDict

import redis
from dynaconf import settings as dynasettings


class Config(UserDict):
    def __init__(self, config_dict):
        self.reverse_dict = {item['code']: key for key, item in config_dict.items()}
        super().__init__(config_dict)

    def __getitem__(self, key):
        if super().__contains__(key):
            return super().__getitem__(key)
        if key in self.reverse_dict:
            return self.reverse_dict[key]
        raise KeyError(key)

    def __iter__(self):
        return super().__iter__()

    def __contains__(self, key):
        return super().__contains__(key) or key in self.reverse_dict

    def __len__(self):
        return super().__len__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.reverse_dict[value['code']] = key

    def __delitem__(self, key):
        item = super()[key]
        super().__delitem__(key)
        del self.reverse_dict[item['code']]

    def __getattr__(self, key):
        return self.__getitem__(key)

    def model_choices(self):
        return [(key, item['code']) for key, item in self.items()]

    def number_name_dict(self):
        return {key: item['name'] for key, item in self.items()}


MARKETER_TYPES = Config({
    0: {'code': 'MARKETER', 'name': '邀请人'},
    1: {'code': 'SALESMAN', 'name': '业务员'},
})

MERCHANT_ADMIN_TYPES = Config({
    0: {'code': 'ADMIN', 'name': '商户管理员'},
    1: {'code': 'CASHIER', 'name': '收银员'},
})

SYSTEM_USER_STATUS = Config({
    0: {'code': 'USING', 'name': '正常'},
    1: {'code': 'DISABLED', 'name': '已禁用'},
})

ADMIN_PERMISSIONS = {
    'PLATFORM_ADMIN': '平台管理员',
    'AREA_ADMIN': '区域管理员',
}

MERCHANT_TYPE = Config({
    0: {'code': 'INDIVIDUAL', 'name': '个人商户'},
    1: {'code': 'ENTERPRISE', 'name': '企业商户'},
})

MERCHANT_STATUS = Config({
    0: {'code': 'REVIEWING', 'name': '审核中'},
    1: {'code': 'USING', 'name': '已通过'},
    2: {'code': 'REJECTED', 'name': '审核拒绝'},
    3: {'code': 'DISABLED', 'name': '已禁用'},
})

VALID_STRATEGY = Config({
    0: {'code': 'DATE_RANGE', 'name': '指定日期区间'},
    1: {'code': 'EXPIRATION', 'name': '指定有效天数'},
})

COUPON_STATUS = Config({
    0: {'code': 'NOT_USED', 'name': '未使用'},
    1: {'code': 'USED', 'name': '已使用'},
    2: {'code': 'DESTROYED', 'name': '已销毁'},
})

PAYMENT_STATUS = Config({
    0: {'code': 'UNPAID', 'name': '未支付'},
    1: {'code': 'FROZEN', 'name': '冻结期'},
    2: {'code': 'REFUND_REQUESTED', 'name': '退款处理中'},
    3: {'code': 'REFUND', 'name': '退款成功'},
    4: {'code': 'REFUND_FAILED', 'name': '退款失败'},
    5: {'code': 'FINISHED', 'name': '已完成'},
    6: {'code': 'CANCELLED', 'name': '已取消'},
})

WITHDRAW_STATUS = Config({
    0: {'code': 'PROCESSING', 'name': '处理中'},
    1: {'code': 'FAILED', 'name': '已失败'},
    2: {'code': 'FINISHED', 'name': '已完成'},
})

WITHDRAW_TYPE = Config({
    0: {'code': 'WECHAT', 'name': '微信'},
    1: {'code': 'ALIPAY', 'name': '支付宝'},
})

SETTLEMENT_STATUS = Config({
    0: {'code': 'PROCESSING', 'name': '结算中'},
    1: {'code': 'FINISHED', 'name': '已结算'},
})

VERIFY_ACCOUNT_STATUS = Config({
    0: {'code': 'VERIFYING', 'name': '验证中'},
    1: {'code': 'SUCCESS', 'name': '成功'},
    2: {'code': 'FAIL', 'name': '失败'}
})

TRANSFER_STATUS = Config({
    0: {'code': 'PROCESSING', 'name': '处理中'},
    1: {'code': 'FAILED', 'name': '已失败'},
    2: {'code': 'FINISHED', 'name': '已完成'},
})

REFUND_STATUS = Config({
    0: {'code': 'REQUESTED', 'name': '已申请'},
    1: {'code': 'FAILED', 'name': '已失败'},
    2: {'code': 'FINISHED', 'name': '已完成'},
})

PAY_CHANNELS = Config({
    0: {'code': 'WECHAT', 'name': '微信'},
    1: {'code': 'ALIPAY', 'name': '支付宝'},
})

TRANSACTION_TYPE = Config({
    0: {'code': 'PLATFORM_RECEIVE', 'name': '平台收款'},
    1: {'code': 'PLATFORM_EXPEND_MERCHANT_RECEIVE', 'name': '平台支出商户收款'},
    2: {'code': 'MERCHANT_RECEIVE', 'name': '商户收款'},
    3: {'code': 'MERCHANT_REFUND', 'name': '商户退款'},
    4: {'code': 'PLATFORM_EARNING_MERCHANT_REFUND', 'name': '平台收入商户退款'},
    5: {'code': 'PLATFORM_REFUND', 'name': '平台退款'},
    6: {'code': 'PLATFORM_EXPEND_MERCHANT_SHARE', 'name': '平台支出商户分成'},
    7: {'code': 'MERCHANT_SHARE', 'name': '商户分成'},
    8: {'code': 'PLATFORM_EXPEND_MARKETER_SHARE', 'name': '平台支出邀请人分成'},
    9: {'code': 'MARKETER_SHARE', 'name': '邀请人分成'},
    10: {'code': 'PLATFORM_EXPEND_PLATFORM_SHARE', 'name': '平台支出平台分成'},
    11: {'code': 'PLATFORM_SHARE', 'name': '平台分成'},
    12: {'code': 'MERCHANT_WITHDRAW', 'name': '商户提现'},
    13: {'code': 'MARKETER_WITHDRAW', 'name': '邀请人提现'},
    14: {'code': 'MARKETER_ALIPAY_ACCOUNT_AUTH', 'name': '邀请人支付宝账号验证'},
    15: {'code': 'MERCHANT_WECHAT_SETTLEMENT', 'name': '商户微信结算'},
    16: {'code': 'MERCHANT_ALIPAY_SETTLEMENT', 'name': '商户支付宝结算'},
})

MESSAGE_STATUS = Config({
    0: {'code': 'DELETE', 'name': '已删除'},
    1: {'code': 'HANDLED', 'name': '已处理'},
    2: {'code': 'UNHANDLED', 'name': '未处理'},
})

MESSAGE_TYPE = Config({
    1: {'code': 'AREA_WITHOUT_MARKETER', 'name': '区域没有业务员'},
})

SUBSCRIPTION_ACCOUNT_REPLY_STATUS = Config({
    0: {'code': 'DELETE', 'name': '已删除'},
    1: {'code': 'USING', 'name': '使用中'},
})

SUBSCRIPTION_ACCOUNT_REPLY_RULE = Config({
    0: {'code': 'NOT_MATCH', 'name': '不匹配'},
    1: {'code': 'PARTIAL', 'name': '半匹配'},
    2: {'code': 'COMPLETE', 'name': '全匹配'},
})
SUBSCRIPTION_ACCOUNT_REPLY_TYPE = Config({
    0: {'code': 'KEY_WORD', 'name': '关键字回复'},
    1: {'code': 'BE_PAID_ATTENTION', 'name': '被关注回复'},
    2: {'code': 'RECEIVED', 'name': '收到消息回复'},
})

SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT = Config({
    0: {'code': 'USER', 'name': '用户公众号'},
    1: {'code': 'MERCHANT', 'name': '商户公众号'},
    2: {'code': 'MARKETER', 'name': '业务员公众号'},
})

CLIENT_TOKEN_TIMEOUT = 24 * 60 * 60  # 24h

NOT_SUPER_MENU = [
    {'id': 1, 'name': '首页', 'children': [], 'icon': 'home', 'url': '/main/'},
    {'id': 2, 'name': '商户管理', 'children': [], 'icon': 'bars', 'url': '/merchant/'},
    {'id': 3, 'name': '邀请人管理', 'children': [], 'icon': 'exception', 'url': '/inviter/'},
    {'id': 4, 'name': '业务员管理', 'children': [], 'icon': 'solution', 'url': '/salesman/'},
    # {'id': 5, 'name': '公众号管理', 'children': [], 'icon': 'wechat', 'url': '/subscription/'},
    {'id': 6, 'name': '二维码生成', 'children': [], 'icon': 'qrcode', 'url': '/qrcode/'},
]

SUPER_EXTRA_MENU = [
    {'id': 7, 'name': '后台用户管理', 'children': [], 'icon': 'solution', 'url': '/admins/'},
    # {'id': 8, 'name': '城市管理', 'children': [], 'icon': 'pie-chart', 'url': '/cities/'},
    {'id': 9, 'name': '财务管理', 'children': [
        {'id': 91, 'name': '财报与报表', 'children': [], 'icon': 'area-chart', 'url': '/report_forms/'},
        {'id': 92, 'name': '提现申请记录', 'children': [], 'icon': 'bars', 'url': '/withdraw_record/'},
        # {'id': 93, 'name': '资金流水', 'children': [], 'icon': 'bars', 'url': '/cash_flow/'},
        {'id': 94, 'name': '结算明细', 'children': [], 'icon': 'bars', 'url': '/settlement/'},
    ], 'icon': 'pay-circle', 'url': '/financial/'},
    # {'id': 10, 'name': '数据统计', 'children': [], 'icon': '', 'url': ''},
]

ALLOWED_ORIGINS = []

if dynasettings.IS_DEBUG:
    ALLOWED_ORIGINS.extend(
        [scheme + domain for scheme in ['http://', 'https://']
         for domain in ['payweb.alpha.muchbo.com',
                        'payweb.mishitu.com',
                        'payweb-alpha.mishitu.com']])

MIN_WITHDRAW_AMOUNT = 1  # 最小单次提现金额
WECHAT_MAX_WITHDRAW_AMOUNT = 20000  # 微信最大单次提现金额
ALIPAY_MAX_WITHDRAW_AMOUNT = 50000  # 支付宝最大单次提现金额

PLATFORM_SHARE_RATE = 0.03
INVITER_SHARE_RATE = 0.01
ORIGINATOR_SHARE_RATE = 0.01

WECHAT_PAY_BROKERAGE = 0.006
ALIPAY_PAY_BROKERAGE = 0.006

PLATFORM_ACCOUNT_ID = 1

GRANT_COUPON_DISTANCE = 5 * 1000  # m
PAYMENT_FROZEN_TIME = 60 if dynasettings.IS_DEBUG else 60 * 5  # 秒，支付冻结期。冻结期内不能提现，可以退款。冻结期后可以提现，不能退款
REFUND_STATUS_SYNC_TIME_WINDOW = 3600 * 24 * 3  # 只有3天内未完成的退款才会主动去查询，超过3天的暂时不管（需观察是否存在这种情况再决定如何处理）


# wechat mini program
class MerchantMiniProgram:
    user_token_expiration_time = 30 * 60  # 30min


# 微信模板消息id
class TemplateIdConfig:
    merchant_refund_success = 'op8cLZc9Gy2fdHUOJkTUp6dtlZBwpfdaqxi0VqtHlb4'  # 退款成功通知
    merchant_refund_fail = 'sgUQXI2RYdNatWZNtiUHcAbb0knXaHEc13OdjsOKays'  # 退款失败通知
    merchant_receive = 'KvQIA_TXEBPYV0d4VqNC8gCMmYlxtqurQJIno6kgQrc'  # 收款账单提醒


# 讯飞输出音频配置
class XunfeiVoiceSynthesisConfig:
    # https://doc.xfyun.cn/rest_api/语音合成.html
    api_url = 'http://api.xfyun.cn/v1/service/v1/tts'
    app_id = dynasettings.XUNFEI_API_ID
    api_key = dynasettings.XUNFEI_API_KEY

    auf = 'audio/L16;rate=8000'  # 音频采样率 可选值: 'audio/L16;rate=8000', 'audio/L16;rate=16000'
    aue = 'lame'  # 音频编码, 可选值: raw(未压缩的pcm或wav格式) , lame(mp3格式) 
    voice_name = 'xiaoyan'  # 发音人, 可选值: 详见发音人列表(https://www.xfyun.cn/services/online_tts)
    speed = '65'  # 语速[0,100]
    volume = '100'  # 音量[0,100]
    pitch = '50'  # 音高[0,100]
    engine_type = 'intp65'  # 引擎类型, 可选值: aisound(普通效果) , intp65(中文) , intp65_en(英文)

    receive_chunk_size = 512


# 百度输出音频配置
class BaiduVoiceSynthesisConfig:
    # https://ai.baidu.com/docs#/TTS-API/top

    token_url = 'http://openapi.baidu.com/oauth/2.0/token'

    api_key = dynasettings.BAIDU_API_KEY
    secret_key = dynasettings.BAIDU_SECRET_KEY


VIPS = {
    'dev': {
        'PAYWEB': 'http://payweb.alpha.muchbo.com',
        'SERVER': 'http://payserver.alpha.muchbo.com'
    },
    'test': {
        'PAYWEB': 'http://payweb-alpha.mishitu.com',
        'SERVER': 'http://api-alpha.mishitu.com'
    },
    'prod': {
        'PAYWEB': 'http://payweb.mishitu.com',
        'SERVER': 'http://api.mishitu.com'
    }
}[dynasettings.ENV]

# redis connection pool
SUBSCRIPT_REDIS_CONFIG = {
    "host": dynasettings.REDIS_HOST,
    "password": dynasettings.REDIS_PASSWORD if dynasettings.REDIS_PASSWORD else '',
    "port": dynasettings.as_int('REDIS_PORT'),
    "decode_responses": True,
    "db": 1
}

SUBSCRIPT_REDIS_POOL = redis.ConnectionPool(**SUBSCRIPT_REDIS_CONFIG)

# 管理后台生成二维码环境配置
QRCODE_ENVS = {
    'test': 'GenerateQrCodeEnvTest',
    'dev': 'GenerateQrCodeEnvTest',
    'prod': 'GenerateQrCode',
}

QINIU_IMAGE_SERVERS = {
    'test': 'ss-alpha.mishitu.com',
    'dev': 'ss-alpha.mishitu.com',
    'prod': 'ss.mishitu.com',
}

IO_BUFF_SIZE = 4096

TENCENT_MAP_KEY = 'GPSBZ-VJPW2-2TSUH-COVZS-CIYM6-ZOB2R'

API_VERSION = dict(
    USER=(1, 2, 0),
    MERCHANT=(1, 2, 0),
    MARKETER=(1, 2, 0),
)
