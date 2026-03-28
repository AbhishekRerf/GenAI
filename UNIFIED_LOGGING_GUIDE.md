# Unified Logging Implementation

## Overview
All logging is now consolidated into **ONE comprehensive log file** (`logs/app.log`) that tracks the complete pipeline from start to finish.

## What Gets Logged

### 1. **Pipeline Stages** 
- When each stage starts and ends
- Duration of each stage
- Status (success/error)

### 2. **LLM Requests to Azure**
- System message being sent
- Prompt being sent
- Temperature and model settings
- Character counts

### 3. **LLM Responses from Azure**
- Response received
- Duration of API call
- Response preview

### 4. **MongoDB Query Generation**
- Generated query (full JSON)
- Query type (find vs aggregation)
- User's original prompt

### 5. **MongoDB Execution**
- Collection being queried
- Query executed
- Number of results
- Execution duration

### 6. **Response Formatting**
- Number of results formatted
- Format type (IS_TABLEVIEW)
- Formatting duration

### 7. **Error Details**
- Error type and message
- Context where error occurred
- Additional diagnostic data

### 8. **Performance Summary**
- Total pipeline duration
- Breakdown by stage
- Results count
- Tokens used

## Log File Location
```
logs/app.log
```

## Sample Log Output

```
2024-03-28 23:30:44 | routes.query           | INFO     | 🚀 STAGE START: STRUCTURED_RESPONSE_PIPELINE | Prompt: 'Find all senior Python developers...' | Collection: resources
2024-03-28 23:30:44 | mongo_query_generator  | INFO     | Step 1: Generating MongoDB query from LLM
2024-03-28 23:30:44 | MONGO_QUERY_GENERATION | INFO     | 🚀 STAGE START: MONGO_QUERY_GENERATION | Prompt: 'Find all senior Python developers...' | Collection: resources
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    | → Sending to Azure OpenAI:
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    |   Model: Azure OpenAI
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    |   Temperature: 0.2
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    |   System Message Length: 245 chars
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    |   Prompt Length: 1842 chars
2024-03-28 23:30:44 | LLM_REQUEST            | DEBUG    |   Prompt Preview: You are a MongoDB query expert. Generate ONLY a valid MongoDB query (as JSON) for the following request...
2024-03-28 23:30:44 | mongo_query_generator  | DEBUG    | Calling Azure OpenAI API...
2024-03-28 23:30:45 | LLM_RESPONSE           | INFO     | ← Received from Azure OpenAI: (0.567s)
2024-03-28 23:30:45 | LLM_RESPONSE           | DEBUG    | Response Preview: {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}...
2024-03-28 23:30:45 | mongo_query_generator  | DEBUG    | Raw Azure response: {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}
2024-03-28 23:30:45 | mongo_query_generator  | DEBUG    | Cleaned response: {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}
2024-03-28 23:30:45 | MONGO_GENERATION       | INFO     | 📋 Generated find query for: 'Find all senior Python developers...'
2024-03-28 23:30:45 | MONGO_GENERATION       | DEBUG    |   Query Type: find
2024-03-28 23:30:45 | MONGO_GENERATION       | DEBUG    |   Query:
{
  "resource_type": "developer",
  "skill_level": "senior",
  "skills": {
    "$in": [
      "Python"
    ]
  }
}
2024-03-28 23:30:45 | MONGO_QUERY_GENERATION | INFO     | ✅ STAGE COMPLETE: MONGO_QUERY_GENERATION | Duration: 0.567s
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Step 2: Executing MongoDB query
2024-03-28 23:30:45 | MONGO_EXECUTION        | INFO     | 🚀 STAGE START: MONGO_EXECUTION | Collection: resources
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Executing query on collection 'resources'
2024-03-28 23:30:45 | mongo_query_generator  | DEBUG    | Collection selected: resources
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Executing find query
2024-03-28 23:30:45 | mongo_query_generator  | DEBUG    | Query: {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Query executed successfully. Found 3 results in 0.045s
2024-03-28 23:30:45 | MONGO_EXECUTION        | INFO     | ✓ Query executed on 'resources' → 3 results (0.045s)
2024-03-28 23:30:45 | MONGO_EXECUTION        | DEBUG    |   Query: {"resource_type": "developer", "skill_level": "senior", "skills": {"$in": ["Python"]}}
2024-03-28 23:30:45 | MONGO_EXECUTION        | INFO     | ✅ STAGE COMPLETE: MONGO_EXECUTION | Duration: 0.045s | Results: 3
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Step 3: Formatting response
2024-03-28 23:30:45 | RESPONSE_FORMAT        | INFO     | 📊 Formatted 3 results as IS_TABLEVIEW (0.002s)
2024-03-28 23:30:45 | mongo_query_generator  | INFO     | Pipeline completed successfully in 0.614s with 3 results
2024-03-28 23:30:45 | STRUCTURED_RESPONSE_PIPELINE | INFO     | ✅ STAGE COMPLETE: STRUCTURED_RESPONSE_PIPELINE | Duration: 0.614s | Results: 3
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | ════════════════════════════════════════════════════════════════════════════════
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | 📨 MONGODB_QUERY REQUEST-RESPONSE CYCLE
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | ════════════════════════════════════════════════════════════════════════════════
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | Status: success
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | Duration: 0.614s
2024-03-28 23:30:45 | REQUEST_RESPONSE       | DEBUG    | Request: {
  "prompt": "Find all senior Python developers",
  "collection_type": "resources"
}
2024-03-28 23:30:45 | REQUEST_RESPONSE       | DEBUG    | Response: {
  "query": "Find all senior Python developers",
  "status": "success",
  "mongo_query": {
    "resource_type": "developer",
    "skill_level": "senior",
    "skills": {
      "$in": [
        "Python"
      ]
    }
  },
  "collection_type": "resources",
  "results_count": 3,
  "summary": "Found 3 relevant record(s) matching your request",
  "response": {
    "IS_TABLEVIEW": true,
    "summary": "Found 3 relevant record(s) matching your request",
    "data": [...]
  },
  "pipeline_time": 0.614
}
2024-03-28 23:30:45 | REQUEST_RESPONSE       | INFO     | ════════════════════════════════════════════════════════════════════════════════
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | ════════════════════════════════════════════════════════════════════════════════
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | 📈 PIPELINE PERFORMANCE SUMMARY
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | ════════════════════════════════════════════════════════════════════════════════
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | Total Duration: 0.614s
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | Results: 3
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | 
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | Stage Breakdown:
2024-03-28 23:30:45 | PERFORMANCE            | INFO     |   • Query Generation              :   0.567s ( 92.4%)
2024-03-28 23:30:45 | PERFORMANCE            | INFO     |   • Query Execution              :   0.045s (  7.3%)
2024-03-28 23:30:45 | PERFORMANCE            | INFO     |   • Response Formatting          :   0.002s (  0.3%)
2024-03-28 23:30:45 | PERFORMANCE            | INFO     | ════════════════════════════════════════════════════════════════════════════════
```

