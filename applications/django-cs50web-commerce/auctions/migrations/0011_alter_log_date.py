# Generated by Django 4.1 on 2022-08-21 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0010_alter_listing_options_profile_user_model_pk_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
