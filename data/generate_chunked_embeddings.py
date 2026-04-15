import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import chromadb
import re

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "genai_bot")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

def make_chunks(text):
    """Renamed function - NO 'chunk_text' name to avoid any conflicts"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    chunk_size = 500
    for sentence in sentences:
        candidate = current_chunk + " " + sentence if current_chunk else sentence
        if len(candidate) < chunk_size:
            current_chunk = candidate
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

def generate_chunked_embeddings():
    """Completely self-contained synchronous version"""
    print("🔄 Generating chunked embeddings...")
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    print("📦 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    collections = ["resources", "projects", "assignments"]
    
    for coll_name in collections:
        print(f"\n📦 Processing {coll_name}...")
        
        docs = list(db[coll_name].find())
        if not docs:
            print(f"  ⚠️ No data in {coll_name}. Run: python data/bulk_insert_sample_resources.py")
            continue
        
        chunks = []
        ids = []
        metadatas = []
        embeddings = []
        
        for doc in docs:
            text = f"Document Type: {coll_name}\nDocument ID: {doc.get('_id', 'N/A')}\n"
            for k, v in doc.items():
                if k not in ['_id'] and v is not None:
                    if isinstance(v, list):
                        text += f"{k}: {', '.join(str(x) for x in v[:5])}\n"
                    else:
                        text += f"{k}: {str(v)}\n"
            
            # Use renamed function
            chunk_texts = make_chunks(text)
            for j, chunk_text in enumerate(chunk_texts):
                chunk_id = f"{coll_name}_{str(doc.get('_id', 'unknown'))}_{j}"
                emb = model.encode(chunk_text).tolist()
                chunks.append(chunk_text)
                ids.append(chunk_id)
                metadatas.append({
                    "type": coll_name,
                    "doc_id": str(doc.get('_id')),
                    "chunk": j
                })
                embeddings.append(emb)
        
        if chunks:
            coll = chroma_client.get_or_create_collection(f"{coll_name}_chunks")
            coll.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            print(f"  ✅ Added {len(chunks)} chunks. Collection total: {coll.count()}")
        else:
            print("  ⚠️ No chunks generated")
    
    client.close()
    print("\n🎉 Chunked embeddings generated successfully!")
    print("📁 Chroma collections: resources_chunks, projects_chunks, assignments_chunks")

if __name__ == "__main__":
    generate_chunked_embeddings()

