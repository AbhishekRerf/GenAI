"""
SIMPLE STEP-BY-STEP: How to Generate Chunks in ChromaDB
Run this file to index your mongo_query_examples.json into ChromaDB
"""

import json
from query_example_manager import QueryExampleManager

# ============================================================
# STEP 1: Load your mongo_query_examples.json
# ============================================================
print("\n" + "="*60)
print("STEP 1: Loading mongo_query_examples.json")
print("="*60)

json_file = "data/mongo_query_examples.json"

with open(json_file, 'r') as f:
    examples = json.load(f)

print(f"✓ Loaded {len(examples)} examples from {json_file}")
print(f"\nFirst 3 examples:")
for i, ex in enumerate(examples[:3], 1):
    print(f"  {i}. Prompt: {ex['prompt']}")

# ============================================================
# STEP 2: Create chunks (each example = 1 chunk)
# ============================================================
print("\n" + "="*60)
print("STEP 2: Creating Chunks")
print("="*60)
print(f"Total examples: {len(examples)}")
print(f"Chunk size: 1 example per chunk")
print(f"Total chunks will be: {len(examples)}")

chunks_info = []
for i, example in enumerate(examples):
    chunk = {
        "id": f"query_chunk_{i}",
        "text": f"Prompt: {example['prompt']}\nQuery: {json.dumps(example['mongo_query'])}",
        "original_prompt": example['prompt']
    }
    chunks_info.append(chunk)

print(f"✓ Created {len(chunks_info)} chunks")
print(f"\nFirst chunk looks like:")
print(f"  ID: {chunks_info[0]['id']}")
print(f"  Text: {chunks_info[0]['text'][:100]}...")

# ============================================================
# STEP 3: Convert chunks to embeddings (semantic vectors)
# ============================================================
print("\n" + "="*60)
print("STEP 3: Converting to Embeddings (Creating Vectors)")
print("="*60)
print("This converts text to numerical vectors...")
print("Each chunk -> 384-dimensional vector")
print("This is what makes semantic search work!")

from sentence_transformers import SentenceTransformer

print("\nLoading embedding model (first time takes ~5 seconds)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings for first 3 examples to show
sample_texts = [chunk["text"] for chunk in chunks_info[:3]]
print("Converting first 3 chunk texts to vectors...")
embeddings = embedder.encode(sample_texts)

print(f"✓ Created {len(embeddings)} embeddings")
print(f"Each embedding size: {embeddings[0].shape[0]} dimensions")
print(f"\nFirst embedding (first 10 dimensions):")
print(f"  {embeddings[0][:10]}")

# ============================================================
# STEP 4: Store in ChromaDB
# ============================================================
print("\n" + "="*60)
print("STEP 4: Store All Chunks in ChromaDB")
print("="*60)
print("Creating ChromaDB database...")

manager = QueryExampleManager()

print("\nIndexing all examples into ChromaDB...")
print("This is a ONE-TIME operation (takes ~30 seconds for 60+ examples)")
print("After this, searches will be INSTANT!\n")

try:
    manager.index_examples(json_file)
    print("\n✓ SUCCESS! All chunks indexed in ChromaDB!")
    
except Exception as e:
    print(f"\n✗ Error during indexing: {e}")
    exit(1)

# ============================================================
# STEP 5: Test it!
# ============================================================
print("\n" + "="*60)
print("STEP 5: Test Semantic Search on ChromaDB")
print("="*60)

test_queries = [
    "Find senior developers",
    "Python developers with experience",
    "Count resources by department",
    "Cloud engineers with AWS skills"
]

for i, query in enumerate(test_queries, 1):
    print(f"\nTest {i}: '{query}'")
    print("-" * 40)
    
    results = manager.search_relevant_examples(query, top_k=2)
    print("Top 2 matching examples:")
    print(results[:150] + "...\n")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("SUMMARY: What Just Happened?")
print("="*60)
print(f"""
1. ✓ Loaded {len(examples)} query examples
2. ✓ Created {len(chunks_info)} chunks (1 example = 1 chunk)
3. ✓ Converted text to semantic vectors (embeddings)
4. ✓ Stored all chunks in ChromaDB (./chroma_db/)
5. ✓ Tested semantic search

NOW YOU CAN:
- Use ChromaDB in your main application
- Search for relevant examples instantly
- Send only top 5 to LLM (instead of all 60)
- Keep token cost LOW (only ~600 tokens!)

NEXT STEP:
Run: python integrate_chromadb.py
This shows how to use ChromaDB in your app
""")

print("="*60)
print("✓ DONE! Your MongoDB examples are now in ChromaDB!")
print("="*60 + "\n")
