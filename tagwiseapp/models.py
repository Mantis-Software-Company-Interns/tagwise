from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Bookmark(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    main_categories = models.ManyToManyField(Category, related_name='main_bookmarks')
    subcategories = models.ManyToManyField(Category, blank=True, related_name='sub_bookmarks')
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    
    def __str__(self):
        return self.title

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
