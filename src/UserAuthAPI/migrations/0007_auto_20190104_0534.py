# Generated by Django 2.1.3 on 2019-01-04 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserAuthAPI', '0006_auto_20190103_0454'),
    ]

    operations = [
        migrations.AddField(
            model_name='cssadept',
            name='brief',
            field=models.CharField(blank=True, default=None, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='cssadept',
            name='description',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]