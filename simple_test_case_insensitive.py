"""
Simple Test: Case-Insensitive Query Logic
Shows the transformation without MongoDB imports
"""

import json

def make_query_case_insensitive(query):
    """Convert string comparisons to case-insensitive regex patterns"""
    
    def convert_dict(obj):
        if not isinstance(obj, dict):
            return obj
        
        result = {}
        for key, value in obj.items():
            if key.startswith("$"):
                result[key] = value
                continue
            
            if isinstance(value, dict) and "$in" in value:
                new_in_list = []
                for item in value["$in"]:
                    if isinstance(item, str):
                        new_in_list.append({"$regex": f"^{item}$", "$options": "i"})
                    else:
                        new_in_list.append(item)
                result[key] = {"$in": new_in_list}
                continue
            
            if isinstance(value, str):
                result[key] = {"$regex": f"^{value}$", "$options": "i"}
                continue
            
            if isinstance(value, dict):
                result[key] = convert_dict(value)
                continue
            
            result[key] = value
        
        return result
    
    if isinstance(query, dict):
        return convert_dict(query)
    return query


print("\n" + "="*70)
print("✅ CASE-INSENSITIVE QUERY CONVERTER - DEMONSTRATION")
print("="*70)

# Test cases
tests = [
    ("Find resources with docker skill", {"skills": {"$in": ["docker"]}}),
    ("Find resources with aws", {"skills": {"$in": ["aws"]}}),
    ("Find QA resources", {"resource_type": "qa"}),
    ("Multiple skills", {"skills": {"$in": ["docker", "python"]}}),
]

for title, query in tests:
    print(f"\n📌 Test: {title}")
    print("-" * 70)
    print(f"Input Query:")
    print(f"  {json.dumps(query, indent=2)}")
    
    converted = make_query_case_insensitive(query)
    print(f"\nConverted to Case-Insensitive:")
    print(f"  {json.dumps(converted, indent=2)}")
    
    print(f"\n✓ Explanation:")
    if "skills" in converted and "$in" in converted["skills"]:
        for item in converted["skills"]["$in"]:
            if isinstance(item, dict) and "$regex" in item:
                print(f"   - String matched with regex: {item['$regex']} (case-insensitive)")
    
    if "resource_type" in converted and "$regex" in converted["resource_type"]:
        print(f"   - String matched with regex: {converted['resource_type']['$regex']} (case-insensitive)")


print("\n" + "="*70)
print("📊 REAL-WORLD SCENARIO")
print("="*70)

print("""
Database Document:
{
  "_id": "res_000000",
  "name": "Resource_0001_Qa",
  "resource_type": "QA",
  "skills": ["React", "Agile", "AWS", "Figma", "Docker"]
}

User Question: "Find all resources who are having skill in docker"

Processing:
1. LLM generates: {"skills": {"$in": ["docker"]}}
2. System converts: {"skills": {"$in": [{"$regex": "^docker$", "$options": "i"}]}}
3. MongoDB searches with case-insensitive regex
4. "docker" matches "Docker" ✓

Result: FOUND! Resource with Docker skill returned!
""")

print("="*70)
print("✅ TRANSFORMATION SUMMARY")
print("="*70)

transformations = [
    ("lowercase", "docker", "^docker$", "Matches: Docker, DOCKER, DocKer"),
    ("lowercase", "aws", "^aws$", "Matches: AWS, aws, Aws"),
    ("lowercase", "qa", "^qa$", "Matches: QA, qa, Qa"),
    ("lowercase", "python", "^python$", "Matches: Python, PYTHON, PyThOn"),
]

print("\nCase Transformation Table:")
print(f"{'Input':<15} {'Regex Pattern':<20} {'Matches':<40}")
print("-" * 75)

for _, input_val, pattern, matches in transformations:
    print(f"{input_val:<15} {pattern:<20} {matches:<40}")

print("\n" + "="*70)
print("✅ BENEFITS OF THIS FIX")
print("="*70)

benefits = [
    "✓ 'docker' now matches 'Docker' in database",
    "✓ 'aws' now matches 'AWS' in database",
    "✓ 'qa' now matches 'QA' (resource_type) in database",
    "✓ Works for ANY string field (not just skills)",
    "✓ Automatic - no changes needed in LLM prompt",
    "✓ Transparent - users don't notice the conversion",
    "✓ Scalable - works for any number of records",
]

for benefit in benefits:
    print(benefit)

print("\n" + "="*70)
