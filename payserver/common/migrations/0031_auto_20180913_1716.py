# Generated by Django 2.0.4 on 2018-09-13 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0030_auto_20180917_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketer',
            name='wechat_avatar_url',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='merchantadmin',
            name='phone',
            field=models.CharField(db_index=True, default='', max_length=32),
        ),
    ]
