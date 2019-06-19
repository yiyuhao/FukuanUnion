import logging
import json
import datetime

from django.db.models import Sum, Count, Q
from django.db import connection
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.transaction import atomic

from common.doclink.tencent_apis import fetch_adcode
from common.doclink.exceptions import ApiStatusCodeError, ApiReturnedError
from common.model_manager.base import ModelManagerBase
from common.msg_service.wechat_msg_send import MerchantAdminMessageSender, MarketerMessageSender
from common.models import Merchant, Account, MerchantAdmin, Message, Marketer, Transaction, Payment, Withdraw, \
    MerchantCategory, Area, MerchantMarketerShip, PaymentQRCode, City
from marketer.config import CONTENT_TEMPLATE
import config
from marketer.config import PAYMENT_QR_CODE_STATUS, CITY_MAP
from marketer.exceptions import CreateErrorException


logger = logging.getLogger(__name__)


class CreateModelManager(ModelManagerBase):
    def create(self, data):
        return self.model.objects.create(**data)


class CreateMerchantManager:
    """创建商铺"""
    account_manager = CreateModelManager(Account)
    merchant_manager = CreateModelManager(Merchant)
    merchant_admin_manager = CreateModelManager(MerchantAdmin)
    message_manager = CreateModelManager(Message)

    def create(self, merchant_data, merchant_admin_data, merchant_acct_data):
        with atomic():
            unionid = merchant_admin_data.get('wechat_unionid')
            merchant_admin = MerchantAdmin.objects.select_for_update().filter(wechat_unionid=unionid).first()
            if merchant_admin:
                if merchant_admin.merchant_admin_type == config.MERCHANT_ADMIN_TYPES.ADMIN:
                    raise CreateErrorException('管理员已存在')
                if merchant_admin.merchant_admin_type == config.MERCHANT_ADMIN_TYPES.CASHIER and merchant_admin.status == config.SYSTEM_USER_STATUS.USING:
                    raise CreateErrorException('该管理员为其他商铺收银员')
            merchant_acct_data.update(balance=0,
                                      withdrawable_balance=0,
                                      alipay_balance=0,
                                      alipay_withdrawable_balance=0)
            account_instance = self.account_manager.create(merchant_acct_data)
            merchant_data.update(account=account_instance,
                                 status=config.MERCHANT_STATUS.REVIEWING)
            merchant_instance = self.merchant_manager.create(merchant_data)
            if merchant_admin:
                merchant_admin.merchant_admin_type = config.MERCHANT_ADMIN_TYPES.ADMIN
                merchant_admin.status = config.SYSTEM_USER_STATUS.USING
                merchant_admin.work_merchant = merchant_instance
                merchant_admin.alipay_userid = merchant_admin_data.get('alipay_userid')
                merchant_admin.alipay_user_name = merchant_admin_data.get('alipay_user_name')
                merchant_admin.save()
            else:
                merchant_admin_data.update(merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN,
                                           status=config.SYSTEM_USER_STATUS.USING,
                                           work_merchant=merchant_instance)
                self.merchant_admin_manager.create(merchant_admin_data)
            if not merchant_instance.area.marketer_set.all():
                extra_data = json.dumps(
                    dict(id=merchant_instance.id, name=merchant_instance.name, area=merchant_instance.area.name))
                message_data = dict(content=CONTENT_TEMPLATE['NO_INVITER'],
                                    status=config.MESSAGE_STATUS.UNHANDLED,
                                    type=config.MESSAGE_TYPE.AREA_WITHOUT_MARKETER,
                                    extra_data=extra_data)
                self.message_manager.create(message_data)
            return merchant_instance


class CreateMarketerManager:
    """创建邀请人"""
    account_manager = CreateModelManager(Account)
    marketer_manager = CreateModelManager(Marketer)

    def create(self, marketer_data):
        with atomic():
            account_instance = self.account_manager.create(dict(balance=0,
                                                                withdrawable_balance=0,
                                                                alipay_balance=0,
                                                                alipay_withdrawable_balance=0))
            marketer_data['account'] = account_instance
            marketer = self.marketer_manager.create(marketer_data)
        return marketer


class UserTransactionModelManager:
    """账单"""
    model = Transaction

    def __init__(self, user):
        self.user = user

    def get_user_transactions(self, start_date=None, end_date=None, content_type=None):
        """用户账单查询"""
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m')
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m')
        if content_type:
            if content_type == 'payment':
                content_type = ContentType.objects.get_for_model(Payment)
            elif content_type == 'withdraw':
                content_type = ContentType.objects.get_for_model(Withdraw)
            else:
                content_type = None
        value_dict = dict(account=self.user.account,
                          datetime__gte=start_date,
                          datetime__lte=end_date,
                          content_type=content_type)
        query_value = dict()
        for k, v in value_dict.items():
            if v:
                query_value[k] = v
        return self.model.objects.filter(**query_value).order_by('-datetime')

    def get_sharing(self, merchant):
        query_sql = f'''
        select SUM(amount) 
        from common_transaction INNER JOIN common_payment on common_transaction.object_id=common_payment.serial_number 
        where common_transaction.transaction_type={config.TRANSACTION_TYPE.MARKETER_SHARE} and common_payment.merchant_id=%s
        '''

        with connection.cursor() as cursor:
            cursor.execute(query_sql, [merchant.id])
            row = cursor.fetchone()[0] or 0
        return row


