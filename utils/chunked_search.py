"""
Semantic search on chunked embeddings
Search across chunks and aggregate results intelligently
"""
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

class ChunkedVectorSearch:
    """Search functionality for chunked embeddings"""
    
    # Initialize (lazy loaded)
    _client = None
    _embedder = None
    
    VECTOR_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    @classmethod
    def _initialize(cls):
        """Initialize ChromaDB and embedder if not already done"""
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path=cls.VECTOR_DB_PATH)
            cls._embedder = SentenceTransformer(cls.EMBEDDING_MODEL)
    
    
    @staticmethod
    def search_resource_chunks(
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search resource chunks
        
        Args:
            query: Search query (natural language)
            top_k: Number of results to return
            filters: Optional metadata filters (not yet implemented)
            
        Returns:
            List of chunk results with similarity scores
        """
        ChunkedVectorSearch._initialize()
        
        collection = ChunkedVectorSearch._client.get_collection("resources_chunks")
        query_embedding = ChunkedVectorSearch._embedder.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                "chunk_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "type": "resource_chunk"
            })
        
        return formatted_results
    
    
    @staticmethod
    def search_project_chunks(
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search project chunks"""
        ChunkedVectorSearch._initialize()
        
        collection = ChunkedVectorSearch._client.get_collection("projects_chunks")
        query_embedding = ChunkedVectorSearch._embedder.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "similarity_score": 1 - results['distances'][0][i],
                "chunk_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "type": "project_chunk"
            })
        
        return formatted_results
    
    
    @staticmethod
    def search_assignment_chunks(
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search assignment chunks"""
        ChunkedVectorSearch._initialize()
        
        collection = ChunkedVectorSearch._client.get_collection("assignments_chunks")
        query_embedding = ChunkedVectorSearch._embedder.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "similarity_score": 1 - results['distances'][0][i],
                "chunk_text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "type": "assignment_chunk"
            })
        
        return formatted_results
    
    
    @staticmethod
    def search_all_chunks(
        query: str,
        top_k: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all chunk collections
        
        Args:
            query: Search query
            top_k: Results per collection
            
        Returns:
            Dict with results grouped by type
        """
        resources = ChunkedVectorSearch.search_resource_chunks(query, top_k=top_k)
        projects = ChunkedVectorSearch.search_project_chunks(query, top_k=top_k)
        assignments = ChunkedVectorSearch.search_assignment_chunks(query, top_k=top_k)
        
        return {
            "resources": resources,
            "projects": projects,
            "assignments": assignments,
            "total_results": len(resources) + len(projects) + len(assignments)
        }
    
    
    @staticmethod
    def aggregate_chunk_results(
        chunks: List[Dict[str, Any]],
        group_by: str = "document_id",
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Aggregate chunks by source document
        Useful for getting back to original documents instead of chunks
        
        Args:
            chunks: List of chunk results
            group_by: Field to group by ('resource_id', 'project_id', etc.)
            top_k: Top chunks per document
            
        Returns:
            Aggregated results by document
        """
        grouped = {}
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            
            # Extract document ID based on type
            if chunk['type'] == 'resource_chunk':
                doc_id = metadata.get('name', 'unknown')
                doc_type = 'resource'
            elif chunk['type'] == 'project_chunk':
                doc_id = metadata.get('name', 'unknown')
                doc_type = 'project'
            elif chunk['type'] == 'assignment_chunk':
                doc_id = f"{metadata.get('resource_id', 'unknown')} → {metadata.get('project_id', 'unknown')}"
                doc_type = 'assignment'
            else:
                continue
            
            key = f"{doc_type}:{doc_id}"
            
            if key not in grouped:
                grouped[key] = {
                    "document_id": doc_id,
                    "document_type": doc_type,
                    "chunks": [],
                    "metadata": metadata,
                    "max_similarity": 0
                }
            
            grouped[key]["chunks"].append(chunk)
            grouped[key]["max_similarity"] = max(
                grouped[key]["max_similarity"],
                chunk.get('similarity_score', 0)
            )
        
        # Sort by best chunk similarity and limit chunks per document
        results = []
        for doc_result in grouped.values():
            doc_result["chunks"] = sorted(
                doc_result["chunks"],
                key=lambda x: x.get('similarity_score', 0),
                reverse=True
            )[:top_k]
            results.append(doc_result)
        
        return sorted(results, key=lambda x: x['max_similarity'], reverse=True)
    
    
    @staticmethod
    def search_with_context(
        query: str,
        context_size: int = 2,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search and return chunks with context from adjacent chunks
        
        Args:
            query: Search query
            context_size: Number of adjacent chunks to include
            top_k: Top results
            
        Returns:
            Results with context
        """
        results = ChunkedVectorSearch.search_all_chunks(query, top_k=top_k)
        
        contextualized = []
        
        for result_type in ['resources', 'projects', 'assignments']:
            for chunk in results[result_type][:top_k]:
                chunk_data = {
                    "chunk_id": chunk["chunk_id"],
                    "similarity_score": chunk["similarity_score"],
                    "context": {
                        "main_chunk": chunk["chunk_text"],
                        "metadata": chunk["metadata"]
                    },
                    "type": result_type[:-1]  # Remove 's'
                }
                contextualized.append(chunk_data)
        
        return contextualized
    
    
    @staticmethod
    def get_chunking_statistics() -> Dict[str, Any]:
        """Get statistics about chunked embeddings"""
        ChunkedVectorSearch._initialize()
        
        stats = {
            "collections": {}
        }
        
        for collection_name in ["resources_chunks", "projects_chunks", "assignments_chunks"]:
            try:
                collection = ChunkedVectorSearch._client.get_collection(collection_name)
                count = collection.count()
                stats["collections"][collection_name] = {
                    "chunk_count": count,
                    "embedding_dimension": 384  # all-MiniLM-L6-v2 dimension
                }
            except Exception as e:
                stats["collections"][collection_name] = {"error": str(e)}
        
        total_chunks = sum(
            c.get('chunk_count', 0)
            for c in stats["collections"].values()
        )
        
        stats["total_chunks"] = total_chunks
        stats["total_storage_mb"] = (total_chunks * 384 * 4) / 1024 / 1024
        
        return stats


# Example usage
if __name__ == "__main__":
    print("Testing Chunked Vector Search")
    print("=" * 60)
    
    # Test 1: Search with chunks
    print("\n🔍 Test 1: Search Resources with Chunks")
    results = ChunkedVectorSearch.search_resource_chunks(
        "Python developer with AWS experience",
        top_k=3
    )
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. Similarity: {result['similarity_score']:.4f}")
        print(f"     Chunk: {result['chunk_text'][:80]}...")
        print(f"     Skills: {result['metadata'].get('skills', 'N/A')}")
    
    # Test 2: Search all collections
    print("\n\n🔍 Test 2: Search All Collections")
    all_results = ChunkedVectorSearch.search_all_chunks(
        "E-commerce platform development",
        top_k=2
    )
    print(f"Resources: {len(all_results['resources'])} results")
    print(f"Projects: {len(all_results['projects'])} results")
    print(f"Assignments: {len(all_results['assignments'])} results")
    
    # Test 3: Statistics
    print("\n\n📊 Test 3: Chunking Statistics")
    stats = ChunkedVectorSearch.get_chunking_statistics()
    for collection, details in stats["collections"].items():
        if "chunk_count" in details:
            print(f"  {collection}: {details['chunk_count']} chunks")
    print(f"  Total: {stats['total_chunks']} chunks")
    print(f"  Storage: ~{stats['total_storage_mb']:.2f} MB")
