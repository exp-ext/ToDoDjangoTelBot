# Generated by Django 4.2.5 on 2023-11-02 07:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='postscounter',
            options={'ordering': ('-created_at',), 'verbose_name': 'статистика по посту', 'verbose_name_plural': 'статистика по постам'},
        ),
    ]
