# Generated by Django 4.2.11 on 2024-03-08 16:11

from django.db import migrations
import django_ckeditor_5.fields
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='image',
            field=sorl.thumbnail.fields.ImageField(blank=True, help_text='При выборе картинки, она считается в приоритете', upload_to='tasks/', verbose_name='картинка'),
        ),
        migrations.AlterField(
            model_name='task',
            name='text',
            field=django_ckeditor_5.fields.CKEditor5Field(blank=True, help_text='Введите текст напоминания.', verbose_name='текст напоминания'),
        ),
    ]