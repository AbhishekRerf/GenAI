"""
Advanced Query Example Management with ChromaDB
For handling large datasets (100+ examples)
"""

import json
import os
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import hashlib

class QueryExampleManager:
    """
    Manages query examples using ChromaDB for semantic search
    Perfect for 100+ examples
    """
    
    def __init__(self, chroma_path: str = "./chroma_db"):
        """Initialize ChromaDB client"""
        self.chroma_path = chroma_path
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "query_examples"
    
    def load_and_chunk_examples(self, json_file: str, chunk_size: int = 1) -> List[Dict]:
        """
        Load examples from JSON and chunk them
        
        Args:
            json_file: Path to mongo_query_examples.json
            chunk_size: How many examples per chunk (usually 1 for examples)
        
        Returns:
            List of chunks with metadata
        """
        print(f"📂 Loading examples from {json_file}...")
        
        with open(json_file, 'r') as f:
            examples = json.load(f)
        
        print(f"✓ Loaded {len(examples)} examples")
        
        chunks = []
        for i in range(0, len(examples), chunk_size):
            chunk_examples = examples[i:i+chunk_size]
            
            # Create chunk text for embedding
            chunk_text = "\n".join([
                f"Prompt: {ex['prompt']}\nQuery: {json.dumps(ex['mongo_query'])}"
                for ex in chunk_examples
            ])
            
            chunk = {
                "id": f"query_chunk_{i}",
                "text": chunk_text,
                "examples": chunk_examples,
                "start_idx": i,
                "end_idx": min(i + chunk_size, len(examples))
            }
            chunks.append(chunk)
        
        print(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def index_examples(self, json_file: str):
        """
        Index all examples into ChromaDB
        Run this ONCE when initializing
        """
        print(f"\n🗂️  INDEXING EXAMPLES INTO ChromaDB")
        print("="*50)
        
        # Load and chunk
        chunks = self.load_and_chunk_examples(json_file)
        
        # Get or create collection
        try:
            self.client.delete_collection(name=self.collection_name)
            print("✓ Deleted old collection")
        except:
            pass
        
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add chunks to ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk["id"])
            documents.append(chunk["text"])
            
            # Store metadata about examples in this chunk
            metadatas.append({
                "prompt": chunk["examples"][0]["prompt"],
                "start_idx": str(chunk["start_idx"]),
                "end_idx": str(chunk["end_idx"]),
                "example_count": str(len(chunk["examples"]))
            })
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Indexed {len(ids)} chunks into ChromaDB")
        print("="*50)
    
    def search_relevant_examples(
        self,
        user_query: str,
        top_k: int = 5
    ) -> str:
        """
        Search for most relevant examples using vector similarity
        
        Args:
            user_query: User's natural language question
            top_k: Number of most relevant examples to return
        
        Returns:
            Formatted string with relevant examples (ready for LLM)
        """
        collection = self.client.get_collection(name=self.collection_name)
        
        # Search
        results = collection.query(
            query_texts=[user_query],
            n_results=top_k
        )
        
        # Format results
        formatted_examples = []
        for i, doc in enumerate(results['documents'][0], 1):
            formatted_examples.append(f"""
Example {i}:
{doc}
""")
        
        return "".join(formatted_examples)


# ==================== USAGE EXAMPLES ====================

def example_small_dataset():
    """For 12 examples - use keyword matching (current approach)"""
    print("\n🔹 SMALL DATASET (12 examples)")
    print("="*50)
    print("✓ Use: Keyword matching")
    print("✓ No ChromaDB needed")
    print("✓ Load all → keyword filter → send to LLM")
    print("="*50)


def example_medium_dataset():
    """For 50-100 examples - use ChromaDB"""
    print("\n🔹 MEDIUM DATASET (50-100 examples)")
    print("="*50)
    print("✓ Use: ChromaDB with semantic search")
    print("""
    manager = QueryExampleManager()
    
    # ONE TIME: Index all examples
    manager.index_examples("data/mongo_query_examples.json")
    
    # EVERY REQUEST: Search for relevant
    relevant = manager.search_relevant_examples(
        user_query="Find senior developers",
        top_k=5  # Send only top 5 to LLM
    )
    """)
    print("="*50)


def example_large_dataset():
    """For 500+ examples - use ChromaDB with smart chunking"""
    print("\n🔹 LARGE DATASET (500+ examples)")
    print("="*50)
    print("✓ Use: ChromaDB with chunking")
    print("""
    # Chunk size = 1 (each example is a chunk)
    # OR chunk_size = 3 (group similar examples)
    
    manager = QueryExampleManager()
    
    # Index with chunks
    manager.index_examples(
        json_file="data/mongo_query_examples.json",
        chunk_size=1  # Each example separately
    )
    
    # Search (sends only top 5 chunks to LLM)
    relevant = manager.search_relevant_examples(
        user_query="Count resources by department",
        top_k=5  # Token cost: ~2,000 instead of 50,000!
    )
    """)
    print("="*50)


# ==================== COMPARISON ====================

def show_token_comparison():
    """Show token cost comparison"""
    print("\n📊 TOKEN COST COMPARISON")
    print("="*70)
    
    scenarios = [
        {
            "name": "12 examples (Current)",
            "examples": 12,
            "send_to_llm": 12,
            "avg_tokens_per_ex": 50,
            "total_tokens": "~600"
        },
        {
            "name": "500 examples (NO filtering)",
            "examples": 500,
            "send_to_llm": 500,
            "avg_tokens_per_ex": 50,
            "total_tokens": "~25,000 ❌ TOO MUCH"
        },
        {
            "name": "500 examples (WITH ChromaDB + top 5)",
            "examples": 500,
            "send_to_llm": 5,
            "avg_tokens_per_ex": 50,
            "total_tokens": "~250 ✅ OPTIMIZED"
        }
    ]
    
    for scenario in scenarios:
        print(f"""
{scenario['name']}:
  Total examples: {scenario['examples']}
  Send to LLM: {scenario['send_to_llm']}
  Tokens per example: {scenario['avg_tokens_per_ex']}
  Total tokens: {scenario['total_tokens']}
""")
    print("="*70)


# ==================== UPDATED FLOW ====================

def show_updated_flow():
    """Show the updated flow with ChromaDB"""
    print("\n🔄 UPDATED FLOW FOR 500 EXAMPLES")
    print("="*70)
    print("""
INITIALIZATION (ONE TIME):
1. Load mongo_query_examples.json (500 examples)
2. Create chunks (1 example per chunk)
3. Embed each chunk using SentenceTransformer
4. Store in ChromaDB
5. ChromaDB creates vector index

EVERY USER QUERY:
1. User: "Find all senior developers"
2. Search ChromaDB for similar examples
3. Get top 5 most relevant chunks
4. Format as string
5. Include in LLM prompt

LLM Receives:
  Schema (text) +
  Top 5 examples only (not all 500!) +
  User question
  
LLM Generates:
  MongoDB query

Execute Query:
  Get actual results
""")
    print("="*70)


if __name__ == "__main__":
    example_small_dataset()
    example_medium_dataset()
    example_large_dataset()
    show_token_comparison()
    show_updated_flow()
