# Generated by Django 4.0.4 on 2022-06-01 11:51

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 6, 1, 11, 51, 40, 408937, tzinfo=utc), verbose_name='date published'),
        ),
    ]