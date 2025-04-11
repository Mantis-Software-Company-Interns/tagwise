#!/usr/bin/env python3
"""
Test script to demonstrate structured output capabilities with LangChain.
"""

import logging
import json
from tagwiseapp.reader.llm_factory import LLMChain
from tagwiseapp.reader.schemas import ContentAnalysisModel, get_content_analysis_json_schema
from tagwiseapp.reader.prompts import TEXT_SYSTEM_INSTRUCTION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_structured_output():
    """
    Test structured output capabilities with LangChain.
    """
    logger.info("Testing structured output with LangChain...")
    
    # Sample content to categorize
    content = """
    # Python Programming Language
    
    Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.
    
    Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming. It is often described as a "batteries included" language due to its comprehensive standard library.
    
    ## Key Features
    
    - Easy to learn and use
    - Interpreted language
    - Object-oriented
    - Extensive standard library
    - Cross-platform
    
    ## Popular Frameworks
    
    - Django and Flask for web development
    - TensorFlow, PyTorch, and scikit-learn for machine learning
    - Pandas and NumPy for data analysis
    """
    
    url = "https://example.com/python-programming"
    
    # Method 1: Using JSON Schema
    try:
        logger.info("Method 1: Using JSON Schema")
        
        # Get JSON schema
        json_schema = get_content_analysis_json_schema()
        
        # Create LLM chain with JSON schema
        llm_chain_json = LLMChain(
            system_prompt=TEXT_SYSTEM_INSTRUCTION,
            output_schema=json_schema
        )
        
        # Run the chain
        result_json = llm_chain_json.run(f"""
        Bu bir web sayfası içeriğidir. Lütfen bu içeriği analiz edip kategorilere ayır ve etiketle.
        
        URL: {url}
        
        İçerik:
        {content}
        """)
        
        # Print result
        logger.info(f"Result type: {type(result_json)}")
        logger.info(f"Structured output:\n{json.dumps(result_json, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"Error using JSON schema: {str(e)}")
    
    # Method 2: Using Pydantic Model
    try:
        logger.info("\nMethod 2: Using Pydantic Model")
        
        # Create LLM chain with Pydantic model
        llm_chain_pydantic = LLMChain(
            system_prompt=TEXT_SYSTEM_INSTRUCTION,
            output_schema=ContentAnalysisModel
        )
        
        # Run the chain
        result_pydantic = llm_chain_pydantic.run(f"""
        Bu bir web sayfası içeriğidir. Lütfen bu içeriği analiz edip kategorilere ayır ve etiketle.
        
        URL: {url}
        
        İçerik:
        {content}
        """)
        
        # Print result
        logger.info(f"Result type: {type(result_pydantic)}")
        logger.info(f"Result is Pydantic model: {isinstance(result_pydantic, ContentAnalysisModel)}")
        if isinstance(result_pydantic, ContentAnalysisModel):
            logger.info(f"Model validation: OK")
            logger.info(f"Title: {result_pydantic.title}")
            logger.info(f"Categories: {len(result_pydantic.categories)}")
            for i, category in enumerate(result_pydantic.categories):
                logger.info(f"  Category {i+1}: {category.main} > {category.sub}")
            logger.info(f"Tags: {', '.join(result_pydantic.tags)}")
        else:
            logger.info(f"Structured output:\n{json.dumps(result_pydantic, indent=2, ensure_ascii=False) if isinstance(result_pydantic, dict) else str(result_pydantic)}")
        
    except Exception as e:
        logger.error(f"Error using Pydantic model: {str(e)}")
    
    # Method 3: Traditional approach (for comparison)
    try:
        logger.info("\nMethod 3: Traditional approach (for comparison)")
        
        # Create LLM chain without structured output
        llm_chain_traditional = LLMChain(
            system_prompt=TEXT_SYSTEM_INSTRUCTION
        )
        
        # Run the chain
        result_traditional = llm_chain_traditional.run(f"""
        Bu bir web sayfası içeriğidir. Lütfen bu içeriği analiz edip kategorilere ayır ve etiketle.
        
        URL: {url}
        
        İçerik:
        {content}
        """)
        
        # Print result
        logger.info(f"Result type: {type(result_traditional)}")
        logger.info(f"Raw output:\n{result_traditional[:500]}...")
        
        # Try to parse the JSON
        try:
            from tagwiseapp.reader.utils import correct_json_format
            corrected_json = correct_json_format(result_traditional)
            parsed_json = json.loads(corrected_json)
            logger.info(f"Successfully parsed JSON from raw output")
            logger.info(f"Parsed output:\n{json.dumps(parsed_json, indent=2, ensure_ascii=False)}")
        except Exception as parse_error:
            logger.error(f"Error parsing JSON from raw output: {str(parse_error)}")
        
    except Exception as e:
        logger.error(f"Error using traditional approach: {str(e)}")
    
    logger.info("Structured output test completed.")

if __name__ == "__main__":
    test_structured_output() 