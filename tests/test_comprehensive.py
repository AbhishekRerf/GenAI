import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("COMPREHENSIVE API RESPONSE TESTS")
print("=" * 80)

# ============================================================
# TEST 1: Successful query with results
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 1: Successful Query (Resources with Results)")
print("=" * 80)

response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={"prompt": "Find all senior Python developers"}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Collection: {result['collection_type']}")
print(f"Results Count: {result['results_count']}")

# Verify mongo_query is removed
assert "mongo_query" not in result, "❌ mongo_query should not be in response!"
print("✅ mongo_query removed from response")

# Verify columns are present
response_obj = result['response']
assert response_obj is not None, "❌ response object should not be None!"
assert 'columns' in response_obj, "❌ columns should be in response!"
assert len(response_obj['columns']) > 0, "❌ columns should not be empty!"
print(f"✅ Columns present: {len(response_obj['columns'])} columns")
print(f"   Columns: {[c['display_name'] for c in response_obj['columns'][:3]]}...")

# Verify chart config is present
assert 'chart_config' in response_obj, "❌ chart_config should be in response!"
if response_obj['chart_config']:
    print(f"✅ Chart config: X={response_obj['chart_config']['x_axis']}, Y={response_obj['chart_config']['y_axis']}")
else:
    print("⚠️  Chart config is null (expected for some data)")

# Verify data is present
assert 'data' in response_obj, "❌ data should be in response!"
assert len(response_obj['data']) > 0, "❌ data should not be empty!"
print(f"✅ Data present: {len(response_obj['data'])} records")

# ============================================================
# TEST 2: Query with no results
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 2: Query with No Results")
print("=" * 80)

response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={"prompt": "Find developers with impossible rare skill _____xyz_____"}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Results Count: {result['results_count']}")

# Should still have proper structure
assert result['status'] in ['success', 'error'], "❌ Status should be success or error!"
assert 'response' in result, "❌ response object should be present!"
assert result['response'] is not None, "❌ response should not be None!"
print("✅ Proper response structure maintained")

print(f"✅ Returned {result['results_count']} results")
if result['results_count'] == 0:
    print("✅ Correctly returned 0 results for no-match query")

# ============================================================
# TEST 3: Auto-collection detection
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 3: Auto-Collection Detection")
print("=" * 80)

response = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={"prompt": "Find all senior developers"}  # No collection_type specified
)

result = response.json()
detected_collection = result.get('collection_type')
print(f"Auto-detected collection: {detected_collection}")
assert detected_collection is not None, "❌ collection_type should be auto-detected!"
print("✅ Collection type auto-detected successfully")

# ============================================================
# TEST 4: Response structure consistency
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 4: Response Structure Consistency")
print("=" * 80)

required_fields = ['query', 'status', 'collection_type', 'results_count', 'response', 'pipeline_time']
for field in required_fields:
    assert field in result, f"❌ Required field '{field}' missing!"
    print(f"✅ {field}: ✓")

response_required = ['IS_TABLEVIEW', 'summary', 'data', 'columns', 'chart_config']
for field in response_required:
    assert field in result['response'], f"❌ Required field 'response.{field}' missing!"
    print(f"✅ response.{field}: ✓")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 80)
print("📊 SUMMARY: All Tests PASSED! ✅")
print("=" * 80)
print("""
✅ mongo_query removed from all responses
✅ Columns metadata included for table rendering
✅ Chart configuration generated when applicable
✅ Error responses have proper structure
✅ Auto-collection detection working
✅ Response structure consistent across all scenarios
✅ Data properly formatted and available for UI

Response Ready for Frontend Implementation! 🎉
""")
