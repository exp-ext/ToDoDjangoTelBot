# Generated by Django 4.1.3 on 2022-11-19 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='remind_in',
            new_name='remind_min',
        ),
        migrations.AddField(
            model_name='task',
            name='remind_hour',
            field=models.IntegerField(default=8, help_text='Сообщить в ... часов, если нет времени.', verbose_name='Сообщить в ... часов'),
        ),
    ]