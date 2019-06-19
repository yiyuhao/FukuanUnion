from dynaconf import settings as dynasettings

from config import Config

MARKETER_MINI_PROGRAM = Config({
    60 * 10: {'code': 'user_token_expiration_time', 'name': '用户token失效时间(秒)'},
})

CONTENT_TEMPLATE = {
    'NO_INVITER': '所属区域没有业务员',
}

PAYMENT_QR_CODE_STATUS = {
    'DOES_NOT_EXIST': 0,
    'CAN_USE': 1,
    'HAS_BEEN_BIND': 2
}

PHONE_CODE_STATUS = {
    'EXIST': 0,
    'CAN_USE': 1,
}

AREA_STATUS_CODE = {
    'DISABLE': -1,
    'NO_MARKETER': 0,
    'HAS_MARKETER': 1
}

IDENTIFICATION_STATUS_CODE = {
    'IDENTIFY_FAIL': 0,
    'SUCCESS': 1
}

# 支付宝账号验证接口限制
UNIONID_LIMIT = {
    'limit_seconds': 7 * 24 * 60 * 60,  # 7天 转换为秒
    'max_times': 5  # limit_seconds内最多转账max_times次
}
MAX_REQUEST_ONE_DAY = 1000  # 接口一天请求上限

ALIPAY_VERIFY_TRANSFER_AMOUNT = 10

# 当adcode不存在时,根据adcode前4位匹配城市
CITY_MAP = {
    '1101': "北京市",
    '3101': "上海市",
    '5101': "成都市"
}

# 关于阿里云api的config
CONTENT_TYPE = (
    CONTENT_TYPE_FORM, CONTENT_TYPE_STREAM,
    CONTENT_TYPE_JSON, CONTENT_TYPE_XML, CONTENT_TYPE_TEXT
) = (
    'application/x-www-form-urlencoded;charset=UTF-8', 'application/octet-stream',
    'application/json', 'application/xml', 'application/text'
)

ALIYUN_MARKET_API_CONFIG = {
    'corp_account_verify': {
        'url': 'http://verifycorp.market.alicloudapi.com/lianzhuo/verifyCorpAccount',
        'method': 'get',
        'params': ('acctName', 'bankName', 'cardno'),
    },
    'corp_verify_result': {
        'url': 'http://queryverif.market.alicloudapi.com/lianzhuo/queryVerifyResult',
        'method': 'get',
        'params': ('requestNo',)
    },
    'identify_bank_card': {
        'url': 'https://api06.aliyun.venuscn.com/ocr/bank-card',
        'method': 'post',
        'params': ('pic',),
    }
}

ALIYUN_ACCOUNT_CONFIG = {
    'appcode': dynasettings.ALIYUN_APPCODE,
    'app_key': str(dynasettings.ALIYUN_APP_KEY),
    'app_secret': dynasettings.ALIYUN_APP_SECRET
}

MAX_VERIFY_ACCOUNT_REQUEST_AN_HOUR = 10
