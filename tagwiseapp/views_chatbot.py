import json
import logging
import os
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .rag.chatbot import BookmarkChatbot
from .rag.indexer import index_user_bookmarks
from .models import ChatConversation, ChatMessage
from django.shortcuts import get_object_or_404
from django.db.models import Max

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
        "category": "optional category filter",
        "conversation_id": null or id,  # if null, creates a new conversation
        "generate_title": false  # if true, generates a title using AI
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
        conversation_id = data.get("conversation_id", None)
        generate_title = data.get("generate_title", False)
        
        if not message:
            return JsonResponse({
                "status": "error", 
                "message": "No message provided"
            }, status=400)
            
        # Get user ID from session
        user_id = request.user.id
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
            except ChatConversation.DoesNotExist:
                # If conversation doesn't exist or doesn't belong to user, create a new one
                conversation = ChatConversation.objects.create(
                    user=request.user,
                    title="New conversation"  # Use a placeholder title initially
                )
        else:
            # Create a new conversation
            conversation = ChatConversation.objects.create(
                user=request.user,
                title="New conversation"  # Use a placeholder title initially
            )
        
        # Create chatbot instance
        try:
            chatbot = BookmarkChatbot(user_id)
            
            # Load previous messages from this conversation into chatbot memory
            previous_messages = ChatMessage.objects.filter(conversation=conversation).order_by('created_at')
            for prev_msg in previous_messages:
                if prev_msg.is_user:
                    chatbot.memory.chat_memory.add_user_message(prev_msg.content)
                else:
                    chatbot.memory.chat_memory.add_ai_message(prev_msg.content)
            
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
        
        # Save user message to database
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            is_user=True,
            content=message
        )
        
        # Get response with a fallback
        try:
            response = chatbot.get_response(message)
            
            # Save bot response to database
            bot_message = ChatMessage.objects.create(
                conversation=conversation,
                is_user=False,
                content=response["answer"]
            )
            
            # Generate AI title if this is the first message AND generate_title is True
            is_first_message = conversation.messages.count() <= 2  # Only user message and bot response
            
            if generate_title and is_first_message:
                try:
                    # Use a more descriptive title prompt
                    title_prompt = f"Generate a short and concise title (maximum 5 words) for this conversation based on the user's query. User query: '{message}'"
                    title_response = chatbot.get_response(title_prompt)
                    
                    # Clean up the title
                    ai_title = title_response["answer"].strip(' "\'.')
                    # Limit to 50 chars and remove any markdown or unwanted formatting
                    ai_title = ai_title.replace('*', '').replace('#', '').replace('`', '')[:50]
                    
                    if ai_title:
                        conversation.title = ai_title
                        conversation.save()
                    else:
                        # Fallback to first message if AI generated an empty title
                        conversation.title = message[:50]
                        conversation.save()
                except Exception as e:
                    logger.error(f"Error generating title: {str(e)}")
                    # Fallback to first user message
                    conversation.title = message[:50]
                    conversation.save()
            elif is_first_message:
                # If no AI title requested, use first message
                conversation.title = message[:50]
                conversation.save()
                
            # Update conversation.updated_at
            conversation.save(update_fields=['updated_at'])
                
        except Exception as e:
            logger.error(f"Error in chatbot response: {str(e)}")
            response = {
                "answer": "I'm sorry, I encountered an error processing your request. Please try again later.",
                "sources": []
            }
            # Still save the error response
            bot_message = ChatMessage.objects.create(
                conversation=conversation,
                is_user=False,
                content=response["answer"]
            )
        
        # Format response
        return JsonResponse({
            "status": "success",
            "message": response["answer"],
            "sources": response.get("sources", []),
            "conversation_id": conversation.id,
            "conversation_title": conversation.title
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_ask: {str(e)}")
        return JsonResponse({
            "status": "error", 
            "message": "An error occurred processing your request. Please try again later."
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_conversations(request):
    """Get list of user's conversations"""
    try:
        conversations = ChatConversation.objects.filter(user=request.user)
        
        # Format response
        result = []
        for conv in conversations:
            # Get first message content to use as title if needed
            try:
                first_message = conv.messages.filter(is_user=True).earliest('created_at').content
                title = conv.title or first_message[:50]
            except ChatMessage.DoesNotExist:
                title = conv.title or "New conversation"
                
            result.append({
                "id": conv.id,
                "title": title,
                "created_at": conv.created_at.strftime("%d.%m.%Y"),
                "updated_at": conv.updated_at.strftime("%d.%m.%Y %H:%M")
            })
            
        return JsonResponse({
            "status": "success",
            "conversations": result
        })
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to retrieve conversations"
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    """Get messages from a specific conversation"""
    try:
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        messages = conversation.messages.all().order_by('created_at')
        
        # Format the messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.id,
                "is_user": msg.is_user,
                "content": msg.content,
                "created_at": msg.created_at.strftime("%H:%M")
            })
            
        return JsonResponse({
            "status": "success",
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "messages": formatted_messages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to retrieve conversation messages"
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def create_conversation(request):
    """Create a new conversation and return its ID"""
    try:
        # Create a new conversation
        conversation = ChatConversation.objects.create(
            user=request.user,
            title="New conversation"
        )
        
        # Add initial welcome message from bot
        ChatMessage.objects.create(
            conversation=conversation,
            is_user=False,
            content="Hello! I can help you search through your bookmarks. What are you looking for?"
        )
        
        return JsonResponse({
            "status": "success",
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.strftime("%d.%m.%Y"),
                "updated_at": conversation.updated_at.strftime("%d.%m.%Y %H:%M")
            }
        })
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to create new conversation"
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    try:
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        conversation.delete()
        
        return JsonResponse({
            "status": "success",
            "message": "Conversation deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to delete conversation"
        }, status=500)

@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def rename_conversation(request, conversation_id):
    """Rename a conversation"""
    try:
        data = json.loads(request.body)
        new_title = data.get("title", "").strip()
        
        if not new_title:
            return JsonResponse({
                "status": "error",
                "message": "Title cannot be empty"
            }, status=400)
            
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        conversation.title = new_title
        conversation.save()
        
        return JsonResponse({
            "status": "success",
            "conversation": {
                "id": conversation.id,
                "title": conversation.title
            }
        })
        
    except Exception as e:
        logger.error(f"Error renaming conversation: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to rename conversation"
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