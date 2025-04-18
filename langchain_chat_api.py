# langchain_banking_api.py
import os
import traceback
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
import uvicorn
import uuid
import logging


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LangChain Banking Agent API")

# Store active conversations
conversations = {}

# Define request and response models
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

class SessionRequest(BaseModel):
    pass

class SessionResponse(BaseModel):
    session_id: str
    agent_type: str = "langchain"
    agent_name: str = "Experto en Productos Bancarios Panameños"

# Middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request path and method
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process the request and get the response
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Create a new conversation session
@app.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    # Generate a session ID
    session_id = str(uuid.uuid4())
    
    try:
        logger.info("Initializing embeddings...")
        # Initialize embeddings
        embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
        
        logger.info("Checking for vector store directory...")
        # Check if vector store directory exists
        persist_directory = "./data/vector_store"
        if not os.path.exists(persist_directory):
            raise HTTPException(
                status_code=500, 
                detail=f"Vector store directory not found: {persist_directory}"
            )
        
        logger.info("Initializing Chroma vector store...")
        # Initialize the vector store from the persist directory
        try:
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize vector store: {str(e)}"
            )
        
        logger.info("Creating retriever...")
        # Create a retriever with diverse search results
        retriever = vectorstore.as_retriever(
            # *** Standard similarity search for top 3 documents ***
            #search_type="similarity",            
            #search_kwargs={"k": 5}  
            
            # *** Similarity search with a score threshold ***
            search_type="similarity_score_threshold",
            search_kwargs={'k': 10, 'score_threshold': 0.90} 
        )
        
        logger.info("Initializing ChatOllama model...")
        # Initialize the ChatOllama model
        try:
            llm = ChatOllama(model="gemma3:1b",temperature=0)
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize LLM. Is Ollama running? Error: {str(e)}"
            )
        
        logger.info("Setting up memory...")
        # Initialize memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        logger.info("Creating prompt template...")
        # Create custom prompt template for the Panamanian Banking Expert
        # --- Historial de conversación: {chat_history}
        prompt_template = """Eres un experto en productos y tarifas de servicios bancarios de Panamá.        
        Debes responder siempre en español. Utiliza la siguiente información de contexto para responder a la pregunta del usuario.        
        Si no conoces la respuesta, simplemente indica que no tienes esa información, no inventes respuestas. No menciones bancos de otros paises que no sea de Panamá.        
        Mantén tus respuestas concisas, precisas y profesionales.
        
        Contexto: {context}        
        
        Pregunta: {question}
        
        Respuesta:"""
        
        qa_prompt = PromptTemplate(
            template=prompt_template, 
            #input_variables=["context", "chat_history", "question"]
            input_variables=["context", "question"]
        )
        
        logger.info("Creating ConversationalRetrievalChain...")
        # Create the conversational chain with custom prompt
        try:
            conversation = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                combine_docs_chain_kwargs={"prompt": qa_prompt},
                verbose=True
            )
        except Exception as e:
            logger.error(f"Failed to create ConversationalRetrievalChain: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create conversation chain: {str(e)}"
            )
        
        # Test query to verify everything works
        logger.info("Testing the chain with a simple query...")
        try:
            # Simple test query
            test_result = conversation.invoke({"question": "Hola"})
            logger.info(f"Test query successful. Response: {test_result['answer'][:50]}...")
        except Exception as e:
            logger.error(f"Test query failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Test query failed: {str(e)}"
            )
        
        # Store the conversation
        conversations[session_id] = {
            "conversation": conversation,
            "memory": memory
        }
        
        logger.info(f"Created new session: {session_id}")
        
        return {
            "session_id": session_id,
            "agent_type": "langchain",
            "agent_name": "Experto en Productos Bancarios Panameños"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_message = f"Unexpected error creating session: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

# Chat with the agent
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversation_data = conversations[request.session_id]
    
    try:
        # Get the conversation chain
        conversation = conversation_data["conversation"]
        
        logger.info(f"Processing message for session {request.session_id}")
        logger.info(f"User message: {request.message}")
        
        # Process the message
        response = conversation.invoke({"question": request.message})
        
        answer = response["answer"]
        
        logger.info(f"Agent response: {answer[:100]}...")
        
        return {
            "session_id": request.session_id,
            "response": answer
        }
        
    except Exception as e:
        error_message = f"Error processing chat: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

# Get agent information
@app.get("/info")
async def get_info():
    return {
        "agent_type": "langchain",
        "agent_name": "Experto en Productos Bancarios Panameños",
        "description": "Un experto en productos bancarios panameños y tarifas de servicios bancarios que responde en español."
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Check if Ollama is available
        try:
            embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
            embed_test = embeddings.embed_query("test")
            ollama_status = "ok" if len(embed_test) > 0 else "error"
        except Exception as e:
            ollama_status = f"error: {str(e)}"
        
        # Check if vector store exists
        persist_directory = "./data/vector_store"
        vector_store_exists = os.path.exists(persist_directory)
        
        return {
            "status": "up",
            "ollama": ollama_status,
            "vector_store": "exists" if vector_store_exists else "missing",
            "active_sessions": len(conversations)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)