import streamlit as st
import uuid
import os
from typing import List, Dict, Any
import time
from io import BytesIO

from document_processor import DocumentProcessor
from vector_store import VectorStore
from agent import DocumentQAAgent
from storage import Storage

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
agent = DocumentQAAgent(vector_store)

# Initialize storage for persistent data
storage = Storage()

# Set page configuration
st.set_page_config(
    page_title="Document QA System",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling - more like Windsurf chat interface
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        max-width: 90%;
    }
    
    /* User message styling - right aligned */
    .chat-message.user {
        background-color: #2b6cb0;
        margin-left: auto;
        margin-right: 0;
        border-bottom-right-radius: 0;
    }
    
    /* Assistant message styling - left aligned */
    .chat-message.assistant {
        background-color: #374151;
        margin-right: auto;
        margin-left: 0;
        border-bottom-left-radius: 0;
    }
    
    /* Message content styling */
    .chat-message .message-content {
        color: white;
        margin-bottom: 0.5rem;
        white-space: pre-wrap;
    }
    
    /* Sources styling */
    .sources-container {
        margin-top: 0.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        padding-top: 0.5rem;
    }
    
    .source-header {
        font-weight: bold;
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 0.3rem;
    }
    
    .source-item {
        background-color: rgba(0, 0, 0, 0.2);
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        font-size: 0.75rem;
    }
    
    .source-text {
        color: rgba(255, 255, 255, 0.7);
        font-style: italic;
    }
    
    /* Input area styling */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background-color: #1e1e1e;
        border-top: 1px solid #333;
        z-index: 100;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #1e1e1e;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 4px;
        padding: 0.3rem 1rem;
        border: none;
        background-color: #2b6cb0;
        color: white;
    }
    
    /* Chat header */
    .chat-header {
        margin-bottom: 2rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #333;
    }
    
    /* Message container to ensure proper spacing */
    .messages-container {
        margin-bottom: 5rem; /* Space for input area */
        padding-bottom: 1rem;
    }
    
    /* Form styling */
    .stForm {
        background-color: transparent;
        border: none;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 20px;
        border: 1px solid #444;
        padding: 0.5rem 1rem;
        background-color: #2d3748;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history and uploaded documents
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
    # Load existing chat histories from storage
    existing_chats = storage.list_all_chats()
    for chat_info in existing_chats:
        chat_id = chat_info["id"]
        chat_history = storage.load_chat_history(chat_id)
        if chat_history:
            st.session_state.chat_histories[chat_id] = chat_history

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "uploaded_docs" not in st.session_state:
    # Load existing document info from storage
    st.session_state.uploaded_docs = storage.load_all_documents()

# Function to display chat message in a Windsurf-like style
def display_message(role, content, sources=None):
    if role == "user":
        st.markdown(f'<div class="chat-message user"><div class="message-content">{content}</div></div>', unsafe_allow_html=True)
    else:
        # Process content to ensure proper formatting
        # Replace newlines with <br> for proper HTML display
        formatted_content = content.replace('\n', '<br>')
        
        message_html = f'<div class="chat-message assistant"><div class="message-content">{formatted_content}</div>'
        
        # Add sources if available
        if sources and len(sources) > 0:
            message_html += '<div class="sources-container">'
            message_html += '<div class="source-header">Sources:</div>'
            
            for source in sources:
                source_type = source.get("source_type", "UNKNOWN")
                page = source.get("page", "N/A")
                sheet_name = source.get("sheet_name", "")
                relevance = source.get("relevance_score", 0)
                snippet = source.get("text_snippet", "")
                
                source_html = f'<div class="source-item">'
                source_html += f'<div class="source-header">{source_type}'
                
                if page != "N/A" and page is not None:
                    source_html += f' - Page {page}'
                
                if sheet_name and sheet_name != "unknown":
                    source_html += f' - Sheet "{sheet_name}"'
                
                source_html += f' (Relevance: {relevance:.2f})</div>'
                source_html += f'<div class="source-text">{snippet}</div>'
                source_html += '</div>'
                
                message_html += source_html
            
            message_html += '</div>'
        
        message_html += '</div>'
        st.markdown(message_html, unsafe_allow_html=True)

# Function to create a new chat
def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chat_histories[chat_id] = []
    st.session_state.current_chat_id = chat_id
    # Save empty chat to storage
    storage.save_chat_history(chat_id, [])
    return chat_id

# Function to handle file upload
def handle_upload(uploaded_file):
    if uploaded_file is not None:
        try:
            # Read file content
            content = uploaded_file.read()
            
            # Get file type from content type
            content_type = uploaded_file.type
            supported_types = {
                "application/pdf": "pdf",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
            }
            
            if content_type not in supported_types:
                st.error(f"Unsupported file type: {content_type}. Supported types: PDF, PPTX, XLSX, DOCX")
                return None
            
            file_type = supported_types[content_type]
            
            # Process document
            with st.spinner("Processing document..."):
                chunks = document_processor.process_document(content, file_type)
                
                # Generate unique namespace for this document
                namespace = str(uuid.uuid4())
                
                # Store in vector database
                vector_store.add_documents(chunks, namespace)
                
                # Save document info
                doc_info = {
                    "name": uploaded_file.name,
                    "namespace": namespace,
                    "status": "Processed"
                }
                
                # Add to uploaded docs
                st.session_state.uploaded_docs.append(doc_info)
                
                # Save document info to storage
                storage.save_document_info(doc_info)
                
                return namespace
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None

# Sidebar for document management
with st.sidebar:
    st.title("📚 Document QA System")
    
    # Document upload section
    st.subheader("Upload Documents")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "xlsx", "pptx"])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            namespace = handle_upload(uploaded_file)
            if namespace:
                st.success(f"Document processed successfully: {uploaded_file.name}")
    
    # Display uploaded documents
    if st.session_state.uploaded_docs:
        st.subheader("Uploaded Documents")
        for i, doc in enumerate(st.session_state.uploaded_docs):
            with st.expander(f"{i+1}. {doc['name']}"):
                st.write(f"**Status:** {doc.get('status', 'N/A')}")
                st.write(f"**Namespace:** {doc.get('namespace', 'N/A')}")
                
                # Add a delete button for each document
                if st.button(f"Delete {doc['name']}", key=f"delete_doc_{i}"):
                    # Delete from vector store
                    vector_store.delete_namespace(doc['namespace'])
                    # Remove from session state
                    st.session_state.uploaded_docs.remove(doc)
                    # Delete from storage
                    storage.delete_document_info(doc['namespace'])
                    st.rerun()
    
    # Chat management
    st.subheader("Chat Management")
    if st.button("New Chat"):
        create_new_chat()
        st.rerun()
    
    # Display existing chats
    if st.session_state.chat_histories:
        st.subheader("Your Chats")
        for chat_id, history in st.session_state.chat_histories.items():
            # Get the first user message or use a default name
            chat_name = "New Chat"
            for msg in history:
                if msg["role"] == "user":
                    chat_name = msg["content"][:20] + "..." if len(msg["content"]) > 20 else msg["content"]
                    break
            
            # Create a container for each chat with button and delete option
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                # Chat selection button
                with col1:
                    if st.button(chat_name, key=f"chat_{chat_id}"):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                
                # Delete button
                with col2:
                    if st.button("🗑️", key=f"delete_chat_{chat_id}"):
                        # Delete from storage
                        storage.delete_chat(chat_id)
                        
                        # Remove from session state
                        if chat_id in st.session_state.chat_histories:
                            del st.session_state.chat_histories[chat_id]
                        
                        # If we deleted the current chat, set current_chat_id to None
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            
                            # If there are other chats, select the first one
                            if st.session_state.chat_histories:
                                st.session_state.current_chat_id = next(iter(st.session_state.chat_histories.keys()))
                        
                        st.rerun()

