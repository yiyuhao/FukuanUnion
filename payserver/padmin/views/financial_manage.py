# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import math

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import JsonResponse

from padmin.auth import DefaultAuthMixin, SuperAdminLoggedIn
from padmin.query_manage.financial_query import FinancialQuery, TimeTransform, CsvResponseFactory
from padmin.query_manage.settlement_query import SettlementQuery, UpdateUnLiquidatedSettlementUseCase
from padmin.query_manage.csv_stream_response import out_put_csv
from padmin.paginations import PAGE_SIZE


class FinancialManageView(DefaultAuthMixin, viewsets.GenericViewSet):

    permission_classes = (SuperAdminLoggedIn, )

    def data_overview(self, request, *args, **kwargs):
        data = FinancialQuery.data_overview()
        return JsonResponse(data)

    def transaction_details(self, request, *args, **kwargs):
        is_csv_download = self.request.query_params.get("type")
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        data = FinancialQuery.transaction_details(
            TimeTransform.date_string_to_start_date(start_date),
            TimeTransform.date_string_to_end_date(end_date))

        if is_csv_download != 'csv':
            return JsonResponse(data)

        csv_response = CsvResponseFactory.transaction_details_csv_response(data)
        return csv_response

    def sharing_details(self, request, *args, **kwargs):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        data = FinancialQuery.sharing_details(
            TimeTransform.date_string_to_start_date(start_date),
            TimeTransform.date_string_to_end_date(end_date))
        is_csv_download = self.request.query_params.get("type")
        if is_csv_download != 'csv':
            return JsonResponse(data)

        csv_response = CsvResponseFactory.sharing_details_csv_response(data)
        return csv_response

    def withdraw_record(self, request, *args, **kwargs):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status = self.request.query_params.get('status')
        data = FinancialQuery.withdraw_record(
            status,
            TimeTransform.date_string_to_start_date(start_date),
            TimeTransform.date_string_to_end_date(end_date))
        is_csv_download = self.request.query_params.get("type")
        if is_csv_download != 'csv':
            return JsonResponse(data)

        csv_response = CsvResponseFactory.withdraw_record_csv_response(data)
        return csv_response

    def un_liquidated_settlement_list(self, request, *args, **kwargs):
        """ 未结算账单 分页查询"""
        return JsonResponse(SettlementQuery.query_un_liquidated_settlement_list(self.request.query_params))
        
    def liquidated_settlement_list(self, request, *args, **kwargs):
        """ 已经结算账单 分页查询"""
        download_type = self.request.query_params.get('download_type')
        # 下载csv
        if download_type == 'csv':
            def get_rows(temp_page_size, temp_query_helper):
                temp_page_size = 5 * temp_page_size
                temp_total_count, temp_total_money = query_helper.count()
                max_page_num = int(math.ceil(temp_total_count / temp_page_size) + 1)
                yield ['结算时间', '商户名称（编号）', '交易单号', '户名', '银行', '银行卡号', '结算金额']
                for page in range(1, max_page_num):
                    temp_result_list = temp_query_helper.page_data(page, temp_page_size)
                    for item in temp_result_list:
                        yield [f"`{item['finished_datetime']}",
                               item['merchant_name'],
                               f"`{item['serial_number']}",
                               item['real_name'],
                               item['bank_name'],
                               f"`{item['bank_card_number']}",
                               item['all_money']]
                yield [f'共{temp_total_count}条记录，结算金额总计：{temp_total_money}（元）']
            current_page, query_helper = SettlementQuery.query_liquidated_settlement_list(self.request.query_params)
            return out_put_csv(get_rows(PAGE_SIZE, query_helper), out_file_name="结算账单.csv")
            
        # 查询
        current_page, query_helper = SettlementQuery.query_liquidated_settlement_list(self.request.query_params)
        total, total_money = query_helper.count()
        result_list = query_helper.page_data(current_page, PAGE_SIZE)

        return JsonResponse(dict(
            total_money=total_money,
            total=total,
            page=current_page,
            data=result_list
        ))
    
    def un_liquidated_settlement_update(self, request, *args, **kwargs):
        serial_number = self.request.query_params.get('serial_number')
        http_code, resp_data = UpdateUnLiquidatedSettlementUseCase.un_liquidated_settlement_update(serial_number)
        return Response(status=http_code, data=resp_data)
    

data_overview = FinancialManageView.as_view({
    'get': 'data_overview',
})

transaction_details = FinancialManageView.as_view({
    'get': 'transaction_details',
})

sharing_details = FinancialManageView.as_view({
    'get': 'sharing_details',
})

withdraw_record = FinancialManageView.as_view({
    'get': 'withdraw_record',
})

unliquidated_settlement_list = FinancialManageView.as_view({
    'get': 'un_liquidated_settlement_list',
    'patch': 'un_liquidated_settlement_update',
})

liquidated_settlement_list = FinancialManageView.as_view({
    'get': 'liquidated_settlement_list',
})


