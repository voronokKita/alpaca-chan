# Generated by Django 4.1 on 2022-08-22 12:57

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='choice',
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='question',
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
    ]