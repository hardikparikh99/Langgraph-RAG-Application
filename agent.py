from typing import Dict, Any, List, Tuple, TypedDict
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq
from config import LLM_MODEL, SYSTEM_PROMPT, AGENT_SETTINGS
import os

class AgentStateDict(TypedDict):
    messages: List[Dict[str, str]]
    context: List[Dict[str, Any]]
    current_response: str
    is_general_conversation: bool
    sources: List[Dict[str, Any]]

class DocumentQAAgent:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.llm = ChatGroq(
            model_name=LLM_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=AGENT_SETTINGS["temperature"],
            max_tokens=AGENT_SETTINGS["max_tokens"]
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        # Define the nodes
        def analyze_query(state: AgentStateDict) -> AgentStateDict:
            if not state["messages"]:
                return state
            
            last_message = state["messages"][-1]["content"].lower()
            # Check if it's a general conversation
            general_phrases = ["hi", "hello", "hey", "how are you", "good morning", "good afternoon", "good evening"]
            state["is_general_conversation"] = any(phrase in last_message for phrase in general_phrases)
            return state

        # def retrieve_context(state: AgentStateDict) -> AgentStateDict:
        #     if not state["messages"] or state["is_general_conversation"]:
        #         return state
            
        #     last_message = state["messages"][-1]["content"]
            
        #     # Search across all namespaces
        #     all_context = []
        #     namespaces = self.vector_store.list_all_documents()
            
        #     for doc in namespaces:
        #         namespace = doc["namespace"]
        #         # Increase top_k to get more relevant chunks
        #         results = self.vector_store.search(
        #             query=last_message,
        #             namespace=namespace,
        #             top_k=5  # Increased from 3 to 5
        #         )
        #         if results:
        #             # Sort by score to get most relevant chunks
        #             sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
        #             all_context.extend(sorted_results)
            
        #     # Take top 5 most relevant chunks across all documents
        #     state["context"] = all_context[:5]
        #     return state

        def retrieve_context(state: AgentStateDict) -> AgentStateDict:
            if not state["messages"] or state["is_general_conversation"]:
                return state
            
            last_message = state["messages"][-1]["content"]
            
            # Silently retrieve context for message
            
            # Search across all namespaces
            all_context = []
            try:
                namespaces = self.vector_store.list_all_documents()
                # Process namespaces silently
                
                if not namespaces:
                    print("Warning: No documents found in vector store")
                    state["context"] = []
                    return state
                
                # Create multiple query variations to improve retrieval
                query_variations = [
                    last_message,  # Original query
                    f"information about {last_message}",  # More general version
                    f"details regarding {last_message}",  # Alternative phrasing
                ]
                
                for doc in namespaces:
                    namespace = doc.get("namespace")
                    if not namespace:
                        continue
                        
                    # Process namespace silently
                    
                    # Try each query variation with hybrid search
                    for query in query_variations:
                        try:
                            # Use hybrid search with different alpha values to balance semantic vs keyword
                            # Try multiple hybrid configurations for better coverage
                            hybrid_configs = [
                                {"alpha": 0.3, "name": "semantic-leaning"},  # More weight on semantic
                                {"alpha": 0.5, "name": "balanced"},          # Equal weight
                                {"alpha": 0.7, "name": "keyword-leaning"}    # More weight on keywords
                            ]
                            
                            for config in hybrid_configs:
                                results = self.vector_store.search(
                                    query=query,
                                    namespace=namespace,
                                    top_k=6,  # Slightly reduced since we're doing multiple searches
                                    hybrid_alpha=config["alpha"]
                                )
                                
                                if results:
                                    # Process results silently
                                    # Add all results with their scores
                                    all_context.extend(results)
                        except Exception as e:
                            # Silently handle search errors
                            pass
                
                # Remove duplicates (same text content) while keeping highest scores
                unique_texts = {}
                for item in all_context:
                    text = item.get('text', '')
                    score = item.get('score', 0)
                    
                    if text not in unique_texts or score > unique_texts[text].get('score', 0):
                        unique_texts[text] = item
                
                # Sort by score and take top results
                all_context = sorted(unique_texts.values(), key=lambda x: x.get('score', 0), reverse=True)[:10]  # Increased from 5 to 10
                # Silently process final context
                
                # Add a lower threshold for inclusion - even somewhat related content should be included
                filtered_context = []
                for item in all_context:
                    score = item.get('score', 0)
                    # Use a lower threshold (0.2) to include more potentially relevant content
                    if score > 0.2:  
                        filtered_context.append(item)
                
                state["context"] = filtered_context if filtered_context else all_context[:3]  # Always include at least some context
            except Exception as e:
                # Silently handle retrieval errors
                state["context"] = []
            
            return state

        # def generate_response(state: AgentStateDict) -> AgentStateDict:
        #     if not state["messages"]:
        #         return state
            
        #     last_message = state["messages"][-1]["content"]
            
        #     if state["is_general_conversation"]:
        #         # Handle general conversation without context
        #         prompt = "You are a friendly AI assistant. Respond naturally to this greeting: " + last_message
        #     else:
        #         # Format context with source information
        #         if not state["context"]:
        #             state["current_response"] = "I don't have information about that in the uploaded documents."
        #             return state

        #         context_text = "\n\n".join([
        #             f"Content: {doc['text']}"
        #             for doc in state["context"]
        #         ])
                
        #         prompt = f"""You are a document QA assistant. Your task is to answer questions based on the provided document content.
        #         If the answer is in the content, provide it directly. If not, simply state that the information is not available.
        #         Do not apologize or make suggestions about uploading documents.
                
        #         Document Content:
        #         {context_text}
                
        #         Question: {last_message}
                
        def generate_response(state: AgentStateDict) -> AgentStateDict:
            if not state["messages"]:
                return state
            
            last_message = state["messages"][-1]["content"]
            
            if state["is_general_conversation"]:
                # Handle general conversation without context
                prompt = "You are a friendly AI assistant. Respond naturally to this greeting: " + last_message
                # No sources for general conversation
                state["sources"] = []
            else:
                # Format context with source information
                if not state["context"]:
                    state["current_response"] = "I don't have specific information about that in the uploaded documents. Please try rephrasing your question or upload relevant documents."
                    state["sources"] = []
                    return state

                # Improved context formatting with debug info
                context_text = ""
                # Prepare sources list for the response
                sources_list = []
                
                for i, doc in enumerate(state["context"]):
                    # Extract document metadata for better citations
                    metadata = doc.get("metadata", {})
                    source_type = metadata.get("source", "unknown")
                    page_num = metadata.get("page", "N/A")
                    sheet_name = metadata.get("sheet_name", "") if source_type == "xlsx" else ""
                    score = doc.get("score", 0)
                    
                    # Format source citation
                    source_info = f"[{source_type.upper()}"
                    if page_num != "N/A":
                        source_info += f", Page {page_num}"
                    if sheet_name:
                        source_info += f", Sheet '{sheet_name}'"
                    source_info += f", Relevance: {score:.2f}]"
                    
                    # Add to sources list for the response
                    sources_list.append({
                        "source_type": source_type.upper(),
                        "page": str(page_num) if page_num != "N/A" else None,
                        "sheet_name": sheet_name if sheet_name else None,
                        "relevance_score": float(f"{score:.2f}"),
                        "text_snippet": doc['text'][:150] + "..." if len(doc['text']) > 150 else doc['text']
                    })
                    
                    # Format context entry with metadata including hybrid search scores
                    semantic_score = doc.get('semantic_score', 0)
                    keyword_score = doc.get('keyword_score', 0)
                    score_info = f", Semantic: {semantic_score:.2f}, Keyword: {keyword_score:.2f}"
                    context_text += f"Context {i+1} {source_info}{score_info}:\n{doc['text']}\n\n"
                
                # Sort sources by relevance score and take top 3 only
                sources_list = sorted(sources_list, key=lambda x: x["relevance_score"], reverse=True)
                # Take exactly 3 sources if available, or fewer if not enough
                state["sources"] = sources_list[:min(3, len(sources_list))]
                
                # Get conversation history for context
                conversation_context = ""
                if len(state["messages"]) > 1:
                    # Format previous messages for context
                    conversation_context = "Previous conversation:\n"
                    # Include up to 5 previous messages for context
                    prev_messages = state["messages"][:-1][-5:]
                    for msg in prev_messages:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        conversation_context += f"{role}: {msg['content']}\n"
                    conversation_context += "\n"
                
                prompt = f"""You are a strictly context-bound document assistant with conversation memory. Your task is to answer the user's question based ONLY on the provided document content while maintaining context from the conversation history.
                
                IMPORTANT INSTRUCTIONS:
                1. If a user sends a simple greeting (like "hello", "hi", "hey", etc.) without a specific question, respond with a friendly greeting and introduce yourself as a document assistant.
                
                2. If the user asks about documents, ONLY answer based on the provided document context. If the context does not contain sufficient information to answer the question, respond that you cannot answer based on the given documents.
                
                3. DO NOT include any citations, source references, or context details in your answer. Just provide a clean, direct answer.
                
                4. DO NOT mention which document, page number, or source the information came from in your answer.
                
                5. DO NOT say phrases like "According to the document", "As mentioned in the text", "Based on the provided context", etc.
                
                6. MAINTAIN CONVERSATION CONTEXT: When the user refers to previous questions or uses pronouns like "it", "that", "they", etc., use the conversation history to understand what they're referring to.
                
                7. If the user asks a follow-up question, connect it to previous questions and answers in the conversation history.
                
                8. If ANY of the provided document content contains information RELATED to the question, use it to formulate an answer.
                
                9. Only state that information is not available if NONE of the provided content is even remotely related to the question.
                
                10. Keep your answer concise and to the point, focusing only on answering the question directly.
                
                11. DO NOT apologize for or explain your limitations in the answer.
                
                12. DO NOT mention relevance scores or any metadata about the sources.
                
                Always maintain a professional, helpful tone and DO NOT generate information not present in the provided context.
                
                {conversation_context}
                Document Content:
                {context_text}
                
                Current Question: {last_message}
                
                Answer:"""
                
            
            try:
                # Use higher temperature for more creative responses when information is partial
                response = self.llm.invoke(prompt, temperature=0.7)
                state["current_response"] = response.content
                
                # If the response indicates no information is available but we have context,
                # try again with an even more explicit instruction
                if "not available" in state["current_response"].lower() and state["context"]:
                    # Get conversation history for context
                    conversation_context = ""
                    if len(state["messages"]) > 1:
                        # Format previous messages for context
                        conversation_context = "Previous conversation:\n"
                        # Include up to 5 previous messages for context
                        prev_messages = state["messages"][:-1][-5:]
                        for msg in prev_messages:
                            role = "User" if msg["role"] == "user" else "Assistant"
                            conversation_context += f"{role}: {msg['content']}\n"
                        conversation_context += "\n"
                    
                    retry_prompt = f"""You are a document QA assistant with conversation memory. The user has asked: "{last_message}"
                    
                    {conversation_context}
                    
                    I have found some potentially related information in the documents. Even if it doesn't directly answer the question,
                    please extract ANY relevant details from this content that might help address the query:
                    
                    {context_text}
                    
                    IMPORTANT RULES:
                    1. DO NOT include any citations, source references, or context details in your answer.
                    2. DO NOT mention which document, page number, or source the information came from.
                    3. DO NOT say phrases like "According to the document", "As mentioned in the text", etc.
                    4. Keep your answer concise and to the point, focusing only on answering the question directly.
                    5. DO NOT mention relevance scores or any metadata about the sources.
                    6. MAINTAIN CONVERSATION CONTEXT: When the user refers to previous questions or uses pronouns like "it", "that", "they", etc., use the conversation history to understand what they're referring to.
                    7. If the user asks a follow-up question, connect it to previous questions and answers in the conversation history.
                    
                    Provide the most helpful response possible using this information, even if it only partially addresses the question.
                    If you can make reasonable inferences based on the available information, please do so.
                    Only say information is not available as an absolute last resort.
                    """
                    
                    retry_response = self.llm.invoke(retry_prompt, temperature=0.8)
                    state["current_response"] = retry_response.content
            except Exception as e:
                state["current_response"] = f"Error generating response: {str(e)}"
            
            return state
            
        # Build the graph
        workflow = StateGraph(AgentStateDict)
        
        # Add nodes
        workflow.add_node("analyze_query", analyze_query)
        workflow.add_node("retrieve_context", retrieve_context)
        workflow.add_node("generate_response", generate_response)
        
        # Add edges
        workflow.add_edge("analyze_query", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.set_entry_point("analyze_query")
        
        # Compile the graph
        return workflow.compile()

    def process_message(self, message: str) -> dict:
        # Initialize state as a dictionary
        state: AgentStateDict = {
            "messages": [{"role": "user", "content": message}],
            "context": [],
            "current_response": "",
            "is_general_conversation": False,
            "sources": []
        }
        
        # Run the graph
        final_state = self.graph.invoke(state)
        
        # Debug: Print source information
        print("\n===== SOURCE INFORMATION =====")
        print(f"Total sources: {len(final_state['sources'])}")
        for i, source in enumerate(final_state['sources']):
            print(f"Source {i+1}:")
            print(f"  Type: {source.get('source_type', 'Unknown')}")
            print(f"  Page: {source.get('page', 'N/A')}")
            print(f"  Sheet: {source.get('sheet_name', 'N/A')}")
            print(f"  Score: {source.get('relevance_score', 0)}")
            print(f"  Snippet: {source.get('text_snippet', '')[:50]}...")
        print("==============================\n")
        
        # Ensure we have Excel sources if they exist in the context
        excel_sources = []
        for ctx in final_state['context']:
            metadata = ctx.get('metadata', {})
            if metadata.get('source') == 'xlsx':
                # Create a dedicated Excel source
                excel_sources.append({
                    "source_type": "XLSX",
                    "page": str(metadata.get('page', 'N/A')),
                    "sheet_name": metadata.get('sheet_name', 'unknown'),
                    "relevance_score": ctx.get('score', 0.0),
                    "text_snippet": ctx.get('text', '')[:150] + '...' if len(ctx.get('text', '')) > 150 else ctx.get('text', '')
                })
        
        # If we found Excel sources but they're not in the final sources, add them
        if excel_sources and not any(s.get('source_type') == 'XLSX' for s in final_state['sources']):
            # Replace or append Excel sources
            if len(final_state['sources']) >= 3:
                # Replace the lowest scoring source
                final_state['sources'] = sorted(final_state['sources'], key=lambda x: x.get('relevance_score', 0), reverse=True)
                final_state['sources'][-1] = excel_sources[0]  # Replace lowest with top Excel source
            else:
                # Just append the Excel source
                final_state['sources'].append(excel_sources[0])
        
        # Return both the response and sources
        return {
            "answer": final_state["current_response"],
            "sources": final_state["sources"]
        }
        
    def process_message_with_history(self, message: str, conversation_history: List[Dict[str, str]]) -> dict:
        """
        Process a message with conversation history to maintain context across messages.
        
        Args:
            message: The current user message
            conversation_history: List of previous messages with roles and content
            
        Returns:
            Dictionary with answer and sources
        """
        # Initialize state as a dictionary
        state: AgentStateDict = {
            "messages": conversation_history + [{"role": "user", "content": message}],
            "context": [],
            "current_response": "",
            "is_general_conversation": False,
            "sources": []
        }
        
        # Run the graph
        final_state = self.graph.invoke(state)
        
        # Debug: Print source information
        print("\n===== SOURCE INFORMATION =====")
        print(f"Total sources: {len(final_state['sources'])}")
        for i, source in enumerate(final_state['sources']):
            print(f"Source {i+1}:")
            print(f"  Type: {source.get('source_type', 'Unknown')}")
            print(f"  Page: {source.get('page', 'N/A')}")
            print(f"  Sheet: {source.get('sheet_name', 'N/A')}")
            print(f"  Score: {source.get('relevance_score', 0)}")
            print(f"  Snippet: {source.get('text_snippet', '')[:50]}...")
        print("==============================\n")
        
        # Ensure we have Excel sources if they exist in the context
        excel_sources = []
        for ctx in final_state['context']:
            metadata = ctx.get('metadata', {})
            if metadata.get('source') == 'xlsx':
                # Create a dedicated Excel source
                excel_sources.append({
                    "source_type": "XLSX",
                    "page": str(metadata.get('page', 'N/A')),
                    "sheet_name": metadata.get('sheet_name', 'unknown'),
                    "relevance_score": ctx.get('score', 0.0),
                    "text_snippet": ctx.get('text', '')[:150] + '...' if len(ctx.get('text', '')) > 150 else ctx.get('text', '')
                })
        
        # If we found Excel sources but they're not in the final sources, add them
        if excel_sources and not any(s.get('source_type') == 'XLSX' for s in final_state['sources']):
            # Replace or append Excel sources
            if len(final_state['sources']) >= 3:
                # Replace the lowest scoring source
                final_state['sources'] = sorted(final_state['sources'], key=lambda x: x.get('relevance_score', 0), reverse=True)
                final_state['sources'][-1] = excel_sources[0]  # Replace lowest with top Excel source
            else:
                # Just append the Excel source
                final_state['sources'].append(excel_sources[0])
        
        # Return both the response and sources
        return {
            "answer": final_state["current_response"],
            "sources": final_state["sources"]
        } 