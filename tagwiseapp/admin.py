from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Category, Tag, Bookmark, Profile, Collection, ChatConversation, ChatMessage
from .api.models import ApiKey

# Register your models here.

class CategoryTypeFilter(admin.SimpleListFilter):
    title = 'Category Type'
    parameter_name = 'category_type'
    
    def lookups(self, request, model_admin):
        return (
            ('main', 'Main Categories'),
            ('sub', 'Subcategories'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'main':
            return queryset.filter(parent__isnull=True)
        if self.value() == 'sub':
            return queryset.filter(parent__isnull=False)
        return queryset

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'category_type')
    list_filter = (CategoryTypeFilter, 'parent')
    search_fields = ('name',)
    
    def category_type(self, obj):
        return "Main Category" if obj.parent is None else "Subcategory"
    
    category_type.short_description = "Type"

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('bookmarks',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('id',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'created_at', 'updated_at')
    list_filter = ('conversation', 'created_at', 'updated_at')
    search_fields = ('id', 'conversation__id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('description', 'user', 'key_preview', 'created_at', 'last_used', 'is_active', 'expires_at')
    list_filter = ('is_active', 'created_at', 'expires_at', 'user')
    search_fields = ('description', 'user__username')
    readonly_fields = ('id', 'key_display', 'created_at', 'last_used')
    actions = ['generate_new_api_key']
    add_form_template = 'admin/apikey_add_form.html'
    change_form_template = 'admin/apikey_change_form.html'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'description')
        }),
        ('API Key', {
            'fields': ('key_display',),
            'classes': ('collapse',),
            'description': 'API anahtarı - Bu değer sadece bir kez gösterilir, lütfen güvenli bir yerde saklayın.'
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Info', {
            'fields': ('id', 'created_at', 'last_used')
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """
        Customize fieldsets based on whether this is an add or change view
        """
        if not obj:  # Add view
            return (
                (None, {
                    'fields': ('user', 'description', 'is_active', 'expires_at')
                }),
            )
        return super().get_fieldsets(request, obj)
    
    def key_preview(self, obj):
        """Truncated API key preview"""
        if obj.key:
            # Show only first 8 and last 4 characters
            return f"{obj.key[:8]}...{obj.key[-4:]}"
        return "-"
    
    key_preview.short_description = "API Key (Preview)"
    
    def key_display(self, obj):
        """Display the API key with a copy button"""
        if obj.key:
            return format_html(
                '<div style="font-family: monospace; padding: 10px; background-color: #f5f5f5; '
                'border-radius: 4px; margin-bottom: 10px;">'
                '<span id="api-key-value">{}</span>'
                '<button type="button" onclick="copyApiKey()" '
                'style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">'
                'Kopyala</button></div>'
                '<script>'
                'function copyApiKey() {{'
                '  const keyElem = document.getElementById("api-key-value");'
                '  const textArea = document.createElement("textarea");'
                '  textArea.value = keyElem.textContent;'
                '  document.body.appendChild(textArea);'
                '  textArea.select();'
                '  document.execCommand("copy");'
                '  document.body.removeChild(textArea);'
                '  alert("API anahtarı panoya kopyalandı");'
                '}}'
                '</script>',
                obj.key
            )
        return "-"
    
    key_display.short_description = "API Key"
    
    def generate_new_api_key(self, request, queryset):
        """Generate a new API key for selected items"""
        import secrets
        import string
        from django.utils import timezone
        
        count = 0
        for api_key in queryset:
            # Generate a secure random key
            key_chars = string.ascii_letters + string.digits
            new_key = ''.join(secrets.choice(key_chars) for _ in range(32))
            
            # Update the API key
            api_key.key = new_key
            api_key.is_active = True
            api_key.last_used = None  # Reset last used time
            api_key.save()
            
            count += 1
        
        # Show success message
        if count == 1:
            message = "1 API anahtarı yeniden oluşturuldu."
        else:
            message = f"{count} API anahtarı yeniden oluşturuldu."
            
        self.message_user(request, message)
    
    generate_new_api_key.short_description = "Seçilen API anahtarları için yeni anahtar oluştur"
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle creating new API keys"""
        is_new = not obj.pk
        
        if is_new:  # If this is a new object being created
            import secrets
            import string
            
            # Generate a random key
            key_chars = string.ascii_letters + string.digits
            obj.key = ''.join(secrets.choice(key_chars) for _ in range(32))
        
        super().save_model(request, obj, form, change)
        
        if is_new:
            # Store the key in a message to display it to the user
            messages.success(
                request, 
                format_html(
                    'API anahtarı başarıyla oluşturuldu. API anahtarınız: <br><strong style="font-family: monospace;">{}</strong>'
                    '<br><br><strong>ÖNEMLİ:</strong> Bu anahtarı güvenli bir yerde saklayın. Bu ekrandan ayrıldıktan sonra '
                    'anahtarın tamamını bir daha göremeyeceksiniz.',
                    obj.key
                )
            )
    
    def response_add(self, request, obj, post_url_continue=None):
        """Customize response after adding a new API key"""
        # Use the default response
        return super().response_add(request, obj, post_url_continue)

class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created_at', 'user')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'description', 'url')
    filter_horizontal = ('main_categories', 'subcategories', 'tags')

admin.site.register(Bookmark, BookmarkAdmin)
