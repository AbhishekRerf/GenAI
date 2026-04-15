"""Test if ChromaDB has data"""
import chromadb

# Load ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# List collections
print("📚 Collections in ChromaDB:")
collections = client.list_collections()
for col in collections:
    print(f"  - {col.name}: {col.count()} items")

# Check each collection for data
for col in collections:
    collection = client.get_collection(name=col.name)
    count = collection.count()
    print(f"\n📊 Collection '{col.name}':")
    print(f"   Total items: {count}")
    
    if count > 0:
        # Get first few items to verify structure
        items = collection.get(limit=3)
        print(f"   Sample IDs: {items['ids'][:3]}")
        if items['documents']:
            print(f"   Sample doc preview: {items['documents'][0][:100]}...")
