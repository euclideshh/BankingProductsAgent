# BankingProductsAgent

An AI-powered banking chatbot specialized in Panamanian banking products and services, leveraging data from SBP (Superintendencia de Bancos de Panamá) and banking websites.

## Features

- **Dual Agent System**:
  - LangChain-based Expert Agent: Specialized in Panamanian banking products (Spanish)
  - CrewAI Banking Analyst Team (Coming soon)

- **Data Processing**:
  - Dynamic content extraction using BeautifulSoup and PDFPlumberLoader
  - Efficient vector storage with Chroma DB
  - Advanced document retrieval with similarity score threshold

- **Technical Stack**:
  - Backend: FastAPI, LangChain, Ollama (Gemma 3 1B model)
  - Frontend: Streamlit
  - Embeddings: Nomic Embed
  - Vector Store: Chroma
  - Session Management: UUID-based conversation tracking

- **User Interface**:
  - Interactive chat interface
  - Real-time API status monitoring
  - Session-based conversations
  - Agent switching capability

## Architecture

- `app.py`: Streamlit-based frontend interface
- `langchain_chat_api.py`: FastAPI backend service
- `docs_scraper.py`: Web scraping functionality
- `docs_downloader.py`: Document processing and downloading
- `helper.py`: Utility functions

## Features

- Bilingual support (Spanish responses)
- Context-aware conversations
- Real-time API health monitoring
- Persistent vector storage
- Advanced document retrieval system
- Error handling and logging

## Getting Started

1. Ensure Ollama is running with the required models:
   - gemma3:1b for chat
   - nomic-embed-text for embeddings

2. Start the FastAPI backend:
   ```bash
   uvicorn langchain_chat_api:app --host 0.0.0.0 --port 8001
   ```

3. Launch the Streamlit frontend:
   ```bash
   streamlit run app.py
   ```

## Data Sources

- Superintendencia de Bancos de Panamá (SBP)
- Panamanian banking websites
- Processed and stored in vectorized format for efficient retrieval

## Security and Performance

- Session-based conversation management
- Logging system for monitoring and debugging
- Error handling and graceful degradation
- API health monitoring

