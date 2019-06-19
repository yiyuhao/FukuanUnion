import logging

from django.db.models import Q
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import mixins, viewsets, views, status

from common.models import Merchant
from common.auth.wechat.web_auth import WeChantWebAuthHandler
from common.auth.alipay.web_auth import AlipayWebAuthHandler
from common.model_manager.merchant_category_manager import MerchantCategoryModelManager
from marketer.serializers.merchant import MerchantSerializer
from marketer.serializers.merchant import CreateMerchantSerializer, MerchantDetailSerializer, AuditMerchantSerializer
from marketer.serializers.account import VerifyAccountSerializer
from marketer.utils.auth import MarketerAuthentication
from marketer.utils.pagenations import BasePagination
from marketer.model_manager import UserMerchantModelManager, PaymentQRCodeModelManager, MerchantAdminModelManager, \
    MerchantMessageManager
from dynaconf import settings as dynasettings
from marketer.exceptions import CreateErrorException, InvalidParamsException
from marketer.utils.verify_account_handler import VerifyAccountHandler
from ws_service.utils import PublishToRedisChannel
import config
from marketer.utils.redis_utils import VerifyAccountLimitRecord

ENV = dynasettings.ENV
app_id = dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_MERCHANT if ENV != 'dev' else dynasettings.SUBSCRIPTION_ACCOUNT_APP_ID_USER
app_secret = dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_MERCHANT if ENV != 'dev' else dynasettings.SUBSCRIPTION_ACCOUNT_SECRET_USER
logger = logging.getLogger(__name__)


class CreateMerchantViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    create:
        创建商铺
    """
    serializer_class = CreateMerchantSerializer
    authentication_classes = [MarketerAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            merchant = serializer.save()
        except CreateErrorException as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=dict(message=e.message))
        merchant_msg_manager = MerchantMessageManager(merchant=merchant)
        merchant_msg_manager.merchant_wait_to_be_audit()
        headers = self.get_success_headers(serializer.data)
        try:
            VerifyAccountLimitRecord.decr_record_request(self.request.user.wechat_unionid)
        except Exception as e:
            return Response({'data': serializer.data, 'other_info': e},
                            status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ShowInvitedMerchantsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list:
        获取被邀请商户
    """

    def get_queryset(self):
        merchant_status = self.request.query_params.get('merchant_status')
        if not merchant_status:
            return Merchant.objects.filter(inviter=self.request.user)
        if merchant_status == 'using':
            merchant_status = (config.MERCHANT_STATUS.USING,)
        if merchant_status == 'reviewing':
            merchant_status = (config.MERCHANT_STATUS.REVIEWING, config.MERCHANT_STATUS.REJECTED)
        return Merchant.objects.filter(inviter=self.request.user, status__in=merchant_status).order_by(
            '-update_datetime')

    serializer_class = MerchantSerializer
    pagination_class = BasePagination
    authentication_classes = [MarketerAuthentication]


