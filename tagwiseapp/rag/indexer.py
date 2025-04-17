from django.contrib.auth.models import User
from tagwiseapp.models import Bookmark
from .vectorstore import create_vectorstore, load_vectorstore, save_vectorstore
from .embeddings import get_embeddings
import logging

logger = logging.getLogger(__name__)

def prepare_bookmark_data(bookmark):
    """
    Prepare a bookmark record for embedding by extracting relevant text
    and metadata.
    
    Args:
        bookmark: Bookmark model instance
        
    Returns:
        tuple: (text, metadata)
    """
    try:
        # Combine relevant text fields with error handling
        tags = [tag.name for tag in bookmark.tags.all()] if bookmark.tags.exists() else []
        categories = [cat.name for cat in bookmark.main_categories.all()] if bookmark.main_categories.exists() else []
        subcategories = [subcat.name for subcat in bookmark.subcategories.all()] if bookmark.subcategories.exists() else []
        
        text_content = f"""
        Title: {bookmark.title or 'No title'}
        URL: {bookmark.url or 'No URL'}
        Description: {bookmark.description or 'No description'}
        Tags: {', '.join(tags) if tags else 'No tags'}
        Categories: {', '.join(categories) if categories else 'No categories'}
        Subcategories: {', '.join(subcategories) if subcategories else 'No subcategories'}
        """
        
        # Prepare metadata
        metadata = {
            "id": bookmark.id,
            "title": bookmark.title or "Untitled bookmark",
            "url": bookmark.url or "",
            "description": bookmark.description or "",
            "created_at": bookmark.created_at.isoformat() if bookmark.created_at else "",
            "tags": tags,
            "categories": categories,
            "subcategories": subcategories,
            "source": "bookmark"
        }
        
        return text_content, metadata
    except Exception as e:
        logger.error(f"Error preparing bookmark data for bookmark {bookmark.id}: {str(e)}")
        # Return a safe fallback
        return f"Bookmark {bookmark.id}", {"id": bookmark.id, "title": "Error bookmark", "url": "", "source": "error"}

def index_user_bookmarks(user_id):
    """
    Index all bookmarks for a specific user.
    
    Args:
        user_id: User ID whose bookmarks should be indexed
        
    Returns:
        FAISS vectorstore or None if there was an error
    """
    try:
        # Validate embeddings are working
        embeddings = get_embeddings()
        if embeddings is None:
            logger.error("Failed to initialize embeddings for indexing. Check if GEMINI_API_KEY is set.")
            return None
            
        # Get user and bookmarks
        user = User.objects.get(id=user_id)
        bookmarks = Bookmark.objects.filter(user=user)
        
        bookmarks_count = bookmarks.count()
        if not bookmarks_count:
            logger.warning(f"No bookmarks found for user {user_id}")
            return None
            
        logger.info(f"Starting indexing {bookmarks_count} bookmarks for user {user_id}")
        
        texts = []
        metadatas = []
        successful_bookmarks = 0
        
        for bookmark in bookmarks:
            try:
                text, metadata = prepare_bookmark_data(bookmark)
                texts.append(text)
                metadatas.append(metadata)
                successful_bookmarks += 1
            except Exception as e:
                logger.error(f"Error processing bookmark {bookmark.id} for indexing: {str(e)}")
                # Continue with the next bookmark
        
        if not texts:
            logger.warning(f"No valid bookmark data to index for user {user_id}")
            return None
            
        logger.info(f"Successfully prepared {successful_bookmarks}/{bookmarks_count} bookmarks for user {user_id}")
            
        # Create the vectorstore
        try:
            logger.info(f"Creating vectorstore with {len(texts)} documents")
            vectorstore = create_vectorstore(texts, metadatas, user_id)
            if vectorstore:
                logger.info(f"Successfully created vectorstore for user {user_id}")
                return vectorstore
            else:
                logger.error(f"Failed to create vectorstore for user {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error creating vectorstore for user {user_id}: {str(e)}")
            return None
    
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return None
    except Exception as e:
        logger.error(f"Error indexing bookmarks for user {user_id}: {str(e)}")
        return None

def add_bookmark_to_index(bookmark):
    """
    Add a single bookmark to the existing vectorstore index.
    
    Args:
        bookmark: Bookmark model instance
        
    Returns:
        bool: Success status
    """
    try:
        user_id = bookmark.user.id
        
        # Validate embeddings are working
        embeddings = get_embeddings()
        if embeddings is None:
            logger.error("Failed to initialize embeddings for adding bookmark")
            return False
            
        vectorstore = load_vectorstore(user_id)
        
        # If no vectorstore exists, create a new one with all bookmarks
        if vectorstore is None:
            logger.info(f"No existing vectorstore found for user {user_id}, creating a new one")
            return index_user_bookmarks(user_id) is not None
            
        # Add the bookmark to the vectorstore
        try:
            text, metadata = prepare_bookmark_data(bookmark)
            vectorstore.add_texts([text], [metadata])
            save_vectorstore(vectorstore, user_id)
            return True
        except Exception as e:
            logger.error(f"Error adding bookmark {bookmark.id} to vectorstore: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error adding bookmark {bookmark.id} to index: {str(e)}")
        return False 