class MerchantCategoryModelManager:
    """种类"""
    model = MerchantCategory

    def get_all(self):
        """查询全部种类"""
        all_cat = self.model.objects.all()
        all_root_cat = [cat for cat in all_cat if not cat.parent_id]
        all_sub_cat = [cat for cat in all_cat if cat.parent_id]
        res_list = []
        for root_cat in all_root_cat:
            root_dict = dict(id=root_cat.id, name=root_cat.name, children=[])
            for sub_cat in all_sub_cat:
                if sub_cat.parent_id == root_cat.id:
                    sub_dict = dict(id=sub_cat.id, name=sub_cat.name)
                    root_dict['children'].append(sub_dict)
                else:
                    continue
            res_list.append(root_dict)
        return res_list


class AreaModelManager:
    """区域"""
    model = Area
    ADCODE_FMT = '<012d'

    def has_marketer(self, adcode):
        """查询区域是否有业务员"""
        try:
            return self.model.objects.get(adcode=adcode).marketer_set.exists()
        except Area.DoesNotExist:
            return 'DISABLE'

    def check_and_complete_adcode(self, adcode):
        """ 查询是否存在adcode,不存在就添加 """
        adcode = format(int(adcode), self.ADCODE_FMT)
        area = self.model.objects.filter(adcode=adcode).first()
        if area:
            return area

        return self._add_adcode(adcode=adcode)

    def _check_and_get_city(self, adcode):
        """
        检查是否存在,并返回城市对象
        :param adcode: 城市下面行政区的adcode
        :return:
        """
        adcode_prefix = str(adcode)[:4]
        if adcode_prefix not in CITY_MAP:
            return None

        city_name = CITY_MAP[adcode_prefix]
        try:
            city = City.objects.get(name=city_name)
        except City.DoesNotExist as e:
            logger.info(f"在数据库中未查询到{city_name}的相关记录, e: {e}")
            return None

        return city

    def _check_and_get_area(self, adcode):
        """
        检查是否存在,并返回行政区
        :param adcode: 城市下面行政区的adcode
        :return:
        """
        adcode = format(int(adcode[:6]), self.ADCODE_FMT)
        area = self.model.objects.filter(adcode=adcode).first()
        if not area:
            return None
        return area

    def _add_adcode(self, adcode):
        """ 当前adcode不在数据库中, 将其添加到数据库 """
        adcode = str(adcode)
        if not adcode.endswith('000') or len(adcode) != 12:
            logger.error("当前adcode: {adcode} 格式错误")
            return None

        # check city
        city = self._check_and_get_city(adcode)
        if not city:
            return None

        # 街道 adcode 9位
        try:
            block_item = fetch_adcode(adcode=adcode[:9])
        except (ApiStatusCodeError, ApiReturnedError):
            return None

        block_adcode = format(int(block_item['id']), self.ADCODE_FMT)
        block_name = block_item['fullname']

        area = self._check_and_get_area(adcode=adcode)
        if not area:
            # 区域 adcode 6位
            try:
                area_item = fetch_adcode(adcode=adcode[:6])
            except (ApiStatusCodeError, ApiReturnedError):
                return None

            area_adcode = format(int(area_item['id']), self.ADCODE_FMT)
            area_name = area_item['fullname']

            area = self.model.objects.create(city=city, name=area_name,
                                             adcode=area_adcode, parent=None)

        block = self.model.objects.create(city=area.city, name=block_name,
                                          adcode=block_adcode, parent=area)
        return block


class UserMerchantModelManager:
    """用户关联商铺"""
    model = Merchant

    def __init__(self, user):
        self.user = user

    def audit_merchant(self, merchant_instance, to_status, audit_info=None):
        """审核商铺"""
        with atomic():
            audit_ship = MerchantMarketerShip(marketer=self.user, merchant=merchant_instance)
            if to_status != merchant_instance.status:
                merchant_instance.status = to_status
            if audit_info:
                audit_ship.audit_info = audit_info
            audit_ship.save()
            merchant_instance.save()
        return merchant_instance

    def get_to_be_audit_merchant(self):
        merchants = self.model.objects.filter(status=config.MERCHANT_STATUS.REVIEWING,
                                              area__in=self.user.working_areas.all()).order_by('-create_datetime')
        return merchants

    def get_invited_merchant_num(self):
        query = self.model.objects.filter(inviter=self.user). \
            aggregate(using_merchants_num=Count('pk',
                                                filter=Q(status=config.MERCHANT_STATUS.USING)),

                      reviewing_merchants_num=Count('pk',
                                                    filter=(Q(status=config.MERCHANT_STATUS.REVIEWING) |
                                                            Q(status=config.MERCHANT_STATUS.REJECTED))))
        return query

    def get_auditor_merchants(self, merchant_status=None):
        if merchant_status is None:
            merchants = self.model.objects.filter(
                status__in=(config.MERCHANT_STATUS.REVIEWING, config.MERCHANT_STATUS.USING),
                area__in=self.user.working_areas.all()).order_by('update_datetime')
        else:
            merchants = self.model.objects.filter(
                status=merchant_status,
                area__in=self.user.working_areas.all()).order_by('update_datetime')
        return merchants


