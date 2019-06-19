from django.utils import timezone

from config import VERIFY_ACCOUNT_STATUS, MERCHANT_TYPE

CREATE_MERCHANT_DATA = {
    'type': MERCHANT_TYPE.ENTERPRISE,
    'name': 'this created merchant',
    'payment_qr_code': None,
    'category_id': None,
    'contact_phone': '15888888888',
    'area_id': None,
    'address': 'this merchant address',
    'location_lon': 102,
    'location_lat': 27,
    'description': 'this merchant desc',
    'avatar_url': 'this avatar url',
    'license_url': 'this url',
    'id_card_front_url': '',
    'id_card_back_url': '',
    'merchant_admin_openid': 'this openid',
    'merchant_admin_unionid': 'this unionid',
    'merchant_admin_data': {
        'wechat_openid': 'this openid',
        'wechat_unionid': 'this unionid',
        'wechat_avatar_url': 'this url',
        'wechat_nickname': 'this nickname',
        'alipay_userid': 'this alipay id',
        'alipay_user_name': 'this alipay name'
    },
    'merchant_acct_data': {
        'bank_name': 'bank name',
        'bank_card_number': '88888888888',
        'real_name': 'real name'
    }

}

CREATE_MARKETER_DATA_NEW = {
    'merchant': {
        'name': 'this created merchant',
        'payment_qr_code': None,
        'category': None,
        'contact_phone': '15888888888',
        'area': None,
        'address': 'this merchant address',
        'location_lon': 102,
        'location_lat': 27,
        'description': 'this merchant desc',
        'avatar_url': 'this avatar url',
        'photo_url': 'this photo url',
        'license_url': 'this license url',
        'id_card_front_url': 'this id card front url',
        'id_card_back_url': 'this id card back url',
    },
    'merchant_admin': {
        'wechat_openid': 123456789,
    }

}

REGISTER_MARKETER_DATA = {
    'name': '小张',
    'alipay_id': 'alipay account',
    'phone': '18888888888',
    'id_card_front_url': 'this is url',
    'id_card_back_url': 'this is url',
    'verify_code': '000000',
    'wechat_info': {'openid': 'wechat openid',
                    'nickname': 'wechat nickname',
                    'headimgurl': 'avatar url',
                    'unionid': 'wechat unionid'}

}

UPDATE_ACCOUNT_DATA = {
    'bank_name': 'this update bank',
    'bank_card_number': '88888888888888888 ',
    'bank_account_name': 'this update name'
}

FILTER_PARAMS = {
    'start_date': '2018-2-1',
    'end_date': '2018-7-1',
    'choose_type': 'with_draw',
    'keywords': '肯德基'
}


VERIFY_ACCOUNT_INFO = {
    'VERIFYING': {
        'real_name': 'verifying name',
        'bank_name': 'verifying bank',
        'bank_card_number': '88888888888888888',
        'verify_status': VERIFY_ACCOUNT_STATUS.VERIFYING,
        'request_number': 'verifying request number'
    },
    'SUCCESS': {
        'real_name': 'success name',
        'bank_name': 'success bank',
        'bank_card_number': '77777777777777777',
        'verify_status': VERIFY_ACCOUNT_STATUS.SUCCESS,
        'request_number': 'success request number'
    },
    'FAIL': {
        'real_name': 'fail name',
        'bank_name': 'fail bank',
        'bank_card_number': '66666666666666666',
        'verify_status': VERIFY_ACCOUNT_STATUS.FAIL,
        'request_number': 'fail request number'
    },
    'CHECK_AGAIN': {
        'real_name': 'check again name',
        'bank_name': 'check again bank',
        'bank_card_number': '55555555555555555',
        'verify_status': VERIFY_ACCOUNT_STATUS.FAIL,
        'request_number': 'check again request number',
        'datetime': timezone.now() - timezone.timedelta(hours=2)
    },
}
