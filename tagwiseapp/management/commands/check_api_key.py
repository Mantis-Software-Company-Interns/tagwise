from django.core.management.base import BaseCommand
import os
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Check if the API key is correctly loaded from .env file'
    
    def handle(self, *args, **options):
        # Explicitly load environment variables to ensure they're loaded
        load_dotenv(override=True)
        
        # Check if API key exists in environment variables
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            self.stdout.write(self.style.ERROR("ERROR: GEMINI_API_KEY not found in environment variables"))
            self.stdout.write("Please check your .env file and make sure it contains GEMINI_API_KEY=your_key_here")
            return
            
        # Check API key format
        self.stdout.write(f"API key found: {api_key[:5]}{'*' * (len(api_key) - 5)}")
        self.stdout.write(f"API key length: {len(api_key)} characters")
        
        # Common formats for Google API keys
        if api_key.startswith("AIza"):
            self.stdout.write(self.style.SUCCESS("API key format looks valid (starts with AIza)"))
        else:
            self.stdout.write(self.style.WARNING("API key format may not be valid - Google API keys typically start with 'AIza'"))
        
        # Suggest creating a new key
        self.stdout.write("\nIf you're getting 'API key not valid' errors despite having the correct format,")
        self.stdout.write("please try the following steps:")
        self.stdout.write("1. Go to https://ai.google.dev/ (Google AI Studio)")
        self.stdout.write("2. Create an account or sign in")
        self.stdout.write("3. Get a new API key for the Gemini API")
        self.stdout.write("4. Replace your old key in the .env file")
        self.stdout.write("5. Make sure you enable the 'Generative Language API' for your key") 