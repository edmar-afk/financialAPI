# Generated by Django 5.0.6 on 2024-09-17 09:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_userquiz_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userquiz',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='userquiz',
            name='comment',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userquiz',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_quiz', to='api.quiz'),
        ),
    ]
