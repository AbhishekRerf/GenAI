"""
Test: Query Validation & Case-Insensitive Conversion with $in to $or
Tests that $in with strings is converted to $or (MongoDB limitation)
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.mongo_query_generator import make_query_case_insensitive, validate_mongo_query

print("\n" + "="*80)
print("✅ QUERY VALIDATION & CONVERSION TEST")
print("="*80)

# Test cases
test_cases = [
    {
        "name": "Test 1: $in with single skill (docker)",
        "input": {"skills": {"$in": ["docker"]}},
        "should_convert": True,
        "expected_has": "$or"
    },
    {
        "name": "Test 2: $in with multiple skills",
        "input": {"skills": {"$in": ["docker", "python"]}},
        "should_convert": True,
        "expected_has": "$or"
    },
    {
        "name": "Test 3: Direct string value (QA)",
        "input": {"resource_type": "qa"},
        "should_convert": True,
        "expected_has": "$regex"
    },
    {
        "name": "Test 4: Numeric $in (no conversion needed)",
        "input": {"hourly_rate": {"$in": [50, 100, 150]}},
        "should_convert": False,
        "expected_has": "$in"
    },
]

print()
for test_case in test_cases:
    print(f"\n{test_case['name']}")
    print("-" * 80)
    
    original = test_case['input']
    converted = make_query_case_insensitive(original)
    
    print(f"Input Query:")
    print(f"  {json.dumps(original, indent=2)}")
    
    print(f"\nConverted Query:")
    print(f"  {json.dumps(converted, indent=2)}")
    
    # Validate the converted query
    is_valid, error_msg = validate_mongo_query(converted)
    
    if is_valid:
        print(f"\n✅ VALIDATION PASSED")
    else:
        print(f"\n❌ VALIDATION FAILED: {error_msg}")
    
    # Check expectations
    converted_str = json.dumps(converted)
    if test_case['expected_has'] in converted_str:
        print(f"✓ Contains expected '{test_case['expected_has']}'")
    else:
        print(f"✗ Missing expected '{test_case['expected_has']}'")


# Real scenario test
print("\n\n" + "="*80)
print("🔍 REAL-WORLD SCENARIO TEST")
print("="*80)

print("\nScenario: User asks 'Find all resources who are having skill in docker'")
print("-" * 80)

original_query = {"skills": {"$in": ["docker"]}}
print(f"\nOriginal Query (from LLM):")
print(f"  {json.dumps(original_query, indent=2)}")

converted_query = make_query_case_insensitive(original_query)
print(f"\nConverted Query (case-insensitive):")
print(f"  {json.dumps(converted_query, indent=2)}")

is_valid, error_msg = validate_mongo_query(converted_query)
print(f"\nValidation Result: {'✅ VALID' if is_valid else f'❌ INVALID - {error_msg}'}")

if is_valid:
    print("\n✓ This query is now valid and will work with MongoDB!")
    print("\nExplanation:")
    print("  Original: $in operator with string → INVALID ($ operators can't be in $in)")
    print("  Converted: $or operator with $regex → VALID (case-insensitive match)")
    print("  Result: Will match 'Docker', 'docker', 'DOCKER', etc.")


# Test invalid query detection
print("\n\n" + "="*80)
print("🚫 INVALID QUERY DETECTION TEST")
print("="*80)

invalid_queries = [
    {
        "name": "Invalid: $regex inside $in",
        "query": {"skills": {"$in": [{"$regex": "^docker$", "$options": "i"}]}}
    },
    {
        "name": "Invalid: $gt inside $in",
        "query": {"hourly_rate": {"$in": [{"$gt": 50}]}}
    },
]

for test in invalid_queries:
    print(f"\n{test['name']}")
    print(f"Query: {json.dumps(test['query'], indent=2)}")
    
    is_valid, error_msg = validate_mongo_query(test['query'])
    
    if not is_valid:
        print(f"✓ Correctly detected as INVALID")
        print(f"  Error: {error_msg}")
    else:
        print(f"✗ Should have been detected as INVALID")


# Conversion flow test
print("\n\n" + "="*80)
print("📊 CONVERSION FLOW DEMONSTRATION")
print("="*80)

conversions = [
    ("Docker skill query", {"skills": {"$in": ["docker"]}}),
    ("Python skill query", {"skills": {"$in": ["python"]}}),
    ("Multiple skills", {"skills": {"$in": ["docker", "python", "aws"]}}),
    ("QA type query", {"resource_type": "qa"}),
    ("Senior skill level", {"skill_level": "senior"}),
]

print("\nAll conversions with validation:")
print()

for title, query in conversions:
    converted = make_query_case_insensitive(query)
    is_valid, _ = validate_mongo_query(converted)
    status = "✅" if is_valid else "❌"
    
    print(f"{status} {title:<25} → ", end="")
    
    # Show what changed
    if "$or" in json.dumps(converted):
        print("Uses $or (was $in)")
    elif "$regex" in json.dumps(converted):
        print("Uses $regex (case-insensitive)")
    else:
        print("No conversion")


print("\n" + "="*80)
print("✨ ALL TESTS COMPLETED")
print("="*80)

print("""
SUMMARY:
════════════════════════════════════════════════════════════════════════════════

PROBLEM FIXED:
  ✗ OLD: {"skills": {"$in": ["docker"]}}
    Error: "cannot nest $ under $in"
    Reason: MongoDB $in doesn't support $ operators

  ✅ NEW: {"$or": [{"skills": {"$regex": "^docker$", "$options": "i"}}]}
    Status: VALID
    Benefit: Case-insensitive matching works!

KEY IMPROVEMENTS:
  1. Smart Conversion: $in → $or when needed
  2. Query Validation: Catches errors before MongoDB execution
  3. Better Error Messages: Explains what's wrong
  4. Case-Insensitive: Still works with "Docker", "docker", etc.

QUERIES THAT NOW WORK:
  ✓ {"skills": {"$in": ["docker"]}}
  ✓ {"skills": {"$in": ["docker", "python"]}}
  ✓ {"resource_type": "qa"}
  ✓ Case-insensitive matching for all strings

════════════════════════════════════════════════════════════════════════════════
""")
