from django.conf.urls import url

from config import SUBSCRIPTION_ACCOUNT_REPLY_TYPE
from padmin.views import qiniu
from padmin.views.system_admin import login, logout, me, system_admin_list, system_admin_detail
from padmin.views.menu import MenuView
from padmin.views.merchant_manage import merchant_list, merchant_detail
from padmin.views.merchant_category import merchant_category_list
from padmin.views.message import message_list, message_detail
from padmin.views.financial_manage import (
    data_overview,
    transaction_details,
    sharing_details,
    withdraw_record,
    unliquidated_settlement_list,
    liquidated_settlement_list,
)
from padmin.views.marketer_manage import (
    inviter_list,
    inviter_detail,
    salesman_list,
    salesman_detail,
    areas_list,
    marketer_merchant_list,
    marketer_merchant_ship_list
)
from padmin.views.generate_qrcode import generate_qrcode, generate_sign_qrcode
from padmin.views.subscription_account_reply import (
    reply_user,
    reply_merchant,
    reply_marketer,
    refresh_access_token,
    obtain_access_token,
    push_merchant_month_bill
)
from padmin.views.subscription_account_manage import (
    reply_key_word_list,
    reply_key_word_detail,
    reply_message,
    reply_attention,
)
from padmin.views.timer_manage import timer_generate_settlement_bill

urlpatterns = [
    url(r'^qiniu/uptoken$', qiniu.qiniu_uptoken, name='qiniu_uptoken'),
    url(r'^system_admins/login$', login, name='system-admin-login'),
    url(r'^system_admins/logout$', logout, name='system-admin-logout'),
    url(r'^system_admins/me$', me, name='system-admin-me'),
    url(r'^system_admins/$', system_admin_list, name='system-admin-list'),
    url(r'^system_admins/(?P<pk>[0-9]+)/$', system_admin_detail, name='system-admin-detail'),
    url(r'^menus/$', MenuView.as_view(), name='menu-list'),
    url(r'^merchants/$', merchant_list, name='merchant-list'),
    url(r'^merchants/(?P<pk>[0-9]+)/$', merchant_detail, name='merchant-detail'),
    url(r'^merchant_category/$', merchant_category_list, name='merchant-category-list'),
    url(r'^messages/$', message_list, name='message-list'),
    url(r'^messages/(?P<pk>[0-9]+)/$', message_detail, name='message-detail'),
    url(r'^financial/data_overview/$', data_overview, name='data-overview'),
    url(r'^financial/transaction_details/$', transaction_details, name='transaction-details'),
    url(r'^financial/sharing_details/$', sharing_details, name='sharing-details'),
    url(r'^financial/withdraw_record/$', withdraw_record, name='withdraw-record'),
    url(r'^financial/unliquidated_settlement_list/$', unliquidated_settlement_list, name='unliquidated-settlement-list'),
    url(r'^financial/liquidated_settlement_list/$', liquidated_settlement_list, name='liquidated-settlement-list'),
    url(r'^inviters/$', inviter_list, name='inviter-list'),
    url(r'^inviters/(?P<pk>[0-9]+)/$', inviter_detail, name='inviter-detail'),
    url(r'^salesman/$', salesman_list, name='salesman-list'),
    url(r'^salesman/(?P<pk>[0-9]+)/$', salesman_detail, name='salesman-detail'),
    url(r'^areas/$', areas_list, name='areas-list'),
    url(r'^marketer_merchants/$', marketer_merchant_list, name='marketer-merchants-list'),
    url(r'^merchants_auditors_ship/$', marketer_merchant_ship_list, name='marketer-merchants-ship-list'),
    url(r'^qrcode/', generate_qrcode, name='qrcode-generate'),
    url(r'^merchant_qrcode/', generate_sign_qrcode, name='merchant-qrcode-generate'),
    url(r'^wechat/reply/user/$', reply_user, name='reply-user'),
    url(r'^wechat/reply/merchant/$', reply_merchant, name='reply-merchant'),
    url(r'^wechat/reply/marketer/$', reply_marketer, name='reply-marketer'),
    url(r'^wechat/access_token/refresh$', refresh_access_token, name='refresh-access-token'),
    url(r'^wechat/access_token/obtain$', obtain_access_token, name='obtain-access-token'),
    url(r'^wechat/push_merchant_month_bill', push_merchant_month_bill, name='push-merchant-month-bill'),
    url(r'^subscriptions/reply/key_word/(?P<pk>[0-9]+)/$', reply_key_word_detail,
        name='reply-key-word-detail'),
    url(r'^subscriptions/reply/key_word/', reply_key_word_list, name='subscription-reply-list'),
    url(r'^subscriptions/reply/message/$',
        reply_message,
        kwargs={"reply_type": SUBSCRIPTION_ACCOUNT_REPLY_TYPE['RECEIVED']},
        name='reply-message'
        ),
    url(r'^subscriptions/reply/attention/$',
        reply_attention,
        kwargs={"reply_type": SUBSCRIPTION_ACCOUNT_REPLY_TYPE['BE_PAID_ATTENTION']},
        name='reply-attention'
        ),
    url(r'^timer/generate_settlement_bill', timer_generate_settlement_bill, name='timer-generate-settlement-bill'),
]
