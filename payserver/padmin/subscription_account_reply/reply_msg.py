# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


"""
回复给微信服务器的消息

"""

import time

from config import TemplateIdConfig
from padmin.subscription_account_reply.const import WEChAT_MINI_PROGRAM


class ReplyTextMsg(object):
    """ 回复文本消息 """

    def __init__(self, to_user_name, from_user_name, content):
        self.__dict = dict()
        self.__dict['ToUserName'] = to_user_name
        self.__dict['FromUserName'] = from_user_name
        self.__dict['CreateTime'] = int(time.time())
        self.__dict['Content'] = content

    def get_msg_body(self):
        XmlForm = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{Content}]]></Content>
        </xml>
        """
        return XmlForm.format(**self.__dict)


class ReplyPictureTextMsg(object):
    """ 回复图文消息 """

    def __init__(self, params_dict):
        self.__dict = params_dict

    def get_msg_body(self):
        XmlForm = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[news]]></MsgType>
        <ArticleCount>{ArticleCount}</ArticleCount>
        <Articles>
            <item>
                <Title><![CDATA[{title1}]]></Title>
                <Description><![CDATA[{description1}]]></Description>
                <PicUrl><![CDATA[{picurl1}]]></PicUrl>
                <Url><![CDATA[{url1}]]></Url>
            </item>
            <item>
                <Title><![CDATA[{title2}]]></Title>
                <Description><![CDATA[{description2}]]></Description>
                <PicUrl><![CDATA[{picurl2}]]></PicUrl>
                <Url><![CDATA[{url2}]]></Url>
            </item>
            <item>
                <Title><![CDATA[{title3}]]></Title>
                <Description><![CDATA[{description3}]]></Description>
                <PicUrl><![CDATA[{picurl3}]]></PicUrl>
                <Url><![CDATA[{url3}]]></Url>
            </item>
        </Articles>
        </xml>
        """
        return XmlForm.format(**self.__dict)


#  模板消息
class TemplateMessage(object):
    def __init__(self, open_id, dict_data):
        self.open_id = open_id
        self.dict_data = dict_data

    def get_msg_body(self):
        raise NotImplementedError("class TemplateMessage's get_msg_body must be implemented")


#
#  商户公众号消息推送
#
class MerchantMothBillTemplateMessage(TemplateMessage):
    """ 商户月度账单模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "_PFSU-1cDcJwdC0G8lgfNF9XozNpb3-k4z_Z5pbk_TI",
            "data": {
                "first": {
                    "value": f"您{self.dict_data['month']}月份的账单已生成，请及时查收",
                },
                "keyword1": {
                    "value": f"{self.dict_data['turnover']}元",
                    "color": "#173177"
                },
                "keyword2": {
                    "value": f"{self.dict_data['sharing_earning']}元",
                    "color": "#173177"
                },
                "keyword3": {
                    "value": self.dict_data['bill_month'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "",
                },
            }
        }

        return message_content


class MerchantCommitInfoTemplateMessage(TemplateMessage):
    """ 商户提交资料信息成功模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "hN2A9e_4BP4EajXH_jXkExQD9J4L4zSM5GXRKoLFigY",
            "miniprogram": {
              "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
              "pagepath": "pages/index"
            },
            "data": {
                "first": {
                    "value": "您好，您的商户信息已提交",
                },
                "keyword1": {
                    "value": self.dict_data['merchant_name'],
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['commit_time'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "请等待审核。",
                },
            }
        }

        return message_content


class MerchantBeApprovedTemplateMessage(TemplateMessage):
    """ 商户审核通过模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "jH7vd4bcbkURK3MH7cOf-fIYjSIXrMK1FgfE_ikn-OE",
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": "pages/index"
            },
            "data": {
                "first": {
                    "value": "您好，您的商户信息已通过审核",
                },
                "keyword1": {
                    "value": "审核通过",
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['pass_time'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "点击进入小程序查看详情！",
                },
            }
        }

        return message_content


class MerchantNotBeApprovedTemplateMessage(TemplateMessage):
    """ 商户审核没有通过模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "kBiZ-kQDtr6vnaDV_R6-Dvxn-2tHks2kZ3wqS_1DqZY",
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": "pages/index"
            },
            "data": {
                "first": {
                    "value": "您好,您的提交的商户信息未通过",
                },
                "keyword1": {
                    "value": "审核未通过",
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['reason'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "点击进入小程序修改资料！",
                },
            }
        }

        return message_content


