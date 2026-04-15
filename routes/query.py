"""
FastAPI routes for MongoDB Query Generation and Execution
Uses LLM to generate MongoDB queries from natural language
"""

import time
from fastapi import APIRouter, Query as QueryParam
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from utils.mongo_query_generator import (
    generate_mongo_query_from_llm,
    execute_mongo_query,
    generate_structured_response,
    validate_mongo_query
)
from utils.logger_config import get_logger

router = APIRouter(prefix="/query", tags=["query"])
logger = get_logger("routes.query")


# ==================== Request/Response Models ====================

class QueryRequest(BaseModel):
    """Query generation and execution request"""
    prompt: str
    collection_type: Optional[str] = None  # Optional: "resources", "projects", "assignments". If None, auto-detected from prompt
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Find all senior Python developers",
                "collection_type": None  # Auto-detect: will determine "resources"
            }
        }


class ColumnMetadata(BaseModel):
    """Column metadata for table rendering"""
    name: str
    type: str  # "string", "number", "boolean", "date"
    display_name: str
    

class ChartConfig(BaseModel):
    """Chart configuration"""
    type: str  # "bar", "line", "pie", "scatter"
    x_axis: str  # Single column for X axis
    y_axis: List[str]  # Multiple columns for Y axis
    title: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response with results"""
    query: str
    status: str  # "success" or "error"
    results_count: int = 0
    summary: Optional[str] = None
    response: Optional[Dict[str, Any]] = None  # { IS_TABLEVIEW, IS_CHARTVIEW, data, columns, chart_config }
    error: Optional[str] = None
    pipeline_time: float = 0.0
    
    # Note: mongo_query and collection_type are intentionally NOT included in frontend response


class GenerateQueryOnlyRequest(BaseModel):
    """Request to only generate query without executing"""
    prompt: str
    collection_type: Optional[str] = None  # Optional: will auto-detect if not provided


class GenerateQueryOnlyResponse(BaseModel):
    """Response with generated query only"""
    prompt: str
    mongo_query: Union[Dict[str, Any], List]
    query_type: str  # "find" or "aggregation"
    execution_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Find senior developers with Python skills",
                "mongo_query": {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}},
                "query_type": "find",
                "execution_time": 0.123
            }
        }


# ==================== Endpoints ====================

@router.post("/generate", response_model=GenerateQueryOnlyResponse)
async def generate_query_only(request: GenerateQueryOnlyRequest):
    """
    Generate a MongoDB query from natural language WITHOUT executing it
    
    Request body:
    {
        "prompt": "Find all senior Python developers",
        "collection_type": "resources"
    }
    
    Returns:
    {
        "prompt": "...",
        "mongo_query": {...},
        "query_type": "find",
        "execution_time": 0.123
    }
    """
    logger.info(f"Generate-only request: {request.prompt[:60]}")
    
    start_time = time.time()
    
    start_time = time.time()
    
    try:
        query_gen_result = await generate_mongo_query_from_llm(
            request.prompt,
            request.collection_type if request.collection_type else None
        )
        
        mongo_query = query_gen_result.get("query")
        detected_collection_type = query_gen_result.get("collection_type")
        
        # Determine query type
        query_type = "aggregation" if isinstance(mongo_query, list) else "find"
        
        execution_time = time.time() - start_time
        
        logger.info(f"Query generated successfully in {execution_time:.3f}s for collection: {detected_collection_type}")
        
        return {
            "prompt": request.prompt,
            "mongo_query": mongo_query,
            "query_type": query_type,
            "execution_time": execution_time
        }
        
    except Exception as e:
        logger.error(f"Query generation failed: {str(e)}")
        return {
            "prompt": request.prompt,
            "mongo_query": {},
            "query_type": "error",
            "execution_time": time.time() - start_time,
            "error": str(e)
        }


@router.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Generate a MongoDB query from natural language and execute it
    Returns structured results
    
    Request body:
    {
        "prompt": "Find senior developers with Python skills",
        "collection_type": "resources"
    }
    
    Returns:
    {
        "query": "...",
        "status": "success",
        "mongo_query": {...},
        "results_count": 5,
        "summary": "Found 5 senior Python developers",
        "response": {
            "IS_TABLEVIEW": true,
            "data": [...]
        }
    }
    """
    logger.info(f"Execute request: {request.prompt[:60]}")
    
    try:
        # Pass None for collection_type if not provided, to enable auto-detection
        result = await generate_structured_response(
            request.prompt,
            request.collection_type if request.collection_type else None,
            include_raw_results=True
        )
        
        logger.info(f"Query executed: {request.prompt[:30]}... → {result.get('results_count')} results")
        
        return result
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        
        return {
            "query": request.prompt,
            "status": "error",
            "results_count": 0,
            "summary": "Query execution failed",
            "error": str(e),
            "pipeline_time": 0
        }