class UserAccountModelManager:
    """用户账户"""

    def __init__(self, user):
        self.user = user
        self.account = Account.objects.get(marketer=user)

    def get_total_withdrawable_balance(self):
        """获取用户账户余额"""
        return self.account.withdrawable_balance + self.account.alipay_withdrawable_balance

    def get_withdrawable_balance(self, withdraw_type=None):
        _mapping_dict = {
            'wechat': {'account': self.user.wechat_nickname, 'balance': self.account.withdrawable_balance},
            'alipay': {'account': self.user.alipay_id, 'balance': self.account.alipay_withdrawable_balance}}
        return _mapping_dict[withdraw_type] if withdraw_type else _mapping_dict


class PaymentModelManager:
    """支付"""
    model = Payment

    def get_merchant_sharing(self, obj):
        """获取支付账单邀请人分成"""
        return self.model.objects.filter(merchant=obj, status=config.PAYMENT_STATUS.FINISHED).aggregate(
            sharing=Sum('inviter_share'))['sharing'] or 0


class PaymentQRCodeModelManager:
    """付款码"""
    model = PaymentQRCode

    def can_use(self, code):
        """查询付款码是否可以使用"""
        instance = self.model.objects.filter(uuid=code).first()
        if not instance:
            return PAYMENT_QR_CODE_STATUS['DOES_NOT_EXIST'], None, '付款码不存在'
        if hasattr(instance, 'merchant'):
            return PAYMENT_QR_CODE_STATUS['HAS_BEEN_BIND'], None, '已被其他商户绑定'
        else:
            return PAYMENT_QR_CODE_STATUS['CAN_USE'], instance, '可以使用'


class MerchantAdminModelManager:
    """商户管理员"""
    model = MerchantAdmin

    def check_admin_exist(self, unionid):
        """查询商户管理员是否存在"""
        return self.model.objects.filter(wechat_unionid=unionid).exists()

    def can_create(self, unionid):
        """查询管理员是否可以创建"""
        return self.model.objects.filter(
            Q(wechat_unionid=unionid, merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN) |
            Q(wechat_unionid=unionid, merchant_admin_type=config.MERCHANT_ADMIN_TYPES.CASHIER,
              status=config.SYSTEM_USER_STATUS.USING)).exists()

    def check_admin_type(self, unionid):
        """ 获取该unionid对应管理员类型 确保调用时已经存在 """
        admin = self.model.objects.filter(wechat_unionid=unionid).first()
        return config.MERCHANT_ADMIN_TYPES[admin.merchant_admin_type]['name']


class MerchantMessageManager:
    """ 商户新建、审核相关消息 """

    def __init__(self, merchant):
        self.merchant = merchant
        self.commit_date = timezone.now()
        self.merchant_msg_handler = MerchantAdminMessageSender(
            merchant.admins.filter(
                merchant_admin_type=config.MERCHANT_ADMIN_TYPES['ADMIN']
            ).first())
        self.marketer_msg_handler = MarketerMessageSender(merchant)

    def _get_salesman_from_area(self):
        marketers = self.merchant.area.marketer_set.filter(
            status=config.SYSTEM_USER_STATUS['USING'],
            inviter_type=config.MARKETER_TYPES['SALESMAN']).order_by('?')
        return marketers

    @property
    def _merchant_status_passed(self):
        if self.merchant.status == config.MERCHANT_STATUS['USING']:
            return True

    def _get_latest_audit_info(self):
        latest_audit = self.merchant.merchantmarketership_set.all(). \
            order_by('-audit_datetime').first()
        if not latest_audit:
            return None, ''
        return latest_audit.audit_datetime, latest_audit.audit_info

    def to_marketer(self):
        salesmans = self._get_salesman_from_area()
        for salesman in salesmans:
            self.marketer_msg_handler.salesman_marchant_audit(
                salesman.wechat_openid, self.commit_date)

    def merchant_wait_to_be_audit(self):
        # 给商户管理员推待审核消息
        self.merchant_msg_handler.wait_to_be_audit(
            self.merchant.name, self.commit_date)

        # 给商户所在区域的业务员推待审核消息
        self.to_marketer()

    def merchant_audited(self):
        # 给商户管理员推审核结果 消息
        audit_date, audit_info = self._get_latest_audit_info()
        if self._merchant_status_passed:
            self.merchant_msg_handler.audited_success(audit_date)
            # 给邀请人推消息，当前店铺审核成功
            self.marketer_msg_handler.inviter_marchant_audited(
                self.merchant.inviter.wechat_openid, audit_date)
        else:
            self.merchant_msg_handler.audited_fail(audit_info, audit_date)
