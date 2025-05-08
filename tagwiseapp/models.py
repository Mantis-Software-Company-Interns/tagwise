from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Tag(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ['name', 'user']

class Bookmark(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    main_categories = models.ManyToManyField(Category, related_name='main_bookmarks')
    subcategories = models.ManyToManyField(Category, blank=True, related_name='sub_bookmarks')
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    screenshot_data = models.CharField(max_length=255, blank=True, null=True)  # Path to the screenshot file
    
    def __str__(self):
        return self.title
    
    @property
    def screenshot_url(self):
        if self.screenshot_data:
            # Ensure the path always starts with /media/
            if self.screenshot_data.startswith('/media/'):
                return self.screenshot_data
            elif self.screenshot_data.startswith('media/'):
                return f"/{self.screenshot_data}"
            else:
                return f"/media/{self.screenshot_data}"
        return "/media/default-thumbnail.png"

class Collection(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='collections_bookmark')
    bookmarks = models.ManyToManyField(Bookmark, related_name='collections')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    new_features = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Language preference field
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('tr', 'Türkçe'),
    ]
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create/update Profile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)
        else:
            instance.profile.save()

class ChatConversation(models.Model):
    """Model to store chat conversations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=255, default="New Chat Session")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%d.%m.%Y')})"

class ChatMessage(models.Model):
    """Model to store chat messages within a conversation"""
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField(default=True)  # True if sent by user, False if bot response
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        sender = "User" if self.is_user else "Bot"
        return f"{sender}: {self.content[:50]}..." if len(self.content) > 50 else self.content