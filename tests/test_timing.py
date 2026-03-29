"""Test timing breakdown for RAG pipeline with Azure LLM"""
import time
from utils.db import get_embedding_model
import chromadb
import os
from utils.llm import get_llm_provider, generate_answer

print("⏱️ Testing RAG Pipeline Timing Breakdown\\n")

# 1. Test embedding generation
print("1️⃣ Testing Query Embedding Generation...")
start = time.time()
embedding_model = get_embedding_model()
query_embedding = embedding_model.encode("Tell me about senior developers").tolist()
embed_time = time.time() - start
print(f"   ✓ Embeddings: {embed_time:.2f}s\\n")

# 2. Test ChromaDB search
print("2️⃣ Testing ChromaDB Search...")
start = time.time()
chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
client = chromadb.PersistentClient(path=chroma_path)
collection = client.get_collection(name="resources_vectors")
results = collection.query(query_embeddings=[query_embedding], n_results=3)
search_time = time.time() - start
print(f"   ✓ ChromaDB Search: {search_time:.2f}s")
print(f"   ✓ Found: {len(results['documents'][0])} documents\\n")

# 3. Test LLM Provider
print("3️⃣ Testing LLM Provider Response...")
query = "Tell me about senior developers"
context = "\\n\\n".join(results['documents'][0][:2])

start = time.time()
provider = get_llm_provider()
if provider:
    response_text = generate_answer(query, context)
    llm_time = time.time() - start
    print(f"   ✓ {provider.name} Response: {llm_time:.2f}s (first 100 chars: {response_text[:100]}...)\\n")
else:
    llm_time = 0
    print("   ✗ No LLM provider available (add API key to .env)\\n")

# Total
total_time = embed_time + search_time + llm_time
print("="*50)
print(f"📊 TOTAL TIME: {total_time:.2f}s")
print(f"   - Embedding: {embed_time:.2f}s ({embed_time/total_time*100:.1f}%)")
print(f"   - ChromaDB: {search_time:.2f}s ({search_time/total_time*100:.1f}%)")
print(f"   - LLM Provider: {llm_time:.2f}s ({llm_time/total_time*100:.1f}%)")
print("="*50)
