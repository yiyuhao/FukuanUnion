# Generated by Django 2.0.6 on 2018-07-31 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0021_subscriptionaccountreply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='openid',
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='marketer',
            name='wechat_openid',
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='merchantadmin',
            name='wechat_openid',
            field=models.CharField(db_index=True, max_length=128, unique=True),
        ),
    ]
