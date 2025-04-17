import os
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_core.messages import AIMessage, HumanMessage
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
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
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
                
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Daha az sonuç almayı deneyelim
            )
            
            # Basitleştirilmiş zincir oluşturma
            return ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                chain_type="stuff",  # En basit chain türü
                get_chat_history=lambda h: h,  # chat history'yi olduğu gibi kullan
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
            # Basit test yanıtı - API henüz düzgün çalışmıyorsa
            if not self.api_key:
                logger.error("No API key provided for Gemini")
                return {
                    "answer": "I can't search your bookmarks right now. API configuration is missing.",
                    "sources": []
                }
                
            # Güvenli bir şekilde chain'i çağır
            try:
                result = self.chain({"question": query})
            except Exception as e:
                logger.error(f"Chain execution error: {str(e)}")
                # Fallback yanıt
                return {
                    "answer": "I'm sorry, I encountered an error searching your bookmarks. Please try again later.",
                    "sources": []
                }
            
            # Format the response
            response = {
                "answer": result.get("answer", "I couldn't find an answer to your question."),
                "sources": []
            }
            
            # Add sources if available
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    if hasattr(doc, "metadata") and "url" in doc.metadata and "title" in doc.metadata:
                        if doc.metadata.get("source") not in ["empty", "error"]:
                            response["sources"].append({
                                "title": doc.metadata["title"],
                                "url": doc.metadata["url"],
                                "id": doc.metadata.get("id")
                            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return {"answer": "I'm sorry, I encountered an error trying to process your question.", "sources": []}
            
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
                
            # Update the retriever with the filter
            self.chain.retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 3,  # Daha az sonuç almayı deneyelim
                    "filter": filter_func
                }
            )
        except Exception as e:
            logger.error(f"Error filtering by category: {str(e)}")
            
    def reset_filter(self):
        """Reset any filters on the retriever"""
        try:
            vectorstore = self._get_vectorstore()
            self.chain.retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Daha az sonuç almayı deneyelim
            )
        except Exception as e:
            logger.error(f"Error resetting filter: {str(e)}")
            
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear() 