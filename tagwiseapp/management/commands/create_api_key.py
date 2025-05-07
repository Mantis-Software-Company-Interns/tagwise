import secrets
import string
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from tagwiseapp.api.models import ApiKey


class Command(BaseCommand):
    help = 'Creates an API key for a user'

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument('username', type=str, help='Username of the user to create an API key for')
        
        # Optional arguments
        parser.add_argument('--description', type=str, help='Description for the API key', default='API Key')
        parser.add_argument('--days', type=int, help='Number of days until the API key expires', default=None)
        parser.add_argument('--active', action='store_true', help='Set the API key as active')

    def handle(self, *args, **options):
        username = options['username']
        description = options['description']
        days = options['days']
        is_active = options.get('active', True)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        # Generate a random API key
        key_chars = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(key_chars) for _ in range(30))
        
        # Calculate expiry date if provided
        expires_at = None
        if days is not None:
            expires_at = timezone.now() + timedelta(days=days)
        
        # Create the API key
        api_key = ApiKey.objects.create(
            user=user,
            description=description,
            key=key,
            is_active=is_active,
            expires_at=expires_at
        )
        
        self.stdout.write(self.style.SUCCESS(f'API key created successfully'))
        self.stdout.write(f'Key: {key}')
        self.stdout.write(f'Description: {description}')
        self.stdout.write(f'User: {user.username}')
        self.stdout.write(f'Active: {is_active}')
        
        if expires_at:
            self.stdout.write(f'Expires: {expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write('Expires: Never')
            
        self.stdout.write("\nImportant: Save this API key in a secure place. You won't be able to view it again.") 