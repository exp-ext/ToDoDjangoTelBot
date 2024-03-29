# Generated by Django 4.2.7 on 2023-12-05 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostsCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('browser', models.CharField(max_length=200, verbose_name='браузер')),
                ('os', models.CharField(max_length=200, verbose_name='операционная система')),
                ('is_bot', models.BooleanField(default=False)),
                ('is_mobile', models.BooleanField(default=False)),
                ('is_pc', models.BooleanField(default=False)),
                ('is_tablet', models.BooleanField(default=False)),
                ('is_touch_capable', models.BooleanField(default=False)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_count', to='posts.post')),
            ],
            options={
                'verbose_name': 'статистика по посту',
                'verbose_name_plural': 'статистика по постам',
                'ordering': ('-created_at',),
            },
        ),
    ]
