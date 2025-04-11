# LangChain Structured Output Feature

This document explains how to use the structured output feature implemented with LangChain to get more reliable and consistent JSON responses from AI models.

## Overview

The structured output feature uses LangChain's output parsers to convert raw AI responses directly into structured Python objects (dictionaries or Pydantic models). This offers several advantages:

1. **More consistent results**: Reduces parsing errors and formatting issues
2. **Type validation**: When using Pydantic models, responses are validated against the defined schema
3. **Better prompting**: Provides clear format instructions to the AI model
4. **Reduced post-processing**: Less need for JSON correction and fixing malformed outputs

## Implementation Details

We've implemented structured output in the following components:

1. **LLMChain Class**: Enhanced to support both JSON schema and Pydantic model output parsing
2. **Content Analyzer Module**: Updated to use structured output for both HTML content and screenshots
3. **Schema Module**: Added Pydantic models matching our expected output format
4. **System Prompts**: Updated to explicitly match our JSON schema format
5. **Utility Functions**: Helper functions to create Pydantic models from dictionary schemas

## How to Use

### 1. Using JSON Schema

```python
from tagwiseapp.reader.llm_factory import LLMChain
from tagwiseapp.reader.schemas import get_content_analysis_json_schema

# Get JSON schema
json_schema = get_content_analysis_json_schema()

# Create LLMChain with JSON schema
llm_chain = LLMChain(
    system_prompt="Your system prompt here",
    output_schema=json_schema
)

# Run the chain - returns a dictionary matching the schema
result = llm_chain.run("Your input text here")
```

### 2. Using Pydantic Models

```python
from tagwiseapp.reader.llm_factory import LLMChain
from tagwiseapp.reader.schemas import ContentAnalysisModel

# Create LLMChain with Pydantic model
llm_chain = LLMChain(
    system_prompt="Your system prompt here",
    output_schema=ContentAnalysisModel
)

# Run the chain - returns a validated Pydantic model
result = llm_chain.run("Your input text here")

# Access model properties
print(f"Title: {result.title}")
print(f"Categories: {len(result.categories)}")
for category in result.categories:
    print(f"  {category.main} > {category.sub}")
```

### 3. In Content Analyzer

The content analyzer now supports structured output by default:

```python
from tagwiseapp.reader.content_analyzer import categorize_content

# Use structured output (default)
result = categorize_content(
    content="Your HTML content here",
    url="https://example.com",
    use_structured_output=True  # This is the default
)

# Use traditional approach
result = categorize_content(
    content="Your HTML content here",
    url="https://example.com",
    use_structured_output=False
)
```

## Schema Structure

The default `ContentAnalysisModel` Pydantic model has the following structure:

```python
class CategoryModel(BaseModel):
    main: str
    sub: str
    main_id: Optional[int] = None
    sub_id: Optional[int] = None

class TagModel(BaseModel):
    name: str
    id: Optional[int] = None

class ContentAnalysisModel(BaseModel):
    url: str
    title: str
    description: str
    categories: List[CategoryModel]
    tags: List[str]
```

## Creating Custom Schemas

You can create custom schemas either as dictionaries or Pydantic models:

```python
# As dictionary
custom_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        # ... other properties
    }
}

# As Pydantic model
from pydantic import BaseModel, Field
from typing import List, Optional

class CustomModel(BaseModel):
    title: str = Field(description="Title of the content")
    content: str = Field(description="Main content")
    # ... other fields
```

## Dynamic Pydantic Model Creation

For advanced use cases, you can dynamically create Pydantic models from dictionary schemas:

```python
from tagwiseapp.reader.llm_factory import create_pydantic_model_from_dict

schema_dict = {
    "title": {"type": "string"},
    "items": {
        "type": "array",
        "items": {"type": "string"}
    }
}

DynamicModel = create_pydantic_model_from_dict(schema_dict, "CustomName")
```

## Troubleshooting

If structured output parsing fails, the `LLMChain` class will fall back to returning the raw string response. You can then use the traditional JSON correction utilities:

```python
from tagwiseapp.reader.utils import correct_json_format

corrected_json_text = correct_json_format(raw_response)
json_result = json.loads(corrected_json_text)
```

## Best Practices

1. **Clear Prompts**: Ensure your system prompts clearly specify the expected output format
2. **Model Selection**: For complex schemas, use more capable models (e.g., GPT-4, Claude, Gemini Pro)
3. **Error Handling**: Always implement fallback mechanisms for parsing failures
4. **Schema Complexity**: Start with simpler schemas and add complexity as needed
5. **Temperature Setting**: Lower temperature settings (0.0-0.3) typically produce more consistent structured outputs 