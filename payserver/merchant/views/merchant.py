#      File: merchant.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/6/15
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

import logging
import time

from ipware import get_client_ip
from rest_framework import permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.model_manager.account_manager import AccountManager
from common.model_manager.area_manager import AreaModelManager
from common.model_manager.merchant_admin_manager import MerchantAdminManager
from common.model_manager.merchant_category_manager import MerchantCategoryModelManager
from common.model_manager.merchant_manager import MerchantManager
from common.models import Merchant
from config import PAY_CHANNELS, MerchantMiniProgram
from marketer.model_manager import MerchantMessageManager
from merchant.auth import MerchantAdminAuthentication
from merchant.permissions import NotDisabled, is_merchant_admin, merchant_is_rejected, merchant_is_using, \
    merchant_is_using_or_rejected
from merchant.serializers import MerchantAuthSerializer, LoginSerializer, MerchantDatetimeFilterSerializer, \
    MerchantWithdrawSerializer, MerchantSerializer, MerchantDayBeginMinuteSerializer, MerchantListEarningSerializer, \
    MerchantAdminVoiceOnSerializer

logger = logging.getLogger(__name__)


class MerchantViewSet(GenericViewSet):
    queryset = Merchant.objects.all()
    authentication_classes = [MerchantAdminAuthentication]
    permission_classes = [NotDisabled]

    @action(detail=False, url_name='statistics')
    def statistics(self, request):
        """首页 商户名|商户状态|头像|余额| 今日营业额|引流收益|付款单数|引流支出"""

        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        data = dict(
            name=merchant.name,
            status=merchant.status,
            avatar_url=merchant.avatar_url,
            wechat_balance=merchant.account_wechat_balance,
            alipay_balance=merchant.account_alipay_balance,
        )
        data.update(merchant.today_business_report())

        return Response(status=status.HTTP_200_OK, data=data)

    @action(detail=False, url_name='business_report')
    def business_report(self, request):
        """首页 按照时间统计(券领取数/券使用数/营业额/引流收益 付款单数 营业额按天list)"""

        query_params = dict(
            start_date=request.GET.get('start_date'),
            end_date=request.GET.get('end_date'),
        )

        serializer = MerchantDatetimeFilterSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        datetime_start = serializer.validated_data['start_date']
        datetime_end = serializer.validated_data['end_date']

        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        data = merchant.merchant_business_report(datetime_start, datetime_end)

        return Response(status=status.HTTP_200_OK, data=data)

    @action(detail=False, url_name='list_earning')
    def list_earning(self, request):
        """商户一年内每日净利润"""

        query_params = dict(
            start_date=request.GET.get('start_date'),
        )

        serializer = MerchantListEarningSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        date_start = serializer.validated_data['start_date']

        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        earning = merchant.merchant_earning_list_by_day(date_start=date_start)

        return Response(status=status.HTTP_200_OK, data=earning)

    @action(detail=False, url_name='info')
    def info(self, request):
        """我的店铺 商户名/银行卡号/收款员账户数量/营业时间 """

        merchant = request.user.work_merchant
        merchant = MerchantManager(merchant)

        return Response(
            status=status.HTTP_200_OK,
            data=dict(
                name=merchant.name,
                avatar_url=merchant.avatar_url,
                employer_num=merchant.employer_num,
                day_begin_minute=merchant.day_begin_minute,
            )
        )

    @merchant_is_using
    @action(detail=False, methods=['PUT'], url_name='day-begin-minute')
    def day_begin_minute(self, request):
        """修改营业开始时间"""

        merchant = request.user.work_merchant
        old_day_begin_minute = merchant.day_begin_minute

        serializer = MerchantDayBeginMinuteSerializer(merchant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'modified day_begin_minute from {old_day_begin_minute} to {merchant.day_begin_minute})')

        return Response(serializer.data)

    @is_merchant_admin
    @merchant_is_using_or_rejected
    @action(detail=False, url_name='me')
    def me(self, request):
        """商铺具体信息"""

        merchant = request.user.work_merchant
        serializer = MerchantSerializer(merchant)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )

    @is_merchant_admin
    @merchant_is_rejected
    @action(detail=False, methods=['PUT'], url_name='modify')
    def modify(self, request):
        """修改商户具体信息"""
        merchant = request.user.work_merchant

        serializer = MerchantSerializer(merchant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'merchant({merchant.id, merchant.name} '
                    f'modified merchant detail  to {serializer.data})')

        merchant_msg_manager = MerchantMessageManager(merchant=merchant)
        merchant_msg_manager.to_marketer()

        return Response(serializer.data)

    @merchant_is_using_or_rejected
    @action(detail=False, url_name='category')
    def category(self, request):
        """获取商户分类"""
        manager = MerchantCategoryModelManager()
        categories = manager.list_categories()
        return Response(
            status=status.HTTP_200_OK,
            data=categories
        )

    @merchant_is_using
    @action(detail=False, url_name='area')
    def area(self, request):
        """获取商戶地区分级"""
        manager = AreaModelManager()
        areas = manager.list_areas()
        return Response(
            status=status.HTTP_200_OK,
            data=areas
        )

    @merchant_is_using
    @is_merchant_admin
    @action(detail=False, url_name='balance')
    def balance(self, request):
        merchant = MerchantManager(request.user.work_merchant)
        merchant_admin = MerchantAdminManager(request.user)

        return Response(
            status=status.HTTP_200_OK,
            data=dict(
                wechat_balance=merchant.account_wechat_balance,
                wechat_withdrawable_balance=merchant.account_wechat_withdraw_balance,
                alipay_balance=merchant.account_alipay_balance,
                alipay_withdrawable_balance=merchant.account_alipay_withdraw_balance,
                wechat_nickname=merchant_admin.wechat_nickname,
                alipay_user_name=merchant_admin.alipay_user_name,
            )
        )

    @merchant_is_using
    @is_merchant_admin
    @action(detail=False, methods=['PUT'], url_name='withdraw')
    def withdraw(self, request):
        merchant = request.user.work_merchant
        client_ip, _ = get_client_ip(request._request)

        logger.info(f'merchant({merchant.id, merchant.name, client_ip} requested a withdraw: {request.data}')

        serializer = MerchantWithdrawSerializer(merchant.account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        manager = AccountManager(merchant.account)

        if request.data['channel'] == PAY_CHANNELS.WECHAT:
            withdraw_error = manager.wechat_withdraw(serializer.validated_data['amount'], client_ip)
        else:
            withdraw_error = manager.alipay_withdraw(serializer.validated_data['amount'])

        logger.info(f'merchant({merchant.id, merchant.name, client_ip} withdraw error is {withdraw_error}')

        return Response(status=status.HTTP_200_OK, data=withdraw_error or {})

    @action(detail=False, url_name='auth')
    def auth(self, request):
        """for testing authentication module"""
        serializer = MerchantAuthSerializer(request.user.work_merchant)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data)

    @merchant_is_using
    @action(detail=False, methods=['PUT'], url_name='voice-on')
    def voice_on(self, request):
        """修改merchant_admin语音播报开关"""

        merchant_admin = request.user

        old_voice_on = merchant_admin.voice_on

        serializer = MerchantAdminVoiceOnSerializer(merchant_admin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f'merchant_admin (id: {merchant_admin.id}, union_id:{merchant_admin.wechat_unionid}'
                    f'modified voice_on from {old_voice_on} to {merchant_admin.voice_on})')

        return Response(serializer.data)


class MerchantLoginViewSet(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merchant = serializer.user.work_merchant

        logger.info(f'merchant_admin({serializer.user.id, serializer.user.wechat_nickname}) '
                    f'which worked in work_merchant({merchant.id, merchant.name}), '
                    f'logged in successfully')

        return Response(
            status=status.HTTP_200_OK,
            data=dict(
                token=serializer.token,
                token_expiration_time=int(time.time()) + MerchantMiniProgram.user_token_expiration_time,
                merchant_id=merchant.id,
                merchant_admin_type=serializer.user.merchant_admin_type,
                merchant_admin_status=serializer.user.status,
                merchant_status=merchant.status,
                merchant_type=merchant.type,
                voice_on=serializer.user.voice_on,
                payment_qr_code_uuid=merchant.payment_qr_code.uuid,
                payment_qr_code_id=merchant.payment_qr_code_id,
                address=merchant.address,
            )
        )
