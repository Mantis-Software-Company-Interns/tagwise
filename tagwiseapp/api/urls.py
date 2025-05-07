from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, 
    TagViewSet, 
    ApiKeyViewSet, 
    CategoryListView,
    CategoryAssignmentView,
    BookmarkAPI
)

# Configure routers
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'api-keys', ApiKeyViewSet, basename='api-key')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('category-list/', CategoryListView.as_view(), name='category-list'),
    path('categorize/', CategoryAssignmentView.as_view(), name='categorize'),
    path('create-bookmark/', BookmarkAPI.as_view(), name='create-bookmark'),
    
    # Include auth URLs (for browsable API)
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]