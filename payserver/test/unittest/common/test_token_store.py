# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Luo Yufu
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from django.core.cache import cache
import pytest

from common.token_store import TokenStore


@pytest.fixture()
def cache_token():
    cache.set('token_token12345678', 10000)
    yield
    cache.delete('token_token12345678')


def test_cache_key_with_default_namespace_without_token():
    token_store = TokenStore()
    assert (len(token_store.cache_key) > len(token_store.cache_key_prefix) and
            token_store.cache_key_prefix in token_store.cache_key)


def test_cache_key_with_namespace_with_token():
    token_store = TokenStore('token12345678', namespace='client')

    assert token_store.cache_key == 'token_client_token12345678'


@pytest.mark.usefixtures("cache_token")
def test_exists_with_exsit_token():
    token_store = TokenStore('token12345678')
    assert token_store.exists('token12345678')


def test_exists_without_exsit_token():
    token_store = TokenStore('token12345678')
    assert not token_store.exists('token12345678')


def test_create_token_session():
    token_store = TokenStore()
    token_store.create()

    print(f'cache_key: {token_store.cache_key}')
    assert cache.get(token_store.cache_key) == {}
    cache.delete(token_store.cache_key)


def test_update_token_session():
    token_session = TokenStore()
    token_session.create()

    token_session['openid'] = 'openid'
    token_session.save()

    assert cache.get(token_session.cache_key)['openid'] == 'openid'
    cache.delete(token_session.cache_key)


def test_delete_token_session():
    cache.set('token_token12345678', 10000)
    assert cache.get('token_token12345678') is not None

    token_session = TokenStore('token12345678')
    token_session.delete()

    assert cache.get('token_token12345678') is None


def test_get_token_session():
    token_session = TokenStore()
    token_session.create()
    token_session['openid'] = 'openid'
    token_session.save()

    token = token_session.session_key

    new_token_session = TokenStore(token)
    assert new_token_session['openid'] == 'openid'
    assert new_token_session is not token_session

    token_session.delete()


def test_create_token():
    token_session = TokenStore()
    assert token_session.token is None
    token_session.create_token()
    assert token_session.token is not None


def test_token_after_set_namespace():
    token_session = TokenStore()
    token_session.set_namespace('client')

    token_session.create_token()

    assert 'token_client_' in token_session.cache_key
