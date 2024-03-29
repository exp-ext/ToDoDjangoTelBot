# Generated by Django 4.2.10 on 2024-03-05 07:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('telbot', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GptModels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=28, verbose_name='модель GPT')),
                ('default', models.BooleanField(default=False, verbose_name='доступна всем по умолчанию')),
                ('token', models.CharField(max_length=51, verbose_name='токен для запроса')),
                ('context_window', models.IntegerField(verbose_name='окно токенов для передачи истории в запросе')),
                ('max_request_token', models.IntegerField(verbose_name='максимальное количество токенов в запросе пользователя')),
                ('time_window', models.IntegerField(default=30, verbose_name='окно времени для передачи истории в запросе, мин')),
            ],
            options={
                'verbose_name': 'модель GPT OpenAi',
                'verbose_name_plural': 'модели GPT OpenAi',
            },
        ),
        migrations.CreateModel(
            name='UserGptModels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_start', models.DateTimeField(default=django.utils.timezone.now, verbose_name='время начала окна для передачи истории')),
                ('active_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_for_users', to='telbot.gptmodels', verbose_name='Активная модель')),
                ('approved_models', models.ManyToManyField(related_name='approved_users', to='telbot.gptmodels')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='approved_models', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'разрешенная GPT модели юзера',
                'verbose_name_plural': 'разрешенные GPT модели юзера',
            },
        ),
    ]
