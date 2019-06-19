# -*- coding: utf-8 -*-
import uuid

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from dynaconf import settings as dynasettings

from common.encrypt_fileds import EncryptedCharField
from config import MERCHANT_STATUS, MARKETER_TYPES, \
    MERCHANT_ADMIN_TYPES, VALID_STRATEGY, COUPON_STATUS, \
    WITHDRAW_STATUS, PAYMENT_STATUS, PAY_CHANNELS, TRANSACTION_TYPE, \
    SYSTEM_USER_STATUS, MESSAGE_STATUS, MESSAGE_TYPE, REFUND_STATUS, \
    SUBSCRIPTION_ACCOUNT_REPLY_STATUS, SUBSCRIPTION_ACCOUNT_REPLY_RULE, \
    SUBSCRIPTION_ACCOUNT_REPLY_TYPE, SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT, \
    WITHDRAW_TYPE, TRANSFER_STATUS, SETTLEMENT_STATUS, MERCHANT_TYPE, VERIFY_ACCOUNT_STATUS

AES_KEY = dynasettings.OPENID_AES_KEY


class LoginStats(models.Model):
    last_success_login = models.DateTimeField(null=True, blank=True)  # 上次成功登录时间
    last_success_ip = models.GenericIPAddressField(null=True, blank=True)  # 上次成功登录IP
    last_failed_login = models.DateTimeField(null=True, blank=True)  # 上次失败登录时间
    last_failed_ip = models.GenericIPAddressField(null=True, blank=True)  # 上次失败登录IP
    failed_login_count = models.IntegerField(default=0,
                                             validators=[MinValueValidator(0)])  # 累计失败登录次数


class SystemAdmin(models.Model):
    username = models.CharField(max_length=128, unique=True)  # 用户名
    password = models.CharField(max_length=128)  # 密码
    name = models.CharField(max_length=128)  # 姓名
    status = models.IntegerField(choices=SYSTEM_USER_STATUS.model_choices())  # 状态
    is_super = models.BooleanField(default=False)  # 是否是超级管理员
    permissions = models.CharField(max_length=2048)  # 权限
    login_stats = models.OneToOneField(LoginStats, on_delete=models.PROTECT)  # 登录情况统计


class MerchantAdmin(models.Model):
    wechat_openid = EncryptedCharField(max_length=128, unique=True, db_index=True, key=AES_KEY)  # 微信openid
    wechat_unionid = models.CharField(max_length=128, default='', db_index=True)  # 微信unionid
    wechat_avatar_url = models.CharField(null=True, blank=True, max_length=1024)  # 收银员微信头像(商户管理员为空)
    wechat_nickname = models.CharField(null=True, blank=True, max_length=128)  # 收银员微信昵称(商户管理员为空)
    alipay_userid = models.CharField(null=True, blank=True, max_length=128)  # 支付宝user id
    alipay_user_name = models.CharField(null=True, blank=True, max_length=128)  # 支付宝用户真实姓名
    merchant_admin_type = models.IntegerField(choices=MERCHANT_ADMIN_TYPES.model_choices())  # 类型：管理员/收银员
    status = models.IntegerField(choices=SYSTEM_USER_STATUS.model_choices())  # 用户状态
    voice_on = models.BooleanField(default=True)  # 语音播报开关 (True-开)
    work_merchant = models.ForeignKey('Merchant', related_name='admins', on_delete=models.CASCADE)  # 所属店铺
    phone = models.CharField(max_length=32, default='', db_index=True)  # 手机号


class Marketer(models.Model):
    wechat_openid = EncryptedCharField(max_length=128, unique=True, db_index=True, key=AES_KEY)  # 微信openid
    wechat_unionid = models.CharField(max_length=128, default='', db_index=True)  # 微信unionid
    wechat_avatar_url = models.CharField(null=True, blank=True, max_length=1024)  # 微信头像
    wechat_nickname = models.CharField(null=True, blank=True, max_length=128)  # 微信昵称
    alipay_id = models.CharField(null=True, blank=True, max_length=128)  # 支付宝账号
    inviter_type = models.IntegerField(choices=MARKETER_TYPES.model_choices())  # 推广员类型：业务员/普通邀请人
    status = models.IntegerField(choices=SYSTEM_USER_STATUS.model_choices())  # 用户状态
    name = models.CharField(max_length=128)  # 用户姓名
    phone = models.CharField(max_length=32, default='', db_index=True)  # 手机号
    id_card_front_url = models.CharField(max_length=1024, default='')  # 身份证正面
    id_card_back_url = models.CharField(max_length=1024, default='')  # 身份证反面
    account = models.OneToOneField('Account', on_delete=models.PROTECT)  # 账户

    worker_number = models.CharField(max_length=128, null=True, blank=True)  # 工号，业务员专属
    working_areas = models.ManyToManyField('Area')  # 负责区域，业务员专属


