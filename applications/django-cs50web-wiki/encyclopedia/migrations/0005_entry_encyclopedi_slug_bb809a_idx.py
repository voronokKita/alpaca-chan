# Generated by Django 4.0.6 on 2022-07-18 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encyclopedia', '0004_alter_entry_slug'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='entry',
            index=models.Index(fields=['slug'], name='encyclopedi_slug_bb809a_idx'),
        ),
    ]
