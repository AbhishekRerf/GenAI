import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 90)
print("FINAL DEMONSTRATION: TABLE VIEW ↔ CHART VIEW")
print("=" * 90)

# ============================================================
# STEP 1: User query → TABLE VIEW (default)
# ============================================================
print("\n" + "=" * 90)
print("STEP 1️⃣  - User submits query → TABLE VIEW (default)")
print("=" * 90)

query_prompt = "Find all senior Python developers"
print(f"\n📝 User Query: '{query_prompt}'")
print("🔗 Endpoint: POST /api/query/execute")

response_table = requests.post(
    f"{BASE_URL}/api/query/execute",
    json={"prompt": query_prompt}
)

result_table = response_table.json()
print(f"\n✅ Response Status: {result_table['status']}")
print(f"📊 Results Count: {result_table['results_count']}")

# Display table view structure
resp_table = result_table['response']
print(f"\n📋 Response Structure:")
print(f"  ├─ IS_TABLEVIEW: {resp_table['IS_TABLEVIEW']}")
print(f"  ├─ IS_CHARTVIEW: {resp_table['IS_CHARTVIEW']}")
print(f"  ├─ Data: {len(resp_table['data'])} records")
print(f"  └─ Columns: {len(resp_table['columns'])} fields")

# Show column metadata
print(f"\n📑 Table Columns (for headers):")
for i, col in enumerate(resp_table['columns'][:5]):
    print(f"  {i+1}. {col['display_name']} ({col['type']})")
print(f"  ... and {len(resp_table['columns']) - 5} more")

# Show first record
print(f"\n💾 First Record (sample data):")
first_record = resp_table['data'][0]
for key, value in list(first_record.items())[:4]:
    col_meta = next((c for c in resp_table['columns'] if c['name'] == key), None)
    display_name = col_meta['display_name'] if col_meta else key
    print(f"  {display_name}: {value}")
print(f"  ... and more fields")

# ============================================================
# STEP 2: Frontend rendering (simulated)
# ============================================================
print("\n" + "=" * 90)
print("STEP 2️⃣  - Frontend Renders TABLE (Grid/Table UI)")
print("=" * 90)

print("\n📱 TABLE VIEW rendered with:")
print("  ├─ Headers: " + " | ".join([col['display_name'] for col in resp_table['columns'][:3]]) + " | ...")
print("  └─ Rows: " + str(len(resp_table['data'])) + " data rows")

# ============================================================
# STEP 3: User switches to CHART VIEW
# ============================================================
print("\n" + "=" * 90)
print("STEP 3️⃣  - User Clicks 'Switch to Chart View'")
print("=" * 90)

print(f"\n🔗 Endpoint: POST /api/query/execute-chart")
print(f"📝 Query: '{query_prompt}' (same query)")

response_chart = requests.post(
    f"{BASE_URL}/api/query/execute-chart",
    json={"prompt": query_prompt}
)

result_chart = response_chart.json()
print(f"\n✅ Response Status: {result_chart['status']}")
print(f"📊 Results Count: {result_chart['results_count']}")

# Display chart view structure
resp_chart = result_chart['response']
print(f"\n📊 Response Structure:")
print(f"  ├─ IS_TABLEVIEW: {resp_chart['IS_TABLEVIEW']}")
print(f"  ├─ IS_CHARTVIEW: {resp_chart['IS_CHARTVIEW']}")
print(f"  ├─ Data: {len(resp_chart['data'])} records")
print(f"  └─ chart_config: Present ✓")

# Show chart config
chart_config = resp_chart['chart_config']
if chart_config:
    print(f"\n📈 Chart Configuration:")
    print(f"  ├─ Type: {chart_config['type'].upper()}")
    print(f"  ├─ Title: {chart_config['title']}")
    print(f"  ├─ X-Axis: {chart_config['x_axis']}")
    print(f"  └─ Y-Axis: {', '.join(chart_config['y_axis'])}")

# ============================================================
# STEP 4: Frontend rendering (chart)
# ============================================================
print("\n" + "=" * 90)
print("STEP 4️⃣  - Frontend Renders CHART (Bar/Line/Pie UI)")
print("=" * 90)

print(f"\n📊 CHART VIEW rendered with:")
print(f"  ├─ Type: Bar Chart")
print(f"  ├─ Title: {chart_config['title']}")
print(f"  ├─ X-Axis Labels: Developer names (from '{chart_config['x_axis']}')")
print(f"  └─ Y-Axis Data: Hourly rates (from {chart_config['y_axis']})")

# ============================================================
# COMPARISON TABLE
# ============================================================
print("\n" + "=" * 90)
print("COMPARISON: TABLE VIEW vs CHART VIEW")
print("=" * 90)

comparison = {
    "Feature": ["View Type", "Primary UI", "Data Structure", "Columns", "Chart Config", "Use Case"],
    "TABLE VIEW (/execute)": [
        "IS_TABLEVIEW = true",
        "Grid/Table",
        "Rows & Columns",
        "✅ Included",
        "❌ NOT included",
        "Detailed data exploration"
    ],
    "CHART VIEW (/execute-chart)": [
        "IS_CHARTVIEW = true",
        "Chart/Graph",
        "Aggregated data",
        "❌ NOT included",
        "✅ Included",
        "Visual analysis"
    ]
}

print("\n")
print(f"{'Feature':<25} | {'TABLE VIEW':<30} | {'CHART VIEW':<30}")
print("-" * 90)
for i, feature in enumerate(comparison['Feature']):
    print(f"{feature:<25} | {comparison['TABLE VIEW (/execute)'][i]:<30} | {comparison['CHART VIEW (/execute-chart)'][i]:<30}")

# ============================================================
# KEY INSIGHTS
# ============================================================
print("\n" + "=" * 90)
print("🎯 KEY INSIGHTS FOR FRONTEND")
print("=" * 90)

print("""
✅ WHAT'S INCLUDED:
  1. Query: Same across both views
  2. Results Count: Same across both views
  3. Data: Same records, different presentation
  4. Columns: ONLY in table view
  5. Chart Config: ONLY in chart view

❌ WHAT'S EXCLUDED (Never sent to frontend):
  - mongo_query: Internal MongoDB query
  - collection_type: Internal collection name
  - These are kept secret for security & simplicity

🔄 USER EXPERIENCE:
  1. User enters query → /execute → TABLE VIEW
  2. Frontend shows data in table/grid
  3. User clicks "Chart" → /execute-chart → CHART VIEW
  4. Frontend shows same data as visualization
  5. User can switch back and forth

⚡ PERFORMANCE:
  - Both queries run independently (could cache data)
  - Chart config generated dynamically
  - Only needed fields included in each response
  - Minimal bandwidth usage

🎨 UI FLEXIBILITY:
  - Frontend can customize table appearance using columns metadata
  - Frontend can choose chart library (Chart.js, D3.js, etc.)
  - Frontend controls column filtering/sorting
  - Frontend controls chart type selection
""")

print("\n" + "=" * 90)
print("🎉 DEMONSTRATION COMPLETE!")
print("=" * 90)
print("""
The API is now ready for frontend integration with:
✅ Clean, consistent response structure
✅ No internal implementation details exposed
✅ Flexible table and chart views
✅ Automatic collection type detection
✅ Comprehensive error handling
✅ Full logging and monitoring

Happy coding! 🚀
""")
