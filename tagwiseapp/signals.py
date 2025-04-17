from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Bookmark
from .rag.indexer import add_bookmark_to_index, index_user_bookmarks
import logging
import os
import time
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta

# Load environment variables from .env file with priority
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Dictionary to track last index operation for each user
_last_index_time = {}
# Minimum time between index operations for the same user (seconds)
INDEX_COOLDOWN = 5

def with_index_cooldown(func):
    """
    Decorator that prevents too frequent indexing operations for the same user.
    Helps prevent cascading signals and unnecessary processing.
    """
    @wraps(func)
    def wrapper(sender, instance, **kwargs):
        user_id = instance.user.id
        current_time = datetime.now()
        
        # Check if we have indexed recently for this user
        if user_id in _last_index_time:
            time_diff = (current_time - _last_index_time[user_id]).total_seconds()
            if time_diff < INDEX_COOLDOWN:
                logger.info(f"Skipping index operation for user {user_id} - cooldown period ({time_diff:.1f}s < {INDEX_COOLDOWN}s)")
                return
                
        # Update the last index time for this user
        _last_index_time[user_id] = current_time
        
        # Call the original signal handler
        return func(sender, instance, **kwargs)
    return wrapper

@receiver(post_save, sender=Bookmark)
@with_index_cooldown
def bookmark_saved(sender, instance, created, **kwargs):
    """
    Signal handler that automatically updates the vector index when a bookmark is created or updated.
    """
    if 'GEMINI_API_KEY' not in os.environ:
        logger.error("GEMINI_API_KEY environment variable is not set. Cannot update vector index.")
        return
        
    try:
        if created:
            logger.info(f"Adding new bookmark (ID: {instance.id}) to vector index")
        else:
            logger.info(f"Updating bookmark (ID: {instance.id}) in vector index")
            
        # Add or update bookmark in index
        result = add_bookmark_to_index(instance)
        
        if result:
            logger.info(f"Successfully indexed bookmark {instance.id}")
        else:
            logger.error(f"Failed to index bookmark {instance.id}")
    except Exception as e:
        logger.error(f"Error indexing bookmark {instance.id}: {str(e)}")
        
@receiver(post_delete, sender=Bookmark)
@with_index_cooldown
def bookmark_deleted(sender, instance, **kwargs):
    """
    Signal handler that triggers a full reindex when a bookmark is deleted
    because we can't easily delete a single document from the FAISS store.
    """
    if 'GEMINI_API_KEY' not in os.environ:
        logger.error("GEMINI_API_KEY environment variable is not set. Cannot update vector index.")
        return
        
    try:
        logger.info(f"Bookmark (ID: {instance.id}) deleted, rebuilding index for user {instance.user.id}")
        # Rebuild the entire index for this user
        result = index_user_bookmarks(instance.user.id)
        
        if result:
            logger.info(f"Successfully rebuilt index for user {instance.user.id} after bookmark deletion")
        else:
            logger.warning(f"Failed to rebuild index for user {instance.user.id} after bookmark deletion")
    except Exception as e:
        logger.error(f"Error rebuilding index after bookmark deletion: {str(e)}")

# A dictionary to track already processed m2m changes to prevent duplicate processing
_processed_m2m_operations = {}

@receiver(m2m_changed, sender=Bookmark.tags.through)
@receiver(m2m_changed, sender=Bookmark.main_categories.through)
@receiver(m2m_changed, sender=Bookmark.subcategories.through)
@with_index_cooldown
def bookmark_relations_changed(sender, instance, action, **kwargs):
    """
    Signal handler that updates the vector index when a bookmark's related
    fields (tags, categories, subcategories) are changed.
    Only triggers once per related change, regardless of how many m2m tables change.
    """
    # Only trigger on post actions
    if action not in ['post_add', 'post_remove', 'post_clear']:
        return
        
    # Create a unique ID for this operation
    operation_id = f"{instance.id}_{action}_{time.time():.0f}"
    
    # Check if we've already processed an operation for this bookmark recently
    for key in list(_processed_m2m_operations.keys()):
        # Remove entries older than 2 seconds
        if time.time() - _processed_m2m_operations[key] > 2:
            del _processed_m2m_operations[key]
    
    # Skip if we just processed this bookmark
    if any(k.startswith(f"{instance.id}_{action}") for k in _processed_m2m_operations):
        logger.info(f"Skipping duplicate m2m processing for bookmark {instance.id}")
        return
        
    # Mark this operation as processed
    _processed_m2m_operations[operation_id] = time.time()
        
    if 'GEMINI_API_KEY' not in os.environ:
        logger.error("GEMINI_API_KEY environment variable is not set. Cannot update vector index.")
        return
        
    try:
        logger.info(f"Bookmark (ID: {instance.id}) relations changed, updating index")
        # Update bookmark in index
        result = add_bookmark_to_index(instance)
        
        if result:
            logger.info(f"Successfully updated bookmark {instance.id} in index after {action}")
        else:
            logger.error(f"Failed to update bookmark {instance.id} in index after {action}")
    except Exception as e:
        logger.error(f"Error updating index after bookmark relations changed: {str(e)}") 