import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class ApiKey(models.Model):
    """
    API key model for authenticating external services.
    Each API key is associated with a user and can be used to 
    access the API endpoints.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='api_keys',
        verbose_name=_('User')
    )
    description = models.CharField(
        _('Description'), 
        max_length=255,
        help_text=_('A description to help you identify this API key')
    )
    key = models.CharField(
        _('API Key'), 
        max_length=40, 
        unique=True,
        help_text=_('The API key used for authentication')
    )
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    is_active = models.BooleanField(_('Active'), default=True)
    last_used = models.DateTimeField(_('Last used'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expires at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')
        ordering = ['-created_at']
        app_label = 'tagwiseapp'
    
    def __str__(self):
        return f"{self.description} ({self.user.username})"
    
    @property
    def is_valid(self):
        """
        Check if the API key is valid (active and not expired).
        """
        import datetime
        from django.utils import timezone
        
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
            
        return True 