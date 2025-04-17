"""
RAG (Retrieval Augmented Generation) module for TagWise
This module provides the components for creating embeddings,
storing them in a vector database, and using them to power
the TagWise chatbot.
"""

from .chatbot import BookmarkChatbot
from .indexer import index_user_bookmarks, add_bookmark_to_index

__all__ = ['BookmarkChatbot', 'index_user_bookmarks', 'add_bookmark_to_index'] 