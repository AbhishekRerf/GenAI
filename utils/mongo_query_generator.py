"""
MongoDB Query Generation using LLM
Generates, validates, and executes MongoDB queries from natural language prompts
"""

import json
import os
import time
import bson.json_util
from datetime import datetime
from typing import Dict, List, Any, Union
from utils.llm_providers import AzureOpenAIProvider
from utils import db as db_module  # Import as module to access globals
from utils.logger_config import (
    log_llm_request,
    log_llm_response,
    log_mongo_query_generation,
    log_mongo_query_execution,
    log_response_formatting,
    log_error,
    log_pipeline_start,
    log_pipeline_end,
    log_complete_request_response,
    get_logger
)

logger = get_logger("mongo_query_generator")


def load_query_examples() -> List[Dict]:
    """Load MongoDB query examples from JSON file"""
    try:
        with open("data/mongo_query_examples.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("mongo_query_examples.json not found")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse mongo_query_examples.json: {str(e)}")
        return []


def load_schema() -> str:
    """Load MongoDB schema documentation from markdown file"""
    try:
        with open("data/db_schema_for_llm.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("db_schema_for_llm.md not found, using basic schema")
        return """
Collections: resources, projects, assignments
- resources: _id, name, email, resource_type, skill_level, skills[], department, hourly_rate
- projects: _id, name, status, budget, start_date, end_date
- assignments: _id, resource_id, project_id, allocation_percentage, start_date, end_date
"""


def get_relevant_examples(user_prompt: str, examples: List[Dict], limit: int = 3) -> str:
    """
    Find relevant examples from the examples list based on keywords
    
    Args:
        user_prompt: User's natural language query
        examples: List of example queries
        limit: Maximum number of examples to return
        
    Returns:
        Formatted string with relevant examples
    """
    relevant = []
    prompt_lower = user_prompt.lower()
    
    for example in examples:
        example_prompt = example.get("prompt", "").lower()
        # Simple keyword matching
        if any(word in prompt_lower for word in example_prompt.split()):
            relevant.append(example)
    
    relevant = relevant[:limit]
    
    if not relevant:
        relevant = examples[:limit]  # Fallback to first examples
    
    formatted = []
    for ex in relevant:
        query_str = json.dumps(ex.get("mongo_query"), indent=2) if isinstance(ex.get("mongo_query"), dict) else str(ex.get("mongo_query"))
        formatted.append(f"""
Example:
Prompt: {ex.get('prompt')}
Query:
```json
{query_str}
```
""")
    
    return "\n".join(formatted)


async def detect_collection_type(user_prompt: str) -> str:
    """
    Automatically detect which collection(s) the user is querying for
    Uses LLM to classify the query intent
    
    Args:
        user_prompt: Natural language query from user
        
    Returns:
        Collection type: 'resources', 'projects', 'assignments', or 'all'
    """
    logger.debug(f"Auto-detecting collection type for: {user_prompt}")
    
    # Load schema for context
    schema = load_schema()
    
    detection_prompt = f"""Based on the database schema and the user's request, determine which collection to query from.

DATABASE SCHEMA:
{schema}

COLLECTION SELECTION GUIDE:
- resources: "Find developers", "Get team members", "List senior staff", "Who has Python skills", "Find resource", "Get employee"
- projects: "Show all projects", "Get project stats", "Find completed projects", "Project timeline", "active projects"
- assignments: "Who is assigned to", "Resource allocation", "Team allocation", "assignment percentage"
- all: "Get project details with team", "Show resources on each project", "Team and project info", "complete data"

USER REQUEST: {user_prompt}

Respond with ONLY ONE word: resources, projects, assignments, or all
Do not explain, just return the collection name."""

    try:
        provider = AzureOpenAIProvider()
        if not provider.is_available():
            logger.warning("Azure OpenAI not available for collection detection, defaulting to resources")
            return "resources"
        
        logger.debug("Calling Azure OpenAI for collection type detection...")
        response = provider.generate(
            prompt=detection_prompt,
            system_message="You are a database expert. Respond with ONLY the collection name: resources, projects, assignments, or all",
            temperature=0.0  # No randomness
        )
        
        collection_type = str(response).strip().lower()
        
        # Validate response
        valid_collections = ["resources", "projects", "assignments", "all"]
        if collection_type not in valid_collections:
            logger.warning(f"LLM returned invalid collection '{collection_type}', defaulting to resources")
            return "resources"
        
        logger.info(f"✅ Detected collection type: {collection_type}")
        return collection_type
        
    except Exception as e:
        logger.error(f"Collection type detection failed: {str(e)}, defaulting to resources")
        return "resources"


async def generate_mongo_query_from_llm(
    user_prompt: str,
    collection_type: str = None
) -> Dict[str, Any]:
    """
    Generate a MongoDB query from natural language using LLM
    
    Args:
        user_prompt: Natural language query from user
        collection_type: Collection(s) to query: 'resources', 'projects', 'assignments', or 'all'
                        If None, will automatically detect based on user prompt
        
    Returns:
        Dict with keys: query, collection_type
    """
    pipeline_stage = "MONGO_QUERY_GENERATION"
    
    # Auto-detect collection type if not provided
    if not collection_type:
        logger.info("Collection type not specified, auto-detecting...")
        collection_type = await detect_collection_type(user_prompt)
        logger.info(f"Auto-detected collection type: {collection_type}")
    
    log_pipeline_start(pipeline_stage, user_prompt, collection_type)
    
    llm_start_time = time.time()
    
    # Load examples and schema
    logger.debug("Loading query examples and schema...")
    examples = load_query_examples()
    schema = load_schema()
    relevant_examples = get_relevant_examples(user_prompt, examples, limit=3)
    
    # Build LLM prompt
    llm_prompt = f"""You are a MongoDB query expert. Generate ONLY a valid MongoDB query (as JSON) for the following request.

DATABASE SCHEMA:
{schema}

RELEVANT EXAMPLES:
{relevant_examples}

USER REQUEST: {user_prompt}

Collection(s) available: {collection_type}

IMPORTANT RULES:
1. Output ONLY the MongoDB query as valid JSON - no explanations
2. For simple filters, use: {{"field": "value"}} or {{"field": {{"$operator": "value"}}}}
3. For joins/complex queries, use aggregation pipeline: [{{"$match": {{...}}}}, {{"$lookup": {{...}}}}, ...]
4. Use $lookup for relationships between collections
5. Make sure the query is valid and executable
6. If collection_type is 'all', include lookups to join relevant collections

Return ONLY the JSON query, nothing else:"""

    system_message = "You are a MongoDB query generator. Respond with ONLY valid JSON MongoDB queries."
    
    # Log what we're sending to Azure
    log_llm_request(
        prompt=llm_prompt,
        system_message=system_message,
        model="Azure OpenAI",
        temperature=0.2
    )
    
    try:
        provider = AzureOpenAIProvider()
        if not provider.is_available():
            raise Exception("Azure OpenAI not available")
        
        logger.debug("Calling Azure OpenAI API...")
        
        # Call LLM to generate query
        response = provider.generate(
            prompt=llm_prompt,
            system_message=system_message,
            temperature=0.2  # Low temperature for consistency
        )
        
        llm_duration = time.time() - llm_start_time
        
        # Log what we received from Azure
        log_llm_response(
            response=response,
            duration_seconds=llm_duration,
            model="Azure OpenAI"
        )
        
        # Extract JSON from response
        response_str = str(response)
        logger.debug(f"Raw Azure response: {response_str[:200]}...")
        
        # Try to parse JSON
        if isinstance(response, dict):
            query = response
        else:
            # Clean up response if needed (remove markdown code blocks)
            if '```json' in response_str:
                response_str = response_str.split('```json')[1].split('```')[0].strip()
            elif '```' in response_str:
                response_str = response_str.split('```')[1].split('```')[0].strip()
            
            logger.debug(f"Cleaned response: {response_str}")
            query = json.loads(response_str)
        
        # Log the generated query
        query_type = "aggregation" if isinstance(query, list) else "find"
        log_mongo_query_generation(
            user_prompt=user_prompt,
            generated_query=query,
            query_type=query_type
        )
        
        log_pipeline_end(
            pipeline_stage,
            duration_seconds=llm_duration,
            status="success"
        )
        
        return {
            "query": query,
            "collection_type": collection_type
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        logger.error(error_msg)
        log_error("JSONDecodeError", error_msg, context=f"LLM response: {response_str}", stage=pipeline_stage, extra_data={"user_prompt": user_prompt})
        
        log_pipeline_end(pipeline_stage, time.time() - llm_start_time, status="error", error=error_msg)
        
        # Return fallback text search query
        return {
            "query": {"$text": {"$search": user_prompt}},
            "collection_type": collection_type
        }
        
    except Exception as e:
        error_msg = f"LLM query generation failed: {str(e)}"
        logger.error(error_msg)
        log_error("LLMGenerationError", error_msg, context=f"User prompt: {user_prompt}", stage=pipeline_stage)
        
        log_pipeline_end(pipeline_stage, time.time() - llm_start_time, status="error", error=error_msg)
        
        raise


async def execute_mongo_query(
    query: Union[Dict, List],
    collection_type: str = "resources",
    limit: int = 50
) -> Dict[str, Any]:
    """
    Execute a MongoDB query and return results
    
    Args:
        query: MongoDB query (dict for find, list for aggregation)
        collection_type: Which collection to query
        limit: Maximum number of results to return
        
    Returns:
        Dict with results and metadata
    """
    pipeline_stage = "MONGO_EXECUTION"
    log_pipeline_start(pipeline_stage, collection_type=collection_type)
    
    exec_start_time = time.time()
    
    try:
        # Access mongodb global variable dynamically
        if db_module.mongodb is None:
            raise Exception("MongoDB not initialized - check database connection")
        
        db = db_module.mongodb
        logger.info(f"Executing query on collection '{collection_type}'")
        
        # Determine collection
        if collection_type == "all":
            collection = db.resources  # Default to resources if 'all'
        else:
            collection = db[collection_type]
        
        logger.debug(f"Collection selected: {collection.name if hasattr(collection, 'name') else collection_type}")
        
        # Execute query
        results = []
        if isinstance(query, list):
            # Aggregation pipeline
            logger.info(f"Executing aggregation pipeline with {len(query)} stages")
            logger.debug(f"Pipeline: {json.dumps(query, indent=2)}")
            async for doc in collection.aggregate(query):
                results.append(doc)
        else:
            # Find query
            logger.info(f"Executing find query")
            logger.debug(f"Query: {json.dumps(query, indent=2)}")
            async for doc in collection.find(query).limit(limit):
                results.append(doc)
        
        execution_time = time.time() - exec_start_time
        
        # Serialize results using bson.json_util to handle ObjectId and dates
        serialized_results = json.loads(json.dumps(results, default=bson.json_util.default))
        
        logger.info(f"Query executed successfully. Found {len(results)} results in {execution_time:.3f}s")
        
        # Log query execution
        log_mongo_query_execution(
            collection=collection_type,
            query=query,
            results_count=len(results),
            duration_seconds=execution_time
        )
        
        log_pipeline_end(pipeline_stage, duration_seconds=execution_time, status="success", results_count=len(results))
        
        return {
            "status": "success",
            "results": serialized_results,
            "count": len(results),
            "execution_time": execution_time
        }
        
    except Exception as e:
        exec_time = time.time() - exec_start_time
        error_msg = f"Failed to execute MongoDB query: {str(e)}"
        logger.error(error_msg)
        log_mongo_query_execution(
            collection=collection_type,
            query=query,
            results_count=0,
            duration_seconds=exec_time,
            error=error_msg
        )
        log_error("MongoDBExecutionError", error_msg, context=f"Query: {json.dumps(query)}, Collection: {collection_type}", stage=pipeline_stage)
        log_pipeline_end(pipeline_stage, duration_seconds=exec_time, status="error", error=error_msg)
        
        return {
            "status": "error",
            "error": error_msg,
            "results": [],
            "count": 0
        }


def get_column_metadata(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract column metadata from data
    
    Args:
        data: List of document dictionaries
        
    Returns:
        List of column metadata dicts with name, type, display_name
    """
    if not data:
        return []
    
    columns = {}
    sample_doc = data[0]
    
    # Get field names from first document
    for key, value in sample_doc.items():
        if key == "_id":
            continue
            
        # Determine type
        if isinstance(value, bool):
            field_type = "boolean"
        elif isinstance(value, (int, float)):
            field_type = "number"
        elif isinstance(value, dict) and "$date" in value:
            field_type = "date"
        elif isinstance(value, list):
            field_type = "array"
        else:
            field_type = "string"
        
        # Convert key to display name (convert_underscore to Capitalized Words)
        display_name = key.replace("_", " ").title()
        
        columns[key] = {
            "name": key,
            "type": field_type,
            "display_name": display_name
        }
    
    return list(columns.values())


def get_numeric_columns(columns: List[Dict[str, str]]) -> List[str]:
    """Get list of numeric column names for charts"""
    return [col["name"] for col in columns if col["type"] in ["number", "integer", "float"]]


def get_string_columns(columns: List[Dict[str, str]]) -> List[str]:
    """Get list of string column names for chart grouping"""
    return [col["name"] for col in columns if col["type"] == "string"]


def generate_chart_config(
    columns: List[Dict[str, str]],
    data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Generate chart configuration based on data structure
    X-axis: first string column
    Y-axis: numeric columns (up to 5)
    """
    string_cols = get_string_columns(columns)
    numeric_cols = get_numeric_columns(columns)
    
    if not string_cols or not numeric_cols:
        return None
    
    return {
        "type": "bar",
        "x_axis": string_cols[0],  # First string column for X-axis
        "y_axis": numeric_cols[:5],  # Up to 5 numeric columns for Y-axis
        "title": f"Analysis by {string_cols[0]}"
    }


async def generate_structured_response(
    user_prompt: str,
    collection_type: str = "all",
    include_raw_results: bool = True
) -> Dict[str, Any]:
    """
    Complete pipeline: Generate query → Execute → Format response
    Auto-detects chart requests from keywords in user_prompt
    
    Args:
        user_prompt: User's natural language request
        collection_type: Which collection(s) to query
        include_raw_results: Whether to include raw MongoDB results
        
    Returns:
        Structured response with query, results, and metadata (TABLE or CHART format)
    """
    # ============================================================
    # AUTO-DETECT CHART REQUESTS FROM KEYWORDS
    # ============================================================
    chart_keywords = [
        "chart", "graph", "visual", "plot", "bar", "line", "pie", 
        "visualize", "diagram", "representation", "chart view",
        "graph view", "bar chart", "line chart", "pie chart",
        "show as chart", "display chart", "create chart",
        "visualize data", "data visualization"
    ]
    is_chart_request = any(keyword in user_prompt.lower() for keyword in chart_keywords)
    logger.info(f"Chart request detected: {is_chart_request} (query: {user_prompt[:50]}...)")
    
    pipeline_stage = "STRUCTURED_RESPONSE_PIPELINE"
    log_pipeline_start(pipeline_stage, user_prompt, collection_type)
    
    pipeline_start_time = time.time()
    stage_timings = {}
    
    try:
        # Step 1: Generate MongoDB query from LLM
        logger.info("Step 1: Generating MongoDB query from LLM")
        query_gen_start = time.time()
        query_gen_result = await generate_mongo_query_from_llm(user_prompt, collection_type)
        stage_timings["Query Generation"] = time.time() - query_gen_start
        
        # Extract query and detected collection type from result
        mongo_query = query_gen_result.get("query")
        detected_collection_type = query_gen_result.get("collection_type", collection_type)
        logger.info(f"Generated query with collection: {detected_collection_type}")
        
        # Step 2: Execute query
        logger.info("Step 2: Executing MongoDB query")
        exec_start = time.time()
        execution_result = await execute_mongo_query(mongo_query, detected_collection_type)
        stage_timings["Query Execution"] = time.time() - exec_start
        
        if execution_result.get("status") == "error":
            error_msg = execution_result.get("error")
            pipeline_time = time.time() - pipeline_start_time
            stage_timings["Total"] = pipeline_time
            
            log_pipeline_end(pipeline_stage, duration_seconds=pipeline_time, status="error", error=error_msg)
            
            # Build error response with appropriate view flags
            error_response_inner = {
                "IS_TABLEVIEW": not is_chart_request,
                "IS_CHARTVIEW": is_chart_request,
                "summary": error_msg,
                "data": []
            }
            
            # Include columns or chart_config based on request type
            if is_chart_request:
                error_response_inner["chart_config"] = None
            else:
                error_response_inner["columns"] = []
            
            response = {
                "query": user_prompt,
                "status": "error",
                "results_count": 0,
                "summary": "Query execution failed",
                "error": error_msg,
                "response": error_response_inner,
                "pipeline_time": pipeline_time
            }
            
            log_complete_request_response(
                request_type="MONGODB_QUERY",
                request_data={"prompt": user_prompt, "collection_type": collection_type},
                response_status="error",
                response_data=response,
                duration_seconds=pipeline_time
            )
            
            return response
        
        results = execution_result.get("results", [])
        
        # Step 3: Format results for response
        logger.info("Step 3: Formatting response")
        format_start = time.time()
        
        if results:
            summary = f"Found {len(results)} relevant record(s) matching your request"
            if len(results) > 10:
                summary += f" (showing first 10)"
        else:
            summary = "No records found matching your request"
        
        format_view = "IS_CHARTVIEW" if is_chart_request else "IS_TABLEVIEW"
        log_response_formatting(
            results_count=len(results),
            format_type=format_view,
            duration_seconds=time.time() - format_start
        )
        
        stage_timings["Response Formatting"] = time.time() - format_start
        
        pipeline_time = time.time() - pipeline_start_time
        stage_timings["Total"] = pipeline_time
        
        # ============================================================
        # BUILD RESPONSE BASED ON REQUEST TYPE (TABLE or CHART)
        # ============================================================
        if is_chart_request:
            # CHART VIEW RESPONSE
            logger.info("Building CHART VIEW response (chart keywords detected)")
            columns = get_column_metadata(results)
            chart_config = generate_chart_config(columns, results)
            
            response = {
                "query": user_prompt,
                "status": "success",
                "results_count": len(results),
                "summary": summary,
                "response": {
                    "IS_TABLEVIEW": False,
                    "IS_CHARTVIEW": True,
                    "summary": summary,
                    "data": results[:50] if include_raw_results else [],
                    "chart_config": chart_config
                    # columns deliberately excluded for chart view
                },
                "pipeline_time": pipeline_time
            }
        else:
            # TABLE VIEW RESPONSE (DEFAULT)
            logger.info("Building TABLE VIEW response (default)")
            columns = get_column_metadata(results)
            
            response = {
                "query": user_prompt,
                "status": "success",
                "results_count": len(results),
                "summary": summary,
                "response": {
                    "IS_TABLEVIEW": True,
                    "IS_CHARTVIEW": False,
                    "summary": summary,
                    "data": results[:50] if include_raw_results else [],
                    "columns": columns
                    # chart_config deliberately excluded for table view
                },
                "pipeline_time": pipeline_time
            }
        
        if not include_raw_results:
            response.pop("results", None)
        
        logger.info(f"Pipeline completed successfully in {pipeline_time:.3f}s with {len(results)} results (format: {'CHART' if is_chart_request else 'TABLE'})")
        
        log_pipeline_end(pipeline_stage, duration_seconds=pipeline_time, status="success", results_count=len(results))
        
        log_complete_request_response(
            request_type="MONGODB_QUERY",
            request_data={"prompt": user_prompt, "collection_type": collection_type},
            response_status="success",
            response_data=response,
            duration_seconds=pipeline_time
        )
        
        # Log performance summary
        from utils.logger_config import log_performance_summary
        log_performance_summary(
            total_duration=pipeline_time,
            stages=stage_timings,
            results_count=len(results)
        )
        
        return response
        
    except Exception as e:
        pipeline_time = time.time() - pipeline_start_time
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(error_msg)
        log_error("RAGPipelineError", error_msg, context=f"User prompt: {user_prompt}", stage=pipeline_stage)
        
        log_pipeline_end(pipeline_stage, duration_seconds=pipeline_time, status="error", error=error_msg)
        
        response = {
            "query": user_prompt,
            "status": "error",
            "error": error_msg,
            "results": [],
            "results_count": 0,
            "response": None,
            "pipeline_time": pipeline_time
        }
        
        log_complete_request_response(
            request_type="MONGODB_QUERY",
            request_data={"prompt": user_prompt, "collection_type": collection_type},
            response_status="error",
            response_data=response,
            duration_seconds=pipeline_time
        )
        
        return response


async def validate_mongo_query(query: Union[Dict, List]) -> bool:
    """
    Validate MongoDB query syntax
    
    Args:
        query: MongoDB query to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if isinstance(query, dict):
            # Basic dict validation
            return len(query) > 0
        
        if isinstance(query, list):
            # Validate aggregation pipeline stages
            allowed_stages = [
                '$match', '$project', '$lookup', '$group', '$sort',
                '$limit', '$skip', '$unwind', '$addFields', '$count',
                '$out', '$merge', '$replaceRoot', '$facet'
            ]
            
            for stage in query:
                if not isinstance(stage, dict):
                    return False
                
                stage_keys = list(stage.keys())
                if not any(key.startswith('$') for key in stage_keys):
                    return False
            
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Query validation error: {str(e)}")
        return False