class Client(models.Model):
    openid = EncryptedCharField(max_length=128, unique=True, db_index=True, key=AES_KEY)  # openid,可能是微信或支付宝
    wechat_unionid = models.CharField(max_length=128, default='', db_index=True)  # 微信unionid
    openid_channel = models.IntegerField(choices=PAY_CHANNELS.model_choices())  # openid渠道
    phone = models.CharField(null=True, blank=True, max_length=32, unique=True)  # 手机号
    status = models.IntegerField(choices=SYSTEM_USER_STATUS.model_choices(),
                                 default=SYSTEM_USER_STATUS['USING'])  # 状态
    avatar_url = models.CharField(default='', max_length=1024)  # 消费者头像


class City(models.Model):
    name = models.CharField(max_length=32, unique=True)  # 城市名


class Area(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='areas')  # 所属城市
    name = models.CharField(max_length=128)  # 区域名称
    parent = models.ForeignKey('Area', null=True, on_delete=models.CASCADE,
                               related_name='children')  # 上一级区域
    adcode = models.CharField(max_length=128, default='')  # 行政区划代码


class MerchantCategory(models.Model):
    """
    最多允许两级分类
    """
    name = models.CharField(max_length=32)  # 分类名称
    parent = models.ForeignKey('MerchantCategory', null=True, on_delete=models.CASCADE,
                               related_name='children')  # 上一级分类


class PaymentQRCode(models.Model):
    uuid = models.UUIDField(db_index=True, default=uuid.uuid4)


class Merchant(models.Model):
    type = models.IntegerField(choices=MERCHANT_TYPE.model_choices(),
                               default=MERCHANT_TYPE.INDIVIDUAL)  # 商户类型: 个人商户, 企业商户
    status = models.IntegerField(choices=MERCHANT_STATUS.model_choices())  # 商户状态
    name = models.CharField(max_length=128)  # 商户名称
    account = models.OneToOneField('Account', on_delete=models.PROTECT)  # 商户账户
    inviter = models.ForeignKey(Marketer, null=True, on_delete=models.SET_NULL,
                                related_name='invited_merchants')  # 邀请人
    auditors = models.ManyToManyField(Marketer, through='MerchantMarketerShip',
                                      related_name='audited_merchants')  # 审核员
    payment_qr_code = models.OneToOneField(PaymentQRCode, on_delete=models.PROTECT,
                                           db_index=True)  # 付款码
    category = models.ForeignKey(MerchantCategory, on_delete=models.PROTECT)  # 商户业务分类
    contact_phone = models.CharField(max_length=32)  # 联系电话
    area = models.ForeignKey(Area, on_delete=models.PROTECT, db_index=True)  # 商户所在区域
    address = models.CharField(max_length=512)  # 商户地址
    location_lon = models.FloatField(db_index=True)  # 商户位置经度
    location_lat = models.FloatField(db_index=True)  # 商户位置纬度
    description = models.TextField()  # 商户介绍
    avatar_url = models.CharField(max_length=1024)  # 商户头像
    photo_url = models.CharField(max_length=1024, null=True, blank=True)  # 商户照片
    license_url = models.CharField(max_length=1024, null=True, blank=True)  # 营业执照照片
    id_card_front_url = models.CharField(max_length=1024, null=True, blank=True)  # 法人身份证正面
    id_card_back_url = models.CharField(max_length=1024, null=True, blank=True)  # 法人身份证反面
    day_begin_minute = models.PositiveIntegerField(default=0)  # 账单日结开始时间(延后day_begin_minute分钟)
    create_datetime = models.DateTimeField(default=timezone.now)  # 入驻时间
    update_datetime = models.DateTimeField(default=timezone.now)  # 更新时间


