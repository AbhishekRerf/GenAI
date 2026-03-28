# Fix Azure Unable to Read Chunked Data
RAG chunks concatenated to large prompts → Azure token limit errors.

## Steps:
1. [x] Update requirements.txt + install tiktoken ✓
2. [x] Edit utils/llm_providers.py: Configurable model/version, pre-API token check/print, detailed errors/logging ✓
3. [x] Edit utils/rag_pipeline.py: Increased context limit to 6000 chars + token param, added logging, fixed max_tokens ✓
4. [x] utils/llm.py already supports max_tokens ✓
5. [x] Installed deps ✓
6. [ ] Test: uvicorn main:app --reload, check /health, run RAG query.
7. [ ] Verify: Logs show token counts, no Azure errors.
8. [ ] [Complete]

**Progress:** Plan approved. Starting step 1.

