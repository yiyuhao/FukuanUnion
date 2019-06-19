# Generated by Django 2.0.4 on 2018-07-19 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0017_auto_20180718_1343'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='serial_number',
            new_name='object_id',
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.IntegerField(choices=[(0, 'UNPAID'), (1, 'FROZEN'), (2, 'REFUND_REQUESTED'), (3, 'REFUND'), (4, 'FINISHED')]),
        ),
    ]