# Main chat interface
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<div class='chat-header'><h2>Document Question Answering</h2></div>", unsafe_allow_html=True)

# Create a new chat if none exists
if not st.session_state.current_chat_id:
    create_new_chat()

# Display chat history
if st.session_state.current_chat_id:
    chat_history = st.session_state.chat_histories[st.session_state.current_chat_id]
    
    # Container for messages with proper spacing
    with st.container():
        st.markdown("<div class='messages-container'>", unsafe_allow_html=True)
        
        # Display all messages
        for message in chat_history:
            if message["role"] == "user":
                display_message("user", message["content"])
            else:
                display_message("assistant", message["content"], message.get("sources", []))
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create a form for the input with Windsurf-like styling
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)  # Space for fixed input
    
    # Fixed input area at bottom
    st.markdown("<div class='input-area'>", unsafe_allow_html=True)
    with st.form(key="question_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("", placeholder="Ask a question about your documents...", key="user_input_field")
        with col2:
            submit_button = st.form_submit_button("Send")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle form submission
    if submit_button and user_input:
        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_input})
        
        # Get response from agent
        with st.spinner("Thinking..."):
            # Prepare conversation history for the agent
            conversation_history = []
            for msg in chat_history:
                conversation_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get response with conversation history
            response = agent.process_message_with_history(user_input, conversation_history)
            
            # Add assistant message to chat history
            chat_history.append({
                "role": "assistant", 
                "content": response["answer"],
                "sources": response["sources"]
            })
            
            # Save updated chat history to storage
            storage.save_chat_history(st.session_state.current_chat_id, chat_history)
            
            # Force a rerun to update the UI
            st.rerun()
