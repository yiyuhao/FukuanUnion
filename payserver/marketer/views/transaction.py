from rest_framework import mixins, viewsets
from marketer.utils.auth import MarketerAuthentication
from marketer.utils.pagenations import BasePagination
from marketer.model_manager import UserTransactionModelManager
from marketer.serializers.nested_serializers import OperationDetailsSerializer


class ShowOperationsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        params = dict(start_date=self.request.query_params.get('start_date', None),
                      end_date=self.request.query_params.get('end_date', None),
                      content_type=self.request.query_params.get('content_type', None))
        manager = UserTransactionModelManager(user=self.request.user)
        return manager.get_user_transactions(**params)

    serializer_class = OperationDetailsSerializer
    authentication_classes = [MarketerAuthentication]
    pagination_class = BasePagination
