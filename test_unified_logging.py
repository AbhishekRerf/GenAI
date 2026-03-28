#!/usr/bin/env python3
"""
Quick test to verify the UnifiedLogging and MongoDB Query system is working
Run this after starting: python main.py
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*80)
    print("🏥 Testing Health Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query_generate():
    """Test query generation endpoint"""
    print("\n" + "="*80)
    print("🔧 Testing Query Generation (NO Execution)")
    print("="*80)
    
    payload = {
        "prompt": "Find all senior Python developers",
        "collection_type": "resources"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/api/query/generate", json=payload)
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        print(f"Generated Query Type: {result.get('query_type')}")
        print(f"Generated Query: {json.dumps(result.get('mongo_query'), indent=2)}")
        print(f"Execution Time: {result.get('execution_time'):.3f}s")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query_execute():
    """Test query generation AND execution"""
    print("\n" + "="*80)
    print("🚀 Testing Query Generation + Execution")
    print("="*80)
    
    payload = {
        "prompt": "Find all senior Python developers",
        "collection_type": "resources"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/api/query/execute", json=payload)
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        
        print(f"\nStatus: {result.get('status')}")
        print(f"Results Count: {result.get('results_count')}")
        print(f"Summary: {result.get('summary')}")
        print(f"MongoDB Query: {json.dumps(result.get('mongo_query'), indent=2)}")
        print(f"Pipeline Time: {result.get('pipeline_time'):.3f}s")
        
        if result.get('response'):
            print(f"Response Format: {result['response'].get('IS_TABLEVIEW')}")
            print(f"Data Records: {len(result['response'].get('data', []))}")
        
        return result.get('status') == 'success'
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query_examples():
    """Test examples endpoint"""
    print("\n" + "="*80)
    print("📚 Testing Query Examples")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/api/query/examples?limit=3")
        print(f"✅ Status: {response.status_code}")
        result = response.json()
        
        print(f"Examples Available: {result.get('total')}")
        for i, ex in enumerate(result.get('examples', []), 1):
            print(f"\nExample {i}: {ex.get('prompt')}")
            print(f"Query: {json.dumps(ex.get('mongo_query'), indent=2)}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_logs():
    """Check if logs are being created"""
    print("\n" + "="*80)
    print("📋 Checking Log File")
    print("="*80)
    
    import os
    
    log_file = "logs/app.log"
    
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"✅ Log file exists: {log_file}")
        print(f"File size: {file_size} bytes")
        
        # Show last 10 lines
        print(f"\nLast 10 log entries:")
        print("-" * 80)
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"Error reading log: {e}")
        
        return True
    else:
        print(f"⚠️  Log file not found: {log_file}")
        return False


def main():
    print("\n" + "="*80)
    print("🧪 UNIFIED LOGGING & MONGODB QUERY SYSTEM TEST")
    print("="*80)
    
    # Check if server is running
    print("\n⏳ Checking if server is running...")
    for i in range(5):
        try:
            requests.get(f"{API_BASE}/")
            print("✅ Server is running!")
            break
        except:
            if i < 4:
                print(f"⏳ Attempt {i+1}/5... waiting...")
                time.sleep(1)
            else:
                print("❌ Server is not running. Start it with: python main.py")
                return
    
    # Run tests
    results = {
        "Health Check": test_health(),
        "Query Generation": test_query_generate(),
        "Query Execution": test_query_execute(),
        "Query Examples": test_query_examples(),
        "Log File": check_logs(),
    }
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} | {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    print("\n" + "="*80)
    print("📝 NEXT STEPS")
    print("="*80)
    print("""
1. Check logs/app.log to see complete pipeline logging
2. Try different queries in POST /api/query/execute
3. Monitor MongoDB query generation accuracy
4. Track performance in the PIPELINE PERFORMANCE SUMMARY section
5. View all logs with: tail -f logs/app.log
    """)


if __name__ == "__main__":
    main()
