import requests
import json
import time

# Wait for server to be ready
time.sleep(2)

BASE_URL = "http://localhost:8000"

print("=" * 90)
print("TEST: AUTO-DETECTION OF CHART REQUESTS")
print("=" * 90)

# ============================================================
# TEST 1: CHART KEYWORD IN QUERY → SHOULD GET CHART VIEW
# ============================================================
print("\n" + "=" * 90)
print("TEST 1: Query with CHART keywords → Should return IS_CHARTVIEW=true")
print("=" * 90)

chart_query = "Find all senior Python developers in chart view"
print(f"\n📝 Query: '{chart_query}'")
print("🔗 Endpoint: POST /api/query/execute (same endpoint!)")

try:
    response = requests.post(
        f"{BASE_URL}/api/query/execute",
        json={"prompt": chart_query},
        timeout=10
    )
    
    result = response.json()
    resp_inner = result.get('response', {})
    
    print(f"\n✅ Status: {result.get('status')}")
    print(f"📊 Results: {result.get('results_count')} records")
    
    # Check flags
    is_chartview = resp_inner.get('IS_CHARTVIEW', False)
    is_tableview = resp_inner.get('IS_TABLEVIEW', False)
    has_chart_config = 'chart_config' in resp_inner
    has_columns = 'columns' in resp_inner
    
    print(f"\n✅ VIEW FLAGS:")
    print(f"  ├─ IS_TABLEVIEW: {is_tableview}")
    print(f"  └─ IS_CHARTVIEW: {is_chartview}")
    
    print(f"\n✅ RESPONSE STRUCTURE:")
    print(f"  ├─ Has 'columns': {has_columns}")
    print(f"  └─ Has 'chart_config': {has_chart_config}")
    
    if is_chartview and has_chart_config and not has_columns:
        print(f"\n🎉 TEST 1 PASSED ✅")
        print(f"   Chart view properly detected and returned!")
        if resp_inner.get('chart_config'):
            chart = resp_inner['chart_config']
            print(f"   Chart type: {chart.get('type')}")
            print(f"   X-axis: {chart.get('x_axis')}")
            print(f"   Y-axis: {chart.get('y_axis')}")
    else:
        print(f"\n❌ TEST 1 FAILED")
        print(f"   Expected: IS_CHARTVIEW=true, chart_config present, columns absent")
        print(f"   Got: IS_CHARTVIEW={is_chartview}, chart_config={has_chart_config}, columns={has_columns}")

except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 2: REGULAR QUERY (NO CHART KEYWORDS) → TABLE VIEW
# ============================================================
print("\n" + "=" * 90)
print("TEST 2: Query without chart keywords → Should return IS_TABLEVIEW=true")
print("=" * 90)

table_query = "Find all senior Python developers"
print(f"\n📝 Query: '{table_query}'")
print("🔗 Endpoint: POST /api/query/execute (same endpoint!)")

try:
    response = requests.post(
        f"{BASE_URL}/api/query/execute",
        json={"prompt": table_query},
        timeout=10
    )
    
    result = response.json()
    resp_inner = result.get('response', {})
    
    print(f"\n✅ Status: {result.get('status')}")
    print(f"📊 Results: {result.get('results_count')} records")
    
    # Check flags
    is_chartview = resp_inner.get('IS_CHARTVIEW', False)
    is_tableview = resp_inner.get('IS_TABLEVIEW', False)
    has_chart_config = 'chart_config' in resp_inner
    has_columns = 'columns' in resp_inner
    
    print(f"\n✅ VIEW FLAGS:")
    print(f"  ├─ IS_TABLEVIEW: {is_tableview}")
    print(f"  └─ IS_CHARTVIEW: {is_chartview}")
    
    print(f"\n✅ RESPONSE STRUCTURE:")
    print(f"  ├─ Has 'columns': {has_columns}")
    print(f"  └─ Has 'chart_config': {has_chart_config}")
    
    if is_tableview and has_columns and not has_chart_config:
        print(f"\n🎉 TEST 2 PASSED ✅")
        print(f"   Table view properly returned!")
        if resp_inner.get('columns'):
            print(f"   Columns count: {len(resp_inner['columns'])}")
    else:
        print(f"\n❌ TEST 2 FAILED")
        print(f"   Expected: IS_TABLEVIEW=true, columns present, chart_config absent")
        print(f"   Got: IS_TABLEVIEW={is_tableview}, columns={has_columns}, chart_config={has_chart_config}")

except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 3: ORDER COMPARISON (CHART vs TABLE SAME QUERY)
# ============================================================
print("\n" + "=" * 90)
print("TEST 3: Comparison - Different formats, same data")
print("=" * 90)

base_query = "Senior Python developers"

try:
    # Get table view
    resp_table = requests.post(
        f"{BASE_URL}/api/query/execute",
        json={"prompt": base_query},
        timeout=10
    ).json()
    
    # Get chart view (with keyword)
    resp_chart = requests.post(
        f"{BASE_URL}/api/query/execute",
        json={"prompt": f"{base_query} in chart view"},
        timeout=10
    ).json()
    
    results_table = resp_table.get('results_count', 0)
    results_chart = resp_chart.get('results_count', 0)
    
    print(f"\n📊 Results comparison:")
    print(f"  ├─ TABLE VIEW: {results_table} records")
    print(f"  └─ CHART VIEW: {results_chart} records")
    
    table_is_table = resp_table['response'].get('IS_TABLEVIEW', False)
    chart_is_chart = resp_chart['response'].get('IS_CHARTVIEW', False)
    
    print(f"\n✅ View type:")
    print(f"  ├─ Table query returned TABLE VIEW: {table_is_table}")
    print(f"  └─ Chart query returned CHART VIEW: {chart_is_chart}")
    
    if results_table == results_chart and table_is_table and chart_is_chart:
        print(f"\n🎉 TEST 3 PASSED ✅")
        print(f"   Same query, different views requested, proper conversion!")
    else:
        print(f"\n❌ TEST 3 FAILED")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 90)
print("ALL TESTS COMPLETE 🎉")
print("=" * 90)
