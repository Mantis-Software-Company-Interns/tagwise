from django.core.management.base import BaseCommand
import os
from tagwiseapp.rag.embeddings import get_embeddings
import logging
from dotenv import load_dotenv

# Load environment variables from .env file with priority
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test if the embeddings are working properly'
    
    def handle(self, *args, **options):
        # Check API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.stdout.write(self.style.ERROR("ERROR: GEMINI_API_KEY environment variable is not set"))
            self.stdout.write("Please set this environment variable before running the command:")
            self.stdout.write("  export GEMINI_API_KEY=your_api_key_here")
            return
            
        self.stdout.write(f"Using Gemini API key: {api_key[:5]}...")
        
        # Test embeddings
        try:
            self.stdout.write("Attempting to create embedding model...")
            embeddings = get_embeddings()
            
            if embeddings is None:
                self.stdout.write(self.style.ERROR("Failed to create embeddings. See logs for details."))
                return
                
            self.stdout.write(self.style.SUCCESS("Successfully created embedding model!"))
            
            # Test generating an embedding
            self.stdout.write("Testing embedding generation with a sample text...")
            sample_text = "This is a test of the embedding functionality."
            
            try:
                result = embeddings.embed_query(sample_text)
                embedding_length = len(result)
                
                self.stdout.write(self.style.SUCCESS(f"Successfully generated embedding with {embedding_length} dimensions!"))
                self.stdout.write(f"First 5 dimensions: {result[:5]}")
                
                self.stdout.write(self.style.SUCCESS("\nALL TESTS PASSED! The embedding system is working correctly."))
                self.stdout.write("\nYou can now proceed to index your bookmarks with:")
                self.stdout.write("  python manage.py index_bookmarks")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error generating embedding: {str(e)}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error testing embeddings: {str(e)}")) 