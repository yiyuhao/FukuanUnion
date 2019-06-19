from django.conf.urls import url
from django.urls import include
from rest_framework import routers

from marketer.views.account import GetAccountWithdrawableBalanceView
from marketer.views.marketer import CheckAreaMarketerView, GetUserInfoView, MarketerLoginView, \
    MarketerRegisterViewSet, UpdateMarketerInfoView, marketer_msg_send, \
    marketer_withdraw, marketer_msg_verify, get_marketer_wechat_info, \
    authenticated_marketer_msg_send, CheckPhoneExistView, check_alipay_account
from marketer.views.merchant import ShowInvitedMerchantsViewSet, ShowToBeAuditedMerchant, \
    CreateMerchantViewSet, \
    get_merchant_wechat_info, GetAllMerchantCategory, GetMerchantDetailsViewSet, \
    AuditMerchantViewSet, \
    CheckPaymentQRCodeView, CheckAdminExistView, get_merchant_alipay_info, VerifyAccountView
from marketer.views.transaction import ShowOperationsViewSet

router = routers.DefaultRouter()
router.register('create-merchant', CreateMerchantViewSet, base_name='create-merchant')
router.register('create-marketer', MarketerRegisterViewSet, base_name='create-marketer')
router.register('invited-merchants', ShowInvitedMerchantsViewSet, base_name='invited-merchants')
router.register('show-audited', ShowToBeAuditedMerchant, base_name='show-audited')
router.register('show-operation', ShowOperationsViewSet, base_name='show-operation')
router.register('merchant-details', GetMerchantDetailsViewSet, base_name='merchant-details')
router.register('audit-merchant', AuditMerchantViewSet, base_name='audit-merchant')

urlpatterns = [
    url(r'^get-category/$', GetAllMerchantCategory.as_view(), name='get-category'),
    url(r'^has_marketer/$', CheckAreaMarketerView.as_view(), name='has_marketer'),
    url(r'^login/$', MarketerLoginView.as_view(), name='login'),
    url(r'^get-info/$', GetUserInfoView.as_view(), name='get-info'),
    url(r'^login/', MarketerLoginView.as_view(), name='login'),  # TODO 是否重复?
    url(r'^message-send/', marketer_msg_send, name='message-send'),
    url(r'^authenticated-message-send/', authenticated_marketer_msg_send,
        name='authenticated-message-send'),
    url(r'^sms-code-verify/', marketer_msg_verify, name='sms-code-verify'),
    url(r'^get-marketer-wechat-info/', get_marketer_wechat_info, name='get-marketer-wechat-info'),
    url(r'^get-merchant-wechat-info/', get_merchant_wechat_info, name='get-merchant-wechat-info'),
    url(r'^get-merchant-alipay-info/', get_merchant_alipay_info, name='get-merchant-alipay-info'),
    url(r'^check-code/$', CheckPaymentQRCodeView.as_view(), name='check-code'),
    url(r'^check-admin/$', CheckAdminExistView.as_view(), name='check-admin'),
    url(r'^marketer-withdraw/$', marketer_withdraw, name='marketer-withdraw'),
    url(r'^alipay-account-check/$', check_alipay_account, name='alipay-account-check'),
    url(r'^get-balance/$', GetAccountWithdrawableBalanceView.as_view(), name='get-balance'),
    url(r'^update-marketer/$', UpdateMarketerInfoView.as_view(), name='update-marketer'),
    url(r'^check-phone/$', CheckPhoneExistView.as_view(), name='check-phone'),
    url(r'^verify-account/$', VerifyAccountView.as_view(), name='verify-account'),
    url(r'^', include(router.urls)),
]
