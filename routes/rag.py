"""
FastAPI routes for RAG pipeline
HTTP endpoints for semantic search + LLM generation
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from utils.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/api/rag", tags=["rag"])

# Initialize RAG pipeline (singleton)
_rag_pipeline = None

def get_rag_pipeline():
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        try:
            _rag_pipeline = RAGPipeline(
                llm_provider_name="azure",
                search_top_k=5,
                chunk_context_count=2
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RAG pipeline: {e}")
    return _rag_pipeline


# Request/Response models
class RAGQuery(BaseModel):
    """RAG query request"""
    query: str
    collection_type: str = "all"  # "resources", "projects", "assignments", or "all"
    include_context: bool = False
    include_sources: bool = False


class RAGResponse(BaseModel):
    """RAG response"""
    query: str
    response: str
    llm_provider: str
    retrieval_stats: dict
    performance: dict
    context: Optional[dict] = None


@router.post("/query", response_model=dict)
async def rag_query(
    query: str = Query(..., min_length=1, description="Your question"),
    collection_type: str = Query("all", description="Collection to search: 'resources', 'projects', 'assignments', or 'all'"),
    include_context: bool = Query(False, description="Include source chunks in response")
):
    """
    Query the RAG system
    
    Example: `/api/rag/query?query=Which+senior+Python+developers+are+available?`
    """
    try:
        rag = get_rag_pipeline()
        result = rag.generate(
            query=query,
            collection_type=collection_type,
            return_context=include_context
        )
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "query": query,
            "suggestion": "Make sure Azure OpenAI is configured correctly."
        }


@router.post("/chat")
async def rag_chat(request: RAGQuery):
    """
    Chat endpoint with RAG
    
    Request body:
    {
        "query": "Find senior Python developers",
        "collection_type": "resources",
        "include_context": true
    }
    """
    try:
        rag = get_rag_pipeline()
        result = rag.generate(
            query=request.query,
            collection_type=request.collection_type,
            return_context=request.include_context
        )
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "message": "RAG query failed"
        }


@router.get("/providers")
async def get_providers():
    """Get available LLM providers and their status"""
    from utils.llm_providers import AzureOpenAIProvider
    
    providers = {
        "azure": {
            "name": "Azure OpenAI",
            "description": "Azure-hosted OpenAI deployment",
            "setup_url": "https://portal.azure.com",
            "models": ["gpt-35-turbo", "gpt-4"],
            "available": False,
            "notes": "Requires a valid Azure OpenAI endpoint, key, and deployment name"
        }
    }
    
    # Check availability
    try:
        azure = AzureOpenAIProvider()
        providers["azure"]["available"] = azure.is_available()
    except:
        pass
    
    return providers


@router.get("/status")
async def rag_status():
    """Get RAG pipeline status"""
    try:
        rag = get_rag_pipeline()
        return {
            "status": "ready",
            "llm_provider": rag.llm_provider.name,
            "conversation_history_length": len(rag.conversation_history),
            "configurations": {
                "search_top_k": rag.search_top_k,
                "chunk_context_count": rag.chunk_context_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/history")
async def get_conversation_history():
    """Get conversation history"""
    try:
        rag = get_rag_pipeline()
        return {
            "history": rag.get_history(),
            "total_queries": len(rag.conversation_history)
        }
    except Exception as e:
        return {"error": str(e)}


@router.delete("/history")
async def clear_history():
    """Clear conversation history"""
    try:
        rag = get_rag_pipeline()
        count = len(rag.conversation_history)
        rag.clear_history()
        return {"message": f"Cleared {count} items from history"}
    except Exception as e:
        return {"error": str(e)}


# Stream response example (for real-time updates)
@router.get("/query-stream")
async def rag_query_stream(
    query: str = Query(..., min_length=1),
    collection_type: str = Query("all")
):
    """
    Stream RAG response (returns same as /query but structured for streaming)
    """
    try:
        rag = get_rag_pipeline()
        result = rag.generate(
            query=query,
            collection_type=collection_type,
            return_context=True
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# Example queries
@router.get("/examples")
async def example_queries():
    """Get example RAG queries"""
    return {
        "examples": [
            {
                "query": "Which senior Python developers are available for new projects?",
                "collection_type": "resources",
                "category": "resource_search"
            },
            {
                "query": "What's the status of our e-commerce platform project?",
                "collection_type": "projects",
                "category": "project_info"
            },
            {
                "query": "Who is working on the data science team?",
                "collection_type": "assignments",
                "category": "team_composition"
            },
            {
                "query": "Find AWS and Docker experts available for DevOps work",
                "collection_type": "resources",
                "category": "skill_search"
            },
            {
                "query": "What are all the in-progress projects with budgets over $200k?",
                "collection_type": "projects",
                "category": "complex_filter"
            },
            {
                "query": "Create a team of full-stack developers for e-commerce",
                "collection_type": "all",
                "category": "team_building"
            }
        ]
    }
