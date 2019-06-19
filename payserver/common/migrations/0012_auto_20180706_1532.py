# Generated by Django 2.0.4 on 2018-07-06 15:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0011_auto_20180705_1744'),
    ]

    operations = [
        migrations.CreateModel(
            name='MerchantMarketerShip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audit_datetime', models.DateTimeField(null=True)),
            ],
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
            model_name='marketer',
            name='inviter_type',
            field=models.IntegerField(verbose_name=((0, 'MARKETER'), (1, 'SALESMAN'))),
        ),
        migrations.RemoveField(
            model_name='merchant',
            name='auditors',
        ),
        migrations.AddField(
            model_name='merchant',
            name='auditors',
            field=models.ManyToManyField(related_name='audited_merchants', through='common.MerchantMarketerShip',
                                         to='common.Marketer'),
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
            model_name='message',
            name='status',
            field=models.IntegerField(verbose_name=((0, 'DELETE'), (1, 'HANDLED'), (2, 'UNHANDLED'))),
        ),
        migrations.AlterField(
            model_name='message',
            name='type',
            field=models.IntegerField(verbose_name=((1, 'AREA_WITHOUT_MARKETER'),)),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pay_channel',
            field=models.IntegerField(verbose_name=((0, 'WECHAT'), (1, 'ALIPAY'))),
        ),
        migrations.AlterField(
            model_name='systemadmin',
            name='status',
            field=models.IntegerField(verbose_name=((0, 'USING'), (1, 'DISABLED'))),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.IntegerField(verbose_name=((0, 'PLATFORM_RECEIVE'), (1, 'PLATFORM_EXPEND_MERCHANT_RECEIVE'), (2, 'MERCHANT_RECEIVE'), (3, 'MERCHANT_REFUND'), (4, 'PLATFORM_EARNING_MERCHANT_REFUND'), (5, 'PLATFORM_REFUND'), (6, 'PLATFORM_EXPEND_MERCHANT_SHARE'), (7, 'MERCHANT_SHARE'), (8, 'PLATFORM_EXPEND_MARKETER_SHARE'), (9, 'MARKETER_SHARE'), (10, 'PLATFORM_EXPEND_PLATFORM_SHARE'), (11, 'PLATFORM_SHARE'), (12, 'MERCHANT_WITHDRAW'), (13, 'MARKETER_WITHDRAW'))),
        ),
        migrations.AddField(
            model_name='merchantmarketership',
            name='marketer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Marketer'),
        ),
        migrations.AddField(
            model_name='merchantmarketership',
            name='merchant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Merchant'),
        ),
    ]