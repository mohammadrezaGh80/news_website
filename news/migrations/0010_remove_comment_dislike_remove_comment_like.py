# Generated by Django 4.1.1 on 2022-12-05 06:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0009_comment_dislike_comment_like'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='dislike',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='like',
        ),
    ]