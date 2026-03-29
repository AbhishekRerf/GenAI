"""
Comprehensive Automated Test Suite for Query Generation Pipeline
Tests: Schema + Query Examples → LLM → MongoDB Query → Execution → Results
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.mongo_query_generator import (
    generate_mongo_query_from_llm,
    execute_mongo_query,
    generate_structured_response,
    load_query_examples,
    load_schema,
    get_relevant_examples
)
from utils.db import init_mongodb, close_mongodb, get_mongodb
from utils.logger_config import get_logger

logger = get_logger("test_query_pipeline")

# ==================== TEST UTILITIES ====================

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.tests = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.tests.append({
            "name": test_name,
            "status": "PASS",
            "details": details
        })
        print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(error)
        self.tests.append({
            "name": test_name,
            "status": "FAIL",
            "error": error
        })
        print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL}: {test_name}")
        print(f"   Error: {error}")
    
    def summary(self) -> str:
        total = self.passed + self.failed
        return f"\n{'='*60}\n📊 TEST SUMMARY\n{'='*60}\nTotal: {total} | ✅ Passed: {self.passed} | ❌ Failed: {self.failed}"

results = TestResults()

# ==================== PHASE 1: SCHEMA & EXAMPLES LOADING ====================

def test_load_schema():
    """Test 1: Load database schema"""
    try:
        schema = load_schema()
        assert schema, "Schema is empty"
        assert "resources" in schema, "Schema doesn't mention resources collection"
        assert "projects" in schema, "Schema doesn't mention projects collection"
        assert "assignments" in schema, "Schema doesn't mention assignments collection"
        
        results.add_pass(
            "Load Database Schema",
            f"✓ Schema loaded successfully ({len(schema)} chars)"
        )
        return schema
    except Exception as e:
        results.add_fail("Load Database Schema", str(e))
        return None

def test_load_query_examples():
    """Test 2: Load query examples"""
    try:
        examples = load_query_examples()
        assert examples, "Query examples list is empty"
        assert len(examples) > 0, "No query examples found"
        
        # Validate each example has required fields
        for i, example in enumerate(examples):
            assert "prompt" in example, f"Example {i} missing 'prompt' field"
            assert "mongo_query" in example, f"Example {i} missing 'mongo_query' field"
        
        results.add_pass(
            "Load Query Examples",
            f"✓ Loaded {len(examples)} query examples"
        )
        return examples
    except Exception as e:
        results.add_fail("Load Query Examples", str(e))
        return None

def test_get_relevant_examples(examples: List[Dict]):
    """Test 3: Get relevant examples based on user query"""
    try:
        if not examples:
            return
        
        test_query = "Find senior developers"
        relevant = get_relevant_examples(test_query, examples, limit=3)
        
        assert relevant, "No relevant examples found"
        assert isinstance(relevant, str), "Relevant examples should be string"
        assert len(relevant) > 0, "Relevant examples string is empty"
        
        results.add_pass(
            "Get Relevant Examples",
            f"✓ Retrieved relevant examples for query: '{test_query}'"
        )
    except Exception as e:
        results.add_fail("Get Relevant Examples", str(e))

# ==================== PHASE 2: MONGODB CONNECTION ====================

async def test_mongodb_connection():
    """Test 4: Test MongoDB Connection"""
    try:
        await init_mongodb()
        db = await get_mongodb()
        
        # Verify collections exist
        collections = await db.list_collection_names()
        assert "resources" in collections, "Resources collection not found"
        assert "projects" in collections, "Projects collection not found"
        
        results.add_pass(
            "MongoDB Connection",
            f"✓ Connected to MongoDB with {len(collections)} collections"
        )
        return True
    except Exception as e:
        results.add_fail("MongoDB Connection", str(e))
        return False

# ==================== PHASE 3: QUERY GENERATION ====================

async def test_query_generation(test_cases: List[Dict[str, str]]):
    """Test 5-N: Generate MongoDB queries from natural language"""
    if not test_cases:
        return []
    
    generated_queries = []
    
    for i, test_case in enumerate(test_cases, 1):
        test_num = 4 + i
        user_prompt = test_case["prompt"]
        
        try:
            print(f"\n{Fore.CYAN}→ Generating query {test_num}: '{user_prompt}'{Style.RESET_ALL}")
            
            result = await generate_mongo_query_from_llm(
                user_prompt=user_prompt,
                collection_type=test_case.get("collection_type", None)
            )
            
            generated_query = result["query"]
            collection_type = result["collection_type"]
            
            # Validate query format
            assert generated_query, "Generated query is empty"
            assert isinstance(generated_query, (dict, list)), "Query must be dict or list"
            
            # Store for later execution
            generated_queries.append({
                "prompt": user_prompt,
                "generated_query": generated_query,
                "collection_type": collection_type,
                "expected_query": test_case.get("expected_query"),
                "test_num": test_num
            })
            
            query_type = "aggregation" if isinstance(generated_query, list) else "find"
            results.add_pass(
                f"Generate Query {test_num}: {user_prompt[:40]}...",
                f"✓ Generated {query_type} query | Collection: {collection_type}"
            )
            
            print(f"   Query: {json.dumps(generated_query, indent=2)[:100]}...")
            
        except Exception as e:
            results.add_fail(f"Generate Query {test_num}: {user_prompt[:40]}...", str(e))
    
    return generated_queries

# ==================== PHASE 4: QUERY EXECUTION ====================

async def test_query_execution(queries_to_execute: List[Dict]):
    """Test execution of generated queries"""
    if not queries_to_execute:
        return []
    
    execution_results = []
    
    for i, query_info in enumerate(queries_to_execute, 1):
        test_num = query_info["test_num"]
        user_prompt = query_info["prompt"]
        generated_query = query_info["generated_query"]
        collection_type = query_info["collection_type"]
        
        try:
            print(f"\n{Fore.CYAN}→ Executing query {test_num}{Style.RESET_ALL}")
            
            exec_result = await execute_mongo_query(
                query=generated_query,
                collection_type=collection_type,
                limit=10
            )
            
            if exec_result["status"] == "error":
                raise Exception(exec_result.get("error", "Unknown error"))
            
            result_count = exec_result["count"]
            exec_time = exec_result["execution_time"]
            
            execution_results.append({
                "prompt": user_prompt,
                "generated_query": generated_query,
                "collection_type": collection_type,
                "results": exec_result["results"],
                "count": result_count,
                "execution_time": exec_time,
                "test_num": test_num
            })
            
            results.add_pass(
                f"Execute Query {test_num}",
                f"✓ Found {result_count} results in {exec_time:.3f}s"
            )
            
            if result_count > 0:
                print(f"   Sample result: {json.dumps(exec_result['results'][0], indent=2)[:150]}...")
            
        except Exception as e:
            results.add_fail(f"Execute Query {test_num}", str(e))
    
    return execution_results

# ==================== PHASE 5: END-TO-END PIPELINE TEST ====================

async def test_end_to_end_pipeline(test_prompts: List[str]):
    """Test complete pipeline: query → schema → examples → generate → execute"""
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 5: END-TO-END PIPELINE TEST")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    for i, prompt in enumerate(test_prompts, 1):
        try:
            print(f"{Fore.CYAN}→ Full Pipeline Test {i}: '{prompt}'{Style.RESET_ALL}")
            
            response = await generate_structured_response(
                user_prompt=prompt,
                collection_type="all",
                include_raw_results=True
            )
            
            assert response, "Response is empty"
            
            if "error" in response:
                raise Exception(response["error"])
            
            results.add_pass(
                f"End-to-End Pipeline {i}",
                f"✓ Full pipeline completed successfully"
            )
            
            # Print response structure
            if "results" in response:
                print(f"   Results: {len(response.get('results', []))} items found")
            
        except Exception as e:
            results.add_fail(f"End-to-End Pipeline {i}", str(e))

# ==================== PHASE 6: DATA VALIDATION ====================

async def test_data_validation(execution_results: List[Dict]):
    """Test 20+: Validate returned data matches expected schema"""
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 6: DATA VALIDATION")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    for i, result in enumerate(execution_results[:5], 1):  # Test first 5
        try:
            data = result["results"]
            
            if not data:
                results.add_pass(
                    f"Validate Data {i}: Empty Results",
                    "✓ Query executed (returned 0 results)"
                )
                continue
            
            # Check if data is a list
            assert isinstance(data, list), "Results must be a list"
            
            # Check if each item is a dict
            for item in data[:1]:  # Check first item
                assert isinstance(item, dict), "Each result must be a dict"
            
            # Check required fields based on collection
            collection_type = result["collection_type"]
            if collection_type == "resources":
                required_fields = ["name", "email", "resource_type"]
                for field in required_fields:
                    assert any(field in str(item).lower() for item in data[:1]), f"Field '{field}' not found"
            
            results.add_pass(
                f"Validate Data {i}: {len(data)} items",
                f"✓ Data validation passed for {result['collection_type']}"
            )
            
        except Exception as e:
            results.add_fail(f"Validate Data {i}", str(e))

# ==================== MAIN TEST SUITE ====================

async def run_full_test_suite():
    """Run complete test suite"""
    print(f"""
{Fore.CYAN}{'='*60}
🧪 COMPREHENSIVE QUERY GENERATION PIPELINE TEST SUITE
{'='*60}{Style.RESET_ALL}
Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    # ============ PHASE 1: SCHEMA & EXAMPLES ============
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 1: SCHEMA & EXAMPLES LOADING")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    schema = test_load_schema()
    examples = test_load_query_examples()
    if examples:
        test_get_relevant_examples(examples)
    
    # ============ PHASE 2: DATABASE CONNECTION ============
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 2: DATABASE CONNECTION")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    db_connected = await test_mongodb_connection()
    if not db_connected:
        print(f"\n{Fore.RED}❌ Cannot continue without MongoDB connection{Style.RESET_ALL}")
        await close_mongodb()
        return
    
    # ============ PHASE 3: QUERY GENERATION ============
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 3: QUERY GENERATION (LLM WITH SCHEMA + EXAMPLES)")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    test_cases = [
        {"prompt": "Find all senior developers", "collection_type": "resources"},
        {"prompt": "Show active resources with Python skills", "collection_type": "resources"},
        {"prompt": "Projects in progress with budget over $100k", "collection_type": "projects"},
        {"prompt": "Count resources by department", "collection_type": "resources"},
        {"prompt": "Top 5 expensive projects by budget", "collection_type": "projects"},
    ]
    
    generated_queries = await test_query_generation(test_cases)
    
    # ============ PHASE 4: QUERY EXECUTION ============
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("PHASE 4: QUERY EXECUTION")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    execution_results = await test_query_execution(generated_queries)
    
    # ============ PHASE 5: END-TO-END PIPELINE ============
    e2e_prompts = [
        "Find all senior Python developers who are active",
        "Show me projects with budget less than $50k",
        "List resources by department and their skills"
    ]
    
    await test_end_to_end_pipeline(e2e_prompts)
    
    # ============ PHASE 6: DATA VALIDATION ============
    await test_data_validation(execution_results)
    
    # ============ SUMMARY ============
    print(results.summary())
    print(f"\n⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Print detailed results
    print(f"\n{Fore.CYAN}DETAILED TEST RESULTS:{Style.RESET_ALL}")
    print(json.dumps(results.tests, indent=2))
    
    await close_mongodb()
    
    # Return exit code
    return 0 if results.failed == 0 else 1

# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_full_test_suite())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test suite interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error in test suite: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
