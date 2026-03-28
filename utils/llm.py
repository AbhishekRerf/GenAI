import os
from dotenv import load_dotenv
from utils.llm_providers import AzureOpenAIProvider

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI provider
_provider = None

def get_llm_provider():
    global _provider
    if _provider is None:
        try:
            provider = AzureOpenAIProvider()
            _provider = provider   # ✅ proper indentation
        except Exception as e:
            print(f"Azure OpenAI initialization failed: {str(e)}")
            _provider = None
    return _provider

def generate_answer(query: str, context: str) -> dict:
    """
    Generate structured table/chart response using Azure OpenAI
    
    Args:
        query: User's question
        context: Retrieved context from vector DB
    
    Returns:
        Dict with IS_TABLEVIEW/IS_CHARTVIEW structure
    """
    provider = get_llm_provider()
    if not provider:
        return {"error": "Azure OpenAI not available"}
    
    # Detect if chart request (case-insensitive)
    query_lower = query.lower()
    chart_keywords = ["chart", "graph", "visual", "plot", "bar", "line", "pie", "visualize", "diagram", "representation", "chart view"]
    is_chart_request = any(keyword in query_lower for keyword in chart_keywords)
    
    instruction = "IS_CHARTVIEW" if is_chart_request else "IS_TABLEVIEW"
    
    system_message = f"""You are a data analyst AI. ALWAYS respond in VALID JSON format with EXACTLY one of these structures:

TABLE (DEFAULT):
{{"IS_TABLEVIEW": true, "columns": ["Col1", "Col2"], "data": [["val1", "val2"], ["val3", "val4"]], "summary": "brief summary"}}

CHART:
{{"IS_CHARTVIEW": true, "x_axis": "X label", "y_axis": "Y label", "data": [["X1", Y1], ["X2", Y2]], "chart_type": "bar/line/pie", "summary": "brief summary"}}

RULES (MANDATORY):
1. List ALL relevant data from context - NO "top 3", "first few", list EVERYTHING
2. ONLY use data from context provided
3. If no data, use empty arrays and note in summary
4. Columns/data must match context exactly
5. Chart data as list of [x_value, y_value] pairs
6. Use short, clear column names
7. Summary: 1-2 sentences explaining insights

Context:
{context}

Query: {query}

Respond ONLY with the JSON object - no other text."""

    try:
        response = provider.generate(
            prompt=query,  # Query already in system
            system_message=system_message,
            temperature=0.1  # Low for consistency
        )
        return response
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return {"error": str(e)}

def generate_system_prompt(documents_summary: str) -> str:
    """Generate a system prompt based on available documents"""
    return f"""You are an AI assistant with knowledge from these documents: {documents_summary}
    Help users by providing accurate information from your knowledge base."""
