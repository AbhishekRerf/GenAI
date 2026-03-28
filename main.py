import time
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import rag, chat, resources, query  # Import all routers
from utils.llm import get_llm_provider
from utils.logger_config import log_system_event
from utils.db import init_mongodb, close_mongodb

# Load environment variables from .env file
load_dotenv()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Application startup...")
    await init_mongodb()
    log_system_event("APP_STARTUP", "Application started", {
        "llm_provider": os.getenv("AZURE_OPENAI_ENDPOINT", "not configured"),
        "mongodb_uri": "configured" if os.getenv("MONGODB_URI") else "localhost"
    })
    yield
    # Shutdown
    print("🛑 Application shutdown...")
    await close_mongodb()
    log_system_event("APP_SHUTDOWN", "Application shutting down")

app = FastAPI(
    title="Resource Management RAG API",
    version="1.0.0",
    lifespan=lifespan
)

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
app.include_router(query.router, prefix="/api", tags=["Query"])

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
            "resources": "/api/resources",
            "query": "/api/query"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
