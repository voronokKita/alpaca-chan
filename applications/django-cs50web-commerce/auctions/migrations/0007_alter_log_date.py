# Generated by Django 4.1 on 2022-08-08 11:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_alter_log_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.localtime),
        ),
    ]
