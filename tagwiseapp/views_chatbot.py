import json
import logging
import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .rag.chatbot import BookmarkChatbot
from .rag.indexer import index_user_bookmarks

logger = logging.getLogger(__name__)

@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def chatbot_init(request):
    """
    Initialize the chatbot for a user by creating their vectorstore index
    if it doesn't already exist.
    """
    try:
        # Check if Gemini API key is available
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            return JsonResponse({
                "status": "error", 
                "message": "API configuration is missing. Please contact the administrator."
            }, status=500)
            
        user_id = request.user.id
        # Trigger index creation if it doesn't exist
        result = index_user_bookmarks(user_id)
        
        if result is None:
            logger.warning(f"Failed to create index for user {user_id} - no bookmarks or error")
            return JsonResponse({
                "status": "warning", 
                "message": "Initialized, but you don't have any bookmarks yet, or there was an indexing error."
            })
            
        return JsonResponse({"status": "success", "message": "Chatbot initialized successfully"})
        
    except Exception as e:
        logger.error(f"Error initializing chatbot: {str(e)}")
        return JsonResponse({
            "status": "error", 
            "message": "Failed to initialize chatbot. Please try again later."
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def chatbot_ask(request):
    """
    Process a user message and get a response from the chatbot.
    
    Expected request body:
    {
        "message": "user question here",
        "category": "optional category filter"
    }
    """
    try:
        # Check if Gemini API key is available
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            return JsonResponse({
                "status": "error", 
                "message": "API configuration is missing. Please contact the administrator."
            }, status=500)
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error", 
                "message": "Invalid JSON in request body"
            }, status=400)
            
        message = data.get("message", "").strip()
        category = data.get("category", None)
        
        if not message:
            return JsonResponse({
                "status": "error", 
                "message": "No message provided"
            }, status=400)
            
        # Get user ID from session
        user_id = request.user.id
        
        # Create chatbot instance
        try:
            chatbot = BookmarkChatbot(user_id)
        except Exception as e:
            logger.error(f"Error creating chatbot instance: {str(e)}")
            return JsonResponse({
                "status": "error", 
                "message": "Failed to initialize chatbot. Please try again later."
            }, status=500)
            
        # Apply category filter if provided
        if category:
            try:
                chatbot.filter_by_category(category)
            except Exception as e:
                logger.error(f"Error applying category filter: {str(e)}")
                # Continue without filter instead of failing
        
        # Get response with a fallback
        try:
            response = chatbot.get_response(message)
        except Exception as e:
            logger.error(f"Error in chatbot response: {str(e)}")
            response = {
                "answer": "I'm sorry, I encountered an error processing your request. Please try again later.",
                "sources": []
            }
        
        # Format response
        return JsonResponse({
            "status": "success",
            "message": response["answer"],
            "sources": response.get("sources", [])
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_ask: {str(e)}")
        return JsonResponse({
            "status": "error", 
            "message": "An error occurred processing your request. Please try again later."
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def chatbot_reset(request):
    """
    Reset the chatbot conversation by clearing its memory.
    """
    try:
        # Check if Gemini API key is available
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            return JsonResponse({
                "status": "error", 
                "message": "API configuration is missing. Please contact the administrator."
            }, status=500)
            
        user_id = request.user.id
        
        try:
            chatbot = BookmarkChatbot(user_id)
            chatbot.clear_memory()
            return JsonResponse({
                "status": "success", 
                "message": "Conversation reset successfully"
            })
        except Exception as e:
            logger.error(f"Error during chatbot conversation reset: {str(e)}")
            return JsonResponse({
                "status": "error", 
                "message": "Failed to reset conversation. Please try again later."
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error resetting chatbot: {str(e)}")
        return JsonResponse({
            "status": "error", 
            "message": "Failed to reset conversation. Please try again later."
        }, status=500) 