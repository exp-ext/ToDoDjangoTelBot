# Generated by Django 4.2.7 on 2023-12-03 06:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('advertising', '0003_advertisementwidget_advertiser'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='advertisementwidget',
            options={'ordering': ('-created_at',), 'verbose_name': 'скрипт рекламного виджета', 'verbose_name_plural': 'скрипты рекламных виджетов'},
        ),
    ]
