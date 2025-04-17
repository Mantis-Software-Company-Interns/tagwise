from langchain_community.vectorstores import FAISS
from .embeddings import get_embeddings
import os
import shutil
import logging

logger = logging.getLogger(__name__)

# Constants
VECTORSTORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'vectorstores')
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

def get_vectorstore_path(user_id):
    """Get the path to a user's vectorstore"""
    return os.path.join(VECTORSTORE_DIR, f"user_{user_id}_vectorstore")

def create_vectorstore(texts, metadatas, user_id):
    """
    Create a FAISS vectorstore from texts and metadata.
    
    Args:
        texts: List of text strings to embed
        metadatas: List of metadata dicts corresponding to each text
        user_id: User ID for whom this vectorstore is being created
    
    Returns:
        FAISS vectorstore or None if there's an error
    """
    try:
        if not texts or not metadatas:
            logger.error(f"No texts or metadatas provided for user {user_id}")
            return None
            
        if len(texts) != len(metadatas):
            logger.error(f"Texts and metadatas length mismatch for user {user_id}")
            return None
            
        embeddings = get_embeddings()
        if embeddings is None:
            logger.error(f"Failed to initialize embeddings for user {user_id}")
            return None
            
        logger.info(f"Creating vectorstore for user {user_id} with {len(texts)} documents")
        
        try:
            vectorstore = FAISS.from_texts(texts=texts, metadatas=metadatas, embedding=embeddings)
        except Exception as e:
            logger.error(f"Error creating FAISS vectorstore: {str(e)}")
            return None
            
        # Save vectorstore to disk
        if save_vectorstore(vectorstore, user_id):
            return vectorstore
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error in create_vectorstore for user {user_id}: {str(e)}")
        return None

def save_vectorstore(vectorstore, user_id):
    """
    Save the vectorstore to disk using FAISS native methods
    
    Returns:
        bool: Success status
    """
    try:
        path = get_vectorstore_path(user_id)
        
        # If directory exists, delete it first
        if os.path.exists(path):
            shutil.rmtree(path)
            
        # Create a fresh directory
        os.makedirs(path, exist_ok=True)
        
        # Save using LangChain's FAISS native method
        vectorstore.save_local(path)
        logger.info(f"Vectorstore saved for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving vectorstore for user {user_id}: {str(e)}")
        return False

def load_vectorstore(user_id):
    """
    Load a vectorstore from disk using FAISS native methods
    
    Returns:
        FAISS vectorstore or None if it doesn't exist or there's an error
    """
    try:
        path = get_vectorstore_path(user_id)
        
        # If vectorstore doesn't exist, return None
        if not os.path.exists(path):
            logger.info(f"No vectorstore found for user {user_id}")
            return None
            
        try:
            # Get embeddings
            embeddings = get_embeddings()
            if embeddings is None:
                logger.error(f"Failed to initialize embeddings when loading vectorstore for user {user_id}")
                return None
                
            # Load using LangChain's FAISS native method
            vectorstore = FAISS.load_local(path, embeddings)
            logger.info(f"Vectorstore loaded for user {user_id}")
            return vectorstore
        except Exception as e:
            logger.error(f"Error loading vectorstore for user {user_id}: {str(e)}")
            # If loading fails, remove the corrupted directory
            try:
                shutil.rmtree(path)
                logger.info(f"Removed corrupted vectorstore for user {user_id}")
            except:
                pass
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in load_vectorstore for user {user_id}: {str(e)}")
        return None

def delete_vectorstore(user_id):
    """
    Delete a user's vectorstore
    
    Returns:
        bool: Success status
    """
    try:
        path = get_vectorstore_path(user_id)
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"Vectorstore deleted for user {user_id}")
            return True
        else:
            logger.info(f"No vectorstore to delete for user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting vectorstore for user {user_id}: {str(e)}")
        return False 