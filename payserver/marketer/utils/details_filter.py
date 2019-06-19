import datetime
import config
from common.models import Account, Transaction, Payment


class DetailFilterMethod:
    def __init__(self, user=None, start_date=None, end_date=None, keywords=None, choose_type=None):
        self.user = user
        self.start_date = start_date
        self.end_date = end_date
        self.keywords = keywords
        self.choose_type = choose_type

    def _get_with_draw_transactions_list(self):
        account = Account.objects.get(marketer=self.user)
        with_draw_transactions = Transaction.objects.filter(account=account,
                                                            transaction_type=config.TRANSACTION_TYPE.MARKETER_WITHDRAW,
                                                            datetime__gte=self.start_date,
                                                            datetime__lte=self.end_date)
        with_draw_transactions_list = []
        for with_draw_transaction in with_draw_transactions:
            with_draw_transaction_dict = dict(image=None,
                                              name='with_draw',
                                              datetime=with_draw_transaction.datetime,
                                              amount=with_draw_transaction.amount,
                                              detail_type=config.TRANSACTION_TYPE.MARKETER_WITHDRAW,
                                              serial_number=with_draw_transaction.serial_number)
            with_draw_transactions_list.append(with_draw_transaction_dict)
        return sorted(with_draw_transactions_list, key=lambda detail: detail['datetime'], reverse=True)

    def _get_share_payments_list(self, start_date=None, end_date=None, keywords=None, *args, **kwargs):
        share_payments = Payment.objects.filter(merchant__in=self.user.invited_merchants.all(),
                                                datetime__gte=start_date,
                                                datetime__lte=end_date,
                                                merchant__name__icontains=keywords)
        share_payments_list = []
        for share_payment in share_payments:
            share_payment_dict = dict(image=share_payment.merchant.avatar_url,
                                      name=share_payment.merchant.name,
                                      datetime=share_payment.datetime,
                                      amount=share_payment.inviter_share,
                                      detail_type=config.TRANSACTION_TYPE.MARKETER_SHARE,
                                      serial_number=share_payment.serial_number)
            share_payments_list.append(share_payment_dict)
        return sorted(share_payments_list, key=lambda detail: detail['datetime'], reverse=True)

    def _convert_data(self):
        if self.start_date:
            self.start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
        if self.end_date:
            self.end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d')

    def _get_all_details(self):
        all_details = self._get_with_draw_transactions_list() + self._get_share_payments_list()
        return sorted(all_details, key=lambda detail: detail['datetime'], reverse=True)

    def _get_result(self):
        if self.choose_type == 'share':
            return self._get_share_payments_list()
        elif self.choose_type == 'with_draw':
            return self._get_with_draw_transactions_list()
        else:
            return self._get_all_details()

    def get_result(self):
        self._convert_data()
        return self._get_result()
