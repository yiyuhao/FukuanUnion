from rest_framework import views
from rest_framework import status
from rest_framework.response import Response
from marketer.utils.auth import MarketerAuthentication
from marketer.model_manager import UserAccountModelManager


class GetAccountWithdrawableBalanceView(views.APIView):
    """获取用户账户余额"""
    authentication_classes = [MarketerAuthentication]

    def get(self, request):
        manager = UserAccountModelManager(self.request.user)
        withdraw_type = self.request.query_params.get('withdraw_type')
        withdrawable_balance_info = manager.get_withdrawable_balance(withdraw_type)
        return Response(status=status.HTTP_200_OK, data=withdrawable_balance_info)
