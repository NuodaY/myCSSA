# Generated by Django 2.1.7 on 2019-03-20 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserAuthAPI', '0014_auto_20190319_0301'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_business_account',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_council_member',
            field=models.BooleanField(default=False),
        ),
    ]