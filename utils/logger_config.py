"""
Unified Logging Configuration
Single comprehensive log file tracking entire pipeline:
- Chunking operations
- LLM requests/responses
- MongoDB query generation and execution
- All errors and system events
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Single unified log file for everything
UNIFIED_LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configure root logger
def configure_root_logger():
    """Configure the root logger for unified logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler - detailed logging to file
    file_handler = logging.FileHandler(UNIFIED_LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler - less verbose to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize root logger
root_logger = configure_root_logger()


def get_logger(name: str):
    """Get or create a logger instance"""
    return logging.getLogger(name)


# ==================== Pipeline Logging Functions ====================

def log_pipeline_start(
    stage: str,
    user_prompt: Optional[str] = None,
    collection_type: Optional[str] = None
):
    """
    Log the start of a pipeline stage
    
    Args:
        stage: Stage name (e.g., "RAG_PIPELINE", "QUERY_GENERATION")
        user_prompt: User's prompt/request
        collection_type: Which collection is being queried
    """
    logger = get_logger(stage)
    msg = f"🚀 STAGE START: {stage}"
    if user_prompt:
        msg += f" | Prompt: '{user_prompt[:80]}...'"
    if collection_type:
        msg += f" | Collection: {collection_type}"
    logger.info(msg)


def log_pipeline_end(
    stage: str,
    duration_seconds: float,
    status: str = "success",
    results_count: Optional[int] = None,
    error: Optional[str] = None
):
    """
    Log the end of a pipeline stage
    
    Args:
        stage: Stage name
        duration_seconds: Execution time
        status: "success" or "error"
        results_count: Number of results (if applicable)
        error: Error message if failed
    """
    logger = get_logger(stage)
    
    if status == "success":
        msg = f"✅ STAGE COMPLETE: {stage} | Duration: {duration_seconds:.3f}s"
        if results_count is not None:
            msg += f" | Results: {results_count}"
        logger.info(msg)
    else:
        msg = f"❌ STAGE FAILED: {stage} | Duration: {duration_seconds:.3f}s | Error: {error}"
        logger.error(msg)


def log_chunking_operation(
    file_name: str,
    total_chunks: int,
    collection: str,
    duration_seconds: float
):
    """Log document chunking operation"""
    logger = get_logger("CHUNKING")
    logger.info(
        f"📄 Chunked '{file_name}' → {total_chunks} chunks in collection '{collection}' ({duration_seconds:.3f}s)"
    )


def log_llm_request(
    prompt: str,
    system_message: str,
    model: str = "Azure OpenAI",
    temperature: float = 0.7
):
    """
    Log LLM request details
    
    Args:
        prompt: User prompt being sent
        system_message: System message being sent
        model: LLM model name
        temperature: Temperature setting
    """
    logger = get_logger("LLM_REQUEST")
    
    logger.debug(f"→ Sending to {model}:")
    logger.debug(f"  Model: {model}")
    logger.debug(f"  Temperature: {temperature}")
    logger.debug(f"  System Message Length: {len(system_message)} chars")
    logger.debug(f"  Prompt Length: {len(prompt)} chars")
    logger.debug(f"  Prompt Preview: {prompt[:150]}...")
    logger.debug(f"  System Preview: {system_message[:150]}...")


def log_llm_response(
    response: Any,
    duration_seconds: float,
    tokens_used: Optional[int] = None,
    model: str = "Azure OpenAI"
):
    """
    Log LLM response details
    
    Args:
        response: Response received from LLM
        duration_seconds: API call duration
        tokens_used: Tokens consumed
        model: LLM model name
    """
    logger = get_logger("LLM_RESPONSE")
    
    response_str = str(response)[:200] if response else "None"
    msg = f"← Received from {model}: ({duration_seconds:.3f}s)"
    if tokens_used:
        msg += f" | Tokens: {tokens_used}"
    logger.info(msg)
    logger.debug(f"  Response Preview: {response_str}...")


def log_mongo_query_generation(
    user_prompt: str,
    generated_query: Dict[str, Any],
    query_type: str = "find"
):
    """
    Log MongoDB query generation
    
    Args:
        user_prompt: User's natural language request
        generated_query: Generated MongoDB query
        query_type: "find" or "aggregation"
    """
    logger = get_logger("MONGO_GENERATION")
    
    query_str = json.dumps(generated_query, indent=2)
    logger.info(f"📋 Generated {query_type} query for: '{user_prompt[:80]}...'")
    logger.debug(f"  Query Type: {query_type}")
    logger.debug(f"  Query:\n{query_str}")


def log_mongo_query_execution(
    collection: str,
    query: Dict[str, Any],
    results_count: int,
    duration_seconds: float,
    error: Optional[str] = None
):
    """
    Log MongoDB query execution
    
    Args:
        collection: Collection name
        query: Query that was executed
        results_count: Number of results
        duration_seconds: Execution time
        error: Error message if failed
    """
    logger = get_logger("MONGO_EXECUTION")
    
    if error:
        logger.error(
            f"❌ Query failed on '{collection}' ({duration_seconds:.3f}s): {error}\n  Query: {json.dumps(query)}"
        )
    else:
        logger.info(
            f"✓ Query executed on '{collection}' → {results_count} results ({duration_seconds:.3f}s)"
        )
        logger.debug(f"  Query: {json.dumps(query)}")


def log_response_formatting(
    results_count: int,
    format_type: str = "IS_TABLEVIEW",
    duration_seconds: float = 0.0
):
    """
    Log response formatting
    
    Args:
        results_count: Number of results being formatted
        format_type: Response format type
        duration_seconds: Formatting duration
    """
    logger = get_logger("RESPONSE_FORMAT")
    logger.info(f"📊 Formatted {results_count} results as {format_type} ({duration_seconds:.3f}s)")


def log_vector_search(
    query: str,
    collection: str,
    results_count: int,
    duration_seconds: float,
    top_k: int = 5
):
    """
    Log vector search/RAG retrieval
    
    Args:
        query: Search query
        collection: Collection searched
        results_count: Number of results
        duration_seconds: Search duration
        top_k: Number of top results requested
    """
    logger = get_logger("VECTOR_SEARCH")
    logger.info(
        f"🔍 Vector search on '{collection}' for '{query[:60]}...' → {results_count}/{top_k} results ({duration_seconds:.3f}s)"
    )


def log_error(
    error_type: str,
    error_message: str,
    context: str = "",
    stage: str = "SYSTEM",
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Log error with full context
    
    Args:
        error_type: Type of error (ValueError, ConnectionError, etc)
        error_message: Error message
        context: Additional context
        stage: Which stage failed
        extra_data: Additional data to log
    """
    logger = get_logger(stage)
    
    lines = [
        f"⚠️  ERROR [{error_type}]:",
        f"  Message: {error_message}",
    ]
    
    if context:
        lines.append(f"  Context: {context}")
    
    if extra_data:
        lines.append(f"  Data: {json.dumps(extra_data, indent=4)}")
    
    full_message = "\n".join(lines)
    logger.error(full_message)


def log_system_event(
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log system events (startup, shutdown, config, etc)
    
    Args:
        event_type: Type of event
        message: Event message
        details: Additional event details
    """
    logger = get_logger("SYSTEM")
    
    msg = f"🔔 {event_type}: {message}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    
    logger.info(msg)


def log_performance_summary(
    total_duration: float,
    stages: Dict[str, float],
    results_count: int = 0,
    tokens_used: Optional[int] = None
):
    """
    Log performance summary for entire pipeline
    
    Args:
        total_duration: Total pipeline duration
        stages: Dict of {stage_name: duration_seconds}
        results_count: Results found
        tokens_used: Total tokens consumed
    """
    logger = get_logger("PERFORMANCE")
    
    logger.info("=" * 80)
    logger.info("📈 PIPELINE PERFORMANCE SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Duration: {total_duration:.3f}s")
    logger.info(f"Results: {results_count}")
    if tokens_used:
        logger.info(f"Tokens Used: {tokens_used}")
    
    logger.info("\nStage Breakdown:")
    for stage, duration in sorted(stages.items(), key=lambda x: x[1], reverse=True):
        percentage = (duration / total_duration * 100) if total_duration > 0 else 0
        logger.info(f"  • {stage:30s}: {duration:7.3f}s ({percentage:5.1f}%)")
    
    logger.info("=" * 80)


def log_complete_request_response(
    request_type: str,
    request_data: Dict[str, Any],
    response_status: str,
    response_data: Dict[str, Any],
    duration_seconds: float
):
    """
    Log complete request-response cycle
    
    Args:
        request_type: Type of request (RAG_QUERY, MONGO_QUERY, etc)
        request_data: Request parameters
        response_status: Response status (success/error)
        response_data: Response data
        duration_seconds: Total duration
    """
    logger = get_logger("REQUEST_RESPONSE")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"📨 {request_type} REQUEST-RESPONSE CYCLE")
    logger.info("=" * 80)
    logger.info(f"Status: {response_status}")
    logger.info(f"Duration: {duration_seconds:.3f}s")
    logger.debug(f"Request: {json.dumps(request_data, indent=2)}")
    logger.debug(f"Response: {json.dumps(response_data, indent=2)}")
    logger.info("=" * 80 + "\n")

