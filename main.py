from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
import uuid
import os
import uvicorn
import time

from document_processor import DocumentProcessor
from vector_store import VectorStore
from agent import DocumentQAAgent
from config import SUPPORTED_FILE_TYPES
from storage import Storage

app = FastAPI(
    title="Document QA System",
    description="A RAG application for document question answering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    document_processor = DocumentProcessor()
    vector_store = VectorStore()
    agent = DocumentQAAgent(vector_store)
    storage = Storage()  # Initialize storage for chat histories
except Exception as e:
    print(f"Error initializing components: {str(e)}")
    raise

class Question(BaseModel):
    text: str

class Source(BaseModel):
    source_type: str
    page: Optional[str] = None
    sheet_name: Optional[str] = None
    relevance_score: float
    text_snippet: str
    
    # Custom validator to ensure page is always a string
    @validator('page', pre=True)
    def ensure_string_page(cls, v):
        if v is not None:
            return str(v)
        return v

class Response(BaseModel):
    answer: str
    sources: List[Source] = []
    
# Chat history models
class ChatInfo(BaseModel):
    id: str
    preview: str
    modified: str

class ChatMessage(BaseModel):
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None

@app.get("/")
async def root():
    return {
        "message": "Document QA System API is running",
        "endpoints": {
            "upload": "/upload - POST - Upload a document",
            "ask": "/ask - POST - Ask a question",
            "documents": "/documents - GET - List all documents",
            "delete": "/documents/{namespace} - DELETE - Delete a document",
            "chats": "/chats - GET - List all chats",
            "chat": "/chats/{chat_id} - GET - Get a specific chat history",
            "delete_chat": "/chats/{chat_id} - DELETE - Delete a specific chat history"
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
        
    if file.content_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {list(SUPPORTED_FILE_TYPES.keys())}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process document
        file_type = SUPPORTED_FILE_TYPES[file.content_type]
        chunks = document_processor.process_document(content, file_type)
        
        # Generate unique namespace for this document
        namespace = str(uuid.uuid4())
        
        # Store in vector database
        vector_store.add_documents(chunks, namespace)
        
        return {
            "message": "File processed successfully",
            "namespace": namespace,
            "filename": file.filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=Response)
async def ask_question(question: Question):
    try:
        result = agent.process_message(message=question.text)
        return Response(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{namespace}")
async def delete_document(namespace: str):
    try:
        vector_store.delete_namespace(namespace)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    try:
        # Get all documents from the vector store
        documents = vector_store.list_all_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat history endpoints
@app.get("/chats", response_model=List[ChatInfo])
async def list_chats():
    try:
        chats = storage.list_all_chats()
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}", response_model=List[ChatMessage])
async def get_chat(chat_id: str):
    try:
        chat_history = storage.load_chat_history(chat_id)
        if not chat_history:
            raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found")
        return chat_history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        success = storage.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found or could not be deleted")
        return {"message": f"Chat with ID {chat_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 