class MerchantMarketerShip(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    marketer = models.ForeignKey(Marketer, on_delete=models.CASCADE)
    audit_datetime = models.DateTimeField(default=timezone.now)  # 商户被审核时间
    audit_info = models.CharField(max_length=256, default='')  # 审核信息(一般是驳回原因)


class CouponRule(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT)  # 所属商户
    discount = models.IntegerField(validators=[MinValueValidator(0)])  # 优惠金额
    min_charge = models.IntegerField(validators=[MinValueValidator(0)])  # 最低消费
    valid_strategy = models.IntegerField(choices=VALID_STRATEGY.model_choices())  # 有效期策略
    start_date = models.DateField(null=True, blank=True)  # 开始日期
    end_date = models.DateField(null=True, blank=True)  # 结束日期
    expiration_days = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])  # 有效期天数
    stock = models.IntegerField(validators=[MinValueValidator(0)])  # 库存
    photo_url = models.CharField(max_length=1024, null=True, blank=True)  # 照片地址2：1， min-width 380
    note = models.CharField(null=True, blank=True, max_length=300)  # 使用说明
    datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 创建时间
    update_datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 更新时间


class Coupon(models.Model):
    rule = models.ForeignKey(CouponRule, on_delete=models.PROTECT, db_index=True)  # 优惠券规则
    client = models.ForeignKey(Client, on_delete=models.CASCADE, db_index=True)  # 所属用户
    discount = models.IntegerField(validators=[MinValueValidator(0)])  # 优惠金额
    min_charge = models.IntegerField(validators=[MinValueValidator(0)])  # 最低消费
    originator_merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT,
                                            db_index=True)  # 发放优惠券的商户
    status = models.IntegerField(choices=COUPON_STATUS.model_choices())  # 优惠券状态
    obtain_datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 领取时间
    use_datetime = models.DateTimeField(null=True, blank=True, db_index=True)  # 消费时间


class Account(models.Model):
    bank_name = models.CharField(max_length=128, null=True, blank=True)  # 开户行
    bank_card_number = EncryptedCharField(max_length=128, null=True, blank=True, db_index=True, unique=True,
                                          key=AES_KEY)  # 银行卡号
    real_name = models.CharField(max_length=128, null=True, blank=True)  # 真实姓名
    balance = models.IntegerField(validators=[MinValueValidator(0)])  # 微信余额
    withdrawable_balance = models.IntegerField(validators=[MinValueValidator(0)])  # 微信可提现余额
    alipay_balance = models.IntegerField(validators=[MinValueValidator(0)])  # 支付宝余额
    alipay_withdrawable_balance = models.IntegerField(validators=[MinValueValidator(0)])  # 支付宝可提现余额


class VerifiedBankAccount(models.Model):
    bank_name = models.CharField(max_length=128, null=True, blank=True)  # 开户行
    bank_card_number = EncryptedCharField(max_length=128, null=True, blank=True, key=AES_KEY)  # 银行卡号
    real_name = models.CharField(max_length=128, null=True, blank=True)  # 真实姓名
    verify_status = models.IntegerField(choices=VERIFY_ACCOUNT_STATUS.model_choices(),
                                        default=VERIFY_ACCOUNT_STATUS.VERIFYING)  # 验证状态
    request_number = models.CharField(max_length=32, null=True, blank=True)  # 阿里云接口返回的请求单号，用于获取验证结果
    marketer = models.ForeignKey(Marketer, on_delete=models.SET_NULL, null=True)  # 发起验证的邀请人
    datetime = models.DateTimeField(default=timezone.now)  # 验证通过的时间

    class Meta:
        unique_together = ('bank_name', 'bank_card_number', 'real_name')


class Payment(models.Model):
    serial_number = models.CharField(max_length=32, primary_key=True)  # 流水号
    transactions = GenericRelation('Transaction')
    datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 支付时间
    pay_channel = models.IntegerField(choices=PAY_CHANNELS.model_choices())  # 支付渠道，支付宝/微信
    status = models.IntegerField(choices=PAYMENT_STATUS.model_choices())  # 支付状态
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, db_index=True)  # 收款商户
    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_index=True)  # 付款客户
    order_price = models.IntegerField(validators=[MinValueValidator(0)])  # 订单总金额
    coupon = models.OneToOneField(Coupon, null=True, on_delete=models.PROTECT,
                                  db_index=True)  # 使用的优惠券
    coupon_granted = models.BooleanField(default=False)  # 这个订单是否已经发放过优惠券了

    platform_share = models.IntegerField(validators=[MinValueValidator(0)])  # 平台分成
    inviter_share = models.IntegerField(validators=[MinValueValidator(0)])  # 邀请人分成
    originator_share = models.IntegerField(validators=[MinValueValidator(0)])  # 引流商户分成
    note = models.TextField(null=True, blank=True)  # 备注


