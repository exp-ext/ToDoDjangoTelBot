# Generated by Django 4.1.7 on 2023-04-05 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telbot', '0004_historywhisper'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historywhisper',
            name='file_id',
            field=models.CharField(max_length=128, verbose_name='Id файла'),
        ),
    ]
