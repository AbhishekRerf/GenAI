# Resource Management Query Generation System 🚀

## 🎯 Overview
AI-powered Resource Management system that **generates MongoDB queries from natural language**. Ask questions in plain English and get results directly from your MongoDB database.

**New Approach**: Schema + Query Examples → ChromaDB Semantic Search → LLM Query Generation → MongoDB Execution → Results

Key Improvement: Generates **actual MongoDB queries** instead of RAG answers (more accurate, faster, better control)

## 📋 Quick Start (5 minutes)

### 1. Prerequisites
```
- MongoDB (local: mongod or Atlas)
- Python 3.10+
- Azure OpenAI API
```

### 2. Clone & Setup
```bash
git clone <repo>
cd backend
pip install -r requirements.txt
```

### 3. Environment (.env)
```env
# MongoDB
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=resource_management

# Azure OpenAI (Required for query generation)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# ChromaDB (for semantic search of examples)
CHROMA_DB_PATH=./chroma_db
```

### 4. Setup & Generate Chunks
```bash
# Step 1: Start MongoDB
mongod

# Step 2: Generate ChromaDB chunks (ONE TIME)
# This indexes your query examples for semantic search
python run_generate_chunks.py

# Step 3: Start API
uvicorn main:app --reload
```

**Done!** Your system will:
- Accept natural language questions
- Search ChromaDB for relevant query examples (semantic search)
- Use LLM to generate MongoDB query
- Execute on MongoDB
- Return results

## 🗄️ Data Structure (MongoDB)

**Collections**: `resources`, `projects`, `assignments`

### Sample Resource Document:
```json
{
  "name": "John Doe",
  "email": "john@company.com",
  "resource_type": "developer",
  "skill_level": "senior",
  "skills": ["Python", "React", "AWS"],
  "department": "Engineering",
  "hourly_rate": 75.0,
  "is_active": true
}
```

**~50 sample docs ** across devs, designers, PMs with realistic skills/projects.

## 🔄 How It Works

```
1. User Query: "Find senior Python developers"
   ↓
2. ChromaDB Search: Finds 5 most relevant query examples
   (Example: "Show active resources with Python skills")
   ↓
3. LLM Generation: Generates MongoDB query
   {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}
   ↓
4. Case-Insensitive: Converts to regex for case-insensitive matching
   {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": [{"$regex": "^Python$", "$options": "i"}]}}
   ↓
5. MongoDB Execution: Runs query against database
   ↓
6. Results: Returns matching documents directly
```

**Key Components:**
- **Query Examples**: 53 real MongoDB queries in `data/mongo_query_examples.json`
- **ChromaDB**: Semantic search to find relevant examples (not all examples sent to LLM)
- **LLM Generation**: Creates actual MongoDB query (not natural language answer)
- **Case-Insensitive Matching**: Handles database capitalization automatically

## 🧪 Test End-to-End

```bash
# Backend running? Test query generation:
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find senior developers with Python skills"}'

# Expected Response:
{
  "query": "Find senior developers with Python skills",
  "generated_query": {
    "resource_type": "developer",
    "skill_level": "senior",
    "skills": {"$in": ["Python"]}
  },
  "results": [
    {
      "_id": "res_001",
      "name": "John Doe",
      "skills": ["Python", "React", "AWS"],
      "hourly_rate": 85.0
    }
  ],
  "execution_time": 0.23
}
```

## 🚀 Full Workflow

1. **MongoDB**: Store structured resource/project data
2. **Query Examples**: Create `data/mongo_query_examples.json` with sample queries
3. **Index Chunks**: `run_generate_chunks.py` → ChromaDB indexes examples (ONE TIME)
4. **Query**: User question → ChromaDB semantic search → LLM generates MongoDB query → Execute
5. **Scale**: Add more query examples → re-run `run_generate_chunks.py` → instant updates

**Token Optimization:**
- Small dataset (12 examples): Use keyword matching
- Medium dataset (50+ examples): Use ChromaDB semantic search (600 tokens/query)
- Large dataset (500+ examples): Same cost with ChromaDB (semantic search finds only relevant examples)

## ✨ Key Features & Improvements

### Why Query Generation Instead of RAG?

