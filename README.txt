# Banking Agents 

This application provides a chatbot interface for interacting with different banking agents that can answer questions about Panamanian banking products and fee schedules.

## Architecture

The application uses a modular architecture with:

1. **Streamlit Frontend**: A unified interface that can connect to multiple agent APIs
2. **LangChain Agent API**: A FastAPI backend for the LangChain-based banking expert
3. **CrewAI Agent API**: (To be implemented separately) for the CrewAI-based banking analyst team

This separation allows you to develop and scale different agent types independently.

## Setup

### Prerequisites

- Python 3.8+
- Ollama installed with the following models:
  - nomic-embed-text:latest (for embeddings) 
  - gemma3:1b (for chat)
- Existing Chroma vector database in "./data/vector_store"

### Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the LangChain agent API:

```bash
python langchain_banking_api.py
```

This will start the LangChain API server at http://localhost:8001

2. In a separate terminal, start the Streamlit frontend:

```bash
streamlit run streamlit_app.py
```

This will start the Streamlit app and open it in your browser.

3. (Future) Start the CrewAI agent API on port 8002

## Adding More Agents

To add a new agent API:

1. Implement a new API with compatible `/session`, `/chat`, and `/info` endpoints
2. Update the `AGENT_APIS` dictionary in `streamlit_app.py` to include the new agent

## API Documentation

The API documentation for the LangChain agent is available at http://localhost:8001/docs when the backend is running.


