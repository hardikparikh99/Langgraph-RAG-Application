# Document QA System (RAG) with Streamlit & FastAPI

A Retrieval-Augmented Generation (RAG) application for document question answering using LangGraph, Streamlit, FastAPI, and Pinecone. Users can upload documents (PDF, DOCX, XLSX, PPTX) via a web interface and ask questions about their content.

## Features

- **Streamlit Web UI**: Upload documents and chat with the QA agent interactively.
- **REST API (FastAPI)**: Programmatic access for document upload, search, and chat history.
- **Multiple Document Types**: Supports PDF, DOCX, XLSX, and PPTX.
- **Advanced Chunking**: Intelligent document chunking per file type.
- **LangGraph-Powered Agent**: Manages retrieval and answer generation.
- **Pinecone Vector Store**: Efficient similarity search and storage.
- **Persistent History**: Saves chats and uploaded documents for future sessions.

## Prerequisites

- Python 3.8+
- [Pinecone](https://www.pinecone.io/) account and API key
- [Groq](https://groq.com/) API key for fast language model inference

## Setup

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**
    Create a `.env` file in the project root and add your API keys:
    ```
    PINECONE_API_KEY="your_pinecone_api_key"
    PINECONE_ENVIRONMENT="your_pinecone_environment"
    GROQ_API_KEY="your_groq_api_key"
    ```

## Running the Application

### 1. Start the FastAPI Backend

The backend provides REST endpoints for document upload, question answering, and chat/document management.

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Production mode
# uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- The API will be available at: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
- Alternative documentation (ReDoc): http://localhost:8000/redoc

### 2. Start the Streamlit Frontend

The Streamlit app provides a user-friendly web interface for uploading documents and chatting with the agent.

```bash
# Default port (8501)
streamlit run app/streamlit_app.py

# Custom port (if 8501 is in use)
# streamlit run app/streamlit_app.py --server.port 8502
```

- The UI will be available at: http://localhost:8501
- You can stop the server by pressing `Ctrl+C` in the terminal

## Project Structure

```
Langgraph-RAG-Application/
├── app/                    # Main application package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application entry point
│   ├── streamlit_app.py    # Streamlit UI application
│   ├── api/                # API routes and endpoints
│   ├── core/               # Core application logic
│   │   ├── __init__.py
│   │   └── ...
│   ├── config/             # Configuration management
│   │   ├── __init__.py
│   │   └── ...
│   └── utils/              # Utility functions
│       ├── __init__.py
│       └── ...
├── data/                   # Application data
│   ├── chats/              # Chat history storage
│   └── documents/          # Uploaded documents storage
├── tests/                  # Test files
├── .env                    # Environment variables
├── .gitignore
├── requirements.txt        # Python dependencies
├── agent.py                # Legacy agent implementation
├── config.py               # Legacy configuration
├── document_processor.py   # Legacy document processing
├── main.py                 # Legacy entry point
├── storage.py              # Legacy storage
├── test.py                 # Test file
└── README.md               # This file
```

## Key Components

- **`app/streamlit_app.py`**: Main Streamlit application (UI for upload & chat)
- **`main.py`**: FastAPI backend (REST API for document and chat management)
- **`app/core/`**: Core logic (agent, document processing, storage, vector store)
- **`app/api/`**: FastAPI route definitions
- **`data/`**: Persistent storage for chats and documents

## Usage

- **Upload documents** via the Streamlit UI or `/upload` API endpoint.
- **Ask questions** about your documents in the chat UI or via the `/ask` API endpoint.
- **Review chat and document history** in the UI or via API endpoints.

## API Endpoints (FastAPI)

- `POST /upload` — Upload a document
- `POST /ask` — Ask a question
- `GET /documents` — List all documents
- `DELETE /documents/{namespace}` — Delete a document
## API Endpoints

### Document Management
- `POST /upload` - Upload a document
- `GET /documents` - List all uploaded documents
- `DELETE /documents/{doc_id}` - Delete a specific document

### Question Answering
- `POST /ask` - Ask a question about your documents

### Chat Management
- `GET /chats` - List all chats
- `GET /chats/{chat_id}` - Get a specific chat history
- `DELETE /chats/{chat_id}` - Delete a specific chat history

For full interactive API documentation, visit: http://localhost:8000/docs

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
# Install pre-commit hooks
pre-commit install

# Run all pre-commit hooks
pre-commit run --all-files
```

### Linting
```bash
# Run flake8
flake8 .

# Run black code formatter
black .
```

## Notes

- The application uses a modular structure with core functionality in the `app/` directory
- Legacy files (`document_processor.py`, `vector_store.py`, `agent.py`, `storage.py`) are kept for reference but the main implementation is now under `app/core/`
- Make sure your `.env` file is properly configured with all required API keys before running the application
- For production deployment:
  - Remove the `--reload` flag from the Uvicorn command
  - Consider using a production ASGI server like Gunicorn with Uvicorn workers
  - Set up proper logging and monitoring
  - Configure HTTPS using a reverse proxy like Nginx
 