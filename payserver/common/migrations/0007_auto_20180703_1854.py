# Generated by Django 2.0.6 on 2018-07-03 18:54

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_auto_20180629_1053'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=1024)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.IntegerField(verbose_name=((0, 'DELETE'), (1, 'READ'), (2, 'UNREAD')))),
                ('type', models.IntegerField(verbose_name=((0, 'AREA_WITHOUT_MARKETER'),))),
                ('extra_data', models.CharField(default='{}', max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='area',
            name='adcode',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AddField(
            model_name='marketer',
            name='id_card_back_url',
            field=models.CharField(default='', max_length=1024),
        ),
        migrations.AddField(
            model_name='marketer',
            name='id_card_front_url',
            field=models.CharField(default='', max_length=1024),
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
    ]