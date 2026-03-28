"""
📊 Final API Response Structure Documentation

The /api/query/execute endpoint now returns structured responses with:
1. ✅ Columns metadata for table rendering
2. ✅ Chart configuration for visualization
3. ✅ mongo_query REMOVED (not sent to frontend)
4. ✅ Proper error handling
"""

# SUCCESS RESPONSE EXAMPLE (34 results)
success_response = {
    "query": "Find all senior Python developers",
    "status": "success",
    "collection_type": "resources",
    "results_count": 34,
    "summary": "Found 34 relevant record(s) matching your request (showing first 10)",
    "response": {
        "IS_TABLEVIEW": True,
        "summary": "Found 34 relevant record(s) matching your request (showing first 10)",
        "data": [
            {
                "_id": "res_000045",
                "name": "Resource_0046_Developer",
                "email": "resource_0046_developer@company.com",
                "resource_type": "developer",
                "skill_level": "senior",
                "skills": ["Python", "AWS", "Node.js"],
                "department": "Data Science",
                "is_active": True,
                "hourly_rate": 94.6,
                "created_at": {"$date": "2026-03-28T15:13:25.833Z"}
            },
            # ... more records (up to 50)
        ],
        "columns": [
            {
                "name": "name",
                "type": "string",
                "display_name": "Name"
            },
            {
                "name": "email",
                "type": "string",
                "display_name": "Email"
            },
            {
                "name": "skill_level",
                "type": "string",
                "display_name": "Skill Level"
            },
            {
                "name": "hourly_rate",
                "type": "number",
                "display_name": "Hourly Rate"
            },
            # ... more columns
        ],
        "chart_config": {
            "type": "bar",
            "x_axis": "name",                    # Single column for X-axis
            "y_axis": ["hourly_rate"],           # Multiple columns for Y-axis (up to 5)
            "title": "Analysis by name"
        }
    },
    "error": None,
    "pipeline_time": 4.244
}

# NO RESULTS RESPONSE (0 results, still success)
no_results_response = {
    "query": "Find with impossible criteria",
    "status": "success",
    "collection_type": "resources",
    "results_count": 0,
    "summary": "No records found matching your request",
    "response": {
        "IS_TABLEVIEW": True,
        "summary": "No records found matching your request",
        "data": [],
        "columns": [],
        "chart_config": None  # No chart without data
    },
    "error": None,
    "pipeline_time": 3.050
}

# Keys for UI developers:
"""
TABLE RENDERING:
- Use response.columns to create table headers
- Columns have: name, type, display_name
- Use response.data to populate rows
- Each row object has fields matching column.name

CHART RENDERING:
- Check if response.chart_config is not None
- x_axis: single column name to use for X-axis labels
- y_axis: list of column names to create Y-axis series
- type: "bar", "line", "pie", "scatter"
- title: suggested chart title

DATA TYPES (for type conversions):
- string: text field
- number: numeric field (for Y-axis)
- boolean: true/false
- date: ISO date string
- array: list of values

ERRORS:
- If status != "success", check the error field
- Always present: status, collection_type, results_count, response
- Optional fields: error, chart_config (null if no numeric+string columns)
"""
