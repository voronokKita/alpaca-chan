# Generated by Django 4.0.6 on 2022-07-27 05:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_alter_question_options_alter_choice_choice_text_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='choice',
            options={'ordering': ['-votes']},
        ),
    ]
