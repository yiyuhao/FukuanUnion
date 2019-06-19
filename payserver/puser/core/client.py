# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from dynaconf import settings as dynasettings

import config
from common import weixin_login
from common.alipay_login import AlipaySession, LoginError
from common.doclink.alipay_apis import AlipayApis
from common.doclink.exceptions import ApiRequestError, ApiReturnedError
from common.models import Client
from puser import consts


class DbManager:
    @classmethod
    def get_or_create_client_with_weixin_id(cls, openid, unionid):
        unionid = unionid or ''

        client, _ = Client.objects.get_or_create(
            openid=openid,
            defaults={'wechat_unionid': unionid,
                      'openid_channel': config.PAY_CHANNELS.WECHAT})

        return client

    @classmethod
    def get_or_create_client_with_alipay_user_id(cls, user_id):
        client, _ = Client.objects.get_or_create(
            openid=user_id,
            defaults={'openid_channel': config.PAY_CHANNELS.ALIPAY})

        return client


class UseCase:
    flow_cls = weixin_login.LoginFlow
    alipay_api_cls = AlipayApis
    dbManager = DbManager

    @classmethod
    def wechat_login(cls, code, token_session):
        if not token_session.is_empty():
            token_session.flush()

        login_flow = cls.flow_cls(consts.appid, consts.app_secret)
        login_flow.jscode2session(code)
        login_flow.save(token_session)

        weixin_session = login_flow.weixin_session

        client = cls.dbManager.get_or_create_client_with_weixin_id(
            weixin_session.openid,
            weixin_session.unionid)

        token_session['client_id'] = client.id
        token_session['weixin_session'] = weixin_session

        return {'token': token_session.token,
                'client': client}

    @classmethod
    def alipay_login(cls, code, token_session):
        alipay_app_id = dynasettings.ALIPAY_APP_ID
        alipay_private_key = dynasettings.ALIPAY_APP_PRIVATE_KEY
        alipay_public_key = dynasettings.ALIPAY_PUBLIC_KEY

        if not token_session.is_empty():
            token_session.flush()

        alipay_api_instance = cls.alipay_api_cls(alipay_app_id, alipay_private_key,
                                                 alipay_public_key)
        try:
            access_token = alipay_api_instance.exchange_access_token(code)
        except ApiRequestError:
            raise LoginError()
        except ApiReturnedError:
            raise LoginError()

        access_token.pop('alipay_user_id', None)
        alipay_session = AlipaySession(**access_token)

        client = cls.dbManager.get_or_create_client_with_alipay_user_id(alipay_session.user_id)

        token_session['client_id'] = client.id
        token_session['alipay_session'] = alipay_session
        token_session.create_token()

        return {'token': token_session.token,
                'client': client}

    @classmethod
    def set_client_phone(cls, client, phone):
        client.phone = phone
        client.save()
