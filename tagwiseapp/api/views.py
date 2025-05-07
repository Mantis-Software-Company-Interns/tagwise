from django.utils import timezone
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from tagwiseapp.models import Category, Tag, Bookmark
from .models import ApiKey
from .serializers import (
    CategorySerializer, 
    FlatCategorySerializer,
    TagSerializer,
    ApiKeySerializer, 
    ApiKeyCreateSerializer,
    CategoryAssignmentSerializer,
    BookmarkCreateSerializer
)
from .authentication import ApiKeyAuthentication


class ApiKeyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing API keys.
    This allows users to create, view, update, and delete their API keys.
    """
    serializer_class = ApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the API keys owned by the current user"""
        return ApiKey.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return ApiKeyCreateSerializer
        return ApiKeySerializer
    
    def perform_create(self, serializer):
        """Save the API key with the current user"""
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing categories.
    External services can use this to get a list of available categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the categories owned by the current user or public categories"""
        return Category.objects.filter(user=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing tags.
    External services can use this to get a list of available tags.
    """
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the tags owned by the current user or public tags"""
        return Tag.objects.filter(user=self.request.user)


class CategoryAssignmentView(APIView):
    """
    API endpoint for assigning categories to content.
    
    This endpoint accepts content (text, URL, etc.) and returns suggested
    categories based on content analysis using the same AI model used in 
    the main application's content analyzer.
    
    Input:
    - content: The content to categorize
    - url: The URL of the content (optional)
    - title: The title of the content (optional)
    - format: The format of the returned categories (flat or hierarchical)
    - external_categories: List of the external system's categories (optional)
    
    Output:
    - success: Whether the categorization was successful
    - suggested_categories: A list of suggested categories
    - matched_categories: A mapping between external categories and our categories (if external_categories provided)
    - message: A message about the categorization
    """
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_flat_categories(self, user):
        """
        Return a flattened list of categories from user's hierarchical category structure
        """
        # Get all categories for the user
        all_categories = Category.objects.filter(user=user)
        
        # Prepare a flat list with all unique categories
        flat_categories = []
        added_category_ids = set()
        
        for category in all_categories:
            if category.id not in added_category_ids:
                # Add both main and sub categories to the flat list
                flat_categories.append(category)
                added_category_ids.add(category.id)
        
        return flat_categories
    
    def analyze_content(self, content, title="", url=""):
        """
        Analyze content using the main app's AI model for categorization
        
        This function interfaces with the content_analyzer to get the best category matches
        """
        try:
            # Import content analysis modules from the main application
            from tagwiseapp.reader.content_analyzer import categorize_content
            
            # Combine title and content
            full_content = f"{title}\n\n{content}" if title else content
            
            # Call the existing categorize_content function with the user
            # to get personalized categories
            analysis_result = categorize_content(
                content=full_content, 
                url=url, 
                existing_title=title,
                use_structured_output=True,
                user=self.request.user
            )
            
            return analysis_result
                
        except Exception as e:
            # If an error occurs, log it but don't fail the API call
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error analyzing content: {str(e)}")
            return None
    
    def find_matching_categories(self, external_categories, our_categories):
        """
        Find matching categories between external system categories and our categories
        
        Args:
            external_categories: List of category names from external system
            our_categories: List of our Category objects
            
        Returns:
            Dictionary mapping external category names to our category objects
        """
        import re
        from difflib import SequenceMatcher
        
        # Clean category names for better matching
        def clean_name(name):
            if not name:
                return ""
            # Convert to lowercase, remove special chars, normalize spaces
            cleaned = re.sub(r'[^\w\s]', ' ', name.lower())
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned
        
        # Prepare our categories with cleaned names for matching
        our_clean_categories = []
        for cat in our_categories:
            our_clean_categories.append({
                'id': cat.id,
                'name': cat.name,
                'clean_name': clean_name(cat.name),
                'object': cat
            })
        
        # Find matches for each external category
        matches = {}
        
        for ext_cat in external_categories:
            if not ext_cat or not isinstance(ext_cat, str):
                continue
                
            clean_ext_cat = clean_name(ext_cat)
            best_match = None
            best_score = 0
            
            # Try exact match first
            for our_cat in our_clean_categories:
                if clean_ext_cat == our_cat['clean_name']:
                    best_match = our_cat
                    best_score = 1.0
                    break
            
            # If no exact match, try fuzzy match with threshold
            if not best_match:
                for our_cat in our_clean_categories:
                    score = SequenceMatcher(None, clean_ext_cat, our_cat['clean_name']).ratio()
                    if score > 0.6 and score > best_score:  # 0.6 is threshold for good match
                        best_match = our_cat
                        best_score = score
            
            # Store the match if found
            if best_match:
                matches[ext_cat] = {
                    'id': best_match['id'],
                    'name': best_match['name'],
                    'score': best_score,
                    'parent': best_match['object'].parent_id
                }
        
        return matches
    
    def post(self, request):
        """Process the content and return suggested categories"""
        serializer = CategoryAssignmentSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract content for categorization
            content = serializer.validated_data.get('content')
            url = serializer.validated_data.get('url', '')
            title = serializer.validated_data.get('title', '')
            format_type = serializer.validated_data.get('format', 'flat')
            
            # Extract external categories if provided
            external_categories = request.data.get('external_categories', [])
            
            # Get a flat list of user's categories
            flat_categories = self.get_flat_categories(request.user)
            
            # Try AI analysis for category suggestions
            suggested_categories = []
            
            try:
                if len(content) > 20:  # Only attempt AI analysis for non-trivial content
                    # Get AI analysis result
                    result = self.analyze_content(content, title, url)
                    
                    # Process the AI results
                    if result and 'categories' in result:
                        for category_item in result.get('categories', []):
                            # Try to find main category
                            main_id = category_item.get('main_id')
                            sub_id = category_item.get('sub_id')
                            
                            # Add main category if it exists
                            if main_id:
                                main_cat = next((c for c in flat_categories if c.id == main_id), None)
                                if main_cat and main_cat not in suggested_categories:
                                    suggested_categories.append(main_cat)
                            
                            # Add sub category if it exists
                            if sub_id:
                                sub_cat = next((c for c in flat_categories if c.id == sub_id), None)
                                if sub_cat and sub_cat not in suggested_categories:
                                    suggested_categories.append(sub_cat)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception(f"Error during AI categorization: {str(e)}")
            
            # If no categories were found by AI, use default categories
            if not suggested_categories:
                suggested_categories = flat_categories[:3]
            
            # Limit to top 5 categories maximum
            suggested_categories = suggested_categories[:5]
            
            # Process based on format
            if format_type == 'flat':
                # For flat format, we only include id and name
                category_data = [{'id': cat.id, 'name': cat.name} for cat in suggested_categories]
            else:
                # For hierarchical format, include parent information
                category_data = []
                for cat in suggested_categories:
                    cat_data = {
                        'id': cat.id,
                        'name': cat.name,
                        'parent': cat.parent_id,
                    }
                    
                    # Get full path if it's a subcategory
                    if cat.parent:
                        parent_path = cat.parent.name
                        cat_data['full_path'] = f"{parent_path} > {cat.name}"
                    else:
                        cat_data['full_path'] = cat.name
                    
                    category_data.append(cat_data)
            
            # Prepare the response
            response_data = {
                'success': True,
                'suggested_categories': category_data,
                'message': 'Categories suggested based on content analysis'
            }
            
            # If external categories were provided, find matching categories
            if external_categories:
                matches = self.find_matching_categories(external_categories, flat_categories)
                response_data['matched_categories'] = matches
            
            return Response(response_data)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BookmarkAPI(APIView):
    """
    API endpoint for creating bookmarks from external systems
    
    This API allows external systems to create bookmarks in TagWise,
    using the content analyzer to suggest categories and tags.
    """
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a new bookmark from an external system"""
        serializer = BookmarkCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract validated data
            url = serializer.validated_data.get('url')
            title = serializer.validated_data.get('title')
            content = serializer.validated_data.get('content')
            description = serializer.validated_data.get('description', '')
            external_categories = serializer.validated_data.get('external_categories', [])
            external_tags = serializer.validated_data.get('external_tags', [])
            
            # Try content analysis to get category and tag suggestions
            try:
                # Import content analysis modules from the main application
                from tagwiseapp.reader.content_analyzer import categorize_content
                from tagwiseapp.reader.category_matcher import get_existing_categories, get_existing_tags
                
                # Call the existing categorize_content function
                analysis_result = categorize_content(
                    content=content, 
                    url=url, 
                    existing_title=title,
                    use_structured_output=True,
                    user=request.user
                )
                
                # Create the bookmark
                bookmark = Bookmark.objects.create(
                    url=url,
                    title=title,
                    description=description,
                    user=request.user
                )
                
                # Process analyzed categories
                if analysis_result and 'categories' in analysis_result:
                    # Get categories from analysis result
                    for category_item in analysis_result.get('categories', []):
                        # Process main category
                        main_id = category_item.get('main_id')
                        main_name = category_item.get('main', '')
                        
                        main_category = None
                        if main_id:
                            # Kullanıcının bir kategori ID'sine sahipse, o kategoriyi kullan
                            main_category = Category.objects.filter(id=main_id).first()
                        
                        # ID bulunamadıysa veya null ise ve kategori adı varsa, yeni kategori oluştur veya mevcut olanı bul
                        if not main_category and main_name:
                            main_category = Category.objects.filter(name=main_name, user=request.user).first() or \
                                           Category.objects.filter(name=main_name, user=None).first()
                            
                            if not main_category:
                                # Ana kategori yoksa oluştur
                                main_category = Category.objects.create(name=main_name, user=request.user)
                        
                        # Ana kategori eklendi, şimdi alt kategoriyi ekle
                        if main_category:
                            bookmark.main_categories.add(main_category)
                            
                            # Alt kategori için işlem yap
                            sub_id = category_item.get('sub_id')
                            sub_name = category_item.get('sub', '')
                            
                            sub_category = None
                            if sub_id:
                                # Kullanıcının bir alt kategori ID'sine sahipse, o alt kategoriyi kullan
                                sub_category = Category.objects.filter(id=sub_id).first()
                            
                            # ID bulunamadıysa veya null ise ve alt kategori adı varsa, yeni alt kategori oluştur veya mevcut olanı bul
                            if not sub_category and sub_name:
                                # Önce bu ana kategorinin altında böyle bir alt kategori olup olmadığını kontrol et
                                sub_category = Category.objects.filter(name=sub_name, parent=main_category, user=request.user).first() or \
                                              Category.objects.filter(name=sub_name, parent=main_category, user=None).first()
                                
                                if not sub_category:
                                    # Alt kategori yoksa oluştur
                                    sub_category = Category.objects.create(
                                        name=sub_name, 
                                        parent=main_category,
                                        user=request.user
                                    )
                            
                            # Alt kategori varsa ekle
                            if sub_category:
                                bookmark.subcategories.add(sub_category)
                
                # Process analyzed tags
                if analysis_result and 'tags' in analysis_result:
                    for tag_item in analysis_result.get('tags', []):
                        # Handle different tag formats
                        if isinstance(tag_item, dict) and 'name' in tag_item:
                            tag_name = tag_item.get('name')
                        elif isinstance(tag_item, str):
                            tag_name = tag_item
                        else:
                            continue
                            
                        if tag_name:
                            # Find or create tag
                            tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
                                Tag.objects.filter(name=tag_name, user=None).first()
                                
                            if not tag:
                                tag = Tag.objects.create(name=tag_name, user=request.user)
                            
                            bookmark.tags.add(tag)
                
                # Process external tags 
                for tag_name in external_tags:
                    # Find similar tag
                    from tagwiseapp.reader.category_matcher import find_similar_tag
                    
                    # Get existing tags
                    existing_tags = get_existing_tags(request.user)
                    
                    match_result = find_similar_tag(tag_name, existing_tags, accept_new=True)
                    
                    if match_result:
                        tag_id = match_result.get('id')
                        if tag_id:
                            tag = Tag.objects.get(id=tag_id)
                        else:
                            # Create new tag as suggested by matcher
                            tag = Tag.objects.create(name=match_result.get('name'), user=request.user)
                    else:
                        # Create new tag if no match found
                        tag = Tag.objects.create(name=tag_name, user=request.user)
                    
                    bookmark.tags.add(tag)
                
                # Return response with bookmark details and category/tag suggestions
                return Response({
                    'success': True,
                    'bookmark_id': bookmark.id,
                    'url': bookmark.url,
                    'title': bookmark.title,
                    'description': bookmark.description,
                    'analysis_result': analysis_result  # Return the original analysis result from content_analyzer
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception(f"Error creating bookmark via API: {str(e)}")
                return Response({
                    'success': False,
                    'error': f"Error creating bookmark: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListView(APIView):
    """
    API endpoint for listing all categories.
    This view returns all categories in a hierarchical format.
    """
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all categories in hierarchical format"""
        
        # Get main categories (with no parent)
        main_categories = Category.objects.filter(
            parent__isnull=True,
            user__in=[None, request.user]
        ).distinct()
        
        result = []
        
        # Build hierarchical structure
        for main_category in main_categories:
            # Get subcategories for this main category
            subcategories = Category.objects.filter(
                parent=main_category,
                user__in=[None, request.user]
            ).distinct()
            
            # Add to result with subcategories
            main_cat_data = CategorySerializer(main_category).data
            main_cat_data['subcategories'] = CategorySerializer(subcategories, many=True).data
            result.append(main_cat_data)
        
        return Response({
            'main_categories': result
        }) 