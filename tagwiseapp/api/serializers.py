from rest_framework import serializers
from tagwiseapp.models import Category, Tag
from .models import ApiKey


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model"""
    # Add a field to show the full category path (for hierarchical representation)
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'full_path']
        read_only_fields = ['id']
    
    def get_full_path(self, obj):
        """Get the full hierarchical path of the category"""
        path = obj.name
        parent = obj.parent
        
        while parent:
            path = f"{parent.name} > {path}"
            parent = parent.parent
            
        return path


class FlatCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model that represents categories in a flat structure,
    suitable for integration with external systems that don't support hierarchical categories.
    """
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model"""
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class ApiKeySerializer(serializers.ModelSerializer):
    """Serializer for the ApiKey model"""
    class Meta:
        model = ApiKey
        fields = ['id', 'description', 'key', 'created_at', 'is_active', 'last_used', 'expires_at']
        read_only_fields = ['id', 'key', 'created_at', 'last_used']


class ApiKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new API key"""
    
    key = serializers.CharField(read_only=True)
    
    class Meta:
        model = ApiKey
        fields = ['id', 'description', 'key', 'is_active', 'expires_at']
        read_only_fields = ['id', 'key']
    
    def create(self, validated_data):
        """Create a new API key with a randomly generated key"""
        import secrets
        import string
        
        # Generate a random key
        key_chars = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(key_chars) for _ in range(30))
        
        # Add the user from the request
        validated_data['user'] = self.context['request'].user
        validated_data['key'] = key
        
        return super().create(validated_data)


class CategoryAssignmentSerializer(serializers.Serializer):
    """Serializer for content categorization endpoint"""
    content = serializers.CharField(required=True)
    url = serializers.URLField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    format = serializers.ChoiceField(choices=['flat', 'hierarchical'], default='flat')
    external_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class BookmarkCreateSerializer(serializers.Serializer):
    """Serializer for creating new bookmarks through the API"""
    url = serializers.URLField(required=True)
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    external_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    external_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    ) 