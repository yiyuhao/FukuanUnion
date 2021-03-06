# Generated by Django 2.0.4 on 2018-08-15 16:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0025_auto_20180809_1810'),
    ]

    operations = [
        migrations.AddField(
            model_name='couponrule',
            name='update_datetime',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='status',
            field=models.IntegerField(choices=[(0, 'NOT_USED'), (1, 'USED'), (2, 'DESTROYED')]),
        ),
    ]
