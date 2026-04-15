"""Quick test for aggregation pipeline conversion"""
import asyncio
from utils.mongo_query_generator import generate_mongo_query_from_llm, execute_mongo_query
from utils.db import init_mongodb, close_mongodb

async def test():
    await init_mongodb()
    
    result = await generate_mongo_query_from_llm(
        user_prompt='Count resources by department',
        collection_type='resources'
    )
    
    query = result['query']
    print(f'Generated query type: {type(query).__name__}')
    print(f'Query: {query}')
    print()
    
    exec_result = await execute_mongo_query(
        query=query,
        collection_type='resources'
    )
    
    print(f'Execution status: {exec_result["status"]}')
    if exec_result["status"] == 'success':
        print(f'Results: {exec_result["count"]} found')
        if exec_result.get("results"):
            print(f'Sample result: {exec_result["results"][0]}')
    else:
        print(f'Error: {exec_result.get("error", "Unknown")}')
    
    await close_mongodb()

if __name__ == "__main__":
    asyncio.run(test())
