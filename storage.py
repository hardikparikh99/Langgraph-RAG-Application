"""
Storage module for persisting chat histories and document information
"""

import json
import os
import time
from typing import Dict, List, Any, Optional

class Storage:
    def __init__(self, storage_dir: str = "data"):
        """Initialize storage with a directory path"""
        self.storage_dir = storage_dir
        self.chats_dir = os.path.join(storage_dir, "chats")
        self.docs_dir = os.path.join(storage_dir, "documents")
        
        # Create directories if they don't exist
        os.makedirs(self.chats_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
    
    def save_chat_history(self, chat_id: str, chat_history: List[Dict[str, Any]]) -> bool:
        """Save a chat history to disk"""
        try:
            # Create a serializable version of the chat history
            serializable_history = []
            for msg in chat_history:
                # Create a copy of the message to avoid modifying the original
                serialized_msg = msg.copy()
                
                # Handle sources specially (they might contain non-serializable objects)
                if "sources" in serialized_msg:
                    sources = serialized_msg["sources"]
                    serialized_sources = []
                    for source in sources:
                        serialized_source = {
                            "source_type": source.get("source_type", "UNKNOWN"),
                            "page": source.get("page", "N/A"),
                            "sheet_name": source.get("sheet_name", ""),
                            "relevance_score": float(source.get("relevance_score", 0)),
                            "text_snippet": source.get("text_snippet", "")
                        }
                        serialized_sources.append(serialized_source)
                    serialized_msg["sources"] = serialized_sources
                
                serializable_history.append(serialized_msg)
            
            # Write to file
            chat_file = os.path.join(self.chats_dir, f"{chat_id}.json")
            with open(chat_file, 'w') as f:
                json.dump(serializable_history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")
            return False
    
    def load_chat_history(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load a chat history from disk"""
        try:
            chat_file = os.path.join(self.chats_dir, f"{chat_id}.json")
            if not os.path.exists(chat_file):
                return None
            
            with open(chat_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")
            return None
    
    def list_all_chats(self) -> List[Dict[str, Any]]:
        """List all available chat histories"""
        chats = []
        try:
            for filename in os.listdir(self.chats_dir):
                if filename.endswith('.json'):
                    chat_id = filename[:-5]  # Remove .json extension
                    chat_file = os.path.join(self.chats_dir, filename)
                    
                    # Get file stats
                    stats = os.stat(chat_file)
                    modified_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                time.localtime(stats.st_mtime))
                    
                    # Get a preview of the chat (first user message)
                    preview = "New Chat"
                    try:
                        with open(chat_file, 'r') as f:
                            history = json.load(f)
                            for msg in history:
                                if msg.get("role") == "user":
                                    preview = msg.get("content", "")[:30]
                                    if len(msg.get("content", "")) > 30:
                                        preview += "..."
                                    break
                    except:
                        pass
                    
                    chats.append({
                        "id": chat_id,
                        "preview": preview,
                        "modified": modified_time
                    })
        except Exception as e:
            print(f"Error listing chats: {str(e)}")
        
        # Sort by modification time (newest first)
        chats.sort(key=lambda x: x["modified"], reverse=True)
        return chats
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat history"""
        try:
            chat_file = os.path.join(self.chats_dir, f"{chat_id}.json")
            if os.path.exists(chat_file):
                os.remove(chat_file)
                return True
            return False
        except Exception as e:
            print(f"Error deleting chat: {str(e)}")
            return False
    
    def save_document_info(self, doc_info: Dict[str, Any]) -> bool:
        """Save document information to disk"""
        try:
            namespace = doc_info.get("namespace")
            if not namespace:
                return False
            
            doc_file = os.path.join(self.docs_dir, f"{namespace}.json")
            with open(doc_file, 'w') as f:
                json.dump(doc_info, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving document info: {str(e)}")
            return False
    
    def load_all_documents(self) -> List[Dict[str, Any]]:
        """Load all document information"""
        docs = []
        try:
            for filename in os.listdir(self.docs_dir):
                if filename.endswith('.json'):
                    doc_file = os.path.join(self.docs_dir, filename)
                    with open(doc_file, 'r') as f:
                        doc_info = json.load(f)
                        docs.append(doc_info)
        except Exception as e:
            print(f"Error loading documents: {str(e)}")
        return docs
    
    def delete_document_info(self, namespace: str) -> bool:
        """Delete document information"""
        try:
            doc_file = os.path.join(self.docs_dir, f"{namespace}.json")
            if os.path.exists(doc_file):
                os.remove(doc_file)
                return True
            return False
        except Exception as e:
            print(f"Error deleting document info: {str(e)}")
            return False
