# Generated by Django 4.0.6 on 2022-07-18 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encyclopedia', '0003_entry_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='slug',
            field=models.SlugField(null=True, unique=True, verbose_name='URL Shortcut (slug)'),
        ),
    ]
