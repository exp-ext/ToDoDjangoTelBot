# Generated by Django 4.1.3 on 2022-11-19 15:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_rename_remind_in_task_remind_min_task_remind_hour'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='remind_hour',
        ),
    ]
