# Generated by Django 5.1.6 on 2025-04-18 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagwiseapp', '0012_chatconversation_chatmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatconversation',
            name='title',
            field=models.CharField(default='New Chat Session', max_length=255),
        ),
    ]
