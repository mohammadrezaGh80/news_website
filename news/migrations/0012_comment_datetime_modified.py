# Generated by Django 4.1.1 on 2023-01-20 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0011_commentrelation'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='datetime_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
