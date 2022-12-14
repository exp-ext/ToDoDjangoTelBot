# Generated by Django 4.1.4 on 2022-12-27 08:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_user_birthday'),
        ('tasks', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='user_date',
        ),
        migrations.AlterField(
            model_name='task',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Если выбрать группу, то оповещения будут в ней.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='users.group', verbose_name='Группа фаворит'),
        ),
        migrations.AlterField(
            model_name='task',
            name='it_birthday',
            field=models.BooleanField(verbose_name='День рождения'),
        ),
        migrations.AlterField(
            model_name='task',
            name='reminder_period',
            field=models.CharField(choices=[('N', 'Никогда'), ('D', 'Каждый день'), ('W', 'Каждую неделю'), ('M', 'Каждый месяц'), ('Y', 'Каждый год')], default='N', help_text='Выберите период повторения напоминания.', max_length=1, verbose_name='Периодичность напоминания'),
        ),
    ]
