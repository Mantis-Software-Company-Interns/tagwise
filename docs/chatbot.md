# TagWise Chatbot Documentation

The TagWise Chatbot provides an intelligent assistant that helps users search and explore their bookmarks using natural language. The chatbot is powered by Google's Gemini LLM and uses retrieval-augmented generation (RAG) to provide relevant answers based on saved bookmarks.

## Features

- **Natural Language Search**: Ask questions about your bookmarks in everyday language
- **Context-Aware Answers**: The chatbot remembers the conversation context for follow-up questions
- **Source References**: Responses include links to the relevant bookmarks
- **Category Filtering**: Ask about bookmarks in specific categories

## Technical Implementation

The chatbot implementation consists of several components:

1. **Embeddings**: Bookmark content is embedded using `GoogleGenerativeAIEmbeddings` (Gemini)
2. **Vector Database**: Embeddings are stored in a FAISS vector database for efficient semantic search
3. **RAG Pipeline**: The `ConversationalRetrievalChain` retrieves relevant bookmarks and generates responses
4. **API Endpoints**: Django views handle chatbot initialization, messaging, and state management
5. **Frontend UI**: JavaScript integration connects the UI to the backend API

## Usage Examples

Here are some examples of questions you can ask the chatbot:

- "What bookmarks do I have about Python?"
- "Show me my programming tutorials"
- "Find articles about machine learning"
- "What was the website about Django I saved recently?"
- "Tell me more about that first link"
- "What tags are on that bookmark?"

## Backend API Endpoints

The chatbot exposes the following API endpoints:

- **GET /chatbot/init/**: Initialize the chatbot by creating the vector index (if it doesn't exist)
- **POST /chatbot/ask/**: Send a message to the chatbot and get a response
- **POST /chatbot/reset/**: Reset the chatbot conversation memory

## Management Commands

A management command is available to manually rebuild the vector index:

```
python manage.py index_bookmarks [--user_id ID]
```

This is useful when setting up the chatbot for the first time or if you need to rebuild the index from scratch.

## Signal Handlers

Signal handlers are set up to automatically update the vector index when bookmarks are:

- Created: The new bookmark is added to the index
- Updated: The bookmark's index entry is updated
- Deleted: The entire index for that user is rebuilt

## Development Notes

- The chatbot uses the Gemini API key from the environment variables
- Configuration settings are loaded from `gemini_config.json`
- Each user has their own vector database file stored in `tagwiseapp/data/vectorstores/`
- Conversation memory is maintained as long as the chatbot instance is alive 