# Generated by Django 5.0.6 on 2024-09-17 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_remove_userquiz_updated_at_userquiz_comment_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userquiz',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userquiz',
            name='status',
            field=models.TextField(),
        ),
    ]
