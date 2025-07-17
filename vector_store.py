from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_ollama import OllamaEmbeddings
from config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL
)

class VectorStore:
    def __init__(self):
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set in environment variables")
            
        # Initialize Pinecone with environment
        self.pc = Pinecone(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT
        )
        
        # Create index if it doesn't exist
        if PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=2048,  # Dimension for Llama 3.2-1b embeddings
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        
        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        self.embeddings = OllamaEmbeddings(
            model="llama3.2:1b",
            base_url="http://localhost:11434"  # Default Ollama URL
        )

    # def add_documents(self, documents: List[Dict[str, Any]], namespace: str = "documents"):
    #     try:
    #         texts = [doc["text"] for doc in documents]
    #         metadatas = [doc["metadata"] for doc in documents]
            
    #         # Generate embeddings
    #         embeddings = self.embeddings.embed_documents(texts)
            
    #         # Prepare vectors for Pinecone
    #         vectors = [
    #             (f"{namespace}_{i}", embedding, metadata)
    #             for i, (embedding, metadata) in enumerate(zip(embeddings, metadatas))
    #         ]
            
    #         # Upsert to Pinecone
    #         self.index.upsert(vectors=vectors, namespace=namespace)
            
    #     except Exception as e:
    #         raise

    def add_documents(self, documents: List[Dict[str, Any]], namespace: str = "documents"):
        try:
            texts = [doc["text"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            # Generate embeddings
            embeddings = self.embeddings.embed_documents(texts)
            
            # Prepare vectors for Pinecone
            vectors = [
                # Include text in metadata for retrieval
                (f"{namespace}_{i}", embedding, {**metadata, "text": text})
                for i, (embedding, metadata, text) in enumerate(zip(embeddings, metadatas, texts))
            ]
            
            # Upsert to Pinecone
            self.index.upsert(vectors=vectors, namespace=namespace)
            
        except Exception as e:
            print(f"Add documents error: {str(e)}")  # Add logging
            raise


    # def search(self, query: str, namespace: str = "documents", top_k: int = 5) -> List[Dict[str, Any]]:
    #     try:
    #         # Generate query embedding
    #         query_embedding = self.embeddings.embed_query(query)
            
    #         # Search in Pinecone
    #         results = self.index.query(
    #             vector=query_embedding,
    #             namespace=namespace,
    #             top_k=top_k,
    #             include_metadata=True
    #         )
            
    #         if not results.matches:
    #             return []
            
    #         return [
    #             {
    #                 "text": match.metadata.get("text", ""),
    #                 "metadata": match.metadata,
    #                 "score": match.score
    #             }
    #             for match in results.matches
    #         ]
    #     except Exception as e:
    #         return []

    def search(self, query: str, namespace: str = "documents", top_k: int = 5, hybrid_alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching.
        
        Args:
            query: The search query
            namespace: The namespace to search in
            top_k: Number of results to return
            hybrid_alpha: Weight between semantic (0) and keyword (1) search
        
        Returns:
            List of matching documents with scores
        """
        try:
            # 1. Semantic search component
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Pinecone
            semantic_results = self.index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=top_k * 2,  # Get more results for hybrid reranking
                include_metadata=True
            )
            
            if not semantic_results.matches:
                return []
            
            # 2. Keyword search component
            # Extract query keywords (simple tokenization)
            keywords = set([word.lower() for word in query.split() if len(word) > 3])
            
            # Process semantic results and add keyword match score
            hybrid_results = []
            for match in semantic_results.matches:
                text = match.metadata.get("text", "")
                
                # Calculate keyword match score
                keyword_score = 0.0
                if text and keywords:
                    # Count keyword matches
                    text_lower = text.lower()
                    matched_keywords = sum(1 for keyword in keywords if keyword in text_lower)
                    keyword_score = matched_keywords / len(keywords) if matched_keywords > 0 else 0.0
                
                # Normalize semantic score (usually between -1 and 1 for cosine)
                semantic_score = match.score
                
                # Combine scores using weighted average
                hybrid_score = (1 - hybrid_alpha) * semantic_score + hybrid_alpha * keyword_score
                
                hybrid_results.append({
                    "text": text,
                    "metadata": match.metadata,
                    "score": hybrid_score,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                })
            
            # Sort by hybrid score and return top_k results
            hybrid_results.sort(key=lambda x: x["score"], reverse=True)
            return hybrid_results[:top_k]
            
        except Exception as e:
            print(f"Hybrid search error: {str(e)}")  # Add logging
            return []

    def delete_namespace(self, namespace: str):
        try:
            self.index.delete(delete_all=True, namespace=namespace)
        except Exception as e:
            raise

    # def list_all_documents(self) -> List[Dict[str, Any]]:
    #     try:
    #         # Get index statistics
    #         stats = self.index.describe_index_stats()
            
    #         if not stats.namespaces:
    #             return []
            
    #         documents = []
    #         # Iterate through each namespace
    #         for namespace in stats.namespaces:
    #             try:
    #                 # Query with a random vector to get metadata
    #                 zero_vector = [0.0] * 2048  # 2048 is our embedding dimension
    #                 results = self.index.query(
    #                     vector=zero_vector,
    #                     namespace=namespace,
    #                     top_k=1,
    #                     include_metadata=True
    #                 )
                    
    #                 if results.matches:
    #                     match = results.matches[0]
    #                     if match.metadata:
    #                         doc_info = {
    #                             "namespace": namespace,
    #                             "source": match.metadata.get("source", "Unknown"),
    #                             "page": match.metadata.get("page", "N/A")
    #                         }
                            
    #                         # Add sheet name for Excel files
    #                         if match.metadata.get("source") == "xlsx":
    #                             doc_info["sheet_name"] = match.metadata.get("sheet_name")
                            
    #                         documents.append(doc_info)
    #             except Exception:
    #                 continue
            
    #         return documents
    #     except Exception:
    #         return [] 
    def list_all_documents(self) -> List[Dict[str, Any]]:
        try:
            # Get index statistics
            stats = self.index.describe_index_stats()
            
            if not stats.namespaces:
                print("No namespaces found in index")
                return []
            
            print(f"Found namespaces: {list(stats.namespaces.keys())}")
            documents = []
            # Iterate through each namespace
            for namespace in stats.namespaces:
                try:
                    print(f"Processing namespace: {namespace}")
                    # Query with a random vector to get metadata
                    zero_vector = [0.0] * 2048  # 2048 is our embedding dimension
                    results = self.index.query(
                        vector=zero_vector,
                        namespace=namespace,
                        top_k=1,
                        include_metadata=True
                    )
                    
                    if results.matches:
                        match = results.matches[0]
                        if match.metadata:
                            doc_info = {
                                "namespace": namespace,
                                "source": match.metadata.get("source", "Unknown"),
                                "page": match.metadata.get("page", "N/A")
                            }
                            
                            # Add sheet name for Excel files
                            if match.metadata.get("source") == "xlsx":
                                doc_info["sheet_name"] = match.metadata.get("sheet_name")
                            
                            documents.append(doc_info)
                            print(f"Added document info: {doc_info}")
                    else:
                        print(f"No matches found in namespace {namespace}")
                except Exception as e:
                    print(f"Error processing namespace {namespace}: {str(e)}")
                    continue
            
            return documents
        except Exception as e:
            print(f"Error in list_all_documents: {str(e)}")
            return []