class Refund(models.Model):
    serial_number = models.CharField(max_length=32, primary_key=True)  # 流水号
    transactions = GenericRelation('Transaction')
    datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 退款时间
    status = models.IntegerField(choices=REFUND_STATUS.model_choices())  # 状态
    payment = models.ForeignKey(Payment, db_index=True, on_delete=models.PROTECT)


class Withdraw(models.Model):
    withdraw_type = models.IntegerField(choices=WITHDRAW_TYPE.model_choices())
    serial_number = models.CharField(max_length=32, primary_key=True)  # 流水号
    transactions = GenericRelation('Transaction')
    datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 提现时间
    status = models.IntegerField(choices=WITHDRAW_STATUS.model_choices())  # 状态
    account = models.ForeignKey(Account, on_delete=models.PROTECT, db_index=True)  # 提现账户
    amount = models.IntegerField(validators=[MinValueValidator(0)])  # 提现金额


class Settlement(models.Model):
    serial_number = models.CharField(max_length=32, primary_key=True)  # 流水号
    transactions = GenericRelation('Transaction')
    datetime = models.DateTimeField(default=timezone.now, db_index=True)  # 生成结算账单时间
    finished_datetime = models.DateTimeField(db_index=True, null=True, blank=True)  # 已结算时间
    status = models.IntegerField(choices=SETTLEMENT_STATUS.model_choices())  # 状态
    account = models.ForeignKey(Account, on_delete=models.PROTECT, db_index=True)  # 商户账户
    wechat_amount = models.IntegerField(validators=[MinValueValidator(0)])  # 微信结算金额
    alipay_amount = models.IntegerField(validators=[MinValueValidator(0)])  # 支付宝结算金额


class TransferRecord(models.Model):
    """ 转账记录 目前是支付宝账号验证 """
    serial_number = models.CharField(max_length=32, primary_key=True)  # 流水号
    account_number = models.CharField(max_length=128, db_index=True)  # 邀请人支付宝登陆账号：一般是邮箱或手机
    account_name = models.CharField(max_length=64, db_index=True)  # 支付宝用户真实姓名
    wechat_unionid = models.CharField(max_length=128, db_index=True)  # 微信unionid
    status = models.IntegerField(choices=TRANSFER_STATUS.model_choices())  # 状态
    amount = models.IntegerField()
    datetime = models.DateTimeField(default=timezone.now)  # 转账时间


class Transaction(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=32, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPE.model_choices())
    datetime = models.DateTimeField(default=timezone.now, db_index=True)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, db_index=True)
    amount = models.IntegerField()
    balance_after_transaction = models.IntegerField(validators=[MinValueValidator(0)])


class Message(models.Model):
    content = models.CharField(max_length=1024, null=True, blank=True)  # 消息内容
    create_time = models.DateTimeField(default=timezone.now)  # 创建时间
    status = models.IntegerField(choices=MESSAGE_STATUS.model_choices())  # 消息状态
    type = models.IntegerField(choices=MESSAGE_TYPE.model_choices())  # 消息类型
    extra_data = models.CharField(max_length=256, default='{}')  # json field


class SubscriptionAccountReply(models.Model):
    """ 公众号回复 """
    create_time = models.DateTimeField(default=timezone.now)  # 创建时间
    status = models.IntegerField(choices=SUBSCRIPTION_ACCOUNT_REPLY_STATUS.model_choices())  # 规则状态
    rule_name = models.CharField(max_length=60, null=True, blank=True)  # 规则名
    question_text = models.CharField(max_length=30, null=True, blank=True)  # 问题关键字
    reply_rule = models.IntegerField(choices=SUBSCRIPTION_ACCOUNT_REPLY_RULE.model_choices())  # 回复规则: 半匹配、全匹配、不匹配
    reply_text = models.CharField(max_length=300, null=True, blank=True)  # 回复文本
    reply_type = models.IntegerField(choices=SUBSCRIPTION_ACCOUNT_REPLY_TYPE.model_choices())  # 回复类型: 关注回复，关键字回复，其他回复
    reply_account = models.IntegerField(choices=SUBSCRIPTION_ACCOUNT_REPLY_ACCOUNT.model_choices())  # 回复的公众号: 用户、商户、业务员
