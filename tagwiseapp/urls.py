from django.urls import path
from . import views
from . import views_chatbot
app_name = 'tagwiseapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Arama URL'leri
    path('search/bookmarks/', views.search_bookmarks, name='search_bookmarks'),
    path('search/categories/', views.search_categories, name='search_categories'),
    path('search/tags/', views.search_tags, name='search_tags'),
    
    # Profil Ayarları URL'leri
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/profile/update/', views.update_profile, name='update_profile'),
    path('settings/profile/photo/update/', views.update_profile_photo, name='update_profile_photo'),
    path('settings/password/change/', views.change_password, name='change_password'),
    path('settings/notifications/update/', views.update_notifications, name='update_notifications'),
    
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
    path('api/get-bookmark-details/', views.get_bookmark_details, name='get_bookmark_details'),
    path('api/create-collection/', views.create_collection, name='create_collection'),
    path('api/update-collection/', views.update_collection, name='update_collection'),
    path('api/delete-collection/', views.delete_collection, name='delete_collection'),
    path('api/add-bookmarks-to-collection/', views.add_bookmarks_to_collection, name='add_bookmarks_to_collection'),
    path('api/remove-bookmark-from-collection/', views.remove_bookmark_from_collection, name='remove_bookmark_from_collection'),
    
    # Chatbot endpoints
    path('chatbot/init/', views_chatbot.chatbot_init, name='chatbot_init'),
    path('chatbot/ask/', views_chatbot.chatbot_ask, name='chatbot_ask'),
    path('chatbot/reset/', views_chatbot.chatbot_reset, name='chatbot_reset'),
] 