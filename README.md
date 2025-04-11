# TagWise - LLM-Powered Content Analyzer

TagWise is a Django web application that uses AI to analyze web content, extract meaningful information, and categorize it for easier organization and navigation.

## New Features with LangChain Integration

The codebase has been refactored to use LangChain, providing the following benefits:

- **Provider-agnostic architecture**: Easily switch between different LLM providers (Gemini, OpenAI, Anthropic)
- **Automatic failover**: If one LLM provider fails, the system automatically tries another
- **Centralized configuration**: All LLM settings are managed in a central location
- **Enhanced error handling**: Better exception handling and logging

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your environment variables in `.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DEFAULT_LLM_PROVIDER=gemini  # Options: gemini, openai, anthropic
   FALLBACK_LLM_PROVIDERS=openai,anthropic  # Comma-separated list
   ```
4. Run migrations:
   ```
   python manage.py migrate
   ```
5. Start the development server:
   ```
   python manage.py runserver
   ```

## Architecture

The refactored code uses a provider-agnostic approach with LangChain:

- `settings.py`: Central configuration for LLM providers
- `llm_factory.py`: Factory pattern for creating LLM instances with fallback support
- `content_analyzer.py`: Main module for content analysis features
- `gemini_analyzer.py`: Legacy module for backward compatibility

## Usage

The application maintains backward compatibility, so existing code will continue to work. For new code, it's recommended to use the new content_analyzer module directly:

```python
from tagwiseapp.reader.content_analyzer import (
    generate_summary_from_content,
    categorize_content,
    analyze_screenshot
)

# Example: Categorize content
result = categorize_content(
    content="Your HTML or text content",
    url="https://example.com",
    existing_title="Optional title",
    existing_description="Optional description"
)
```

## Extending with New LLM Providers

To add a new LLM provider:

1. Update settings.py to include the new provider configuration
2. Add the provider to the LLMFactory class in llm_factory.py
3. Install the required LangChain integration package

## License

This project is licensed under the MIT License - see the LICENSE file for details.