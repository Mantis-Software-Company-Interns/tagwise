"""
LLM Factory Module

This module provides a factory for creating LLM instances using LangChain.
"""

import base64
import time
import logging
from typing import Optional, List, Dict, Any, Union, Type

# LangChain imports
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, create_model, Field

# LLM provider-specific imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Error handling
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from . import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory class for creating LLM instances with fallback support.
    """
    
    @staticmethod
    def create_llm(
        provider: str = None,
        model_name: str = None,
        temperature: float = None,
        max_tokens: int = None,
        timeout: int = None,
        model_type: str = "text"
    ) -> BaseChatModel:
        """
        Creates an LLM instance for the specified provider.
        
        Args:
            provider (str, optional): The LLM provider (gemini, openai, anthropic)
            model_name (str, optional): The model name
            temperature (float, optional): Temperature setting for generation
            max_tokens (int, optional): Maximum tokens to generate
            timeout (int, optional): Request timeout in seconds
            model_type (str, optional): Type of model (text or vision)
            
        Returns:
            BaseChatModel: LangChain chat model instance
        """
        # If no provider specified, use default
        if not provider:
            provider = settings.DEFAULT_PROVIDER
            
        # Get model configuration
        config = settings.get_model_config(provider, model_type)
        
        # Override config with provided parameters
        if model_name:
            config["model_name"] = model_name
        if temperature is not None:
            config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens
        if timeout is None:
            timeout = settings.REQUEST_TIMEOUT
            
        logger.info(f"Creating LLM with provider: {provider}, model: {config['model_name']}")
        
        # Create LLM instance based on provider
        try:
            if provider == "gemini":
                return ChatGoogleGenerativeAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    max_output_tokens=config["max_tokens"],
                    google_api_key=settings.GEMINI_API_KEY,
                    request_timeout=timeout,
                )
            elif provider == "openai":
                return ChatOpenAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    openai_api_key=settings.OPENAI_API_KEY,
                    request_timeout=timeout,
                )
            elif provider == "anthropic":
                return ChatAnthropic(
                    model=config["model_name"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    request_timeout=timeout,
                )
            else:
                logger.warning(f"Unknown provider: {provider}, falling back to Gemini")
                return LLMFactory.create_llm("gemini", model_type=model_type)
                
        except Exception as e:
            logger.error(f"Error creating LLM with provider {provider}: {str(e)}")
            raise


class LLMChain:
    """
    Class for creating and running LLM chains with fallback support.
    """
    
    def __init__(
        self,
        system_prompt: str,
        providers: List[str] = None, 
        model_type: str = "text",
        output_schema: Optional[Union[Dict, Type[BaseModel]]] = None
    ):
        """
        Initialize LLM chain with fallback support.
        
        Args:
            system_prompt (str): System instruction for the LLM
            providers (List[str], optional): List of providers to try in order
            model_type (str, optional): Type of model (text or vision)
            output_schema (Union[Dict, Type[BaseModel]], optional): Schema for structured output
        """
        self.system_prompt = system_prompt
        self.model_type = model_type
        self.output_schema = output_schema
        
        # Set providers - use default + fallbacks if not provided
        if not providers:
            self.providers = [settings.DEFAULT_PROVIDER] + settings.FALLBACK_PROVIDERS
        else:
            self.providers = providers
            
        # Remove duplicates and empty strings
        self.providers = [p for p in dict.fromkeys(self.providers) if p]
        logger.info(f"Initialized LLM chain with providers: {self.providers}")
        
        # Set up output parser if schema provided
        self.output_parser = None
        if output_schema:
            if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
                # Pydantic model schema
                self.output_parser = PydanticOutputParser(pydantic_object=output_schema)
                logger.info(f"Using PydanticOutputParser with schema: {output_schema.__name__}")
            elif isinstance(output_schema, dict):
                # JSON schema
                self.output_parser = JsonOutputParser()
                # We'll apply the schema validation after parsing
                logger.info("Using JsonOutputParser with custom schema validation")
            else:
                logger.warning(f"Unsupported schema type: {type(output_schema)}, falling back to string output")
                self.output_parser = StrOutputParser()
        else:
            # Default to string output
            self.output_parser = StrOutputParser()
        
    def _create_messages(self, input_text: str, image_data: Optional[Dict] = None, provider: str = None):
        """
        Creates the message list for the LLM.
        
        Args:
            input_text (str): The input text
            image_data (Dict, optional): Image data for vision models
            provider (str, optional): The provider being used
            
        Returns:
            List: List of messages
        """
        # Add output parser format instructions if needed
        system_content = self.system_prompt
        if self.output_parser and hasattr(self.output_parser, "get_format_instructions"):
            format_instructions = self.output_parser.get_format_instructions()
            system_content = f"{system_content}\n\n{format_instructions}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=input_text)
        ]
        
        # Add image content to the human message if provided and it's a vision model
        if image_data and self.model_type == "vision":
            if provider == "gemini":
                # For Gemini, add the image directly to the content
                messages[1] = HumanMessage(content=[
                    {"type": "text", "text": input_text},
                    {"type": "image_url", "image_url": image_data["image_url"]}
                ])
            else:
                # For other providers, use additional_kwargs
                human_message = messages[1]
                human_message.additional_kwargs = {"image_url": image_data}
        
        return messages
        
    @retry(
        stop=stop_after_attempt(settings.RETRY_COUNT),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY, min=1, max=10)
    )
    def _run_with_provider(self, provider: str, input_text: str, image_data: Optional[Dict] = None):
        """
        Run the chain with a specific provider.
        
        Args:
            provider (str): The provider to use
            input_text (str): The input text
            image_data (Dict, optional): Image data for vision models
            
        Returns:
            Any: The LLM response (string or structured object)
        """
        try:
            # Create LLM
            llm = LLMFactory.create_llm(provider=provider, model_type=self.model_type)
            
            # Create messages using the separate method and passing the provider
            messages = self._create_messages(input_text, image_data, provider)
            
            # Run chain
            start_time = time.time()
            response = llm.invoke(messages)
            
            # Extract the content from the response
            if hasattr(response, 'content'):
                result = response.content
            else:
                result = str(response)
            
            duration = time.time() - start_time
            logger.info(f"Provider {provider} responded in {duration:.2f} seconds")
            
            # Parse the result if we have an output parser
            if self.output_parser:
                try:
                    logger.info("Parsing output with parser")
                    parsed_result = self.output_parser.parse(result)
                    logger.info(f"Successfully parsed output: {type(parsed_result)}")
                    return parsed_result
                except Exception as parser_error:
                    logger.warning(f"Error parsing output: {str(parser_error)}")
                    logger.warning("Returning raw output instead")
                    return result
            
            return result
            
        except Exception as e:
            logger.error(f"Error with provider {provider}: {str(e)}")
            raise
    
    def run(self, input_text: str, image_data: Optional[Dict] = None) -> Any:
        """
        Run the chain with fallback support.
        
        Args:
            input_text (str): The input text
            image_data (Dict, optional): Image data for vision models
            
        Returns:
            Any: The LLM response (string or structured object)
        """
        errors = []
        
        # Try each provider in order
        for provider in self.providers:
            try:
                logger.info(f"Trying provider: {provider}")
                return self._run_with_provider(provider, input_text, image_data)
                
            except Exception as e:
                error_msg = f"Provider {provider} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
                # If it's the last provider, don't continue
                if provider == self.providers[-1]:
                    logger.error("All providers failed")
                    raise Exception(f"All providers failed: {'; '.join(errors)}")
                
                # Otherwise, try the next provider
                logger.info(f"Falling back to next provider")
                
    def process_image(self, image_base64: str) -> Dict:
        """
        Process image data for vision models.
        
        Args:
            image_base64 (str): Base64-encoded image
            
        Returns:
            Dict: Image data in the format expected by the model
        """
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Return image data in the format expected by LangChain
        return {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}",
                "detail": "high"
            }
        }

def create_pydantic_model_from_dict(schema_dict: Dict[str, Any], model_name: str = "DynamicOutputModel") -> Type[BaseModel]:
    """
    Create a Pydantic model from a dictionary schema.
    
    Args:
        schema_dict (Dict[str, Any]): Dictionary defining the schema
        model_name (str, optional): Name for the model. Defaults to "DynamicOutputModel".
    
    Returns:
        Type[BaseModel]: A Pydantic model class
    """
    # Helper function to convert schema types to Python types
    def get_field_type(field_schema):
        if isinstance(field_schema, dict):
            # Handle object fields
            if field_schema.get('type') == 'object':
                properties = field_schema.get('properties', {})
                nested_fields = {
                    k: (get_field_type(v), Field(...)) for k, v in properties.items()
                }
                return create_model(f"{model_name}_{k}", **nested_fields)
            # Handle array fields
            elif field_schema.get('type') == 'array':
                items = field_schema.get('items', {})
                return List[get_field_type(items)]
            # Handle simple fields
            else:
                return str if field_schema.get('type') == 'string' else Any
        else:
            # Default to Any if schema is not properly defined
            return Any
    
    # Create model fields
    fields = {}
    for field_name, field_schema in schema_dict.items():
        fields[field_name] = (get_field_type(field_schema), Field(...))
    
    # Create and return the model
    return create_model(model_name, **fields) 