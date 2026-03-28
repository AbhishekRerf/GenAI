"""
Vector Database Search & Retrieval Utility
Query the vector DB and retrieve similar resources, projects, or assignments
"""
import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

load_dotenv()

# Configuration
VECTOR_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Initialize models
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Initialize ChromaDB (new API)
client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

# Collection names
RESOURCE_COLLECTION = "resources_vectors"
PROJECT_COLLECTION = "projects_vectors"
ASSIGNMENT_COLLECTION = "assignments_vectors"


class VectorSearch:
    """Vector similarity search operations"""
    
    @staticmethod
    def embed_text(text: str) -> List[float]:
        """Convert text to embedding vector"""
        return embedding_model.encode(text).tolist()
    
    @staticmethod
    def search_resources(query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Search for resources by natural language query
        
        Args:
            query: Search query (e.g., "Python developer with AWS experience")
            top_k: Number of results to return
            filters: Optional filters (e.g., {"department": "Engineering"})
        
        Returns:
            List of resources with similarity scores
        """
        try:
            collection = client.get_collection(name=RESOURCE_COLLECTION)
            
            # Generate query embedding
            query_embedding = VectorSearch.embed_text(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    # Convert distance to similarity (0-1, where 1 is exact match)
                    similarity = 1 - distance
                    
                    formatted_results.append({
                        "resource_id": metadata.get("resource_id"),
                        "name": metadata.get("name"),
                        "type": metadata.get("resource_type"),
                        "level": metadata.get("skill_level"),
                        "department": metadata.get("department"),
                        "skills": metadata.get("skills", "").split(","),
                        "hourly_rate": float(metadata.get("hourly_rate", 0)),
                        "is_active": metadata.get("is_active") == "True",
                        "similarity_score": round(similarity, 3),
                        "document": doc
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"Error searching resources: {e}")
            return []
    
    @staticmethod
    def search_projects(query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Search for projects by natural language query
        
        Args:
            query: Search query (e.g., "e-commerce platform for TechCorp")
            top_k: Number of results to return
            filters: Optional filters (e.g., {"status": "in_progress"})
        
        Returns:
            List of projects with similarity scores
        """
        try:
            collection = client.get_collection(name=PROJECT_COLLECTION)
            
            # Generate query embedding
            query_embedding = VectorSearch.embed_text(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    similarity = 1 - distance
                    
                    formatted_results.append({
                        "project_id": metadata.get("project_id"),
                        "name": metadata.get("name"),
                        "client": metadata.get("client"),
                        "status": metadata.get("status"),
                        "budget": float(metadata.get("budget", 0)),
                        "similarity_score": round(similarity, 3),
                        "document": doc
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"Error searching projects: {e}")
            return []
    
    @staticmethod
    def search_assignments(query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Search for assignments by natural language query
        
        Args:
            query: Search query (e.g., "backend developer on e-commerce")
            top_k: Number of results to return
            filters: Optional filters (e.g., {"is_active": "True"})
        
        Returns:
            List of assignments with similarity scores
        """
        try:
            collection = client.get_collection(name=ASSIGNMENT_COLLECTION)
            
            # Generate query embedding
            query_embedding = VectorSearch.embed_text(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    similarity = 1 - distance
                    
                    formatted_results.append({
                        "assignment_id": metadata.get("assignment_id"),
                        "resource_id": metadata.get("resource_id"),
                        "project_id": metadata.get("project_id"),
                        "role": metadata.get("role"),
                        "allocation": float(metadata.get("allocation", 0)),
                        "is_active": metadata.get("is_active") == "True",
                        "similarity_score": round(similarity, 3),
                        "document": doc
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"Error searching assignments: {e}")
            return []
    
    @staticmethod
    def search_all(query: str, top_k: int = 3) -> Dict[str, List[Dict]]:
        """
        Search across all collections
        
        Args:
            query: Search query
            top_k: Results per collection
        
        Returns:
            Dictionary with results from each collection
        """
        return {
            "resources": VectorSearch.search_resources(query, top_k),
            "projects": VectorSearch.search_projects(query, top_k),
            "assignments": VectorSearch.search_assignments(query, top_k)
        }
    
    @staticmethod
    def find_similar_resources(resource_id: str, top_k: int = 5) -> List[Dict]:
        """
        Find resources similar to a given resource
        
        Args:
            resource_id: Reference resource ID
            top_k: Number of similar resources to return
        
        Returns:
            List of similar resources
        """
        try:
            collection = client.get_collection(name=RESOURCE_COLLECTION)
            
            # Get the resource
            resource = collection.get(ids=[resource_id], include=["documents"])
            
            if not resource["documents"]:
                return []
            
            # Search for similar resources
            resource_doc = resource["documents"][0]
            query_embedding = VectorSearch.embed_text(resource_doc)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k + 1,  # +1 to exclude the resource itself
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results, excluding the original resource
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for idx, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Skip the first result if it's the same resource
                    if idx == 0 and metadata.get("resource_id") == resource_id:
                        continue
                    
                    similarity = 1 - distance
                    formatted_results.append({
                        "resource_id": metadata.get("resource_id"),
                        "name": metadata.get("name"),
                        "type": metadata.get("resource_type"),
                        "skills": metadata.get("skills", "").split(","),
                        "similarity_score": round(similarity, 3)
                    })
            
            return formatted_results[:top_k]
        
        except Exception as e:
            print(f"Error finding similar resources: {e}")
            return []
    
    @staticmethod
    def find_similar_projects(project_id: str, top_k: int = 5) -> List[Dict]:
        """
        Find projects similar to a given project
        
        Args:
            project_id: Reference project ID
            top_k: Number of similar projects to return
        
        Returns:
            List of similar projects
        """
        try:
            collection = client.get_collection(name=PROJECT_COLLECTION)
            
            # Get the project
            project = collection.get(ids=[project_id], include=["documents"])
            
            if not project["documents"]:
                return []
            
            # Search for similar projects
            project_doc = project["documents"][0]
            query_embedding = VectorSearch.embed_text(project_doc)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k + 1,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for idx, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    if idx == 0 and metadata.get("project_id") == project_id:
                        continue
                    
                    similarity = 1 - distance
                    formatted_results.append({
                        "project_id": metadata.get("project_id"),
                        "name": metadata.get("name"),
                        "client": metadata.get("client"),
                        "status": metadata.get("status"),
                        "similarity_score": round(similarity, 3)
                    })
            
            return formatted_results[:top_k]
        
        except Exception as e:
            print(f"Error finding similar projects: {e}")
            return []
    
    @staticmethod
    def get_collection_stats() -> Dict[str, Dict]:
        """Get statistics about vector collections"""
        stats = {}
        
        for collection_name in [RESOURCE_COLLECTION, PROJECT_COLLECTION, ASSIGNMENT_COLLECTION]:
            try:
                collection = client.get_collection(name=collection_name)
                count = collection.count()
                stats[collection_name] = {
                    "document_count": count,
                    "model": EMBEDDING_MODEL,
                    "embedding_dimension": 384  # all-MiniLM-L6-v2 has 384 dimensions
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats


# Example usage functions for testing
def example_search_resources():
    """Example: Search for resources"""
    print("\n🔍 Example: Search Resources")
    print("Query: 'experienced Python developer in Engineering department'")
    
    results = VectorSearch.search_resources(
        "experienced Python developer in Engineering department",
        top_k=5
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']} (ID: {result['resource_id']})")
        print(f"   Type: {result['type']}, Level: {result['level']}")
        print(f"   Department: {result['department']}")
        print(f"   Skills: {', '.join(result['skills'][:3])}...")
        print(f"   Similarity: {result['similarity_score']:.1%}")


def example_search_projects():
    """Example: Search for projects"""
    print("\n🔍 Example: Search Projects")
    print("Query: 'cloud migration project for enterprise'")
    
    results = VectorSearch.search_projects(
        "cloud migration project for enterprise",
        top_k=5
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']} (ID: {result['project_id']})")
        print(f"   Client: {result['client']}, Status: {result['status']}")
        print(f"   Budget: ${result['budget']:.2f}")
        print(f"   Similarity: {result['similarity_score']:.1%}")


def example_search_all():
    """Example: Search across all collections"""
    print("\n🔍 Example: Search All Collections")
    print("Query: 'React developer on mobile projects'")
    
    results = VectorSearch.search_all("React developer on mobile projects", top_k=3)
    
    print(f"\n📚 Resources: {len(results['resources'])} found")
    for r in results['resources'][:2]:
        print(f"   - {r['name']} (similarity: {r['similarity_score']:.1%})")
    
    print(f"\n📚 Projects: {len(results['projects'])} found")
    for p in results['projects'][:2]:
        print(f"   - {p['name']} (similarity: {p['similarity_score']:.1%})")


if __name__ == "__main__":
    print("="*60)
    print("🚀 VECTOR DATABASE SEARCH UTILITY")
    print("="*60)
    
    # Show stats
    print("\n📊 Vector DB Statistics:")
    stats = VectorSearch.get_collection_stats()
    for collection, info in stats.items():
        if "error" not in info:
            print(f"   {collection}: {info['document_count']:,} documents")
        else:
            print(f"   {collection}: ERROR - {info['error']}")
    
    # Run examples
    example_search_resources()
    example_search_projects()
    example_search_all()
    
    print("\n✅ Examples completed!")
