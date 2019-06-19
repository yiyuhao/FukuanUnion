from django.utils import timezone

from common.models import VerifiedBankAccount
from config import VERIFY_ACCOUNT_STATUS
from marketer.config import MAX_VERIFY_ACCOUNT_REQUEST_AN_HOUR
from common.aliyun_market_handler import AliyunMarketHandler
from marketer.utils.redis_utils import VerifyAccountLimitRecord

VERIFY_ACCOUNT_CODE = {
    'SUCCESS': 0,
    'VERIFYING': 1,
    'FAIL': 2,
    #  3预留为阿里云api返回的错误
    'FREQUENTLY': 4,
    'USE_UP': 5,
    'UNKNOWN_ERROR': 6
}

VERIFY_INTERVAL = 60 * 60


class VerifyAccountHandler:
    def __init__(self, user, params):
        self._user = user
        self._params = params
        self._verified_res = None

    def verify_account(self):
        self._verified_res = VerifiedBankAccount.objects.filter(bank_name=self._params['bankName'],
                                                                bank_card_number=self._params['cardno'],
                                                                real_name=self._params['acctName']).first()
        if self._verified_res:
            return self._check_record()
        return self._verify_account_request()

    def get_result(self):
        self._verified_res = VerifiedBankAccount.objects.get(id=self._params['id'])
        params = {'requestNo': self._verified_res.request_number}
        result_resp = AliyunMarketHandler('corp_verify_result').go(params=params)
        if result_resp.status_code != 200:
            return self._fail_request_callback(result_resp)
        res = result_resp.json()
        return self._request_code_callback(res)

    def _record_verify_result(self, verify_status, request_no):
        if self._verified_res:
            change_status = (self._verified_res.verify_status != verify_status)
            change_request_no = bool(request_no) and (self._verified_res.request_number != request_no)
            if change_status:
                self._verified_res.verify_status = verify_status
            if change_request_no:
                self._verified_res.request_number = request_no
            if change_status or change_request_no:
                self._verified_res.save()
        else:
            self._verified_res = VerifiedBankAccount.objects.create(bank_name=self._params['bankName'],
                                                                    bank_card_number=self._params['cardno'],
                                                                    real_name=self._params['acctName'],
                                                                    marketer=self._user,
                                                                    verify_status=verify_status,
                                                                    request_number=request_no)

    @staticmethod
    def _fail_request_callback(resp):
        if resp.status_code == 403 and resp.reason == 'Forbidden':
            return {'code': VERIFY_ACCOUNT_CODE['USE_UP'],
                    'desc': '阿里云验证次数用尽'}
        return {'code': VERIFY_ACCOUNT_CODE['UNKNOWN_ERROR'],
                'desc': 'unknown error'}

    def _check_user_request_record(self):
        redis_manager = VerifyAccountLimitRecord
        unionid = self._user.wechat_unionid
        request_record = redis_manager.record_request_an_hour(unionid)
        return request_record < MAX_VERIFY_ACCOUNT_REQUEST_AN_HOUR

    def _check_record(self):
        if self._verified_res.verify_status == VERIFY_ACCOUNT_STATUS.VERIFYING:
            return {'code': VERIFY_ACCOUNT_CODE['VERIFYING'],
                    'desc': '验证中',
                    'id': self._verified_res.id}
        if self._verified_res.verify_status == VERIFY_ACCOUNT_STATUS.SUCCESS:
            return {'code': VERIFY_ACCOUNT_CODE['SUCCESS'],
                    'desc': '验证成功',
                    'id': self._verified_res.id}
        curr_time = timezone.now().timestamp()
        if curr_time - self._verified_res.datetime.timestamp() > VERIFY_INTERVAL:
            return self._verify_account_request()
        return {'code': VERIFY_ACCOUNT_CODE['FAIL'],
                'desc': '信息错误，验证失败',
                'id': self._verified_res.id}

    def _verify_account_request(self):
        if not self._check_user_request_record():
            return {'code': VERIFY_ACCOUNT_CODE['FREQUENTLY'],
                    'desc': '超过每小时验证次数，请下个整点再试'}
        verify_resp = AliyunMarketHandler('corp_account_verify').go(params=self._params)
        if verify_resp.status_code != 200:
            return self._fail_request_callback(verify_resp)
        res = verify_resp.json()
        return self._request_code_callback(res)

    def _request_code_callback(self, res):
        code = res.get('code', 3)
        if code == 0:
            self._record_verify_result(verify_status=VERIFY_ACCOUNT_STATUS.SUCCESS,
                                       request_no=res.get('requestNo'))
            return {'code': VERIFY_ACCOUNT_CODE['SUCCESS'], 'desc': '验证成功', 'id': self._verified_res.id}
        if code == 1:
            self._record_verify_result(verify_status=VERIFY_ACCOUNT_STATUS.VERIFYING,
                                       request_no=res.get('requestNo'))
            return {'code': VERIFY_ACCOUNT_CODE['VERIFYING'], 'desc': '验证中', 'id': self._verified_res.id}
        if code == (2 or 3):
            self._record_verify_result(verify_status=VERIFY_ACCOUNT_STATUS.FAIL,
                                       request_no=res.get('requestNo'))
            return {'code': VERIFY_ACCOUNT_CODE['FAIL'], 'desc': '信息错误，验证失败', 'id': self._verified_res.id}
        return res
