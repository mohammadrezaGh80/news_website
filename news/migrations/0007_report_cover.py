# Generated by Django 4.1.1 on 2022-11-30 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0006_alter_comment_datetime_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='cover',
            field=models.ImageField(blank=True, upload_to='covers/'),
        ),
    ]