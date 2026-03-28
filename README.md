# Resource Management RAG System 🚀

## 🎯 Overview
AI-powered Resource Management system using **RAG (Retrieval-Augmented Generation)**. Ask natural questions about team resources, projects, skills, and get accurate answers from your data.

**Data Flow**: MongoDB → Vector Embeddings (ChromaDB) → RAG Pipeline → LLM (Azure OpenAI/Groq/Ollama)

## 📋 Quick Start (5 minutes)

### 1. Prerequisites
```
- MongoDB (local: mongod or Atlas)
- Python 3.10+
- Azure OpenAI or fallback LLM
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
MONGO_URI=Your Mongo DB Connection
DATABASE_NAME=Mongo DB Name

# Azure OpenAI (Recommended)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=Your URL
AZURE_OPENAI_DEPLOYMENT_NAME= Name

# ChromaDB
CHROMA_DB_PATH=./chroma_db
```

### 4. Load Sample Data → Generate Embeddings → Run!
```bash
# Step 1: Start MongoDB
mongod

# Step 2: Insert sample resources (creates ~50 docs)
python -c "from data.bulk_insert_sample_resources import main; main()"  # If exists, else manual insert

# Step 3: Generate vector embeddings from MongoDB
python data/create_vector_embeddings.py

# Step 4: Start API
uvicorn main:app --reload
```

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
1. Query: "Who are our senior Python developers?"
   ↓
2. Vector Search: ChromaDB finds top-matching resource chunks
   ↓  
3. RAG: LLM (Azure) generates answer using retrieved context
   ↓
4. Response: "Senior Python devs: John Doe (React/AWS), Jane Smith (Django)..."
```

**Chunking**: Text split into 500-char chunks w/ overlap for precise retrieval.

## 🧪 Test End-to-End

```bash
# Backend running? Test RAG:
curl -X POST http://localhost:8000/api/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "available senior developers"}'

# Expected:
{
  "answer": "Available senior devs: ...",
  "sources": [{"content": "John Doe...", "similarity": 0.92}]
}
```

## 🚀 Full Workflow

1. **MongoDB**: Store structured resource/project data
2. **Embeddings**: `create_vector_embeddings.py` → ChromaDB/chroma.sqlite3 (~10s for samples)
3. **Query**: Frontend/API hits `/api/rag` → retrieves chunks → LLM answers
4. **Scale**: Add real data → re-run embeddings → instant RAG updates

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Azure 404 | Add `AZURE_OPENAI_DEPLOYMENT_NAME=your-model` to .env |
| No ChromaDB | Run `python data/create_vector_embeddings.py` |
| Mongo empty | Check `data/` scripts or manual insert via schemas.py |
| No LLM | Fallback: `ollama serve && ollama pull mistral` |

## 📁 Project Structure
```
backend/
├── main.py              # FastAPI app
├── utils/llm_providers.py # LLM (Azure/Groq)
├── chroma_db/           # Vector store
├── data/                # DB population scripts
├── models/schemas.py    # Pydantic schemas
├── routes/rag.py        # RAG endpoints
└── .env                 # Secrets
```

## 🎉 Sample Queries
- \"Senior React developers available next month?\"
- \"Total budget for in-progress projects\"
- \"DevOps experts with AWS skills\"

**Ready to deploy!** Edit .env → run embeddings → chat away.
