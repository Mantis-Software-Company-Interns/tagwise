"""
Schema Module

This module defines Pydantic models for structured output parsing.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class CategoryModel(BaseModel):
    """Model for category with main and sub categories"""
    main: str = Field(description="Main category name")
    sub: str = Field(description="Subcategory name")
    
    # These will be populated after matching with existing categories
    main_id: Optional[int] = Field(None, description="Main category ID")
    sub_id: Optional[int] = Field(None, description="Subcategory ID")

class TagModel(BaseModel):
    """Model for tag"""
    name: str = Field(description="Tag name")
    
    # This will be populated after matching with existing tags
    id: Optional[int] = Field(None, description="Tag ID")

class ContentAnalysisModel(BaseModel):
    """Model for content analysis results"""
    url: str = Field(description="URL of the analyzed content")
    title: str = Field(description="Title of the content")
    description: str = Field(description="Description of the content")
    categories: List[CategoryModel] = Field(description="List of categories")
    tags: List[str] = Field(description="List of tags")
    
    class Config:
        """Pydantic config"""
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "title": "Example Title",
                "description": "Example Description",
                "categories": [
                    {"main": "Technology", "sub": "Web Development"}
                ],
                "tags": ["example", "web", "tutorial"]
            }
        }

def get_content_analysis_json_schema() -> dict:
    """
    Returns the JSON schema for content analysis.
    
    This can be used in prompt instructions to guide the AI in generating
    properly structured output.
    
    Returns:
        dict: JSON schema
    """
    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the content"
            },
            "description": {
                "type": "string",
                "description": "Description of the content"
            },
            "categories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "main": {
                            "type": "string",
                            "description": "Main category name"
                        },
                        "sub": {
                            "type": "string",
                            "description": "Subcategory name"
                        }
                    },
                    "required": ["main", "sub"]
                },
                "description": "List of categories"
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of tags"
            }
        },
        "required": ["title", "description", "categories", "tags"]
    } 