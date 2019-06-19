import json
import random
import uuid
import time
import re

from decimal import Decimal

import requests_mock
from django.core.cache import cache
from django.utils import timezone
from redis import StrictRedis
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import config
from common.error_handler import MarketerError
from common.models import Area, MerchantCategory, Marketer, Transaction, MerchantMarketerShip, \
    Merchant, VerifiedBankAccount
from common.msg_service.config import redis_pool
from config import VERIFY_ACCOUNT_STATUS
from marketer.config import PHONE_CODE_STATUS
from marketer.utils.redis_utils import RedisUtil, VerifyAccountLimitRecord
from marketer.utils.verify_account_handler import VERIFY_ACCOUNT_CODE
from test.api_test.marketer.test_marketer_config import VERIFY_ACCOUNT_INFO
from test.api_test.marketer.utils import MarketerLoginedMixin
from test.unittest.fake_factory.fake_factory import PayunionFactory
from test.utils import NonFieldError
from .test_marketer_config import CREATE_MERCHANT_DATA, REGISTER_MARKETER_DATA


class TestMarketerViewSet(MarketerLoginedMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = PayunionFactory()
        cls.inviter_account = cls.factory.create_account(
            balance=Decimal(300.01),
            withdrawable_balance=Decimal(222.01),
            alipay_balance=Decimal(256.00),
            alipay_withdrawable_balance=Decimal(210.00),
            bank_card_number='123456'
        )
        cls.marketer = cls.factory.create_marketer(
            wechat_openid='this open id',
            wechat_unionid='this unionid id',
            name='this marketer',
            account=cls.inviter_account,
            inviter_type=config.MARKETER_TYPES.SALESMAN,
            working_areas_name=['working area1', 'working area2'],
            status=config.SYSTEM_USER_STATUS.USING,
            phone='15888888888',
            wechat_nickname='wechat nickname',
            alipay_id='1234@qq.com'
        )
        super().setUpTestData()

    def test_show_invited(self):
        for i in range(10):
            merchant = self.factory.create_merchant(
                name='this merchant%s' % i,
                inviter=self.marketer
            )
            self.factory.create_payment(inviter_share=1919, merchant=merchant, number=11)

        url = reverse('invited-merchants-list')
        response = self.client.get(url, Token=self.token)
        invited_info = response.data.get('results')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for i in range(10):
            self.assertEqual(invited_info[i]['name'], 'this merchant%s' % i)

    def test_create_merchant(self):
        VerifyAccountLimitRecord.delete_record(self.marketer.wechat_unionid)
        request_times = VerifyAccountLimitRecord.record_request_an_hour(self.marketer.wechat_unionid)
        self.assertEqual(request_times, 0)
        self.factory.create_area(adcode='110119110000')
        self.factory.create_merchant_category(name='this category')
        self.factory.create_payment_qrcode()
        category = MerchantCategory.objects.get(name='this category').id
        payment_qr_code = self.factory.create_payment_qrcode().uuid
        CREATE_MERCHANT_DATA['area_id'] = '110119110000'
        CREATE_MERCHANT_DATA['category_id'] = category
        CREATE_MERCHANT_DATA['payment_qr_code'] = payment_qr_code
        json_data = json.dumps(CREATE_MERCHANT_DATA)
        url = reverse('create-merchant-list')
        response = self.client.post(url, data=json_data, Token=self.token, content_type='application/json')
        end_request_times = int(VerifyAccountLimitRecord.redis_cli.get(f'verify_account_{self.marketer.wechat_unionid}'))
        self.assertEqual(end_request_times, request_times)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        merchant_instance = Merchant.objects.filter(name=CREATE_MERCHANT_DATA['name']).first()
        admin = merchant_instance.admins.filter(merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN).first()
        self.assertEqual(admin.alipay_userid, CREATE_MERCHANT_DATA['merchant_admin_data']['alipay_userid'])
        self.assertEqual(admin.work_merchant, merchant_instance)
        self.assertEqual(merchant_instance.account.alipay_balance, 0)
        self.assertEqual(merchant_instance.account.alipay_withdrawable_balance, 0)
        self.assertEqual(merchant_instance.account.balance, 0)
        self.assertEqual(merchant_instance.account.withdrawable_balance, 0)
        self.assertEqual(merchant_instance.account.bank_name, CREATE_MERCHANT_DATA['merchant_acct_data']['bank_name'])
        self.assertEqual(merchant_instance.account.bank_card_number,
                         CREATE_MERCHANT_DATA['merchant_acct_data']['bank_card_number'])
        self.assertEqual(merchant_instance.account.real_name, CREATE_MERCHANT_DATA['merchant_acct_data']['real_name'])

    def test_register_marketer(self):
        # 设置匿名登陆token
        unregister_token = uuid.uuid4()
        cache.set(
            unregister_token,
            dict(
                openid='unregister openid',
                unionid='unregister unionid',
                session_key='session key'
            ),
            300
        )
        url = reverse('create-marketer-list')

        # 模拟短信验证，缓存注册电话号码及验证码
        redis_cli = StrictRedis(connection_pool=redis_pool)
        redis_cli.set(name=REGISTER_MARKETER_DATA['phone'],
                      value=REGISTER_MARKETER_DATA['verify_code'], ex=1 * 60)

        # 模拟网页授权获取web openid，缓存用户unionid及web openid
        wechat_info = REGISTER_MARKETER_DATA.pop('wechat_info')
        RedisUtil.cache_data('unregister unionid', json.dumps(wechat_info))
        register_data = json.dumps(REGISTER_MARKETER_DATA)
        response = self.client.post(url, data=register_data,
                                    Token=unregister_token,
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        register_marketer = Marketer.objects.get(id=response.data.get('id'))
        self.assertEqual(register_marketer.name, REGISTER_MARKETER_DATA['name'])
        self.assertEqual(register_marketer.alipay_id, REGISTER_MARKETER_DATA['alipay_id'])
        self.assertEqual(register_marketer.wechat_unionid, 'unregister unionid')
        self.assertEqual(register_marketer.wechat_openid, 'wechat openid')
        self.assertEqual(register_marketer.phone, REGISTER_MARKETER_DATA['phone'])
        self.assertEqual(register_marketer.id_card_front_url, REGISTER_MARKETER_DATA['id_card_front_url'])
        self.assertEqual(register_marketer.id_card_back_url, REGISTER_MARKETER_DATA['id_card_back_url'])

    def test_to_be_audited_merchant(self):
        area1 = Area.objects.get(name='working area1')
        area2 = Area.objects.get(name='working area2')
        self.factory.create_merchant(
            number=10,
            status=config.MERCHANT_STATUS.REVIEWING,
            area=area1
        )
        self.factory.create_merchant(
            number=10,
            status=config.MERCHANT_STATUS.REVIEWING,
            area=area2
        )
        self.factory.create_merchant(
            status=config.MERCHANT_STATUS.REVIEWING,
            area=self.factory.create_area(name='not wording area')
        )
        self.factory.create_merchant(
            number=20,
            status=config.MERCHANT_STATUS.USING,
            area=area1
        )
        url = reverse('show-audited-list') + '?page=3'
        response = self.client.get(url, Token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_show_operation(self):
        merchant = self.factory.create_merchant(status=config.MERCHANT_STATUS.USING, inviter=self.marketer)
        for i in range(10):
            coupon = self.factory.create_coupon(discount=100)
            withdraw = self.factory.create_withdraw(amount=1000,
                                                    withdraw_type=random.choice([config.WITHDRAW_TYPE.WECHAT,
                                                                                 config.WITHDRAW_TYPE.ALIPAY]))

            payment = self.factory.create_payment(inviter_share=1000, coupon=coupon, merchant=merchant)
            self.factory.create_transaction(
                account=self.marketer.account,
                content_object=withdraw
            )
            self.factory.create_transaction(
                account=self.marketer.account,
                content_object=payment
            )
        url = reverse('show-operation-list')
        response = self.client.get(url, Token=self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transactions = Transaction.objects.filter(account=self.marketer.account).order_by('-datetime')[:10]
        qs_pk = set([transaction.content_object.pk for transaction in transactions])
        res_pk = set([data.get('object_id') for data in response.data.get('results')])
        self.assertEqual(qs_pk, res_pk)

        pk = transactions[0].pk
        url = reverse('show-operation-detail', kwargs=dict(pk=pk))
        response = self.client.get(url, Token=self.token)
        self.assertEqual(response.data.get('object_id'), transactions[0].object_id)

    def test_get_user_info(self):
        self.factory.create_merchant(inviter=self.marketer, number=5, status=config.MERCHANT_STATUS.USING)
        self.factory.create_merchant(inviter=self.marketer, number=3, status=config.MERCHANT_STATUS.REVIEWING)
        self.marketer.account.alipay_withdrawable_balance = 1000
        self.marketer.account.withdrawable_balance = 500
        self.marketer.account.save()
        url = reverse('get-info')
        response = self.client.get(url, Token=self.token)
        self.assertNotEqual(response.data.get('user_status'), 'not_register')
        self.assertEqual(response.data.get('user_withdrawable_balance'), 1000 + 500)
        self.assertEqual(response.data.get('alipay_withdraw_balance'), 1000)
        self.assertEqual(response.data.get('wechat_withdraw_balance'), 500)

        # 测试存在token，不存在marketer
        unregister_token = uuid.uuid4()
        cache.set(
            unregister_token,
            dict(
                openid='unregister openid',
                unionid='unregister unionid',
                session_key='session key'
            ),
            300
        )
        response = self.client.get(url, Token=unregister_token)
        self.assertEqual(response.data.get('user_status'), 'not_register')

    def test_get_merchant_detail(self):
        merchant = self.factory.create_merchant(inviter=self.marketer)
        self.factory.create_merchant_admin(work_merchant=merchant,
                                           merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
                                           status=config.SYSTEM_USER_STATUS.USING)
        self.factory.create_merchant_marketer_ship(merchant=merchant, marketer=self.marketer,
                                                   audit_info='this is audit')
        url = reverse('merchant-details-detail', kwargs=dict(pk=merchant.pk))
        response = self.client.get(url, Token=self.token)
        pass

    def test_audit_merchant(self):
        area_instance = self.marketer.working_areas.all().first()
        to_using_merchant = self.factory.create_merchant(name='to_using_merchant',
                                                         status=config.MERCHANT_STATUS.REVIEWING)
        self.factory.create_merchant_admin(work_merchant=to_using_merchant,
                                           merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
                                           status=config.SYSTEM_USER_STATUS.USING)
        to_reject_merchant = self.factory.create_merchant(name='to_reject_merchant',
                                                          status=config.MERCHANT_STATUS.REVIEWING,
                                                          area=area_instance)
        self.factory.create_merchant_admin(work_merchant=to_reject_merchant,
                                           merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
                                           status=config.SYSTEM_USER_STATUS.USING)
        url = reverse('audit-merchant-detail', kwargs=dict(pk=to_reject_merchant.pk))
        response = self.client.patch(url, Token=self.token, data=json.dumps(
            dict(status=config.MERCHANT_STATUS.REJECTED, audit_info='this info')), content_type='application/json')
        audit_ship = MerchantMarketerShip.objects.filter(marketer=self.marketer, merchant=to_reject_merchant).order_by(
            '-audit_datetime').first()
        pass

    def test_check_code(self):
        code = self.factory.create_payment_qrcode().uuid
        not_exist_code = uuid.uuid4()
        bind_code = self.factory.create_merchant().payment_qr_code.uuid
        url1 = reverse('check-code') + '?code=%s' % code
        url2 = reverse('check-code') + '?code=%s' % not_exist_code
        url3 = reverse('check-code') + '?code=%s' % bind_code
        response1 = self.client.get(url1, Token=self.token)
        response2 = self.client.get(url2, Token=self.token)
        response3 = self.client.get(url3, Token=self.token)
        pass

    def test_check_admin(self):
        merchant = self.factory.create_merchant()
        exist_unionid = self.factory.create_merchant_admin(work_merchant=merchant).wechat_unionid
        fake_unionid = uuid.uuid4()
        url1 = reverse('check-admin') + '?unionid=%s' % exist_unionid
        url2 = reverse('check-admin') + '?unionid=%s' % fake_unionid
        response1 = self.client.get(url1, Token=self.token)
        response2 = self.client.get(url2, Token=self.token)
        pass

    def test_update_marketer(self):
        redis_cli = StrictRedis(connection_pool=redis_pool)
        redis_cli.set(name='18888888888', value='000000', ex=1 * 60)
        url = reverse('update-marketer')
        response = self.client.put(url,
                                   data=json.dumps(dict(phone='18888888888', verify_code='000000')),
                                   content_type='application/json',
                                   Token=self.token)
        marketer_phone = Marketer.objects.filter(pk=self.marketer.pk).first().phone
        self.assertEqual(response.data.get('phone'), marketer_phone)

    def test_check_phone(self):
        self.factory.create_marketer(phone='18888888888')
        url = reverse('check-phone') + '?phone=18888888888'
        response = self.client.get(url, Token=self.token)
        self.assertEqual(response.data.get('code'), PHONE_CODE_STATUS['EXIST'])

    def test_marketer_sms_send(self):
        # 测试发送短信

        url = reverse('message-send')
        url1 = reverse('authenticated-message-send')

        # 发送失败用例 -- 电话号码不对
        response = self.client.post(url, data={'phone': '123456'},
                                    Token=self.token)
        self.assertEqual(response.data.get('message'), '请确认电话号码是否正确')

        response = self.client.post(url1, data={'phone': '1234567'},
                                    Token=self.token)
        self.assertEqual(response.data.get('message'), '请确认电话号码是否正确')

        # 发送成功用例
        phone = '13281826916'
        response = self.client.post(url, data={'phone': phone},
                                    Token=self.token)
        assert response.data.get('code') in (-2, -1, 0)

    def test_verify_sms_code(self):
        # 验证短信验证码
        url = reverse('sms-code-verify')
        phone = '13281826916'

        # 验证成功用例
        redis_cli = StrictRedis(connection_pool=redis_pool)
        code = redis_cli.get(name=phone) or b''
        response = self.client.post(url,
                                    data={'phone': phone,
                                          'verify_code': code.decode('utf8')},
                                    Token=self.token)
        self.assertEqual(response.data.get('message'), '短信验证成功')

        # 验证失败用例
        response = self.client.post(url, data={'phone': phone,
                                               'verify_code': '42342112'},
                                    Token=self.token)
        self.assertEqual(response.data.get('message'), "验证码输入错误，请重新输入")

    def test_has_marketer(self):
        # 验证该区域是否存在业务员
        url = reverse('has_marketer')
        Area.objects.create(adcode=110105000000, city_id=1)

        # 验证adcode不存在
        response = self.client.get(url, data={'adcode': '110119110000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), -1)

        # 验证adcode存在， 没有业务员
        self.factory.create_area(name='测试区域', adcode='110119110001')
        response = self.client.get(url, data={'adcode': '110119110001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 0)

        # 验证adcode存在且有业务员
        salesman = self.factory.create_marketer(
            wechat_openid='salesman unionid',
            status=config.SYSTEM_USER_STATUS['USING'],
            inviter_type=config.MARKETER_TYPES['SALESMAN'],
            working_areas_name=['测试区域']
        )
        response = self.client.get(url, data={'adcode': '110119110001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 1)

        # 验证110105502000
        response = self.client.get(url, data={'adcode': '110105502000'})
        pass

    def test_get_merchant_category(self):
        # 获取商户分类
        url = reverse('get-category')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wechat_auth_redirect(self):
        # 测试微信授权重定向
        auth_marketer_url = reverse('get-marketer-wechat-info')
        auth_merchant_url = reverse('get-merchant-wechat-info')

        code = 'this is auth code'
        # merketer 授权
        response = self.client.get(auth_marketer_url, data={'code': code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # merchant授权
        response = self.client.get(auth_merchant_url,
                                   data={'code': code, 'state': '66666'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_withdraw_exception(self):
        """ marketer提现异常 """
        url = reverse('marketer-withdraw')
        # 未知提现渠道
        response = self.client.put(url, data=dict(
            amount=22.01,
            channel='xxxxxx',
        ), Token=self.token, format='json')
        resp_json = response.json()
        self.assertEqual(resp_json, {'channel': ['请填写合法的整数值。'], 'error_code': 'invalid'})

        # 微信提现
        response = self.client.put(url, data=dict(
            amount=20000.01,
            channel=config.PAY_CHANNELS.WECHAT,
        ), Token=self.token, format='json')  # 大于单次提现金额
        resp_json = response.json()
        self.assertEqual(resp_json, NonFieldError(MarketerError.exceeding_the_wechat_maximum_withdrawal_balance))

        response = self.client.put(url, data=dict(
            amount=0.5,
            channel=config.PAY_CHANNELS.WECHAT,
        ), Token=self.token, format='json')  # 小于单次提现金额
        resp_json = response.json()
        self.assertEqual(resp_json, {'amount': ["请确保该值大于或者等于 1。"],
                                     'error_code': 'min_value'})

        response = self.client.put(url, data=dict(
            amount=500.11,
            channel=config.PAY_CHANNELS.WECHAT
        ), Token=self.token, format='json')  # 可提现余额不足
        resp_json = response.json()
        self.assertEqual(resp_json.get('error_code'),
                         'withdrawable balance is not sufficient')

        # 支付宝提现
        response = self.client.put(url, data=dict(
            amount=50000.01,
            channel=config.PAY_CHANNELS.ALIPAY,
        ), Token=self.token, format='json')  # 大于单次提现金额
        resp_json = response.json()
        self.assertEqual(resp_json, {'amount': ['请确保该值小于或者等于 50000。'],
                                     'error_code': 'max_value'})

        response = self.client.put(url, data=dict(
            amount=0.55,
            channel=config.PAY_CHANNELS.ALIPAY,
        ), Token=self.token, format='json')  # 小于单次提现金额
        resp_json = response.json()
        self.assertEqual(resp_json, {'amount': ["请确保该值大于或者等于 1。"],
                                     'error_code': 'min_value'})

        response = self.client.put(url, data=dict(
            amount=2222.22,
            channel=config.PAY_CHANNELS.ALIPAY,
        ), Token=self.token, format='json')  # 可提现余额不足
        resp_json = response.json()
        self.assertEqual(resp_json.get('error_code'),
                         'withdrawable balance is not sufficient')

    def test_alipay_transfer(self):
        """ alipay转账接口测试 """
        url = reverse('alipay-account-check')
        account_number = '123456@qq.com'
        account_name = "张三"

        # TransferRecord 没有成功记录
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json.get('message'), "没有与该unionid对应的成功记录")

        # TransferRecord 有成功记录
        new_record = self.factory.create_transfer_record(
            account_number=account_number,
            account_name=account_name,
            wechat_unionid=self.marketer.wechat_unionid,
            status=config.TRANSFER_STATUS.FINISHED
        )
        response = self.client.get(url, Token=self.token)
        resp_json = response.json()
        self.assertEqual(resp_json.get('message'), "存在转账成功记录")

        # 接口限制
        response = self.client.post(url, data=dict(
            account_number='xx',
            account_name=''
        ), Token=self.token)  # 账号或名字为空
        resp_json = response.json()
        self.assertEqual(resp_json.get('message'), "支付宝账号和姓名必填")

        response = self.client.post(url, data=dict(
            account_number=account_number,
            account_name=account_name
        ), Token=self.token)  # 有成功的转账记录
        resp_json = response.json()
        self.assertEqual(resp_json.get('message'), "存在转账成功记录")

    def test_verify_account(self):
        request_no = 'callback request number'

        def verify_success_callback(request, context):
            callback_dict = {
                "code": 0,
                "desc": "验证成功，信息一致",
                "requestNo": f"{request_no}"
            }
            return callback_dict

        def verify_error_bank_name_callback(request, context):
            callback_dick = {
                "code": 3,
                "desc": "开户行名称错误"
            }
            return callback_dick

        def verify_verifying_callback(request, context):
            callback_dick = {
                "code": 1,
                "desc": "正向账户发起一分钱付款验证",
                "requestNo": f"{request_no}"
            }
            return callback_dick

        def result_success_callback(request, context):
            callback_dict = {
                "code": 0,
                "desc": "付款成功，信息一致",
            }
            return callback_dict

        def result_verifying_callback(request, context):
            callback_dict = {
                "code": 1,
                "desc": "验证中，请稍后查询"
            }
            return callback_dict

        def result_fail_callback(request, context):
            callback_dict = {
                "code": 2,
                "desc": "收款银行不存在此银行账号，请核对收款银行与银行账号是否填写正确"
            }
            return callback_dict

        def result_error_callback(request, context):
            callback_dict = {
                "code": 3,
                "desc": "验卡记录不存在"
            }
            return callback_dict

        VERIFY_ACCOUNT_INFO['VERIFYING'].update(marketer_id=self.marketer.id)
        VERIFY_ACCOUNT_INFO['SUCCESS'].update(marketer_id=self.marketer.id)
        VERIFY_ACCOUNT_INFO['FAIL'].update(marketer_id=self.marketer.id)
        VERIFY_ACCOUNT_INFO['CHECK_AGAIN'].update(marketer_id=self.marketer.id)

        # 向数据库中写入数据
        verifying_res = VerifiedBankAccount.objects.create(**VERIFY_ACCOUNT_INFO['VERIFYING'])
        success_res = VerifiedBankAccount.objects.create(**VERIFY_ACCOUNT_INFO['SUCCESS'])
        fail_res = VerifiedBankAccount.objects.create(**VERIFY_ACCOUNT_INFO['FAIL'])
        check_again_res = VerifiedBankAccount.objects.create(**VERIFY_ACCOUNT_INFO['CHECK_AGAIN'])

        def generate_reqeust_data(acct_info):
            return {
                    'acctName': acct_info['real_name'],
                    'bankName': acct_info['bank_name'],
                    'cardno': acct_info['bank_card_number']
                    }

        # 无记录账号
        data = {
            'acctName': '张继华',
            'bankName': '兴业银行',
            'cardno': '622909433958748713'
        }

        verifying_data = generate_reqeust_data(VERIFY_ACCOUNT_INFO['VERIFYING'])
        success_data = generate_reqeust_data(VERIFY_ACCOUNT_INFO['SUCCESS'])
        fail_data = generate_reqeust_data(VERIFY_ACCOUNT_INFO['FAIL'])
        check_again_data = generate_reqeust_data(VERIFY_ACCOUNT_INFO['CHECK_AGAIN'])

        url = reverse('verify-account')
        verify_pattern = re.compile(r'^http://verifycorp\.market\.alicloudapi\.com/lianzhuo/?[\w\W]*')
        result_pattern = re.compile(r'^http://queryverif\.market\.alicloudapi\.com/lianzhuo/?[\w\W]*')

        # 本地数据库中无记录
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', verify_pattern, json=verify_verifying_callback)
            verify_resp = self.client.post(url, data=data, Token=self.token)
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.data['code'], VERIFY_ACCOUNT_CODE['VERIFYING'])
        self.assertEqual(verify_resp.data['desc'], '验证中')
        verify_instance = VerifiedBankAccount.objects.get(id=verify_resp.data['id'])
        self.assertEqual(verify_instance.verify_status, VERIFY_ACCOUNT_STATUS.VERIFYING)
        self.assertEqual(verify_instance.request_number, verify_success_callback(None, None)['requestNo'])
        self.assertEqual(verify_instance.real_name, data['acctName'])
        self.assertEqual(verify_instance.bank_card_number, data['cardno'])
        self.assertEqual(verify_instance.bank_name, data['bankName'])
        self.assertEqual(verify_instance.marketer_id, self.marketer.id)

        # 获取结果
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', result_pattern, json=result_success_callback)
            result_resp = self.client.get(url, data={'id': verify_resp.data['id']}, Token=self.token)
        self.assertEqual(result_resp.status_code, 200)
        self.assertEqual(result_resp.data['code'], VERIFY_ACCOUNT_CODE['SUCCESS'])
        self.assertEqual(result_resp.data['desc'], '验证成功')
        verify_instance = VerifiedBankAccount.objects.get(id=verify_resp.data['id'])
        self.assertEqual(verify_instance.verify_status, VERIFY_ACCOUNT_STATUS.SUCCESS)
        self.assertEqual(verify_instance.request_number, verify_success_callback(None, None)['requestNo'])
        self.assertEqual(verify_instance.real_name, data['acctName'])
        self.assertEqual(verify_instance.bank_card_number, data['cardno'])
        self.assertEqual(verify_instance.bank_name, data['bankName'])
        self.assertEqual(verify_instance.marketer_id, self.marketer.id)

        # 数据库中有待验证记录
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', verify_pattern, json=verify_success_callback)
            verify_resp = self.client.post(url, data=verifying_data, Token=self.token)
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.data['code'], VERIFY_ACCOUNT_CODE['VERIFYING'])
        self.assertEqual(verify_resp.data['desc'], '验证中')
        self.assertEqual(verify_resp.data['id'], verifying_res.id)

        # 获取结果
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', result_pattern, json=result_success_callback)
            result_resp = self.client.get(url, data={'id': verify_resp.data['id']}, Token=self.token)
        self.assertEqual(result_resp.status_code, 200)
        self.assertEqual(result_resp.data['code'], 0)
        self.assertEqual(result_resp.data['desc'], '验证成功')
        verifying_res = VerifiedBankAccount.objects.get(id=verifying_res.id)
        self.assertEqual(VERIFY_ACCOUNT_STATUS.SUCCESS, verifying_res.verify_status)

        # 数据库中有成功记录
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', verify_pattern, json=verify_success_callback)
            verify_resp = self.client.post(url, data=success_data, Token=self.token)
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.data['code'], VERIFY_ACCOUNT_CODE['SUCCESS'])
        self.assertEqual(verify_resp.data['desc'], '验证成功')
        self.assertEqual(verify_resp.data['id'], success_res.id)

        # 数据库中有失败记录
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', verify_pattern, json=verify_verifying_callback)
            verify_resp = self.client.post(url, data=fail_data, Token=self.token)
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.data['code'], VERIFY_ACCOUNT_CODE['FAIL'])
        self.assertEqual(verify_resp.data['desc'], '信息错误，验证失败')
        self.assertEqual(verify_resp.data['id'], fail_res.id)

        # 数据库中有超过验证间隔时间的失败记录
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', verify_pattern, json=verify_verifying_callback)
            verify_resp = self.client.post(url, data=check_again_data, Token=self.token)
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.data['code'], VERIFY_ACCOUNT_CODE['VERIFYING'])
        self.assertEqual(verify_resp.data['desc'], '验证中')
        self.assertEqual(verify_resp.data['id'], check_again_res.id)

        # 获取结果
        with requests_mock.Mocker(real_http=False) as m:
            m.register_uri('GET', result_pattern, json=result_success_callback)
            result_resp = self.client.get(url, data={'id': verify_resp.data['id']}, Token=self.token)
        self.assertEqual(result_resp.status_code, 200)
        self.assertEqual(result_resp.data['code'], 0)
        self.assertEqual(result_resp.data['desc'], '验证成功')
        self.assertEqual(result_resp.data['id'], check_again_res.id)
        check_again_res = VerifiedBankAccount.objects.get(id=check_again_res.id)
        self.assertEqual(check_again_res.verify_status, VERIFY_ACCOUNT_STATUS.SUCCESS)
        self.assertEqual(check_again_res.request_number, verify_success_callback(None, None)['requestNo'])
        self.assertEqual(check_again_res.real_name, check_again_data['acctName'])
        self.assertEqual(check_again_res.bank_card_number, check_again_data['cardno'])
        self.assertEqual(check_again_res.bank_name, check_again_data['bankName'])
        self.assertEqual(check_again_res.marketer_id, self.marketer.id)
