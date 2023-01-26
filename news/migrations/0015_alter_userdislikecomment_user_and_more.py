# Generated by Django 4.1.1 on 2023-01-24 14:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0014_rename_dislike_comment_dislikes_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdislikecomment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments_dislike', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userlikecomment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments_like', to=settings.AUTH_USER_MODEL),
        ),
    ]
