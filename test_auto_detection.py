import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Query without collection_type - should auto-detect "resources"
print("=" * 80)
print("TEST 1: Find all senior Python developers (should auto-detect 'resources')")
print("=" * 80)

response1 = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={
        "prompt": "Find all senior Python developers"
        # NO collection_type - should auto-detect
    }
)
print(f"Status Code: {response1.status_code}")
result1 = response1.json()
print(f"Collection Detected: {result1.get('collection_type')}")
print(f"Results Count: {result1.get('results_count')}")
print(f"Status: {result1.get('status')}")
if result1.get('error'):
    print(f"Error: {result1.get('error')}")
print(f"\nFull Response:\n{json.dumps(result1, indent=2)}\n")

# Test 2: Query for projects - should auto-detect "projects"
print("=" * 80)
print("TEST 2: Show all active projects (should auto-detect 'projects')")
print("=" * 80)

response2 = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={
        "prompt": "Show all active projects with their status"
        # NO collection_type - should auto-detect
    }
)
print(f"Status Code: {response2.status_code}")
result2 = response2.json()
print(f"Collection Detected: {result2.get('collection_type')}")
print(f"Results Count: {result2.get('results_count')}")
print(f"Status: {result2.get('status')}")
if result2.get('error'):
    print(f"Error: {result2.get('error')}")
response_data = result2.get('response', {})
if response_data and isinstance(response_data, dict):
    data = response_data.get('data', [])
    print(f"\nFirst result (if any): {json.dumps(data[:1], indent=2, default=str)}\n")
else:
    print(f"\nNo response data\n")

# Test 3: Generate query only (no execution)
print("=" * 80)
print("TEST 3: Generate query only - Get resource allocation info")
print("=" * 80)

response3 = requests.post(
    f"{BASE_URL}/api/query/generate",
    json={
        "prompt": "Who is assigned to which project and what's their allocation percentage"
        # Should auto-detect "assignments"
    }
)
print(f"Status Code: {response3.status_code}")
result3 = response3.json()
print(f"Generated Query:\n{json.dumps(result3.get('mongo_query'), indent=2, default=str)}")
print(f"Query Type: {result3.get('query_type')}")
print(f"Execution Time: {result3.get('execution_time'):.4f}s\n")

print("=" * 80)
print("✅ All tests completed!")
print("=" * 80)
