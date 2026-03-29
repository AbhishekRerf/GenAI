import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing ERROR Response - Invalid prompt handling")
print("=" * 80)

# Test 1: Query that might cause issues or have no results
response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={
        "prompt": "Find developers with impossible skill set that doesn't exist xyzabc123",
    }
)

print(f"Status Code: {response.status_code}")
result = response.json()

print(f"Status: {result.get('status')}")
print(f"Collection: {result.get('collection_type')}")
print(f"Results Count: {result.get('results_count')}")
print(f"Summary: {result.get('summary')}")
print(f"Error: {result.get('error')}")

# Check if mongo_query is removed even on error
if "mongo_query" in result:
    print(f"❌ mongo_query still in error response (should be removed!)")
else:
    print(f"✅ mongo_query removed from error response too")

response_obj = result.get('response', {})
if response_obj:
    data = response_obj.get('data', [])
    columns = response_obj.get('columns', [])
    print(f"Data points: {len(data)}")
    print(f"Columns: {len(columns)}")

print("\n" + "=" * 80)
print("Full Error Response:")
print("=" * 80)
print(json.dumps(result, indent=2, default=str))

print("\n✅ Error handling test completed!")