| Aspect | RAG Approach | Query Generation (New) |
|--------|--------------|----------------------|
| Output | Natural language answer | Actual MongoDB query |
| Accuracy | Summarized from documents | Direct database access |
| Control | LLM controls filtering | You control data structure |
| Debugging | Hard to trace errors | Easy to see generated query |
| Scalability | Needs more chunks | Works with fewer examples |
| Token cost | Variable (100-500 tokens) | Fixed (600 tokens) |
| Use case | Text search answers | Structured data queries |

### Core Features

✅ **Semantic Search**: ChromaDB finds relevant examples (not keyword matching)
✅ **Case-Insensitive Matching**: "docker" matches "Docker" in database
✅ **Direct MongoDB Access**: Results are raw database documents
✅ **Schema-Aware**: LLM understands your data structure
✅ **Extensible Examples**: Easy to add more query examples
✅ **Token Optimized**: Same cost for 50 or 500 examples

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Azure 404 | Verify `AZURE_OPENAI_DEPLOYMENT_NAME` in .env |
| No ChromaDB | Run `python run_generate_chunks.py` |
| MongoDB empty | Create sample data via MongoDB Atlas or scripts |
| Case sensitivity in results | Already handled by case-insensitive logic! |
| Chunks not found | Verify `mongo_query_examples.json` exists in `data/` |
| Invalid queries from LLM | Add more examples to `mongo_query_examples.json` |

## 📁 Project Structure
```
backend/
├── main.py                          # FastAPI app
├── utils/
│   ├── mongo_query_generator.py     # Query generation + case-insensitive logic
│   ├── llm_providers.py             # LLM (Azure OpenAI)
│   └── db.py                        # MongoDB connection
├── data/
│   ├── mongo_query_examples.json    # 53+ reference query examples
│   └── db_schema_for_llm.md         # Schema docs for LLM
├── models/schemas.py                # Pydantic schemas
├── routes/
│   ├── chat.py                      # Chat endpoint
│   ├── query.py                     # Query generation endpoint
│   └── rag.py                       # RAG endpoints (legacy)
├── tests/                           # Test files
├── chroma_db/                       # ChromaDB vector store (auto-created)
├── run_generate_chunks.py           # Index examples into ChromaDB
├── query_example_manager.py         # ChromaDB management class
└── .env                             # Configuration
```

## 📚 Managing Query Examples

### View Current Examples
```bash
# See all 53 query examples
cat data/mongo_query_examples.json
```

### Add New Examples
```json
{
  "prompt": "Find senior developers with AWS",
  "mongo_query": {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["AWS"]}}
}
```

Add to `data/mongo_query_examples.json` then:
```bash
# Re-index into ChromaDB (takes ~30 seconds)
python run_generate_chunks.py
```

### Best Practices for Examples
✅ Include both FIND queries and AGGREGATION pipelines
✅ Cover different prompt variations (similar questions)
✅ Use realistic field names from your schema
✅ Start with 50+ examples for best LLM performance
✅ Test queries in MongoDB first before adding

## 🎉 Sample Queries & Expected Results

```
Q: "Find senior developers with React skills"
Generated Query: {"skill_level": "senior", "skills": {"$in": ["React"]}, "resource_type": "developer"}
Returns: [Senior React devs from MongoDB]

Q: "Count resources by department"
Generated Query: [{"$group": {"_id": "$department", "count": {"$sum": 1}}}]
Returns: Department counts aggregation

Q: "Find QA engineers"
Generated Query: {"resource_type": "QA"}
Returns: [All QA Engineers]

Q: "Find resources with aws and docker"
Generated Query: {"skills": {"$in": ["AWS", "Docker"]}}
Returns: [Resources with both skills]
```

**Note:** Case variations are handled automatically. Asking for "qa", "QA", or "qa engineers" all work!

## 🔀 Migration from Old Approach

If you were using the old RAG system:

1. **Keep MongoDB data** - No changes needed
2. **Update ChromaDB usage** - Now indexes query examples, not document chunks
3. **Change endpoint** - Use `/api/query` instead of `/api/rag`
4. **Update prompts** - New system generates queries, not answers

The old RAG routes still exist in `routes/rag.py` for reference.
