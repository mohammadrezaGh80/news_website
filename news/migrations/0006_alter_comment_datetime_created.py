# Generated by Django 4.1.1 on 2022-11-30 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_alter_comment_datetime_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='datetime_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
