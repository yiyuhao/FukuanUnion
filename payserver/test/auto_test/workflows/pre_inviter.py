# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

""" 准备邀请人且邀请人邀请商户 """
import uuid
from test.auto_test.workflows.inviter import RegisterInviterWorkflow, InviteMerchantWorkflow, AuditMerchantWorkflow
from test.auto_test.steps.system_admin import LoginStep, ChangeInviterToMarketerStep


class GenerateInviterWorkflow(object):
    def __init__(self, test_case):
        self.test_case = test_case
    
    def generate_inviter(self, unionid=None, name=None, phone=None,
                         id_card_front_url=None, id_card_back_url=None,
                         salesman_info=None):
        """
        注册一个邀请人
        :param unionid: 邀请人unionid
        :param name: 邀请人name
        :param phone: 邀请人phone
        :param id_card_front_url: 邀请人id_card_front_url
        :param id_card_back_url: 邀请人id_card_back_url
        :param salesman_info: 邀请人是否为业务员信息，
                salesman_info = dict(
                    set_salesman=True, 设置为业务员
                    system_admin_name='admin@mishitu.com', 后台管理员账号
                    system_admin_password='123456', 后台管理员密码
                    new_work_ids=new_work_ids, 该邀请人变为业务员工作区域
                    worker_number='00sdfc' 该邀请人变为业务员工号
                )
        :return:
        dict(
            is_salsman=True or False, 是否为业务员
            id=inviter_id, 数据库中邀请人id
            token=res_token, 小程序登陆token
            unionid=res_unionid, unionid
        )
        """
        register_inviter_workflow = RegisterInviterWorkflow(unionid=unionid or str(uuid.uuid4().hex))
        res_token, res_unionid= register_inviter_workflow.go(
            unionid=unionid,
            name=name,
            phone=phone,
            id_card_front_url=id_card_front_url,
            id_card_back_url=id_card_back_url
        )
        inviter_id = register_inviter_workflow.created_info['id']
        if salesman_info and salesman_info.get('set_salesman', False):
            system_admin_login_step = LoginStep(self.test_case)
            resp = system_admin_login_step.login(salesman_info['system_admin_name'],
                                                 salesman_info['system_admin_password'])
            stepper = ChangeInviterToMarketerStep(self.test_case)
            resp = stepper.change_inviter_to_marketer(inviter_id,
                                                      work_areas_ids=salesman_info['new_work_ids'],
                                                      worker_number=salesman_info['worker_number'])
        return dict(
            is_salsman=salesman_info and salesman_info.get('set_salesman', False),
            id=inviter_id,
            token=res_token,
            unionid=res_unionid,
        )

    def invite_merchant(self, inviter_token=None, merchant_info=None):
        """
        邀请人邀请商户
        :param inviter_token: 邀请人登录token
        :param merchant_info: 商户信息
                    merchant_info = dict(
                        address_info=dict(   # 商户地址信息
                            adcode='110105004000',
                            address='北京市朝阳区三里屯太古里',
                            location_lon=39.003,
                            location_lat=39.003
                        ),
                        merchant_name='商户1',
                        merchant_phone='',
                        avatar_url='',
                        photo_url='',
                        description='',
                        license_url='',
                        id_card_front_url='',
                        id_card_back_url=''
                    )
        :return:
        """
        invite_merchant_workflow = InviteMerchantWorkflow(inviter_token)
        resp, res = invite_merchant_workflow.go(
            address_info=merchant_info.get('address_info', None),
            merchant_name=merchant_info.get('merchant_name', None),
            merchant_phone=merchant_info.get('merchant_phone', None),
            avatar_url=merchant_info.get('avatar_url', None),
            photo_url=merchant_info.get('photo_url', None),
            description=merchant_info.get('description', None),
            license_url=merchant_info.get('license_url', None),
            id_card_front_url=merchant_info.get('id_card_front_url', None),
            id_card_back_url=merchant_info.get('id_card_back_url', None),
            merchant_acct_data=merchant_info.get('merchant_acct_data', None)
        )
        return dict(merchant_id=resp.json()['id'])
    
    def aduit_merchant(self, to_status, audit_info=None, merchant_id=None, token=None):
        """
        
        :param to_status: 审核商户结果状态
        :param audit_info: 审核信息
        :param merchant_id: 商户id
        :param token: 业务员登录token
        :return: {'id': 2, 'name': '商户b'}
        """
        audit_merchant_workflow = AuditMerchantWorkflow(merchant_id=merchant_id)
        resp, res = audit_merchant_workflow.go(to_status,
                                          audit_info=audit_info,
                                          merchant_id=merchant_id,
                                          token=token,
                                          )
        return resp.json()

