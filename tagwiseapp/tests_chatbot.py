import json
import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Bookmark, Tag, Category
from .rag.chatbot import BookmarkChatbot

class ChatbotTestCase(TestCase):
    """Test case for chatbot functionality"""
    
    def setUp(self):
        """Set up the test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test categories
        self.category = Category.objects.create(
            name='Programming',
            user=self.user
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='python', user=self.user)
        self.tag2 = Tag.objects.create(name='django', user=self.user)
        
        # Create test bookmarks
        self.bookmark1 = Bookmark.objects.create(
            url='https://www.python.org',
            title='Python Official Website',
            description='The official Python programming language website',
            user=self.user
        )
        self.bookmark1.tags.add(self.tag1)
        self.bookmark1.main_categories.add(self.category)
        
        self.bookmark2 = Bookmark.objects.create(
            url='https://www.djangoproject.com',
            title='Django Web Framework',
            description='The web framework for perfectionists with deadlines',
            user=self.user
        )
        self.bookmark2.tags.add(self.tag1, self.tag2)
        self.bookmark2.main_categories.add(self.category)
        
        # Set up client
        self.client = Client()
        
        # Log in user
        self.client.login(username='testuser', password='password123')
        
    def test_chatbot_init(self):
        """Test chatbot initialization"""
        response = self.client.get(reverse('tagwiseapp:chatbot_init'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
    
    def test_chatbot_ask(self):
        """Test asking a question to the chatbot"""
        # Make sure the API key is available (this is a test, use a test key)
        if not os.environ.get("GEMINI_API_KEY"):
            self.skipTest("GEMINI_API_KEY environment variable not set")
            
        # Initialize index first
        self.client.get(reverse('tagwiseapp:chatbot_init'))
        
        # Ask a simple question
        response = self.client.post(
            reverse('tagwiseapp:chatbot_ask'),
            json.dumps({'message': 'What Python bookmarks do I have?'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertIn('message', response.json())
        
    def test_chatbot_reset(self):
        """Test resetting the chatbot conversation"""
        response = self.client.post(reverse('tagwiseapp:chatbot_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success') 