# Generated by Django 4.2.7 on 2023-12-05 12:46

from django.db import migrations, models
import django_ckeditor_5.fields
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertisementWidget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('title', models.CharField(max_length=100, verbose_name='описание')),
                ('advertiser', models.CharField(max_length=100, verbose_name='рекламодатель')),
                ('script', models.TextField(verbose_name='скрипт для отображения в станице')),
                ('form', models.CharField(choices=[('l', 'линейная форма'), ('s', 'квадратная форма')], default='l', max_length=1, verbose_name='тип виджета')),
            ],
            options={
                'verbose_name': 'скрипт рекламного виджета',
                'verbose_name_plural': 'скрипты рекламных виджетов',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='PartnerBanner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('title', models.CharField(max_length=100, verbose_name='заголовок')),
                ('image', sorl.thumbnail.fields.ImageField(upload_to='advertising/', verbose_name='картинка')),
                ('reference', models.CharField(max_length=200, verbose_name='партнерская ссылка')),
                ('text', django_ckeditor_5.fields.CKEditor5Field(verbose_name='слоган банера')),
            ],
            options={
                'verbose_name': 'банер на сайте',
                'verbose_name_plural': 'банеры на сайте',
            },
        ),
        migrations.CreateModel(
            name='TelegramMailing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('title', models.CharField(max_length=100, verbose_name='заголовок')),
                ('image', sorl.thumbnail.fields.ImageField(upload_to='advertising/', verbose_name='картинка')),
                ('text', django_ckeditor_5.fields.CKEditor5Field(verbose_name='слоган банера')),
                ('reference', models.CharField(blank=True, max_length=200, null=True, verbose_name='партнерская ссылка')),
                ('target', models.CharField(choices=[('u', 'все пользователи'), ('g', 'все группы')], default='u', max_length=1, verbose_name='получатели')),
                ('remind_at', models.DateTimeField(verbose_name='время срабатывания')),
            ],
            options={
                'verbose_name': 'телеграмм рассылка',
                'verbose_name_plural': 'телеграмм рассылки',
            },
        ),
    ]
