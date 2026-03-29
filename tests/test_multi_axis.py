import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing Multiple Y-Axis Support")
print("=" * 80)

# Query that should have multiple numeric columns (like projects with budgets and dates)
response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={
        "prompt": "Show all projects with their budgets and status",
        "collection_type": "projects"  # Explicitly specify to avoid auto-detection issues
    }
)

print(f"Status Code: {response.status_code}")
result = response.json()

print(f"\n✅ Status: {result.get('status')}")
print(f"✅ Collection: {result.get('collection_type')}")
print(f"✅ Results: {result.get('results_count')}")

response_obj = result.get('response', {})
columns = response_obj.get('columns', [])
chart_config = response_obj.get('chart_config')

print(f"\n📊 Column Metadata:")
for col in columns:
    print(f"   {col['name']:20s} ({col['type']:10s}) → {col['display_name']}")

if chart_config:
    print(f"\n📈 Chart Configuration:")
    print(f"   Type: {chart_config.get('type')}")
    print(f"   X-Axis: {chart_config.get('x_axis')}")
    print(f"   Y-Axis columns:")
    for y_col in chart_config.get('y_axis', []):
        print(f"      - {y_col}")
    print(f"   Title: {chart_config.get('title')}")
else:
    print(f"\n⚠️ No chart config (data may not have suitable numeric columns)")

print("\n" + "=" * 80)
print("✅ Multi-axis chart test completed!")
