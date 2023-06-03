# Generated by Django 4.1.7 on 2023-06-02 18:35

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='group',
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание группы'),
        ),
        migrations.AlterField(
            model_name='group',
            name='link',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Пригласительная ссылка для публичных групп'),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=150, verbose_name='Название группы'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='id полученное в Телеграмм'),
        ),
    ]
