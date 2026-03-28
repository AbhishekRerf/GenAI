from utils.db import get_chroma_collection, get_embedding_model
import chromadb
from utils.llm import generate_answer
from typing import List, Dict
import os

async def retrieve_relevant_documents(query: str, top_k: int = 3) -> List[Dict]:
    """
    Retrieve relevant documents from all Chroma collections using semantic search
    
    Args:
        query: Search query
        top_k: Number of top documents to retrieve per collection
    
    Returns:
        List of relevant documents with similarity scores
    """
    embedding_model = get_embedding_model()
    
    # Generate embedding for the query
    query_embedding = embedding_model.encode(query).tolist()
    
    # Get ChromaDB client
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Search all collections (prioritize resources first)
    all_documents = []
    collection_names = ["resources_vectors", "projects_vectors", "assignments_vectors"]
    
    for collection_name in collection_names:
        try:
            collection = client.get_collection(name=collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k  # Get top_k from each, then merge
            )
            
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 / (1 + distance)
                    
                    all_documents.append({
                        "content": doc,
                        "similarity": round(similarity, 3),
                        "source": collection_name,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })
        except Exception as e:
            print(f"Warning: Could not search {collection_name}: {str(e)}")
    
    # Sort by similarity and return top_k
    all_documents.sort(key=lambda x: x['similarity'], reverse=True)
    return all_documents[:top_k]

async def rag_query(user_query: str, top_k: int = 3) -> Dict:
    """
    Full RAG pipeline: retrieve documents and generate answer
    
    Args:
        user_query: User's question
        top_k: Number of documents to retrieve
    
    Returns:
        Dictionary with answer and sources
    """
    # Retrieve relevant documents
    relevant_docs = await retrieve_relevant_documents(user_query, top_k)
    
    # Prepare context from retrieved documents
    context = "\n\n".join([doc['content'] for doc in relevant_docs])
    
    if not context.strip():
        context = "No relevant documents found in the knowledge base."
    
    # Generate answer using LLM
    answer = generate_answer(user_query, context)
    
    return {
        "answer": answer,
        "sources": relevant_docs
    }

def add_to_vector_store(document_id: str, title: str, content: str, metadata: dict = None):
    """
    Add document to Chroma vector store
    
    Args:
        document_id: Unique document ID
        title: Document title
        content: Document content
        metadata: Additional metadata
    """
    collection = get_chroma_collection()
    embedding_model = get_embedding_model()
    
    # Generate embedding
    embedding = embedding_model.encode(content).tolist()
    
    # Prepare metadata
    meta = metadata or {}
    meta['title'] = title
    
    # Add to collection
    collection.add(
        ids=[document_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[meta]
    )

def remove_from_vector_store(document_id: str):
    """Remove document from Chroma"""
    collection = get_chroma_collection()
    collection.delete(ids=[document_id])

def search_vector_store(query: str, top_k: int = 5) -> List[Dict]:
    """Simple keyword search in vector store"""
    return retrieve_relevant_documents(query, top_k)
