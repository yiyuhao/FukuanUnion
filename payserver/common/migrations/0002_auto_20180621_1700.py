# Generated by Django 2.0.6 on 2018-06-21 17:00

import django.core.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketer',
            name='phone',
            field=models.CharField(default='', max_length=32),
        ),
        migrations.AddField(
            model_name='merchant',
            name='create_datetime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='account',
            name='balance',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='account',
            name='withdrawable_balance',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='client',
            name='openid_channel',
            field=models.IntegerField(verbose_name=((0, 'WECHAT'), (1, 'ALIPAY'))),
        ),
        migrations.AlterField(
            model_name='client',
            name='status',
            field=models.IntegerField(default=0, verbose_name=((0, 'USING'), (1, 'DISABLED'))),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='discount',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='min_charge',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='couponrule',
            name='discount',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='couponrule',
            name='min_charge',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='marketer',
            name='inviter_type',
            field=models.IntegerField(verbose_name=((0, 'MARKETER'), (1, 'SALESMAN'))),
        ),
        migrations.AlterField(
            model_name='merchantadmin',
            name='merchant_admin_type',
            field=models.IntegerField(verbose_name=((0, 'ADMIN'), (1, 'CASHIER'))),
        ),
        migrations.AlterField(
            model_name='merchantadmin',
            name='status',
            field=models.IntegerField(verbose_name=((0, 'USING'), (1, 'DISABLED'))),
        ),
        migrations.AlterField(
            model_name='payment',
            name='inviter_share',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order_price',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='originator_share',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_channel',
            field=models.IntegerField(verbose_name=((0, 'WECHAT'), (1, 'ALIPAY'))),
        ),
        migrations.AlterField(
            model_name='payment',
            name='platform_share',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='systemadmin',
            name='status',
            field=models.IntegerField(verbose_name=((0, 'USING'), (1, 'DISABLED'))),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=6, max_digits=20),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='balance_after_transaction',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.IntegerField(verbose_name=((0, 'MERCHANT_RECEIVE'), (1, 'MERCHANT_REFUND'), (2, 'MERCHANT_WITHDRAW'), (3, 'MERCHANT_SHARE'), (4, 'MERCHANT_SHARE_REFUND'), (5, 'MARKETER_SHARE'), (6, 'MARKETER_SHARE_REFUND'), (7, 'MARKETER_WITHDRAW'), (8, 'PLATFORM_SHARE'), (9, 'PLATFORM_SHARE_REFUND'))),
        ),
        migrations.AlterField(
            model_name='withdraw',
            name='amount',
            field=models.DecimalField(decimal_places=6, max_digits=20, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
