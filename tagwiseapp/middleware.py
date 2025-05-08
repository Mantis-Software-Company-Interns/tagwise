from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to set the language based on user preferences
    """
    def process_request(self, request):
        # Handle "Clear" requests for improved debugging
        if request.method == 'POST' and request.path == '/settings/update-language/':
            # Skip processing as this request is handled by view
            return None
        
        # Set language based on user profile if authenticated
        if request.user.is_authenticated:
            try:
                # Try to get the language preference from the user's profile
                language = request.user.profile.language
                
                # If user has a valid language preference
                if language and language in [lang[0] for lang in settings.LANGUAGES]:
                    # Activate the language
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
                    # Save the language setting in the session
                    request.session[translation.LANGUAGE_SESSION_KEY] = language
            except Exception as e:
                # Log error but continue with default language
                print(f"Error in UserLanguageMiddleware: {str(e)}")
        
        # If not authenticated or error, language will be determined by Django's 
        # built-in LocaleMiddleware or settings.LANGUAGE_CODE
        return None 