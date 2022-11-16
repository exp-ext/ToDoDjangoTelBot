# Generated by Django 4.1.3 on 2022-11-15 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CelebratoryFriend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('gift', models.BooleanField(default=False)),
                ('remind_in', models.IntegerField(help_text='Оповестить за ... дней до наступления события.', verbose_name='Оповестить за ... дней')),
            ],
            options={
                'verbose_name': 'Подписка на праздники друзей',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('datetime', models.DateField(verbose_name='Дата и время мероприятия')),
                ('text', models.TextField(help_text='Введите текст напоминания.', verbose_name='Текст напоминания')),
                ('remind_in', models.IntegerField(default=120, help_text='Оповестить за ... минут до наступления события.', verbose_name='Оповестить за ... минут')),
                ('remind_at', models.TimeField(verbose_name='Время срабатывания оповещения')),
                ('reminder_period', models.CharField(choices=[('N', 'Никогда'), ('D', 'Каждый день'), ('W', 'Каждую неделю'), ('M', 'Каждый месяц'), ('Y', 'Каждый год')], default='N', max_length=1, verbose_name='Периодичность напоминания')),
            ],
            options={
                'verbose_name': 'Напоминание',
                'verbose_name_plural': 'Напоминания',
            },
        ),
        migrations.CreateModel(
            name='WishList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('wish', models.CharField(max_length=256, verbose_name='Желание')),
            ],
            options={
                'verbose_name': 'Желание',
                'verbose_name_plural': 'Желания',
            },
        ),
    ]
