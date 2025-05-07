from django.utils import timezone
from rest_framework import authentication
from rest_framework import exceptions
from .models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom API Key authentication system.
    
    This authentication class looks for an API key in the request headers
    and validates it against the database. If the API key is valid, it returns
    the associated user.
    
    Usage: Add the X-API-Key header to your requests with the API key value.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        If authentication fails, return None.
        """
        api_key_header = request.META.get('HTTP_X_API_KEY')
        
        if not api_key_header:
            return None
        
        try:
            api_key = ApiKey.objects.get(key=api_key_header)
            
            # Check if the API key is valid
            if not api_key.is_valid:
                msg = 'API key is inactive or expired.'
                raise exceptions.AuthenticationFailed(msg)
            
            # Update last used timestamp
            api_key.last_used = timezone.now()
            api_key.save(update_fields=['last_used'])
            
            # Return authenticated user
            return (api_key.user, api_key)
        
        except ApiKey.DoesNotExist:
            # Invalid API key
            return None
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthorized response.
        """
        return 'API-Key' 