## How to View Logs

### View entire log file:
```bash
tail -f logs/app.log
```

### View only INFO level:
```bash
grep "INFO" logs/app.log
```

### View only errors:
```bash
grep "ERROR\|❌" logs/app.log
```

### View specific stage:
```bash
grep "MONGO_EXECUTION" logs/app.log
```

### View LLM interactions:
```bash
grep "LLM_REQUEST\|LLM_RESPONSE" logs/app.log
```

## Log Levels

- **DEBUG**: Detailed information for debugging
  - Request/response full content
  - Query details
  - Stage progression

- **INFO**: General information
  - Stage start/end
  - Success messages
  - Results count
  - Performance summaries

- **ERROR**: Error messages
  - Failed stages
  - Exceptions
  - Error context

## Structured Information

Each log entry contains:
```
TIMESTAMP | LOGGER_NAME | LEVEL | MESSAGE
```

Example:
```
2024-03-28 23:30:45 | MONGO_EXECUTION | INFO | ✓ Query executed on 'resources' → 3 results (0.045s)
```

## Key Sections in Log

When you open `logs/app.log`, you can search for:

1. **Pipeline Start**: `🚀 STAGE START:`
2. **Pipeline End**: `✅ STAGE COMPLETE:` or `❌ STAGE FAILED:`
3. **LLM Request**: `→ Sending to Azure OpenAI:`
4. **LLM Response**: `← Received from Azure OpenAI:`
5. **MongoDB Query**: `📋 Generated` and `✓ Query executed`
6. **Performance**: `📈 PIPELINE PERFORMANCE SUMMARY`
7. **Errors**: `⚠️  ERROR` or `❌`

## Example: Tracking Chunking to Azure to Results

To see the complete flow from chunking to Azure to MongoDB results, search for:

```
🚀 STAGE START: STRUCTURED_RESPONSE_PIPELINE
  → Sending to Azure OpenAI:
  ← Received from Azure OpenAI:
  📋 Generated query
  ✓ Query executed
  📊 Formatted
  ✅ STAGE COMPLETE:
  📈 PIPELINE PERFORMANCE SUMMARY
```

This shows you the complete journey of your request!

## Log File Size Management

Since everything is in one file, you may want to rotate logs periodically. The log file is in:
```
logs/app.log
```

To clear old logs:
```bash
# Backup current log
mv logs/app.log logs/app.log.backup

# Application will create new logs/app.log on next request
```

## Integration with Other Components

The logging system is used by:
- `utils/mongo_query_generator.py` - Logs query generation and execution
- `routes/query.py` - Logs API requests
- `utils/rag_pipeline.py` - Can log RAG operations (if integrated)
- `data/generate_chunked_embeddings.py` - Can log chunking (if integrated)
- `utils/chunked_search.py` - Can log vector searches (if integrated)

## Future Enhancements

To add logging to other parts:

```python
from utils.logger_config import (
    log_chunking_operation,
    log_vector_search,
    log_pipeline_start,
    log_pipeline_end,
    get_logger
)

# Use get_logger for quick one-offs
logger = get_logger("my_module")
logger.info("Something happened")

# Use specific functions for pipeline tracking
log_chunking_operation(
    file_name="embeddings.json",
    total_chunks=150,
    collection="resources",
    duration_seconds=1.234
)
```