class MerchantRefundSuccessTemplateMessage(TemplateMessage):
    """ 商户退款成功的模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": TemplateIdConfig.merchant_refund_success,
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": f"pages/billDetail?serial_number={self.dict_data['serial_number']}"
            },
            "data": {
                "first": {
                    "value": self.dict_data['first'],
                },
                "keyword1": {
                    "value": self.dict_data['keyword1'],
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['keyword2'],
                    "color": "#173177"
                },
                "keyword3": {
                    "value": self.dict_data['keyword3'],
                    "color": "#173177"
                },
                "remark": {
                    "value": self.dict_data.get('remark', ''),
                },
            }
        }

        return message_content


class MerchantRefundFailTemplateMessage(TemplateMessage):
    """ 商户退款失败的模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": TemplateIdConfig.merchant_refund_fail,
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": f"pages/billDetail?serial_number={self.dict_data['keyword1']}"
            },
            "data": {
                "first": {
                    "value": self.dict_data['first'],
                },
                "keyword1": {
                    "value": self.dict_data['keyword1'],
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['keyword2'],
                    "color": "#173177"
                },
                "keyword3": {
                    "value": self.dict_data['keyword3'],
                    "color": "#173177"
                },
                "keyword4": {
                    "value": self.dict_data['keyword4'],
                    "color": "#173177"
                },
                "remark": {
                    "value": self.dict_data.get('remark', ''),
                },
            }
        }

        return message_content


class MerchantReceiveTemplateMessage(TemplateMessage):
    """ 商户收款到帐的模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": TemplateIdConfig.merchant_receive,
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['merchant']['app_id'],
                "pagepath": f"pages/billDetail?serial_number={self.dict_data['serial_number']}"
            },
            "data": {
                "first": {
                    "value": self.dict_data['first'],
                },
                "keyword1": {
                    "value": self.dict_data['keyword1'],
                },
                "keyword2": {
                    "value": self.dict_data['keyword2'],
                    "color": "#173177"
                },
                "keyword3": {
                    "value": self.dict_data['keyword3'],
                },
                "remark": {
                    "value": self.dict_data.get('remark', ''),
                },
            }
        }

        return message_content


class MerchantSettlementTemplateMessage(TemplateMessage):
    """ 企业商户结算通知消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": 'd3v53vcSi3Ex-FnPoo9gD-VY0ZVEwfTi1tzD7KDKRVY',
            "data": {
                "first": {
                    "value": f"{self.dict_data['first']}收入已结算，请注意查看",
                },
                "keyword1": {
                    "value": f"{self.dict_data['keyword1']} 元",
                },
                "keyword2": {
                    "value": self.dict_data['keyword2'],
                },
            }
        }
        
        return message_content
    

# 业务员
class MarketerAuditMerchantTemplateMessage(TemplateMessage):
    """ 业务员收到审核商户通知模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "GQQ2x6ekqAOo4nrcwhHyLzQkghZKnBJL_0oPsVLwvIc",
            "miniprogram": {
                "appid": WEChAT_MINI_PROGRAM['marketer']['app_id'],
                "pagepath": "pages/show-merchants/audit-list"
            },
            "data": {
                "first": {
                    "value": "您好！您有新的商户入驻审核待确认！",
                },
                "keyword1": {
                    "value": "待审核",
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['applicant'],
                    "color": "#173177"
                },
                "keyword3": {
                    "value": self.dict_data['apply_time'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "请您尽快处理，点击详情进入小程序进行审核！",
                },
            }
        }

        return message_content


# 邀请人
class InviterInviteMerchantPassTemplateMessage(TemplateMessage):
    """ 邀请人收到邀请的商户审核通过的模板消息 """

    def get_msg_body(self):
        message_content = {
            "touser": self.open_id,
            "topcolor": "#FF0000",
            "template_id": "ofsAfOmCkV5QHkowjjUgaB1irUB2xA-Il7p0lA5xqaw",
            "data": {
                "first": {
                    "value": f"您邀请的商户已通过审核 \\n商户名称：{self.dict_data['merchant_name']}",
                },
                "keyword1": {
                    "value": "审核通过",
                    "color": "#173177"
                },
                "keyword2": {
                    "value": self.dict_data['pass_time'],
                    "color": "#173177"
                },
                "remark": {
                    "value": "",
                },
            }
        }

        return message_content


class ReplyMessageFactory(object):
    @staticmethod
    def get_template_message(message_type, open_id, dict_data):
        if message_type == "marketer_audit_merchant":
            return MarketerAuditMerchantTemplateMessage(open_id, dict_data)
        elif message_type == "inviter_invite_merchant_pass":
            return InviterInviteMerchantPassTemplateMessage(open_id, dict_data)
        elif message_type == "merchant_month_bill":
            return MerchantMothBillTemplateMessage(open_id, dict_data)
        elif message_type == "merchant_commit_info":
            return MerchantCommitInfoTemplateMessage(open_id, dict_data)
        elif message_type == "merchant_be_approved":
            return MerchantBeApprovedTemplateMessage(open_id, dict_data)
        elif message_type == "merchant_not_be_approved":
            return MerchantNotBeApprovedTemplateMessage(open_id, dict_data)
        elif message_type == 'merchant_refund_success':
            return MerchantRefundSuccessTemplateMessage(open_id, dict_data)
        elif message_type == 'merchant_refund_fail':
            return MerchantRefundFailTemplateMessage(open_id, dict_data)
        elif message_type == 'merchant_receive':
            return MerchantReceiveTemplateMessage(open_id, dict_data)
        elif message_type == 'merchant_settlement':
            return MerchantSettlementTemplateMessage(open_id, dict_data)

        return None

    @staticmethod
    def get_text_message(to_user_name, from_user_name, content):
        return ReplyTextMsg(to_user_name, from_user_name, content)
