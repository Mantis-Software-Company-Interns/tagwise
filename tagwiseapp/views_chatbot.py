import json
import logging
import os
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from .rag.chatbot import BookmarkChatbot
from .rag.indexer import index_user_bookmarks
from .models import ChatConversation, ChatMessage
from django.shortcuts import get_object_or_404
from django.db.models import Max
import time
import asyncio

# Define constants
PENDING_AI_TITLE = "PENDING_AI_TITLE"

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
        "generate_title": false,  # if true, generates a title using AI
        "stream": false  # if true, returns a streaming response
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
        stream_response = data.get("stream", False)
        
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
                    title=PENDING_AI_TITLE  # Will be replaced with AI generated title
                )
                logger.info(f"Created replacement conversation with id {conversation.id} (existing one not found)")
        else:
            # Create a new conversation
            conversation = ChatConversation.objects.create(
                user=request.user,
                title=PENDING_AI_TITLE  # Will be replaced with AI generated title
            )
            logger.info(f"Created new conversation with id {conversation.id} (no conversation_id provided)")
        
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
        
        # Check if this is a streaming request
        if stream_response:
            return handle_streaming_response(chatbot, message, conversation, user_message, generate_title)
        
        # Handle non-streaming response (original implementation)
        try:
            response = chatbot.get_response(message)
            
            # Save bot response to database
            bot_message = ChatMessage.objects.create(
                conversation=conversation,
                is_user=False,
                content=response["answer"]
            )
            
            # Generate AI title if this is the first message AND generate_title is True
            # OR if the conversation title is still PENDING_AI_TITLE
            is_first_message = conversation.messages.count() <= 2  # Only user message and bot response
            needs_ai_title = is_first_message or conversation.title == PENDING_AI_TITLE
            
            if generate_title and needs_ai_title:
                try:
                    logger.info(f"Generating title for conversation {conversation.id} using LangChain...")
                    title_prompt = f"""
                    Create a concise, descriptive title (3-5 words) for this conversation based on the user's query and AI response below.
                    The title should reflect the main topic or intent of the conversation.
                    Do not include phrases like 'Title:', 'Chat about:', or similar prefixes.
                    Just return the title itself, nothing else.
                    
                    User: {user_message}
                    AI: {response["answer"]}
                    
                    Examples:
                    - "Data Analysis Project Plan"
                    - "Python Error Debugging"
                    - "Marketing Strategy Ideas"
                    - "React Component Design"
                    
                    Title:
                    """
                    
                    # Use existing chatbot with same template for title generation
                    logger.debug("Sending title generation request to LangChain")
                    title_response = chatbot.ask(title_prompt)
                    raw_title = ""
                    
                    if title_response and hasattr(title_response, 'get') and title_response.get("answer"):
                        raw_title = title_response.get("answer", "")
                        logger.debug(f"Raw title received: {raw_title}")
                    else:
                        logger.warning("Invalid or empty response from LangChain for title generation")
                    
                    # Clean the title (remove common prefixes, quotes, etc.)
                    title = raw_title.strip()
                    for prefix in ["Title:", "title:", "Title", "TITLE:", "TITLE", "Chat Title:", "Chat title:"]:
                        if title.startswith(prefix):
                            title = title[len(prefix):].strip()
                    
                    # Remove quotes if they wrap the entire title
                    if (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
                        title = title[1:-1].strip()
                    
                    # Ensure title is not empty and not too long
                    if not title or len(title) < 3:
                        # Fallback: use first few words of the user message
                        truncated_message = " ".join(message.split()[:5])
                        title = truncated_message + "..." if len(message.split()) > 5 else truncated_message
                        logger.info(f"Using fallback title based on user message: {title}")
                    elif len(title) > 100:
                        title = title[:97] + "..."
                    
                    # Update the conversation title in the database
                    conversation.title = title
                    conversation.save()
                    logger.info(f"Updated conversation {conversation.id} title to: {title}")
                    
                except Exception as e:
                    logger.error(f"Error generating title: {str(e)}")
                    # If title generation fails, set a meaningful title based on the first few words
                    if conversation.title == PENDING_AI_TITLE:
                        truncated_message = " ".join(message.split()[:5])
                        title = truncated_message + "..." if len(message.split()) > 5 else truncated_message
                        conversation.title = title
                        conversation.save()
                        logger.info(f"Set fallback title for conversation {conversation.id}: {title}")
            elif is_first_message:
                # If no AI title requested, use first message
                words = message.split()[:3]
                simple_title = " ".join(words) + "..."
                logger.info(f"Using simple title from first message: '{simple_title}'")
                conversation.title = simple_title
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

def handle_streaming_response(chatbot, message, conversation, user_message, generate_title):
    """
    Handle streaming response from chatbot
    """
    try:
        # Determine if we need to generate a title
        is_first_message = conversation.messages.count() <= 1  # Only user message
        needs_ai_title = is_first_message or conversation.title == PENDING_AI_TITLE
        
        # Create a generator that yields response chunks
        def response_generator():
            # Initial metadata chunk
            yield json.dumps({
                "type": "metadata",
                "conversation_id": conversation.id,
                "initial_title": "Processing..." if needs_ai_title else conversation.title
            }) + "\n"
            
            # Response content
            full_response = ""
            title_stream_started = False
            
            # Stream the main response
            try:
                for chunk in chatbot.stream_response(message):
                    full_response += chunk
                    yield json.dumps({
                        "type": "content",
                        "chunk": chunk
                    }) + "\n"
                    
                # Save the full response to the database
                bot_message = ChatMessage.objects.create(
                    conversation=conversation,
                    is_user=False,
                    content=full_response
                )
                
                # Stream title generation if needed
                if generate_title and needs_ai_title:
                    yield json.dumps({
                        "type": "status",
                        "message": "Generating title..."
                    }) + "\n"
                    
                    title_stream_started = True
                    title_prompt = f"""
                    Create a concise, descriptive title (3-5 words) for this conversation based on the user's query and AI response below.
                    The title should reflect the main topic or intent of the conversation.
                    Do not include phrases like 'Title:', 'Chat about:', or similar prefixes.
                    Just return the title itself, nothing else.
                    
                    User: {user_message.content}
                    AI: {full_response}
                    
                    Examples:
                    - "Data Analysis Project Plan"
                    - "Python Error Debugging"
                    - "Marketing Strategy Ideas"
                    - "React Component Design"
                    
                    Title:
                    """
                    
                    # Stream title generation
                    raw_title_chunks = []
                    for title_chunk in chatbot.stream_title_generation(title_prompt):
                        raw_title_chunks.append(title_chunk)
                        yield json.dumps({
                            "type": "title_progress",
                            "chunk": title_chunk
                        }) + "\n"
                    
                    # Process the complete title
                    raw_title = "".join(raw_title_chunks)
                    
                    # Clean the title (remove common prefixes, quotes, etc.)
                    title = raw_title.strip()
                    for prefix in ["Title:", "title:", "Title", "TITLE:", "TITLE", "Chat Title:", "Chat title:"]:
                        if title.startswith(prefix):
                            title = title[len(prefix):].strip()
                    
                    # Remove quotes if they wrap the entire title
                    if (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
                        title = title[1:-1].strip()
                    
                    # Ensure title is not empty and not too long
                    if not title or len(title) < 3:
                        # Fallback: use first few words of the user message
                        truncated_message = " ".join(user_message.content.split()[:5])
                        title = truncated_message + "..." if len(user_message.content.split()) > 5 else truncated_message
                    elif len(title) > 100:
                        title = title[:97] + "..."
                    
                    # Update the conversation title in the database
                    conversation.title = title
                    conversation.save()
                    
                    # Send the final title
                    yield json.dumps({
                        "type": "title",
                        "title": title
                    }) + "\n"
                elif is_first_message:
                    # If no AI title requested but it's the first message, use first message
                    words = message.split()[:3]
                    simple_title = " ".join(words) + "..."
                    conversation.title = simple_title
                    conversation.save()
                    
                    yield json.dumps({
                        "type": "title",
                        "title": simple_title
                    }) + "\n"
                
                # Update conversation.updated_at
                conversation.save(update_fields=['updated_at'])
                
                # Final metadata with sources
                sources = []
                # Try to extract sources from the chatbot's RAG results
                try:
                    # Use direct query to get sources (this would be available after the streaming)
                    direct_response = chatbot.get_response(message)
                    sources = direct_response.get("sources", [])
                except Exception as e:
                    logger.error(f"Error getting sources: {str(e)}")
                
                yield json.dumps({
                    "type": "completion",
                    "sources": sources
                }) + "\n"
                
            except Exception as e:
                logger.error(f"Error in streaming response: {str(e)}")
                error_message = "I'm sorry, I encountered an error processing your request."
                
                # If we haven't provided a full response yet, save the error message
                if not full_response:
                    full_response = error_message
                    bot_message = ChatMessage.objects.create(
                        conversation=conversation,
                        is_user=False,
                        content=full_response
                    )
                
                # Send error message
                yield json.dumps({
                    "type": "error",
                    "message": error_message
                }) + "\n"
                
                # Set a fallback title if needed
                if needs_ai_title and not title_stream_started:
                    truncated_message = " ".join(message.split()[:5])
                    title = truncated_message + "..." if len(message.split()) > 5 else truncated_message
                    conversation.title = title
                    conversation.save()
                    
                    yield json.dumps({
                        "type": "title",
                        "title": title
                    }) + "\n"
        
        return StreamingHttpResponse(
            response_generator(),
            content_type='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error setting up streaming response: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "Failed to set up streaming response"
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
        # Create a new conversation with a temporary title that will be replaced by AI
        conversation = ChatConversation.objects.create(
            user=request.user,
            title=PENDING_AI_TITLE  # This will be replaced with AI title when first message is processed
        )
        
        # Add initial welcome message from bot
        ChatMessage.objects.create(
            conversation=conversation,
            is_user=False,
            content="Hello! I can help you search through your bookmarks. What are you looking for?"
        )
        
        logger.info(f"Created new conversation with id {conversation.id} - awaiting AI title")
        
        return JsonResponse({
            "status": "success",
            "conversation": {
                "id": conversation.id,
                "title": "New Chat",  # For display only - will be replaced when user sends first message
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