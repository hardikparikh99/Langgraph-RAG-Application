from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "langgraph-rag")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Document Processing Settings
# Increased chunk size and overlap for better semantic coherence
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 500

# Supported File Types
SUPPORTED_FILE_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
}

# LLM Settings
LLM_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "llama3.2:1b"

# Prompt Templates
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context from documents.
Follow these rules strictly:

1. ONLY answer questions that can be answered using the provided context
2. If the question cannot be answered using the provided context:
   - Apologize for not being able to answer
   - Explain that you don't have enough information from the documents
   - Suggest that the user upload the relevant document if they haven't already
3. When answering:
   - Always cite the source (document type and page/sheet number)
   - For Excel files, include the sheet name in your citation
   - Be specific and accurate in your answers
   - If you're unsure about any part of the answer, say so
4. For general conversation (greetings, etc.):
   - Respond naturally and politely
   - Keep responses brief and friendly
5. Keep your answers concise and relevant to the question

Context: {context}

Question: {question}"""

# Agent Settings
AGENT_SETTINGS: Dict[str, Any] = {
    "max_iterations": 3,
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 1000
}

# Pinecone Settings
PINECONE_SETTINGS = {
    "index_name": "document-qa",
    "dimension": 4096,  # Dimension for Llama2 embeddings
    "metric": "cosine"
}

# Chunking Settings
CHUNK_SETTINGS = {
    "chunk_size": 1000,
    "chunk_overlap": 200
} 