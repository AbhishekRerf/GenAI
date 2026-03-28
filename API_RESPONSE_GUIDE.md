"""
🎉 FINAL API Response Structure Documentation
Updated Response Format with TABLE VIEW and CHART VIEW

Updated: March 29, 2026
"""

# ============================================================================
# ENDPOINT 1: /api/query/execute (DEFAULT - TABLE VIEW)
# ============================================================================

TABLE_VIEW_RESPONSE = {
    "query": "Find all senior Python developers",
    "status": "success",
    "results_count": 34,
    "summary": "Found 34 relevant record(s) matching your request (showing first 10)",
    "response": {
        "IS_TABLEVIEW": True,
        "IS_CHARTVIEW": False,
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
                "name": "hourly_rate",
                "type": "number",
                "display_name": "Hourly Rate"
            },
            # ... more columns
        ]
    },
    "error": None,
    "pipeline_time": 4.292
}
# NOTE: chart_config is NOT present in table view


# ============================================================================
# ENDPOINT 2: /api/query/execute-chart (CHART VIEW)
# ============================================================================

CHART_VIEW_RESPONSE = {
    "query": "Find all senior Python developers",
    "status": "success",
    "results_count": 34,
    "summary": "Found 34 relevant record(s) matching your request (showing first 10)",
    "response": {
        "IS_TABLEVIEW": False,
        "IS_CHARTVIEW": True,
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
            # ... more records
        ],
        "chart_config": {
            "type": "bar",
            "x_axis": "name",
            "y_axis": ["hourly_rate"],
            "title": "Analysis by name"
        }
    },
    "error": None,
    "pipeline_time": 4.292
}
# NOTE: columns are NOT present in chart view


# ============================================================================
# FIELD DEFINITIONS
# ============================================================================

"""
TOP-LEVEL FIELDS (Always Present):
- query (string): The original user query/prompt
- status (string): "success" or "error"
- results_count (int): Number of records found
- summary (string): Human-readable summary of results
- error (string|null): Error message if status is "error"
- pipeline_time (float): Total time in seconds

RESPONSE OBJECT (Always Present):
- IS_TABLEVIEW (boolean): true when viewing as table
- IS_CHARTVIEW (boolean): true when viewing as chart
- summary (string): Same as top-level summary
- data (array): Array of result records

TABLEVIEW-SPECIFIC (Only when IS_TABLEVIEW=true):
- columns (array): Array of column metadata objects
  - name: Database field name
  - type: Data type (string, number, boolean, date, array)
  - display_name: Human-readable name for table header

CHARTVIEW-SPECIFIC (Only when IS_CHARTVIEW=true):
- chart_config (object): Chart visualization configuration
  - type: Chart type (bar, line, pie, scatter)
  - x_axis: Single column name for X-axis labels
  - y_axis: Array of column names for Y-axis series
  - title: Suggested chart title

REMOVED FIELDS (Never in Response):
- mongo_query: Internal MongoDB query (NEVER sent to frontend)
- collection_type: Internal collection info (NEVER sent to frontend)
"""


# ============================================================================
# DATA TYPES FOR COLUMNS
# ============================================================================

COLUMN_TYPES = {
    "string": "Text field - display as-is",
    "number": "Numeric field - use for Y-axis in charts",
    "boolean": "True/false - display as checkbox or badge",
    "date": "ISO date format - parse and format as needed",
    "array": "List of values - display as comma-separated or list"
}


# ============================================================================
# FRONTEND IMPLEMENTATION GUIDE
# ============================================================================

"""
BASIC FLOW:

1. USER ENTERS QUERY
   POST /api/query/execute
   { "prompt": "Find all senior Python developers" }

2. RECEIVE TABLE VIEW (default)
   - response.IS_TABLEVIEW = true
   - response.columns available for table headers
   - response.data available for table rows

3. DISPLAY TABLE
   for each column in response.columns:
       add table header with column.display_name
   
   for each row in response.data:
       for each column:
           display row[column.name] with appropriate formatting

4. OFFER CHART VIEW (optional)
   if response.data has numeric columns:
       show "Switch to Chart View" button

5. USER CLICKS "SWITCH TO CHART VIEW"
   POST /api/query/execute-chart
   { "prompt": "Find all senior Python developers" }

6. RECEIVE CHART VIEW
   - response.IS_CHARTVIEW = true
   - response.chart_config contains visualization settings
   - response.data contains records for the chart

7. DISPLAY CHART
   const chart = {
       type: response.chart_config.type,           // "bar"
       title: response.chart_config.title,         // "Analysis by name"
       xAxis: response.chart_config.x_axis,        // "name"
       yAxis: response.chart_config.y_axis,        // ["hourly_rate"]
       data: response.data
   }
   renderChart(chart)

8. USER CAN SWITCH BACK TO TABLE VIEW
   POST /api/query/execute


KEY POINTS FOR UI DEVELOPERS:
✅ Always use response.IS_TABLEVIEW and IS_CHARTVIEW flags to determine view
✅ For table: use columns array to build headers, data array for rows
✅ For chart: use chart_config to configure visualization library
✅ Never show mongo_query or collection_type to users
✅ Use column.type to apply appropriate formatting
✅ Cache columns metadata when switching between views
✅ Error responses maintain same structure (IS_CHARTVIEW=false, no data)
"""


# ============================================================================
# ERROR RESPONSE EXAMPLE
# ============================================================================

ERROR_RESPONSE = {
    "query": "Invalid query",
    "status": "error",
    "results_count": 0,
    "summary": "Query execution failed",
    "response": {
        "IS_TABLEVIEW": False,
        "IS_CHARTVIEW": False,
        "summary": "Query execution failed: [error details]",
        "data": [],
        "columns": []
    },
    "error": "[Detailed error message here]",
    "pipeline_time": 2.15
}
# On error: IS_TABLEVIEW and IS_CHARTVIEW are both false
# Empty data and columns arrays
# Error message in both summary and error fields


# ============================================================================
# COLUMN TYPE EXAMPLES
# ============================================================================

COLUMN_EXAMPLES = [
    {"name": "name", "type": "string", "display_name": "Name"},           # Display as text
    {"name": "email", "type": "string", "display_name": "Email"},         # Display as text
    {"name": "hourly_rate", "type": "number", "display_name": "Rate"},    # Display as number
    {"name": "is_active", "type": "boolean", "display_name": "Active"},   # Display as checkbox/badge
    {"name": "created_at", "type": "date", "display_name": "Created"},    # Parse and format date
    {"name": "skills", "type": "array", "display_name": "Skills"},        # Display as list/tags
]


# ============================================================================
# TESTING COMMANDS
# ============================================================================

"""
TEST TABLE VIEW:
curl -X POST http://localhost:8000/api/query/execute \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "Find all senior Python developers"}'

TEST CHART VIEW:
curl -X POST http://localhost:8000/api/query/execute-chart \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "Find all senior Python developers"}'

PYTHON TEST:
import requests
response = requests.post("http://localhost:8000/api/query/execute",
  json={"prompt": "Find all senior Python developers"})
print(response.json())
"""