class ShowToBeAuditedMerchant(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list:
        获取待审核商户
    """

    def get_queryset(self):
        manager = UserMerchantModelManager(user=self.request.user)
        merchant_status = self.request.query_params.get('merchant_status')
        if not merchant_status:
            return manager.get_auditor_merchants()
        if merchant_status == 'reviewing':
            merchant_status = config.MERCHANT_STATUS.REVIEWING
        if merchant_status == 'using':
            merchant_status = config.MERCHANT_STATUS.USING
        return manager.get_auditor_merchants(merchant_status)

    serializer_class = MerchantSerializer
    pagination_class = BasePagination
    authentication_classes = [MarketerAuthentication]


class AuditMerchantViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    list:
        审核店铺
    """
    serializer_class = AuditMerchantSerializer
    authentication_classes = [MarketerAuthentication]

    def get_queryset(self):
        manager = UserMerchantModelManager(self.request.user)
        return manager.get_to_be_audit_merchant()

    def perform_update(self, serializer):
        merchant = serializer.save()
        merchant_msg_manager = MerchantMessageManager(merchant=merchant)
        merchant_msg_manager.merchant_audited()


class GetMerchantWechatInfo(viewsets.ViewSet):
    """
    微信授权回调 接收wechat code 根据code获取 access_token
    """

    def wechat_auth_redirect(self, request):
        """
        接收回调url的code和参数state, 这里state是channels_key
        """
        code = request.query_params.get('code', '')
        state = request.query_params.get('state', '')

        wechat_auth_handler = WeChantWebAuthHandler(
            app_id=app_id,
            app_secret=app_secret
        )
        access_token, openid = wechat_auth_handler.gen_access_token(code=code)
        user_info = wechat_auth_handler.gen_user_info(access_token, openid)

        user_info['channel_key'] = state

        # 将获取到的数据发送到 websocket
        res = PublishToRedisChannel.publish_to_channel(data=user_info)

        ma_handler = MerchantAdminModelManager()
        if res.get('message') == 'success' and \
                not ma_handler.can_create(user_info.get('unionid')):
            return render(request, 'auth_web/auth_ok.html', {
                'title': "邀请商户",
                'auth_type': "create_merchant",
            })
        elif ma_handler.can_create(user_info.get('unionid')):
            admin_type = ma_handler.check_admin_type(user_info.get('unionid'))
            logger.info(f"{user_info['nickname']} 已经是{admin_type}")
            return render(request, 'auth_web/auth_error.html', {
                'title': "邀请商户",
                'info': f"{user_info.get('nickname')}已经注册为{admin_type}"})
        else:
            return render(request, 'auth_web/auth_error.html', {
                'title': "邀请商户", 'info': "邀请失败,请重试"})


class GetMerchantAlipayInfo(viewsets.ViewSet):
    """
    支付宝授权回调 接收alipay auth_code
    """

    def alipay_auth_redirect(self, request):
        """
        接收回调url的code和参数state, 这里state是channels_key
        """
        auth_code = request.query_params.get('auth_code', '')
        state = request.query_params.get('state', '')

        alipay_auth_handler = AlipayWebAuthHandler()
        access_token = alipay_auth_handler.gen_alipay_access_token(
            code=auth_code)
        user_info = alipay_auth_handler.gen_alipay_user_info(access_token)

        user_info['channel_key'] = state

        # 将获取到的数据发送到 websocket
        res = PublishToRedisChannel.publish_to_channel(data=user_info)

        if res.get('message') == 'success' and user_info.get('msg') == 'Success':
            return render(request, 'auth_web/auth_ok.html', {
                'title': "商户管理员",
                'auth_type': "bind_alipay_account",
                'avatar': user_info['avatar'],
                'nick_name': user_info['nick_name']
            })
        else:
            return render(request, 'auth_web/auth_error.html', {
                'title': "商户管理员", 'info': "绑定失败,请重试"})


class GetAllMerchantCategory(views.APIView):
    """获取店铺类别"""

    def get(self, request):
        manager = MerchantCategoryModelManager()
        return Response(data=manager.list_categories(), status=status.HTTP_200_OK)


class GetMerchantDetailsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """获取商户详情"""

    def get_queryset(self):
        queryset = Merchant.objects.filter(Q(inviter=self.request.user) |
                                           Q(area__in=self.request.user.working_areas.all()))
        return queryset

    serializer_class = MerchantDetailSerializer
    authentication_classes = [MarketerAuthentication]


class CheckPaymentQRCodeView(views.APIView):
    """验证付款码是否可用"""
    authentication_classes = [MarketerAuthentication]

    def get(self, request):
        manager = PaymentQRCodeModelManager()
        res = manager.can_use(self.request.query_params.get('code'))
        number = None if not res[1] else 'NO.%04d' % res[1].id
        return Response(status=status.HTTP_200_OK, data=dict(code=res[0], message=res[2], number=number))


class   CheckAdminExistView(views.APIView):
    """验证管理员是否存在"""
    authentication_classes = [MarketerAuthentication]

    def get(self, request):
        manager = MerchantAdminModelManager()
        if manager.can_create(unionid=self.request.query_params.get('unionid')):
            return Response(status=status.HTTP_200_OK, data=dict(code=-1, message='该用户为商户管理员或收银员'))
        else:
            return Response(status=status.HTTP_200_OK, data=dict(code=1, message='可以成为管理员'))


class VerifyAccountView(views.APIView):
    """验证银行账号信息"""
    authentication_classes = [MarketerAuthentication]

    def post(self, request):
        """发送验证请求"""
        serializer = VerifyAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = VerifyAccountHandler(user=self.request.user, params=serializer.data).verify_account()
        return Response(status=status.HTTP_200_OK, data=res)

    def get(self, request):
        """查询验证结果"""
        if not self.request.query_params.get('id'):
            raise InvalidParamsException('未获取到id')
        res = VerifyAccountHandler(user=self.request.user, params=self.request.query_params).get_result()
        return Response(status=status.HTTP_200_OK, data=res)


get_merchant_wechat_info = GetMerchantWechatInfo.as_view({
    'get': 'wechat_auth_redirect',
})
get_merchant_alipay_info = GetMerchantAlipayInfo.as_view({
    'get': 'alipay_auth_redirect',
})
