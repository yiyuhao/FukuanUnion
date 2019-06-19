from rest_framework import serializers
from common.models import Merchant, Area, MerchantMarketerShip
from marketer.model_manager import CreateMerchantManager, UserMerchantModelManager, PaymentQRCodeModelManager, \
    PaymentModelManager, UserTransactionModelManager, AreaModelManager
from marketer.serializers.category import NestedCategorySerializer
import config
from marketer.config import PAYMENT_QR_CODE_STATUS
from marketer.serializers.account import MerchantCreateAccountSerializer


class MerchantSerializer(serializers.ModelSerializer):
    """商铺信息"""

    class Meta:
        model = Merchant
        fields = (
            'id',
            'status',
            'name',
            'avatar_url',
            'update_datetime',
            'sharing'
        )

    sharing = serializers.SerializerMethodField()
    update_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    def get_sharing(self, obj):
        manager = UserTransactionModelManager(self.context['request'].user)
        return manager.get_sharing(merchant=obj)


class AuditMerchantSerializer(serializers.Serializer):
    """审核商户"""
    status = serializers.IntegerField(write_only=True)
    audit_info = serializers.CharField(write_only=True, required=False)
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('AuditMerchantSerializer cannot be used to create')

    def update(self, instance, validated_data):
        manager = UserMerchantModelManager(user=self.context['request'].user)
        return manager.audit_merchant(merchant_instance=instance, to_status=validated_data.get('status', ''),
                                      audit_info=validated_data.get('audit_info', ''))


class MerchantAdminSerializer(serializers.Serializer):
    """管理员"""

    wechat_openid = serializers.CharField()
    wechat_unionid = serializers.CharField()
    wechat_avatar_url = serializers.CharField()
    wechat_nickname = serializers.CharField()
    alipay_userid = serializers.CharField()
    alipay_user_name = serializers.CharField()

    def create(self, validated_data):
        raise NotImplementedError('MerchantAdminSerializer cannot be used to create')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantAdminSerializer cannot be used to create')


class CreateMerchantSerializer(serializers.Serializer):
    """创建商户"""
    type = serializers.IntegerField(default=config.MERCHANT_TYPE.INDIVIDUAL)
    name = serializers.CharField(max_length=128, write_only=True)
    category_id = serializers.IntegerField(write_only=True)
    contact_phone = serializers.CharField(max_length=32, write_only=True)
    area_id = serializers.IntegerField()
    address = serializers.CharField(max_length=512, write_only=True)
    location_lon = serializers.FloatField(write_only=True)
    location_lat = serializers.FloatField(write_only=True)
    description = serializers.CharField(write_only=True)
    avatar_url = serializers.CharField(max_length=1024, write_only=True)
    photo_url = serializers.CharField(max_length=1024, write_only=True, required=False)
    license_url = serializers.CharField(max_length=1024, required=False, write_only=True, allow_blank=True,
                                        allow_null=True)
    id_card_front_url = serializers.CharField(max_length=1024, required=False, write_only=True, allow_blank=True,
                                              allow_null=True)
    id_card_back_url = serializers.CharField(max_length=1024, required=False, write_only=True, allow_blank=True,
                                             allow_null=True)
    payment_qr_code = serializers.CharField(write_only=True)

    merchant_admin_data = MerchantAdminSerializer(write_only=True)

    merchant_acct_data = MerchantCreateAccountSerializer(write_only=True)

    id = serializers.IntegerField(read_only=True)

    def validate_payment_qr_code(self, payment_qr_code):
        manager = PaymentQRCodeModelManager()
        res = manager.can_use(code=payment_qr_code)
        if res[0] == PAYMENT_QR_CODE_STATUS['DOES_NOT_EXIST']:
            raise serializers.ValidationError('付款码不存在')
        elif res[0] == PAYMENT_QR_CODE_STATUS['HAS_BEEN_BIND']:
            raise serializers.ValidationError('付款码已被其他商家绑定')
        elif res[0] == PAYMENT_QR_CODE_STATUS['CAN_USE']:
            return res[1]

    def validate_area_id(self, area_id):
        area_handler = AreaModelManager()
        instance = area_handler.check_and_complete_adcode(adcode=area_id)
        if instance:
            return instance.id
        else:
            raise serializers.ValidationError('区域不存在')

    def validate(self, attrs):
        account_info = list(attrs['merchant_acct_data'].values())
        account_type = attrs['type']
        license_url = attrs.get('license_url', '')
        id_card_front_url = attrs.get('id_card_front_url', '')
        id_card_back_url = attrs.get('id_card_back_url', '')
        if account_type == config.MERCHANT_TYPE.ENTERPRISE:
            attrs['id_card_front_url'] = ''
            attrs['id_card_back_url'] = ''
            if not all(account_info):
                raise serializers.ValidationError('企业商户银行信息不能为空')
            if not license_url:
                raise serializers.ValidationError('企业营业执照不能为空')
        if account_type == config.MERCHANT_TYPE.INDIVIDUAL:
            attrs['license_url'] = ''
            if not all([id_card_front_url, id_card_back_url]):
                raise serializers.ValidationError('身份证不能为空')
        return attrs

    def create(self, validated_data):
        merchant_acct_data = validated_data.pop('merchant_acct_data')
        merchant_admin_data = validated_data.pop('merchant_admin_data')
        validated_data.update(
            inviter=self.context['request'].user,

        )
        manager = CreateMerchantManager()
        return manager.create(merchant_data=validated_data,
                              merchant_admin_data=merchant_admin_data,
                              merchant_acct_data=merchant_acct_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('CreateMerchantSerializer cannot be used for updating')


class MerchantDetailSerializer(serializers.ModelSerializer):
    """商户详情"""

    class Meta:
        model = Merchant
        fields = (
            'status',
            'name',
            'category',
            'contact_phone',
            'address',
            'description',
            'avatar_url',
            'photo_url',
            'license_url',
            'id_card_front_url',
            'id_card_back_url',
            'create_datetime',
            'audit_info',
            'id',
            'admin',
            'alipay',
            'qr_code'
        )

    category = NestedCategorySerializer()
    create_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    audit_info = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    alipay = serializers.SerializerMethodField()
    qr_code = serializers.SerializerMethodField()

    def get_audit_info(self, obj):
        audit_instance = MerchantMarketerShip.objects.filter(merchant=obj).order_by('-audit_datetime').first()
        if audit_instance:
            return audit_instance.audit_info
        else:
            return None

    def get_admin(self, obj):
        return obj.admins.filter(merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN).first().wechat_nickname

    def get_alipay(self, obj):
        return obj.admins.filter(merchant_admin_type=config.MERCHANT_ADMIN_TYPES.ADMIN).first().alipay_user_name

    def get_qr_code(self, obj):
        return 'NO.%04d' % obj.payment_qr_code.id

    def create(self, validated_data):
        raise NotImplementedError('MerchantDetailSerializer cannot be used for creating')

    def update(self, instance, validated_data):
        raise NotImplementedError('MerchantDetailSerializer cannot be used for updating')
