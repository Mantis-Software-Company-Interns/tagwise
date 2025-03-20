from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Bookmark, Category, Tag, UserProfile, Collection

class BookmarkForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        fields = ['url', 'title', 'description', 'main_categories', 'subcategories', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'main_categories': forms.SelectMultiple(attrs={'class': 'select2'}),
            'subcategories': forms.SelectMultiple(attrs={'class': 'select2'}),
            'tags': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']
        widgets = {
            'parent': forms.Select(attrs={'class': 'select2'}),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['theme_preference', 'default_view', 'items_per_page']
        widgets = {
            'theme_preference': forms.Select(attrs={'class': 'form-control'}),
            'default_view': forms.Select(attrs={'class': 'form-control'}),
            'items_per_page': forms.NumberInput(attrs={'class': 'form-control', 'min': 4, 'max': 48}),
        }

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description', 'icon']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.Select(attrs={'class': 'select2'}),
        } 