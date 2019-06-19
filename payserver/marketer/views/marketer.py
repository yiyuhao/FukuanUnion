import json
import logging

from django.shortcuts import render
from django.utils import timezone
from dynaconf import settings as dynasettings
from ipware import get_client_ip
from rest_framework import mixins, viewsets, status, views
from rest_framework.response import Response

from common.auth.wechat.web_auth import WeChantWebAuthHandler
from common.model_manager.account_manager import AccountManager
from common.model_manager.marketer_manager import MarketerModelManager
from common.model_manager.transfer_record_manager import TransferRecordManager
from common.msg_service.sms_send import SendMessageApi, VerifySmsCode
from config import PAY_CHANNELS
from marketer.config import PHONE_CODE_STATUS, AREA_STATUS_CODE, \
    UNIONID_LIMIT, MAX_REQUEST_ONE_DAY, ALIPAY_VERIFY_TRANSFER_AMOUNT
from marketer.model_manager import AreaModelManager
from marketer.serializers.account import MarketerWithdrawSerializer
from marketer.serializers.marketer import CreateMarketerBaseSerializer, \
    UpdateMarketerSerializer
from marketer.serializers.nested_serializers import MarketerLoginSerializer
from marketer.utils.auth import MarketerRegisterAuthentication, \
    MarketerAuthentication
from marketer.utils.redis_utils import RedisUtil

ENV = dynasettings.ENV

dynasettings.configure()
dynasettings.namespace('PAYUNION')
app_id = dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MARKETER if ENV != 'dev' else dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_USER
app_secret = dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_MARKETER if ENV != 'dev' else dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_USER
logger = logging.getLogger(__file__)


class MarketerLoginView(views.APIView):
    """
    登陆
    """

    def post(self, request):
        serializer = MarketerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            status=status.HTTP_200_OK,
            data=dict(token=serializer.token)
        )


class MarketerRegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    create:
        Register marketer
    """
    serializer_class = CreateMarketerBaseSerializer
    authentication_classes = [MarketerRegisterAuthentication]


class MarketerWithdrawViewSet(viewsets.GenericViewSet):
    """ 邀请人/业务员 账户余额提现 """

    authentication_classes = [MarketerAuthentication]

    @staticmethod
    def withdraw(request):
        """ 提现 """
        marketer = request.user
        client_ip, _ = get_client_ip(request._request)

        logger.info(
            f'merchant({marketer.id, marketer.name, client_ip} '
            f'requested a withdraw: {request.data}')

        serializer = MarketerWithdrawSerializer(marketer.account,
                                                data=request.data,
                                                partial=True)
        serializer.is_valid(raise_exception=True)

        manager = AccountManager(marketer.account)

        if request.data['channel'] == PAY_CHANNELS.WECHAT:
            withdraw_error = manager.wechat_withdraw(
                serializer.validated_data['amount'],
                client_ip,
                dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MARKETER
            )
        else:
            withdraw_error = manager.alipay_withdraw(
                serializer.validated_data['amount'])

        logger.info(
            f'marketer ({marketer.id, marketer.name, client_ip} '
            f'withdraw error is {withdraw_error}')

        return Response(status=status.HTTP_200_OK, data=withdraw_error or {})


class CheckAreaMarketerView(views.APIView):
    """验证区域是否存在业务员"""

    def get(self, request):
        adcode = self.request.query_params.get('adcode')
        manager = AreaModelManager()
        res = manager.has_marketer(adcode=adcode)
        if res:
            if res == 'DISABLE':
                return Response(status=status.HTTP_200_OK,
                                data=dict(code=AREA_STATUS_CODE['DISABLE'],
                                          message='未开放该区域'))
            else:
                return Response(status=status.HTTP_200_OK,
                                data=dict(code=AREA_STATUS_CODE['HAS_MARKETER'],
                                          message='该区域有业务员'))
        else:
            return Response(status=status.HTTP_200_OK,
                            data=dict(code=AREA_STATUS_CODE['NO_MARKETER'],
                                      message='该区域没业务员'))


class GetUserInfoView(views.APIView):
    """获取用户基本信息"""
    authentication_classes = [MarketerAuthentication]

    def get(self, request):
        user = self.request.user
        if user:
            manager = MarketerModelManager()
            user_info = manager.get_user_info(self.request.user.wechat_unionid)
            return Response(status=status.HTTP_200_OK, data=user_info)
        else:
            return Response(status=status.HTTP_200_OK, data=dict(
                user_name=None,
                user_phone=None,
                user_status='not_register',
                user_type=None,
                using_invited_merchants_num=0,
                reviewing_invited_merchants_num=0,
                total_bonus=0,
                user_withdrawable_balance=0,
                alipay_withdraw_balance=0,
                wechat_withdraw_balance=0
            ))


class MarketerSendMessageViewSet(viewsets.ViewSet):
    """ 邀请人、业务员 发短信 """
    authentication_classes = [MarketerRegisterAuthentication]

    def msg_send(self, request):
        # 发送短信验证码
        unionid = request.user.get('unionid')
        phone = request.data.get('phone')
        send_msg_api = SendMessageApi(phone=phone, wechat_unionid=unionid)
        result = send_msg_api.message_send()
        return Response(status=status.HTTP_200_OK, data=result)


class AuthenticatedMarketerSendMessageViewSet(viewsets.ViewSet):
    authentication_classes = [MarketerAuthentication]

    def msg_send(self, request):
        # 发送短信验证码
        user = request.user
        phone = request.data.get('phone')
        send_msg_api = SendMessageApi(phone=phone,
                                      wechat_unionid=user.wechat_unionid)
        result = send_msg_api.message_send()
        return Response(status=status.HTTP_200_OK, data=result)


class VerifySmsCodeViewSet(viewsets.ViewSet):
    """ 验证短信验证码 """
    authentication_classes = [MarketerAuthentication]

    def verfy_sms_code(self, request):
        phone = request.data.get('phone')
        verify_code = request.data.get('verify_code')
        verify_instace = VerifySmsCode(phone=phone, verify_code=verify_code)
        data = {'code': 0, 'message': "短信验证成功"}
        if not verify_instace.verify():
            data = {'code': -1, 'message': "验证码输入错误，请重新输入"}
        return Response(status=status.HTTP_200_OK, data=data)


class GetMarketerWechatInfo(viewsets.ViewSet):
    """
    微信授权回调 接收wechat code 根据code获取 access_token
    1、授权成功，先创建业务员／邀请人
    2、网页展示授权状态
    """

    def wechat_auth_redirect(self, request):
        code = request.query_params.get('code', '')

        wechat_auth_handler = WeChantWebAuthHandler(app_id=app_id,
                                                    app_secret=app_secret)
        access_token, openid = wechat_auth_handler.gen_access_token(code=code)
        user_info = wechat_auth_handler.gen_user_info(access_token, openid)
        if 'openid' not in user_info:
            user_info['openid'] = openid

        if not user_info.get('unionid'):
            return render(request, 'auth_web/auth_marketer_error.html',
                          {'title': "注册业务员", 'info': "授权异常"})
        if MarketerModelManager.check_marketer_exists(
                unionid=user_info['unionid']):
            logger.info(f"{user_info['nickname']} 该邀请人已经注册")
            return render(request, 'auth_web/auth_marketer_error.html',
                          {'title': "注册业务员", 'info': "该邀请人已经注册"})

        # marketer还没有注册 缓存openid, 昵称，缓存头像
        _user_info = json.dumps(user_info)
        RedisUtil.cache_data(user_info['unionid'], _user_info, data_type='wechat_info')

        return render(request, 'auth_web/auth_marketer.html',
                      {'title': "注册业务员", 'nickname': user_info['nickname']})


class UpdateMarketerInfoView(views.APIView):
    authentication_classes = [MarketerAuthentication]

    def put(self, requeest):
        serializer = UpdateMarketerSerializer(data=self.request.data)
        serializer.is_valid()
        serializer.update(instance=self.request.user,
                          validated_data=serializer.validated_data)
        return Response(status=status.HTTP_202_ACCEPTED,
                        data=serializer.validated_data)


class CheckPhoneExistView(views.APIView):
    def get(self, request):
        manager = MarketerModelManager()
        res = manager.check_phone_exist(self.request.query_params.get('phone'))
        if res:
            data = dict(code=PHONE_CODE_STATUS['EXIST'], message='手机已存在')
        else:
            data = dict(code=PHONE_CODE_STATUS['CAN_USE'], message='可以使用')
        return Response(status=status.HTTP_200_OK, data=data)


class CheckAlipayAccountView(viewsets.ViewSet):
    """ 验证支付宝账号名字是否正确 """
    authentication_classes = [MarketerRegisterAuthentication]

    API_CODE = {
        'SUCCESS_RECORD_NOT_EXIST': -5,
        'PARAMS_ERROR': -4,
        'REQUEST_FREQUENTLY': -3,
        'REQUEST_TOO_MANY': -2,
        'TRANSFER_FAILED': -1,
        'TRANSFER_FINISHED': 0,
        'SUCCESS_RECORD_EXIST': 1
    }

    def show_success_transfer_record(self, request):
        """ 根据unionid查询记录 """
        unionid = request.user.get('unionid')
        res = TransferRecordManager.check_transfer_success(unionid=unionid)
        data = dict(code=self.API_CODE['SUCCESS_RECORD_NOT_EXIST'],
                    message="没有与该unionid对应的成功记录",
                    alipay_data=res['record'])
        if res['exist']:
            data.update(
                code=self.API_CODE['SUCCESS_RECORD_EXIST'],
                message="存在转账成功记录",
                alipay_data=res['record'])
        return Response(status=status.HTTP_200_OK, data=data)

    def check_alipay_account(self, request):
        now = timezone.now()
        timestamp = now.timestamp()
        record_key = now.strftime('%Y_%m_%d')
        unionid = request.user.get('unionid')
        account_number = request.data.get('account_number')
        account_name = request.data.get('account_name')

        # 验证账号、名字不为空
        if not all([account_number, account_name]):
            return Response(status=status.HTTP_200_OK, data=dict(
                code=self.API_CODE['PARAMS_ERROR'],
                message="支付宝账号和姓名必填"
            ))

        # 验证当前接口请求次数
        if RedisUtil.record_request_one_day(record_key) > MAX_REQUEST_ONE_DAY:
            return Response(status=status.HTTP_200_OK, data=dict(
                code=self.API_CODE['REQUEST_TOO_MANY'],
                message="接口服务已达到单日请求上限"
            ))

        # 验证当前微信号请求转账频率
        list_len = RedisUtil.get_request_time_len(unionid=unionid)
        if list_len and list_len >= UNIONID_LIMIT['max_times']:
            oldest_time = RedisUtil.get_oldest_item(unionid=unionid)
            if timestamp < float(oldest_time) + UNIONID_LIMIT['limit_seconds']:
                data = dict(
                    code=self.API_CODE['REQUEST_FREQUENTLY'],
                    message=f"过去7天内已达到上限{UNIONID_LIMIT['max_times']}次"
                )
                return Response(status=status.HTTP_200_OK, data=data)

        # 验证该微信号、支付宝账号、姓名是否有成功转账记录
        check_data = TransferRecordManager.check_transfer_success(
            unionid=unionid,
            account_number=account_number,
            account_name=account_name)

        if check_data['exist']:
            data = dict(code=self.API_CODE['SUCCESS_RECORD_EXIST'],
                        message="存在转账成功记录",
                        alipay_data=check_data['record'])
            return Response(status=status.HTTP_200_OK, data=data)

        # 转账并记录
        errors = TransferRecordManager.transfer_to_account(
            unionid=unionid,
            account_number=account_number,
            account_name=account_name,
            amount=ALIPAY_VERIFY_TRANSFER_AMOUNT
        )

        data = dict(
            code=self.API_CODE['TRANSFER_FAILED'],
            message="支付宝账号或姓名错误",
            alipay_data={}
        )

        if not errors:
            RedisUtil.record_request_one_day(record_key, num_incr=True)
            if list_len + 1 > UNIONID_LIMIT['max_times']:
                RedisUtil.get_oldest_item(unionid=unionid, pop_item=True)
            RedisUtil.cache_request_time(unionid=unionid, time=timestamp)
            data.update(
                code=self.API_CODE['TRANSFER_FINISHED'],
                message="支付宝信息验证成功",
                alipay_data=dict(account_number=account_number,
                                 account_name=account_name)
            )

        return Response(status=status.HTTP_200_OK, data=data)


marketer_withdraw = MarketerWithdrawViewSet.as_view({
    'put': 'withdraw',
})
marketer_msg_send = MarketerSendMessageViewSet.as_view({
    'post': 'msg_send',
})
authenticated_marketer_msg_send = AuthenticatedMarketerSendMessageViewSet.as_view({
    'post': 'msg_send',
})
marketer_msg_verify = VerifySmsCodeViewSet.as_view({
    'post': 'verfy_sms_code',
})
get_marketer_wechat_info = GetMarketerWechatInfo.as_view({
    'get': 'wechat_auth_redirect',
})
check_alipay_account = CheckAlipayAccountView.as_view({
    'get': 'show_success_transfer_record',
    'post': 'check_alipay_account',
})
