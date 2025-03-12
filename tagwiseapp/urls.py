from django.urls import path
from . import views
app_name = 'tagwiseapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('categories/', views.categories, name="categories"),
    path('collections/', views.collections, name='collections'),
    path('collections/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('tags/', views.tags, name='tags'),
    path('subcategories/', views.subcategories, name="subcategories"),
    path('topics/', views.topics, name="topics"),
    path('tagged-bookmarks/', views.tagged_bookmarks, name="tagged_bookmarks"),
    path('test/', views.test_page, name='test_page'),
    path('api/analyze-url/', views.analyze_url, name='analyze_url'),
    path('api/save-bookmark/', views.save_bookmark, name='save_bookmark'),
    path('api/update-bookmark/', views.update_bookmark, name='update_bookmark'),
    path('api/test-url/', views.test_url, name='test_url'),
    path('api/related-tags/', views.api_related_tags, name='api_related_tags'),
    path('api/tagged-bookmarks/', views.api_tagged_bookmarks, name='api_tagged_bookmarks'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('api/delete-bookmark/', views.delete_bookmark, name='delete_bookmark'),
    path('api/create-collection/', views.create_collection, name='create_collection'),
] 