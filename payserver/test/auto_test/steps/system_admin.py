# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import config


class LoginStep(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def login(self, username=None, password=None):
        url = "/api/admin/system_admins/login"
        data = {"username": username, 'password': password}
        resp = self.test_case.client.post(url, data=data, format='json')
        return resp
    
    def me(self):
        url = '/api/admin/system_admins/me'
        resp = self.test_case.client.get(url)
        return resp
        

class FinancialQueryStep(object):
    def __init__(self, test_case):
        self.test_case = test_case

    def get_overview_data(self):
        url = "/api/admin/financial/data_overview/"
        resp = self.test_case.client.get(url)
        return resp
    
    def get_transaction_details(self):
        url = "/api/admin/financial/transaction_details/"
        resp = self.test_case.client.get(url)
        return resp

    def get_sharing_details(self):
        url = "/api/admin/financial/sharing_details/"
        resp = self.test_case.client.get(url)
        return resp
    
    def get_withdraw_record(self):
        url = "/api/admin/financial/withdraw_record/"
        resp = self.test_case.client.get(url)
        return resp


class ChangeInviterToMarketerStep(object):
    def __init__(self, test_case):
        self.test_case = test_case
        
    def inviter_list(self):
        url = '/api/admin/inviters/'
        resp = self.test_case.client.get(url)
        return resp

    def change_inviter_to_marketer(self, inviter_id=None, work_areas_ids=None, worker_number=None):
        data = dict(
            id=inviter_id,
            working_areas=work_areas_ids if work_areas_ids else [],
            worker_number=worker_number,
            inviter_type=config.MARKETER_TYPES.SALESMAN
        )
        url = f'/api/admin/salesman/{inviter_id}/?change_inviter=true&inviter_type={config.MARKETER_TYPES.MARKETER}'
        resp = self.test_case.client.patch(url, data=data, format='json')
        return resp
    

class MerchantManageStep(object):
    def __init__(self, test_case):
        self.test_case = test_case
        
    def get_merchant_info(self, merchant_id):
        url = f"/api/admin/merchants/{merchant_id}/"
        resp = self.test_case.client.get(url)
        return resp


