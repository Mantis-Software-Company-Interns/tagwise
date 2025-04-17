from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tagwiseapp.rag.indexer import index_user_bookmarks
from tagwiseapp.models import Bookmark
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file with priority
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Index all bookmarks for all users or a specific user'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user_id',
            type=int,
            help='Optional: User ID to index bookmarks for a specific user only',
            required=False
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output with detailed error messages',
            required=False
        )
        
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        verbose = options.get('verbose', False)
        
        # Check for API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.stdout.write(self.style.ERROR("ERROR: GEMINI_API_KEY environment variable is not set"))
            self.stdout.write("Please set this environment variable before running the command:")
            self.stdout.write("  export GEMINI_API_KEY=your_api_key_here")
            return
            
        self.stdout.write(f"Using Gemini API key: {api_key[:5]}...")
        
        if user_id:
            # Index bookmarks for a specific user
            try:
                user = User.objects.get(id=user_id)
                bookmark_count = Bookmark.objects.filter(user=user).count()
                
                self.stdout.write(f"Indexing {bookmark_count} bookmarks for user {user.username} (ID: {user_id})...")
                
                if bookmark_count == 0:
                    self.stdout.write(self.style.WARNING(f"No bookmarks found for user {user.username}"))
                    return
                
                result = index_user_bookmarks(user_id)
                if result:
                    self.stdout.write(self.style.SUCCESS(f"Successfully indexed {bookmark_count} bookmarks for user {user.username}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to index bookmarks for user {user.username}"))
                    if verbose:
                        self.stdout.write("Check the logs for detailed error messages")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} does not exist"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
        else:
            # Index bookmarks for all users
            users = User.objects.all()
            total_users = users.count()
            success_count = 0
            
            self.stdout.write(f"Indexing bookmarks for {total_users} users...")
            
            for user in users:
                bookmark_count = Bookmark.objects.filter(user=user).count()
                self.stdout.write(f"Processing user {user.username} (ID: {user.id}) with {bookmark_count} bookmarks...")
                
                if bookmark_count == 0:
                    self.stdout.write(self.style.WARNING(f"No bookmarks found for user {user.username}"))
                    continue
                
                result = index_user_bookmarks(user.id)
                if result:
                    self.stdout.write(self.style.SUCCESS(f"Successfully indexed {bookmark_count} bookmarks for user {user.username}"))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to index bookmarks for user {user.username}"))
                    if verbose:
                        self.stdout.write("Check the logs for detailed error messages")
                    
            self.stdout.write(self.style.SUCCESS(f"Finished indexing bookmarks. Success: {success_count}/{total_users} users")) 