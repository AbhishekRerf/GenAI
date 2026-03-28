import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import rag, chat, resources  # Import all routers
from utils.llm import get_llm_provider

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Resource Management RAG API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(resources.router, prefix="/api", tags=["Resources"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    provider = get_llm_provider()
    llm_status = "✅ Available" if provider else "❌ Not configured"
    return {
        "status": "healthy",
        "llm": llm_status,
        "chroma_path": os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """Root endpoint with project info"""
    return {
        "message": "Resource Management RAG API",
        "endpoints": {
            "health": "/health",
            "rag": "/api/rag",
            "chat": "/api/chat",
            "resources": "/api/resources"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
