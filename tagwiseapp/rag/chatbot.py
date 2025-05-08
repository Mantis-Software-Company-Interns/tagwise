import os
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.retrievers import BaseRetriever
from .vectorstore import load_vectorstore
from .indexer import index_user_bookmarks
import json
import logging

logger = logging.getLogger(__name__)

# Load Gemini configuration
try:
    with open('gemini_config.json', 'r') as f:
        GEMINI_CONFIG = json.load(f)
except Exception as e:
    logger.error(f"Error loading Gemini config: {str(e)}")
    GEMINI_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
        "candidate_count": 1,
    }

class BookmarkChatbot:
    """
    Conversational chatbot for bookmark search and information retrieval
    using LangChain and Gemini.
    """
    
    def __init__(self, user_id):
        """Initialize the chatbot with user-specific settings"""
        self.user_id = user_id
        
        # API anahtarını .env dosyasından al
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            # Acil durum için .env dosyasını doğrudan kontrol et
            try:
                with open('.env') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY='):
                            self.api_key = line.split('=')[1].strip()
                            logger.warning("API key loaded directly from .env file as fallback")
                            break
            except Exception as e:
                logger.error(f"Failed to load API key from .env file: {str(e)}")
        
        # Güncellenmiş bellek kullanımı - deprecated warning'i gidermek için
        self.memory = ConversationBufferMemory(
            return_messages=True,
            input_key="question",
            output_key="answer",
            memory_key="chat_history"
        )
        
        self.llm = self._create_llm()
        self.chain = self._create_chain()
    
    def _create_llm(self):
        """Create and configure the LLM"""
        try:
            if not self.api_key:
                logger.error("Cannot create LLM: No API key available")
                raise ValueError("Missing API key for Gemini")
                
            logger.info(f"Creating LLM with API key (starts with): {self.api_key[:5]}...")
            
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.api_key,
                temperature=GEMINI_CONFIG.get("temperature", 0.7),
                top_p=GEMINI_CONFIG.get("top_p", 0.95),
                top_k=GEMINI_CONFIG.get("top_k", 40),
                max_output_tokens=GEMINI_CONFIG.get("max_output_tokens", 2048),
            )
        except Exception as e:
            logger.error(f"Error creating LLM: {str(e)}")
            raise
    
    def _create_system_prompt(self):
        """Create the system prompt template for the chatbot"""
        template = """
        You are a helpful AI assistant for a bookmark management system called TagWise. 
        The user will ask you questions about their saved bookmarks.
        
        Use the following pieces of information to answer the user's question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        When discussing bookmarks, remember to include the title and URL when relevant.
        If multiple bookmarks are relevant, list them in a clear and organized way.
        
        You must focus on maintaining context throughout the conversation. When the user asks 
        follow-up questions, connect them to previous questions and answers. References to "it", 
        "that", "this", or similar pronouns should be resolved to what they refer to in prior exchanges.
        
        Context: {context}
        
        Chat History: {chat_history}
        """
        return SystemMessagePromptTemplate.from_template(template)
    
    def _create_human_prompt(self):
        """Create the human prompt template"""
        return HumanMessagePromptTemplate.from_template("{question}")
    
    def _create_prompt(self):
        """Combine system and human prompts into a chat prompt template"""
        system_prompt = self._create_system_prompt()
        human_prompt = self._create_human_prompt()
        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    
    def _get_vectorstore(self):
        """Get or create the user's vectorstore"""
        try:
            vectorstore = load_vectorstore(self.user_id)
            
            # If no vectorstore exists, create a new one
            if vectorstore is None:
                logger.info(f"No vectorstore found for user {self.user_id}, creating one now")
                vectorstore = index_user_bookmarks(self.user_id)
                
            # If still None (no bookmarks), create an empty response
            if vectorstore is None:
                logger.warning(f"User {self.user_id} has no bookmarks to index")
                from langchain_community.vectorstores import FAISS
                from .embeddings import get_embeddings
                
                embeddings = get_embeddings()
                if embeddings is None:
                    raise ValueError("Failed to initialize embeddings")
                    
                vectorstore = FAISS.from_texts(
                    ["No bookmarks available"], 
                    [{"source": "empty", "title": "No bookmarks", "url": ""}], 
                    embeddings
                )
            
            return vectorstore
        except Exception as e:
            logger.error(f"Error getting vectorstore: {str(e)}")
            # Fallback to a very simple retriever that just returns nothing
            from langchain_community.vectorstores import FAISS
            from .embeddings import get_embeddings
            
            embeddings = get_embeddings()
            if embeddings is None:
                raise ValueError("Failed to initialize embeddings, cannot create fallback vectorstore")
                
            return FAISS.from_texts(
                ["Error retrieving bookmarks"], 
                [{"source": "error", "title": "Error", "url": ""}],
                embeddings
            )
    
    def _create_chain(self):
        """Create the conversational retrieval chain"""
        try:
            vectorstore = self._get_vectorstore()
            if vectorstore is None:
                raise ValueError("Failed to initialize vector database")

            # Basit çözüm: Yerleşik VectorStoreRetriever kullan
            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 20,  # Maximum limit for safety
                    "score_threshold": 0.5  # Minimum similarity score (0-1)
                }
            )
            
            # Define a proper chat history formatter that turns message objects into a string
            def format_chat_history(chat_messages):
                return "\n".join([
                    f"Human: {message.content}" if isinstance(message, HumanMessage) 
                    else f"AI: {message.content}" 
                    for message in chat_messages
                ])
            
            # Create condense question prompt
            condense_question_prompt = PromptTemplate.from_template(
                """Given the following conversation and a follow up question, rephrase the follow up question 
                to be a standalone question that captures all relevant context from the chat history.
                
                Chat History:
                {chat_history}
                
                Follow Up Question: {question}
                
                Standalone Question:"""
            )
            
            # Define a modern message-based condense question prompt as an alternative approach
            # This could be used instead of the string-based approach above
            condense_question_prompt_messages = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    """Given the conversation history and a follow up question, rephrase the follow up question 
                    to be a standalone question that captures all relevant context from the chat history."""
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ])
            
            # Define a QA prompt with message placeholders for proper context integration
            qa_prompt_messages = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    """You are a helpful AI assistant for a bookmark management system called TagWise.
                    Use the following pieces of context to answer the user's question.
                    If you don't know the answer, just say that you don't know.
                    When discussing bookmarks, include titles and URLs when relevant."""
                ),
                SystemMessagePromptTemplate.from_template(
                    "Context information: {context}"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ])
            
            # NOTE: To switch to the modern message-based approach, you would uncomment the code below
            # and comment out the current chain creation. This requires more changes to the LangChain
            # configuration so we're providing it as an alternative implementation.
            
            """
            # Modern approach using create_from_llm_and_messages
            from langchain.chains.conversational_retrieval.base import create_from_llm_and_messages
            
            chain = create_from_llm_and_messages(
                llm=self.llm,
                retriever=retriever,
                condense_question_prompt=condense_question_prompt_messages,
                qa_prompt=qa_prompt_messages,
                memory=self.memory,
                return_source_documents=True,
                verbose=True,
            )
            return chain
            """
            
            # Basitleştirilmiş zincir oluşturma - using the string-based approach for compatibility
            return ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                chain_type="stuff",  # En basit chain türü
                get_chat_history=format_chat_history,  # Convert message objects to formatted string
                condense_question_prompt=condense_question_prompt,  # Custom prompt for question condensation
                return_source_documents=True,
                verbose=True,
            )
        except Exception as e:
            logger.error(f"Error creating chain: {str(e)}")
            raise
    
    def get_response(self, query):
        """
        Get a response from the chatbot for a user query
        
        Args:
            query: User's question string
            
        Returns:
            dict: Contains 'answer' and optionally 'sources'
        """
        try:
            # API anahtarı kontrolü
            if not self.api_key:
                logger.error("No API key provided for Gemini")
                return {
                    "answer": "I can't search your bookmarks right now. API configuration is missing.",
                    "sources": []
                }
            
            logger.info(f"Processing query: '{query[:50]}...' (if longer)")
            
            # Güvenli bir şekilde chain'i çağır
            try:
                logger.info("Calling LLM chain")
                result = self.chain({"question": query})
                logger.info("LLM chain response received")
            except Exception as e:
                logger.error(f"Chain execution error: {str(e)}")
                # Daha detaylı hata günlüğü
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Fallback yanıt
                return {
                    "answer": "I'm sorry, I encountered an error searching your bookmarks. Please try again later.",
                    "sources": []
                }
            
            # Format the response
            answer = result.get("answer", "I couldn't find an answer to your question.")
            logger.info(f"LLM response (truncated): '{answer[:100]}...' (if longer)")
            
            response = {
                "answer": answer,
                "sources": []
            }
            
            # Add sources if available
            if "source_documents" in result:
                source_count = 0
                for doc in result["source_documents"]:
                    if hasattr(doc, "metadata") and "url" in doc.metadata and "title" in doc.metadata:
                        if doc.metadata.get("source") not in ["empty", "error"]:
                            response["sources"].append({
                                "title": doc.metadata["title"],
                                "url": doc.metadata["url"],
                                "id": doc.metadata.get("id")
                            })
                            source_count += 1
                
                logger.info(f"Found {source_count} sources for the query")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            # Daha detaylı hata günlüğü
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return {"answer": "I'm sorry, I encountered an error trying to process your question.", "sources": []}
            
    def ask(self, query):
        """
        Direct query to the LLM without RAG context, used for title generation.
        
        Args:
            query: User's question string
            
        Returns:
            dict: Contains 'answer'
        """
        try:
            if not self.api_key:
                logger.error("No API key provided for Gemini")
                return {"answer": "API configuration is missing."}
            
            logger.info(f"Processing direct LLM query for title generation: '{query[:50]}...' (if longer)")
            
            # Direct query to LLM without RAG context
            try:
                # Create a simple template for direct questions
                from langchain.chains import LLMChain
                from langchain.prompts import PromptTemplate
                
                template = """
                {query}
                """
                prompt = PromptTemplate(template=template, input_variables=["query"])
                chain = LLMChain(llm=self.llm, prompt=prompt)
                
                # Get response
                result = chain.invoke({"query": query})
                return {"answer": result.get("text", "")}
                
            except Exception as e:
                logger.error(f"Direct LLM query error: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"answer": "Failed to generate title."}
            
        except Exception as e:
            logger.error(f"Error in direct query: {str(e)}")
            return {"answer": "Error processing request."}
    
    def stream_response(self, query):
        """
        Stream a response from the chatbot for a user query
        
        Args:
            query: User's question string
            
        Returns:
            generator: Yields chunks of the answer as they are generated
        """
        if not self.api_key:
            logger.error("No API key provided for Gemini")
            yield "I can't search your bookmarks right now. API configuration is missing."
            return
        
        logger.info(f"Streaming response for query: '{query[:50]}...' (if longer)")
        
        try:
            # Use stream method from LangChain's ConversationalRetrievalChain
            for chunk in self.chain.stream({"question": query}):
                if "answer" in chunk:
                    yield chunk["answer"]
        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            yield "I'm sorry, I encountered an error processing your request."
    
    def stream_title_generation(self, title_prompt):
        """
        Stream the title generation process
        
        Args:
            title_prompt: Prompt for title generation
            
        Returns:
            generator: Yields chunks of the title as it is generated
        """
        if not self.api_key:
            logger.error("No API key provided for Gemini")
            yield "Untitled Chat"
            return
        
        logger.info("Streaming title generation")
        
        try:
            # Create a simple template for direct questions
            from langchain.chains import LLMChain
            from langchain.prompts import PromptTemplate
            
            template = """
            {query}
            """
            prompt = PromptTemplate(template=template, input_variables=["query"])
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Stream the title generation
            for chunk in chain.stream({"query": title_prompt}):
                if "text" in chunk:
                    yield chunk["text"]
        except Exception as e:
            logger.error(f"Error streaming title generation: {str(e)}")
            yield "Untitled Chat"
            
    def filter_by_category(self, category):
        """
        Update the retriever to filter by a specific category
        
        Args:
            category: Category name to filter by
        """
        try:
            vectorstore = self._get_vectorstore()
            
            # Create a metadata filter function
            def filter_func(metadata):
                return category.lower() in [c.lower() for c in metadata.get("categories", [])]
                
            # Daha basit çözüm: Doğrudan as_retriever metodunu filtre ile kullan
            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 20,  # Maximum limit for safety
                    "score_threshold": 0.3,  # Minimum similarity score
                    "filter": filter_func
                }
            )
            
            logger.info(f"Created filtered retriever for category '{category}'")
            self.chain.retriever = retriever
        except Exception as e:
            logger.error(f"Error filtering by category: {str(e)}")
            
    def reset_filter(self):
        """Reset any filters on the retriever"""
        try:
            vectorstore = self._get_vectorstore()
            
            # Filtre olmadan yeni retriever oluştur
            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 20,  # Maximum limit for safety
                    "score_threshold": 0.3  # Minimum similarity score
                }
            )
            
            logger.info("Reset retriever filters")
            self.chain.retriever = retriever
        except Exception as e:
            logger.error(f"Error resetting filter: {str(e)}")
            
    def clear_memory(self):
        """Clear the conversation memory"""
        try:
            logger.info(f"Clearing conversation memory for user {self.user_id}")
            self.memory.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False
            
    def trim_memory(self, max_turns=5):
        """
        Trim conversation memory to the latest X turns
        
        Args:
            max_turns: Maximum number of conversation turns to keep
        
        Returns:
            bool: Success or failure
        """
        try:
            logger.info(f"Trimming conversation memory for user {self.user_id} to {max_turns} turns")
            messages = self.memory.chat_memory.messages
            
            # If we don't have enough messages to trim, return
            if len(messages) <= max_turns * 2:  # Each turn is 2 messages (human + ai)
                return True
                
            # Keep only the most recent X turns
            self.memory.chat_memory.messages = messages[-(max_turns * 2):]
            return True
        except Exception as e:
            logger.error(f"Error trimming memory: {str(e)}")
            return False 