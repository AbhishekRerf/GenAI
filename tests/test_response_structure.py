import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing NEW Response Structure - WITH Columns & Chart Config")
print("=" * 80)

response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={
        "prompt": "Find all senior Python developers",
    }
)

print(f"Status Code: {response.status_code}")
result = response.json()

print(f"\n✅ Status: {result.get('status')}")
print(f"✅ Collection: {result.get('collection_type')}")
print(f"✅ Results Count: {result.get('results_count')}")
print(f"✅ Pipeline Time: {result.get('pipeline_time'):.3f}s")

# Check if mongo_query is removed
if "mongo_query" in result:
    print(f"❌ ERROR: mongo_query still in response (should be removed!)")
else:
    print(f"✅ mongo_query successfully removed from response")

# Check if response contains columns
response_obj = result.get('response', {})
columns = response_obj.get('columns', [])
if columns:
    print(f"\n✅ Columns Found: {len(columns)}")
    print(f"   Column Names: {[c['display_name'] for c in columns[:5]]}")
else:
    print(f"❌ No columns found in response")

# Check if chart_config is present
chart_config = response_obj.get('chart_config')
if chart_config:
    print(f"\n✅ Chart Config Generated:")
    print(f"   Type: {chart_config.get('type')}")
    print(f"   X-Axis: {chart_config.get('x_axis')}")
    print(f"   Y-Axis: {chart_config.get('y_axis')}")
    print(f"   Title: {chart_config.get('title')}")
else:
    print(f"⚠️  No chart config (may not have numeric + string columns)")

# Check data structure
data = response_obj.get('data', [])
if data:
    print(f"\n✅ Data Points: {len(data)}")
    sample = data[0]
    print(f"   Sample Record Keys: {list(sample.keys())}")
else:
    print(f"❌ No data in response")

print("\n" + "=" * 80)
print("📊 Full Response Structure:")
print("=" * 80)
print(json.dumps({
    "status": result.get('status'),
    "collection_type": result.get('collection_type'),
    "results_count": result.get('results_count'),
    "response": {
        "IS_TABLEVIEW": response_obj.get('IS_TABLEVIEW'),
        "columns_count": len(columns),
        "columns_sample": columns[:2] if columns else None,
        "chart_config": chart_config,
        "data_count": len(data),
        "data_sample": data[:1] if data else None
    },
    "error": result.get('error')
}, indent=2, default=str))

print("\n✅ Test completed!")
