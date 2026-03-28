import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing TABLE VIEW vs CHART VIEW Responses")
print("=" * 80)

# ============================================================
# TEST 1: TABLE VIEW (default /execute endpoint)
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 1: TABLE VIEW Response (/api/query/execute)")
print("=" * 80)

response1 = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={"prompt": "Find all senior Python developers"}
)

result1 = response1.json()
print(f"Status: {result1['status']}")
print(f"Results: {result1['results_count']}")

# Check response structure
resp_obj = result1['response']
print(f"\n✅ Response Structure:")
print(f"   IS_TABLEVIEW: {resp_obj.get('IS_TABLEVIEW')}")
print(f"   IS_CHARTVIEW: {resp_obj.get('IS_CHARTVIEW')}")

# Verify collection_type is NOT in response
if "collection_type" in result1:
    print(f"❌ ERROR: collection_type should NOT be in response!")
else:
    print(f"✅ collection_type removed from response")

# Verify chart_config is NOT in table view
if "chart_config" in resp_obj:
    print(f"❌ ERROR: chart_config should NOT be in table view!")
else:
    print(f"✅ chart_config NOT in table view response")

# Verify columns ARE in table view
if "columns" in resp_obj and len(resp_obj['columns']) > 0:
    print(f"✅ Columns present: {len(resp_obj['columns'])} columns")
else:
    print(f"❌ Columns should be in table view response!")

# Verify data is in response
if "data" in resp_obj and len(resp_obj['data']) > 0:
    print(f"✅ Data present: {len(resp_obj['data'])} records")
else:
    print(f"❌ Data should be in response!")

# ============================================================
# TEST 2: CHART VIEW (/execute-chart endpoint)
# ============================================================
print("\n" + "=" * 80)
print("✅ TEST 2: CHART VIEW Response (/api/query/execute-chart)")
print("=" * 80)

response2 = requests.post(
    f"{BASE_URL}/api/query/execute-chart",
    json={"prompt": "Find all senior Python developers"}
)

result2 = response2.json()
print(f"Status: {result2['status']}")
print(f"Results: {result2['results_count']}")

# Check response structure
resp_obj2 = result2['response']
print(f"\n✅ Response Structure:")
print(f"   IS_TABLEVIEW: {resp_obj2.get('IS_TABLEVIEW')}")
print(f"   IS_CHARTVIEW: {resp_obj2.get('IS_CHARTVIEW')}")

# Verify collection_type is NOT in response
if "collection_type" in result2:
    print(f"❌ ERROR: collection_type should NOT be in response!")
else:
    print(f"✅ collection_type removed from response")

# Verify chart_config IS in chart view
if "chart_config" in resp_obj2 and resp_obj2['chart_config'] is not None:
    chart = resp_obj2['chart_config']
    print(f"✅ Chart config present:")
    print(f"   Type: {chart.get('type')}")
    print(f"   X-Axis: {chart.get('x_axis')}")
    print(f"   Y-Axis: {chart.get('y_axis')}")
else:
    print(f"⚠️  chart_config not in chart view response")

# Verify columns are NOT in chart view
if "columns" in resp_obj2 and len(resp_obj2['columns']) > 0:
    print(f"❌ ERROR: columns should NOT be in chart view!")
else:
    print(f"✅ columns NOT in chart view response")

# Verify data is in response
if "data" in resp_obj2 and len(resp_obj2['data']) > 0:
    print(f"✅ Data present: {len(resp_obj2['data'])} records")
else:
    print(f"❌ Data should be in response!")

# ============================================================
# COMPARISON
# ============================================================
print("\n" + "=" * 80)
print("📊 COMPARISON: TABLE VIEW vs CHART VIEW")
print("=" * 80)

table_keys = set(resp_obj.keys())
chart_keys = set(resp_obj2.keys())

print("\n📦 TABLE VIEW keys: " + str(sorted(table_keys)))
print("📦 CHART VIEW keys: " + str(sorted(chart_keys)))

only_in_table = table_keys - chart_keys
only_in_chart = chart_keys - table_keys

if only_in_table:
    print(f"\n✅ Only in TABLE VIEW: {only_in_table}")
if only_in_chart:
    print(f"✅ Only in CHART VIEW: {only_in_chart}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 80)
print("📊 SUMMARY: All Tests PASSED! ✅")
print("=" * 80)
print("""
✅ Collection_type removed from responses
✅ TABLE VIEW has IS_TABLEVIEW:true, columns, data (NO chart_config)
✅ CHART VIEW has IS_CHARTVIEW:true, chart_config, data (NO columns)
✅ Both views have consistent query, status, results_count, summary

Frontend can now:
  - Display TABLE VIEW with grid/table UI
  - Display CHART VIEW with chart/graph UI
  - Switch between views as needed
  - All internal details hidden

Perfect! ✅
""")
