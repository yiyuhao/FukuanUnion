import uuid
import threading
import json
import random
from queue import Queue

from rest_framework.test import APITestCase
from test.auto_test.steps.inviter import LoginStep, GetUserInfoStep, GetMarketerWechatInfoStep, SendRegisterMessageStep, \
    VerifyCodeStep, GetQiniuUpTokenStep, CreateMarketerStep, GetMerchantWechatInfoStep, GetMerchantAlipayInfoStep, \
    GetCategoryStep, CreateQrCodeStep, CreateMerchantStep, CheckCodeStep, CheckMarketerStep, CheckAdminExistStep, \
    CheckPhoneExistStep, AuditMerchantStep
from test.unittest.fake_factory.fake_factory import fake
from test.auto_test.steps.socket import WebSocketThread
from marketer.config import PAYMENT_QR_CODE_STATUS, AREA_STATUS_CODE, PHONE_CODE_STATUS

DEFUALT_IMAGE_URL = 'http://t2.hddhhn.com/uploads/tu/201610/198/hkgip2b102z.jpg'


class BaseInviterWorkflow(APITestCase):
    def __init__(self, token=None, unionid=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token, self.unionid = token, unionid

    def login(self, code=None, unionid=None):
        mp_code = str(uuid.uuid4())
        resp = LoginStep(code=mp_code).go(request_data={'code': code or mp_code},
                                          callback_data={'unionid': unionid or self.unionid},
                                          extra_res_keys='mocked_unionid')
        self.assertEqual(resp[0].status_code, 200)
        self.token = resp[0].data.get('token')
        self.unionid = resp[1]['mocked_unionid']
        return self.token

    def get_user_info(self, token=None):
        resp = GetUserInfoStep().go(token=token or self.token)
        self.assertEqual(resp[0].status_code, 200)
        return resp


class WebSocketClientWorkflow(APITestCase):
    def __init__(self, token, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.channel = channel

    def connect_socket(self, message_queue, token=None, channel=None):
        event = threading.Event()  # 创建一个事件
        ws_client = WebSocketThread(marketer_token=token or self.token,
                                    event=event,
                                    channel=channel or self.channel,
                                    queue=message_queue)
        ws_client.start()
        event.wait()
        return ws_client

    def server_callback(self, *args, **kwargs):
        raise NotImplementedError('`server_action` must be implemented.')

    def client_get_info(self, socket_data=None, callback_data=None):
        socket_data, callback_data = socket_data or {}, callback_data or {}
        message_queue = Queue()
        ws_client = self.connect_socket(message_queue, **socket_data)
        self.server_callback(**callback_data)
        ws_client.join()
        if message_queue.empty():
            raise Exception(
                "message_queue is empty, web-socket not receive message")
        msg = message_queue.get()
        info = json.loads(msg['message'])
        return info


class RegisterInviterWorkflow(BaseInviterWorkflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_info = {}
        self.created_info = {}

    def web_auth(self, invalid_code=None, invalid_access_token=None, invalid_openid=None):
        web_code = str(uuid.uuid4())
        resp = GetMarketerWechatInfoStep(code=web_code).go(request_data={'code': invalid_code or web_code},
                                                           callback_data={'access_token': invalid_access_token,
                                                                          'openid': invalid_openid,
                                                                          'unionid': self.unionid},
                                                           extra_res_keys=('unionid', 'openid'))
        self.assertEqual(resp[0].status_code, 200)
        self.assertIn('已成功授权', resp[0].content.decode('utf8'))

    def set_user_name(self, name=None):
        self.user_info['name'] = name or fake.name()

    def set_phone(self, phone=None):
        phone = phone or fake.phone_number()
        resp = CheckPhoneExistStep().go(request_data={'phone': phone})
        self.assertEqual(resp[0].status_code, 200)
        self.assertNotEqual(resp[0].data.get('code'), PHONE_CODE_STATUS['EXIST'])
        self.user_info['phone'] = phone

    def send_message(self, invalid_phone=None, invalid_token=None):
        resp = SendRegisterMessageStep().go(request_data={'phone': invalid_phone or self.user_info['phone']},
                                            token=invalid_token or self.token,
                                            extra_res_keys='get_send_code')
        self.assertEqual(resp[0].status_code, 200)
        self.assertEqual(resp[0].data.get('code'), 0)
        self.assertEqual(resp[0].data.get('message'), '验证码发送成功')
        self.user_info['verify_code'] = str(resp[1]['get_send_code'])

    def verify_code(self, invalid_phone=None, invalid_verify_code=None, invalid_token=None):
        resp = VerifyCodeStep().go(request_data={'phone': invalid_phone or self.user_info['phone'],
                                                 'verify_code': invalid_verify_code or self.user_info['verify_code']},
                                   token=invalid_token or self.token)
        self.assertEqual(resp[0].status_code, 200)
        self.assertEqual(resp[0].data.get('code'), 0)
        self.assertEqual(resp[0].data.get('message'), '短信验证成功')

    def set_id_card_url(self, id_card_front_url=None, id_card_back_url=None):
        resp = GetQiniuUpTokenStep().go()
        self.assertEqual(resp[0].status_code, 200)
        self.user_info['id_card_front_url'] = id_card_front_url or DEFUALT_IMAGE_URL
        self.user_info['id_card_back_url'] = id_card_back_url or DEFUALT_IMAGE_URL

    def create(self, invalid_user_info=None, invalid_token=None):
        resp = CreateMarketerStep().go(request_data=invalid_user_info or self.user_info,
                                       token=invalid_token or self.token)
        self.assertEqual(resp[0].status_code, 201)
        self.created_info = resp[0].json()
        return resp[0].json()

    def go(self, unionid=None, name=None, phone=None, id_card_front_url=None, id_card_back_url=None):
        self.login(unionid=unionid)
        self.get_user_info()
        self.web_auth()
        self.set_user_name(name=name)
        self.set_phone(phone=phone)
        self.send_message(id_card_front_url, id_card_back_url)
        self.verify_code()
        self.set_id_card_url()
        self.create()
        return self.token, self.unionid


class GetMerchantAdminWechatInfoWorkflow(WebSocketClientWorkflow):
    def server_callback(self, state=None, code=None, access_token=None, openid=None):
        mock_code = str(uuid.uuid4())
        resp = GetMerchantWechatInfoStep(code=mock_code).go(
            request_data={'code': code or mock_code, 'state': state or self.channel},
            callback_data={'access_token': access_token,
                           'openid': openid},
            extra_res_keys=('unionid', 'openid'))
        self.assertIn('商户绑定成功', resp[0].content.decode('utf8'))

    def go(self, socket_data=None, callback_data=None):
        info = self.client_get_info(socket_data=socket_data, callback_data=callback_data)
        return info


class GetMerchantAdminAlipayInfoWorkflow(WebSocketClientWorkflow):
    def server_callback(self, state=None, code=None, access_token=None, openid=None):
        mock_code = str(uuid.uuid4())
        resp = GetMerchantAlipayInfoStep(code=mock_code).go(
            request_data={'auth_code': code or mock_code, 'state': state or self.channel},
            callback_data={'access_token': access_token},
            extra_res_keys=('user_id', 'nick_name'))
        self.assertIn('绑定支付宝账号成功', resp[0].content.decode('utf8'))

    def go(self, socket_data=None, callback_data=None):
        info = self.client_get_info(socket_data=socket_data, callback_data=callback_data)
        return info


class InviteMerchantWorkflow(BaseInviterWorkflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_info = {}

    def _get_merchant_category(self):
        return GetCategoryStep().go(token=self.token)

    @staticmethod
    def _get_sub_cate_list(categories):
        sub_list = []
        for root in categories:
            for sub in root['children']:
                sub_list.append(sub)
        return sub_list

    def choose_category(self, category_id=None):
        if category_id:
            return category_id
        get_cate_resp = self._get_merchant_category()
        self.assertEqual(get_cate_resp[0].status_code, 200)
        categories_list = self._get_sub_cate_list(get_cate_resp[0].data)
        return random.choice(categories_list)['id']

    def set_merchant_name(self, name=None):
        self.create_info['name'] = name or fake.company()

    def set_category(self, category_id=None):
        self.create_info['category_id'] = self.choose_category(category_id=category_id)

    def set_phone(self, contact_phone=None):
        self.create_info['contact_phone'] = contact_phone or fake.phone_number()

    def set_location(self, address_info=None):
        address_info = address_info or {}
        adcode = address_info.get('adcode', 110105004000)
        resp = CheckMarketerStep().go(request_data={'adcode': adcode})
        self.assertEqual(resp[0].status_code, 200)
        self.assertNotEqual(resp[0].data.get('code'), AREA_STATUS_CODE['DISABLE'])
        self.create_info['area_id'] = adcode
        self.create_info['address'] = address_info.get('address', '北京市朝阳区三里屯太古里')
        self.create_info['location_lon'] = address_info.get('location_lon', 102)
        self.create_info['location_lat'] = address_info.get('location_lat', 27)

    def set_avatar_url(self, avatar_url=None):
        self.create_info['avatar_url'] = avatar_url or DEFUALT_IMAGE_URL

    def set_photo_url(self, photo_url=None):
        self.create_info['photo_url'] = photo_url or DEFUALT_IMAGE_URL

    def set_description(self, description=None):
        self.create_info['description'] = description or '这是一段测试的代码，测试商户的描述，这一段是商户描述。'

    def set_license_url(self, license_url=None):
        self.create_info['license_url'] = license_url or DEFUALT_IMAGE_URL

    def set_id_card_url(self, id_card_front_url=None, id_card_back_url=None):
        self.create_info['id_card_front_url'] = id_card_front_url or DEFUALT_IMAGE_URL
        self.create_info['id_card_back_url'] = id_card_back_url or DEFUALT_IMAGE_URL

    def bind_payment_qr_code(self, payment_qr_code=None):
        payment_qr_code = payment_qr_code or CreateQrCodeStep.create_qr_code()
        resp = CheckCodeStep().go(request_data={'code': payment_qr_code}, token=self.token)
        self.assertEqual(resp[0].status_code, 200)
        self.assertEqual(resp[0].data.get('code'), PAYMENT_QR_CODE_STATUS['CAN_USE'])
        self.assertEqual(resp[0].data.get('message'), '可以使用')
        self.create_info['payment_qr_code'] = payment_qr_code

    def get_merchant_admin_wechat_info(self):
        wechat_info = GetMerchantAdminWechatInfoWorkflow(channel=random.random(), token=self.token).go()
        resp = CheckAdminExistStep().go(request_data={'unionid': wechat_info['unionid']}, token=self.token)
        self.assertEqual(resp[0].status_code, 200)
        self.assertNotEqual(resp[0].data.get('code'), -1)
        self.create_info['merchant_admin_data'] = dict(wechat_openid=wechat_info['openid'],
                                                       wechat_unionid=wechat_info['unionid'],
                                                       wechat_avatar_url=wechat_info['headimgurl'],
                                                       wechat_nickname=wechat_info['nickname'])

    def get_merchant_admin_alipay_info(self):
        alipay_info = GetMerchantAdminAlipayInfoWorkflow(channel=random.random(), token=self.token).go()
        self.create_info['merchant_admin_data'].update(alipay_userid=alipay_info['user_id'],
                                                       alipay_user_name=alipay_info['nick_name'])

    def set_merchant_acct_data(self, merchant_acct_data=None):
        self.create_info['merchant_acct_data'] = merchant_acct_data or {}

    def submit(self):
        resp = CreateMerchantStep().go(request_data=self.create_info)
        self.assertEqual(resp[0].status_code, 201)
        return resp

    def go(self, address_info=None, merchant_name=None, merchant_phone=None,
            avatar_url=None, photo_url=None, description=None, license_url=None,
           id_card_front_url=None, id_card_back_url=None, merchant_acct_data=None
           ):
        self.set_category()
        self.set_merchant_name(merchant_name)
        self.set_phone(merchant_phone)
        self.set_location(address_info)
        self.set_avatar_url(avatar_url)
        self.set_photo_url(photo_url)
        self.set_description(description)
        self.set_license_url(license_url)
        self.set_id_card_url(id_card_front_url, id_card_back_url)
        self.bind_payment_qr_code()
        self.get_merchant_admin_wechat_info()
        self.get_merchant_admin_alipay_info()
        self.set_merchant_acct_data(merchant_acct_data)
        return self.submit()


class AuditMerchantWorkflow(BaseInviterWorkflow):
    def __init__(self, merchant_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.merchant_id = merchant_id

    def go(self, to_status, audit_info=None, merchant_id=None, token=None):
        request_data = {'status': to_status, 'audit_info': audit_info} if audit_info else {'status': to_status}
        resp = AuditMerchantStep(instance_pk=merchant_id or self.merchant_id).go(
            request_data=request_data, token=token or self.token)
        return resp
