# Generated by Django 2.0.4 on 2018-11-05 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0037_verifiedbankaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='merchantadmin',
            name='voice_on',
            field=models.BooleanField(default=True),
        ),
    ]