@router.post("/execute-chart", response_model=QueryResponse)
async def execute_query_chart_view(request: QueryRequest):
    """
    Generate a MongoDB query and return results in CHART view format
    
    Returns chart configuration instead of columns metadata
    
    Request body:
    {
        "prompt": "Find senior developers with Python skills",
        "collection_type": "resources"
    }
    
    Returns:
    {
        "query": "...",
        "status": "success",
        "results_count": 5,
        "response": {
            "IS_TABLEVIEW": false,
            "IS_CHARTVIEW": true,
            "chart_config": {...},
            "data": [...]
        }
    }
    """
    logger.info(f"Execute chart request: {request.prompt[:60]}")
    
    try:
        # Get the base table view response first
        table_response = await generate_structured_response(
            request.prompt,
            request.collection_type if request.collection_type else None,
            include_raw_results=True
        )
        
        if table_response['status'] == 'error':
            # Return error as-is
            return table_response
        
        # Convert to chart view
        results_data = table_response['response']['data']
        columns = table_response['response']['columns']
        
        # Import chart generation function
        from utils.mongo_query_generator import generate_chart_config
        
        chart_config = generate_chart_config(columns, results_data)
        
        # Build chart view response
        chart_response = {
            "query": table_response['query'],
            "status": "success",
            "results_count": table_response['results_count'],
            "summary": table_response['summary'],
            "response": {
                "IS_TABLEVIEW": False,
                "IS_CHARTVIEW": True,
                "summary": table_response['summary'],
                "data": results_data,
                "chart_config": chart_config
                # columns deliberately excluded for chart view
            },
            "error": None,
            "pipeline_time": table_response['pipeline_time']
        }
        
        logger.info(f"Chart view generated: {request.prompt[:30]}... → {chart_response['results_count']} results")
        
        return chart_response
        
    except Exception as e:
        logger.error(f"Chart view generation failed: {str(e)}")
        
        return {
            "query": request.prompt,
            "status": "error",
            "results_count": 0,
            "summary": "Chart view generation failed",
            "error": str(e),
            "pipeline_time": 0
        }


@router.get("/examples")
async def get_query_examples(
    limit: int = QueryParam(5, ge=1, le=20)
):
    """
    Get example queries to understand the query format
    
    Query params:
    - limit: Number of examples to return (default 5, max 20)
    """
    try:
        import json
        with open("data/mongo_query_examples.json", "r") as f:
            examples = json.load(f)
        
        examples = examples[:limit]
        
        return {
            "total": len(examples),
            "examples": [
                {
                    "prompt": ex.get("prompt"),
                    "mongo_query": ex.get("mongo_query"),
                    "description": f"Example {i+1}"
                }
                for i, ex in enumerate(examples)
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to load examples: {str(e)}")
        return {
            "error": str(e),
            "examples": []
        }


@router.get("/schema")
async def get_database_schema():
    """
    Get the database schema that the LLM uses to generate queries
    """
    try:
        with open("data/db_schema_for_llm.md", "r") as f:
            schema = f.read()
        
        return {
            "schema": schema,
            "format": "markdown"
        }
        
    except Exception as e:
        logger.error(f"Failed to load schema: {str(e)}")
        return {
            "error": str(e),
            "schema": ""
        }


@router.post("/validate")
async def validate_query_endpoint(
    mongo_query: Dict[str, Any],
    query_type: str = QueryParam("find", description="Either 'find' or 'aggregation'")
):
    """
    Validate a MongoDB query for syntax
    
    Request body:
    {
        "mongo_query": {"field": "value"}
    }
    
    Returns:
    {
        "valid": true,
        "message": "Query is valid"
    }
    """
    try:
        is_valid = await validate_mongo_query(mongo_query)
        
        if is_valid:
            return {
                "valid": True,
                "message": "Query is valid and ready to execute",
                "query": mongo_query
            }
        else:
            return {
                "valid": False,
                "message": "Query syntax is invalid",
                "query": mongo_query
            }
            
    except Exception as e:
        logger.error(f"Query validation error: {str(e)}")
        return {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "query": mongo_query
        }


@router.get("/health")
async def health_check():
    """Health check for query service"""
    try:
        from utils.db import mongodb
        db = await mongodb
        
        if db is None:
            return {
                "status": "degraded",
                "message": "MongoDB not connected",
                "service": "query"
            }
        
        await db.command("ping")
        
        return {
            "status": "healthy",
            "message": "Query service ready",
            "service": "query",
            "mongodb": "connected"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "service": "query"
        }
