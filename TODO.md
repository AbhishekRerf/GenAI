# Integrate llm.py and mongo_query_generator.py for chat/query endpoints

## Steps:
- [x] Step 1: Enhance utils/mongo_query_generator.py with generate_structured_response() that generates Mongo query, executes it, and formats results using llm.py structured output.
- [x] Step 2: Update utils/rag.py to use mongo_query_generator.generate_structured_response(query, context) instead of direct llm.generate_answer.
- [x] Step 3: Ensure routes/chat.py uses updated rag_query (inherits).
- [x] Step 4: Update main.py if needed for provider (no change).
- [ ] Step 5: Test endpoints (/api/chat/query, /api/query), check logs, restart uvicorn.
- [ ] Step 6: attempt_completion

Current: Starting Step 1.
