# Structured LLM Response Implementation Plan
Completed steps will be marked ✓

## Step 1: Update models/schemas.py - Add StructuredResponse model ✓
- Add Pydantic model for JSON response: IS_TABLEVIEW/IS_CHARTVIEW flags, columns/data or x_axis/y_axis/data.

## Step 2: Update utils/llm_providers.py - JSON mode + parsing ✓
- Add response_format={"type": "json_object"}
- Parse response.content as JSON, fallback to plain
- Increase max_tokens=4096
- Add error handling

## Step 3: Update utils/llm.py - Strict system prompt ✓
- Chart keywords: chart, graph, visual, plot, bar, line, pie, visualize, diagram, representation
- JSON schema in prompt
- Instruct list ALL data, no truncation like "top 3"
- generate_answer returns dict

## Step 4: Update utils/rag.py - rag_query structured ✓
- Use new generate_answer dict output

## Step 5: Update utils/rag_pipeline.py - RAG generate structured ✓
- Integrate new LLM output

## Step 6: Update routes/chat.py - Handle structured response ✓
- Update ChatResponse model
- Remove sources per feedback

## Step 7: Test endpoints [PENDING]
- Table query: "show available developers"
- Chart query: "chart of project budgets"
- Verify full data listing

## Step 8: attempt_completion [PENDING]
