# Generated by Django 2.0.4 on 2018-08-09 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0024_merge_20180806_1704'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.IntegerField(choices=[(0, 'UNPAID'), (1, 'FROZEN'), (2, 'REFUND_REQUESTED'), (3, 'REFUND'), (4, 'REFUND_FAILED'), (5, 'FINISHED')]),
        ),
    ]
