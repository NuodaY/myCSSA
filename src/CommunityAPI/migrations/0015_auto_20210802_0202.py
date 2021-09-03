# Generated by Django 3.1.12 on 2021-08-01 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CommunityAPI', '0014_notification_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='CommunityAPI.post'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(choices=[('REPLY', '回复'), ('CENSOR', '屏蔽'), ('DECENSOR', '解除屏蔽'), ('FAVORITE', '收藏')], max_length=100, verbose_name='通知类型'),
        ),
    ]