# Generated by Django 4.1 on 2022-08-10 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0008_alter_listing_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='date_published',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='published'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='username',
            field=models.CharField(db_index=True, max_length=30),
        ),
    ]
