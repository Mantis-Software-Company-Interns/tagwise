# Manual migration for registering the existing ApiKey model

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagwiseapp', '0014_add_updated_at_to_chatmessage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='ApiKey',
                    fields=[
                        ('id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('description', models.CharField(help_text='A description to help you identify this API key', max_length=255, verbose_name='Description')),
                        ('key', models.CharField(help_text='The API key used for authentication', max_length=40, unique=True, verbose_name='API Key')),
                        ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                        ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                        ('last_used', models.DateTimeField(blank=True, null=True, verbose_name='Last used')),
                        ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expires at')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                    ],
                    options={
                        'verbose_name': 'API Key',
                        'verbose_name_plural': 'API Keys',
                        'ordering': ['-created_at'],
                        'app_label': 'tagwiseapp',
                    },
                ),
            ]
        ),
    ] 