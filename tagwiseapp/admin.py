from django.contrib import admin
from .models import Category, Tag, Collection

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
