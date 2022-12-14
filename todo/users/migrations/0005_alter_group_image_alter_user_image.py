# Generated by Django 4.1.4 on 2022-12-23 16:32

from django.db import migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_options_remove_user_is_admin_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='image',
            field=sorl.thumbnail.fields.ImageField(blank=True, upload_to='group', verbose_name='Логотип_группы'),
        ),
        migrations.AlterField(
            model_name='user',
            name='image',
            field=sorl.thumbnail.fields.ImageField(blank=True, upload_to='users', verbose_name='Аватар'),
        ),
    ]
