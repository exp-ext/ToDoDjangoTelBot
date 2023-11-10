# Generated by Django 4.2.5 on 2023-11-09 10:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_alter_post_options_alter_comment_post_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostTags',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, unique=True, verbose_name='тэг поста')),
                ('description', models.TextField(blank=True, null=True, verbose_name='краткое описание')),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'тэг',
                'verbose_name_plural': 'тэги',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='passed_moderation',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='PostContents',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250, verbose_name='заголовок/глава/раздел')),
                ('anchor', models.CharField(max_length=250, verbose_name='якорь')),
                ('desc', models.CharField(max_length=255)),
                ('is_root', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children_set', to='posts.postcontents')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='posts.post', verbose_name='глава')),
            ],
            options={
                'verbose_name': 'оглавление',
                'verbose_name_plural': 'оглавления',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(related_name='posts', to='posts.posttags'),
        ),
    ]