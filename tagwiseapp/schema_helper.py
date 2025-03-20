from google.ai.generativelanguage import Schema, Type

def create_response_schema():
    """
    Creates a structured output schema for Gemini API responses.
    
    Returns:
        Schema: A schema object for structured output
    """
    return Schema(
        type=Type.OBJECT,
        properties={
            "title": Schema(
                type=Type.STRING,
            ),
            "description": Schema(
                type=Type.STRING,
            ),
            "categories": Schema(
                type=Type.ARRAY,
                items=Schema(
                    type=Type.OBJECT,
                    properties={
                        "main_category": Schema(
                            type=Type.STRING,
                        ),
                        "subcategory": Schema(
                            type=Type.STRING,
                        ),
                    },
                ),
            ),
            "tags": Schema(
                type=Type.ARRAY,
                items=Schema(
                    type=Type.STRING,
                ),
            ),
        },
    ) 