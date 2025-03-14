# TagWise Reader Package

This package provides functionality for analyzing web pages and categorizing them using Gemini AI.

## Modules

- `django_setup.py`: Functions for setting up the Django environment
- `html_fetcher.py`: Functions for fetching HTML content from URLs
- `screenshot.py`: Functions for capturing screenshots of web pages using Selenium
- `content_extractor.py`: Functions for extracting content from HTML
- `gemini_analyzer.py`: Functions for analyzing content with Gemini AI
- `category_matcher.py`: Functions for matching categories and tags with existing ones in the database
- `utils.py`: Utility functions
- `main.py`: Main functions for URL analysis

## Usage

### From Python Code

```python
from tagwiseapp.reader.main import analyze_url

# Analyze a URL
result = analyze_url("https://www.example.com")
print(result)
```

### From Command Line

```bash
# Using the Django management command
python manage.py analyze_url https://www.example.com

# Interactive mode
python manage.py analyze_url -i

# From a file
python manage.py analyze_url -f urls.txt
```

### Using the CLI Script

```bash
# Direct execution
python tagwiseapp/reader_cli.py https://www.example.com

# Interactive mode
python tagwiseapp/reader_cli.py -i

# From a file
python tagwiseapp/reader_cli.py -f urls.txt
```

## Requirements

- Python 3.8+
- Django
- httpx
- beautifulsoup4
- selenium
- webdriver-manager
- google-generativeai
- python-dotenv
- Pillow

## Configuration

The package requires a Gemini API key to be set in the `.env` file:

```
GEMINI_API_KEY=your_api_key_here
``` 