# Generated by Django 4.2.11 on 2024-03-25 18:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telbot', '0006_alter_gptmodels_context_window_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPrompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=28, verbose_name='название промпта')),
                ('prompt_text', models.TextField(verbose_name='текст промпта')),
                ('default', models.BooleanField(default=False, verbose_name='по умолчанию')),
            ],
            options={
                'verbose_name': 'промпт для GPT',
                'verbose_name_plural': 'промпты для GPT',
            },
        ),
        migrations.AlterField(
            model_name='usergptmodels',
            name='active_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_for_users', to='telbot.gptmodels', verbose_name='активная модель'),
        ),
        migrations.AddField(
            model_name='usergptmodels',
            name='active_prompt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_for_user', to='telbot.userprompt', verbose_name='активный промпт'),
        ),
    ]
