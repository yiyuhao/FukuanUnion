# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from rest_framework import status

from common.models import SubscriptionAccountReply
from config import (
    SUBSCRIPTION_ACCOUNT_REPLY_STATUS,
    SUBSCRIPTION_ACCOUNT_REPLY_RULE,
    SUBSCRIPTION_ACCOUNT_REPLY_TYPE,
    SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT,
)
from test.api_test.system_admin.AdminSystemTestBase import AdminSystemTestBase
from test.unittest.fake_factory.fake_factory import fake

class SubscriptionAccountManagerTests(AdminSystemTestBase):

    def test_add_user_key_word_reply(self):
        """ 添加用户公众号关键字回复 """

        self.set_login_status()

        partial_key_word = dict(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.PARTIAL,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )

        complete_key_word = dict(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.COMPLETE,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )
        url = f"/api/admin/subscriptions/reply/key_word/?reply_account={SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER}"
        # 半匹配回复
        resp = self.client.post(url, data=partial_key_word)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_data = resp.json()
        query = SubscriptionAccountReply.objects.get(pk=json_data['id'])
        self.assertEqual(query.question_text, partial_key_word['question_text'])
        self.assertEqual(query.question_text, json_data['question_text'])
        self.assertEqual(query.reply_text, partial_key_word['reply_text'])
        self.assertEqual(query.reply_text, json_data['reply_text'])
        self.assertEqual(query.rule_name, partial_key_word['rule_name'])
        self.assertEqual(query.rule_name, json_data['rule_name'])
        # 关键字回复
        resp = self.client.post(url, data=complete_key_word)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_data = resp.json()
        query = SubscriptionAccountReply.objects.get(pk=json_data['id'])
        self.assertEqual(query.question_text, complete_key_word['question_text'])
        self.assertEqual(query.question_text, json_data['question_text'])
        self.assertEqual(query.reply_text, complete_key_word['reply_text'])
        self.assertEqual(query.reply_text, json_data['reply_text'])
        self.assertEqual(query.rule_name, complete_key_word['rule_name'])
        self.assertEqual(query.rule_name, json_data['rule_name'])


    def test_update_user_key_word_reply(self):
        """ 修改关键字回复 """

        self.set_login_status()

        test_reply_data = dict(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.PARTIAL,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )
        test_reply = SubscriptionAccountReply.objects.create(**test_reply_data)
        update_data = dict(
            id=test_reply.id,
            question_text=fake.word(),
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.COMPLETE,
            reply_text=fake.word(),
        )
        url = f"/api/admin/subscriptions/reply/key_word/{test_reply.id}/"
        resp = self.client.patch(url, data=update_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_data = resp.json()
        test_reply = SubscriptionAccountReply.objects.get(pk=test_reply.id)
        self.assertEqual(test_reply.question_text, json_data['question_text'])
        self.assertEqual(test_reply.question_text, update_data['question_text'])
        self.assertEqual(test_reply.reply_rule, json_data['reply_rule'])
        self.assertEqual(test_reply.reply_rule, update_data['reply_rule'])
        self.assertEqual(test_reply.reply_text, json_data['reply_text'])
        self.assertEqual(test_reply.reply_text, update_data['reply_text'])


    def test_delete_user_key_word_reply(self):
        """ 删除用户关键字回复 """

        self.set_login_status()

        test_reply_data = dict(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.PARTIAL,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )
        test_reply = SubscriptionAccountReply.objects.create(**test_reply_data)
        url = f"/api/admin/subscriptions/reply/key_word/{test_reply.id}/"
        resp = self.client.delete(url, data={"id": test_reply.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_data = resp.json()
        test_reply = SubscriptionAccountReply.objects.get(pk=test_reply.id)
        self.assertEqual(test_reply.status, SUBSCRIPTION_ACCOUNT_REPLY_STATUS.DELETE)
        self.assertEqual(test_reply.status, json_data['status'])


    def test_get_user_key_word_list(self):
        """ 获取用户关键字列表 """
        self.set_login_status()

        url = f"/api/admin/subscriptions/reply/key_word/?reply_account={SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER}"
        partial_key_word = SubscriptionAccountReply.objects.create(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.PARTIAL,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )

        complete_key_word = SubscriptionAccountReply.objects.create(
            question_text=fake.word(),
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE.COMPLETE,
            reply_text=fake.word(),
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.KEY_WORD,
            rule_name=fake.word(),
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.USING,
        )

        self.assertEqual(SubscriptionAccountReply.objects.all().count(), 2)
        resp = self.client.get(url, headers={'Content-Type': 'application/json'})
        json_data = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(json_data['count'], 2)


    def test_add_user_message_reply(self):
        """ 添加用户消息回复 """

        self.set_login_status()

        msg_reply_data = dict(
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word()
        )

        url = '/api/admin/subscriptions/reply/message/'
        resp = self.client.post(url, data=msg_reply_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.reply_text, msg_reply_data['reply_text'])
        self.assertEqual(msg_reply.reply_rule, SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'])
        self.assertEqual(msg_reply.reply_type, SUBSCRIPTION_ACCOUNT_REPLY_TYPE['RECEIVED'])
        self.assertEqual(msg_reply.reply_account, msg_reply_data['reply_account'])


    def test_update_user_message_reply(self):
        """ 修改用户消息回复 """

        self.set_login_status()

        msg_reply_data = dict(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['RECEIVED'],
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word(),
        )

        msg_reply = SubscriptionAccountReply.objects.create(**msg_reply_data)
        url = '/api/admin/subscriptions/reply/message/'
        update_data = dict(id=msg_reply.id, reply_text="test_"+fake.word())

        resp = self.client.post(url, data=update_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.reply_text, update_data['reply_text'])


    def test_delete_user_message_reply(self):
        """ 删除用户消息回复 """

        self.set_login_status()

        msg_reply_data = dict(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['RECEIVED'],
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word(),
        )

        msg_reply = SubscriptionAccountReply.objects.create(**msg_reply_data)
        url = '/api/admin/subscriptions/reply/message/'
        update_data = dict(id=msg_reply.id)

        resp = self.client.delete(url, data=update_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.status, SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE'])


    def test_add_user_attention_reply(self):
        """ 添加用户关注回复 """

        self.set_login_status()

        attention_reply_data = dict(
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word()
        )

        url = '/api/admin/subscriptions/reply/attention/'
        resp = self.client.post(url, data=attention_reply_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.reply_text, attention_reply_data['reply_text'])
        self.assertEqual(msg_reply.reply_rule, SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'])
        self.assertEqual(msg_reply.reply_type, SUBSCRIPTION_ACCOUNT_REPLY_TYPE['BE_PAID_ATTENTION'])
        self.assertEqual(msg_reply.reply_account, attention_reply_data['reply_account'])


    def test_update_user_attention_reply(self):
        """ 修改用户关注回复 """

        self.set_login_status()

        msg_reply_data = dict(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['BE_PAID_ATTENTION'],
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word(),
        )

        msg_reply = SubscriptionAccountReply.objects.create(**msg_reply_data)
        url = '/api/admin/subscriptions/reply/attention/'
        update_data = dict(id=msg_reply.id, reply_text="test_"+fake.word())

        resp = self.client.post(url, data=update_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.reply_text, update_data['reply_text'])


    def test_delete_user_attention_reply(self):
        """ 删除用户关注回复 """

        self.set_login_status()

        msg_reply_data = dict(
            status=SUBSCRIPTION_ACCOUNT_REPLY_STATUS['USING'],
            reply_rule=SUBSCRIPTION_ACCOUNT_REPLY_RULE['NOT_MATCH'],
            reply_type=SUBSCRIPTION_ACCOUNT_REPLY_TYPE['BE_PAID_ATTENTION'],
            reply_account=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.USER,
            reply_text=fake.word(),
        )

        msg_reply = SubscriptionAccountReply.objects.create(**msg_reply_data)
        url = '/api/admin/subscriptions/reply/attention/'
        update_data = dict(id=msg_reply.id)

        resp = self.client.delete(url, data=update_data)
        resp_json = resp.json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        msg_reply = SubscriptionAccountReply.objects.get(pk=resp_json['id'])
        self.assertEqual(msg_reply.status, SUBSCRIPTION_ACCOUNT_REPLY_STATUS['DELETE'])