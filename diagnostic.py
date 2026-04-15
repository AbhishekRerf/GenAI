#!/usr/bin/env python3
"""
Diagnostic script to check route registration and connection issues
"""

import sys
import asyncio

def check_imports():
    """Check if all imports work"""
    print("🔍 Checking imports...")
    try:
        from main import app
        print("✅ main.py imports OK")
        
        from routes.query import router as query_router
        print(f"✅ query router OK - prefix: {query_router.prefix}, tags: {query_router.tags}")
        
        from utils.db import init_mongodb, mongodb
        print("✅ db module imports OK")
        
        from utils.logger_config import get_logger
        print("✅ logger_config imports OK")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_routes():
    """Check registered routes in the app"""
    print("\n🔍 Checking registered routes...")
    try:
        from main import app
        
        print(f"\nTotal routes: {len(app.routes)}")
        
        for route in app.routes:
            if hasattr(route, "path"):
                method = getattr(route, "methods", ["GET"])[0] if hasattr(route, "methods") else "GET"
                print(f"  {method:6} {route.path}")
        
        # Look specifically for query routes
        query_routes = [r for r in app.routes if hasattr(r, "path") and "/api/query" in r.path]
        
        print(f"\nQuery routes found: {len(query_routes)}")
        for route in query_routes:
            method = getattr(route, "methods", ["GET"])[0] if hasattr(route, "methods") else "GET"
            print(f"  ✅ {method:6} {route.path}")
        
        if not query_routes:
            print("  ⚠️  No /api/query routes found!")
        
        return True
    except Exception as e:
        print(f"❌ Route check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_mongodb():
    """Check if MongoDB connection works"""
    print("\n🔍 Checking MongoDB connection...")
    try:
        from utils.db import init_mongodb, get_mongodb, mongodb
        
        print("  Initializing MongoDB...")
        await init_mongodb()
        
        print("  Getting MongoDB instance...")
        db = await get_mongodb()
        
        if db is None:
            print("  ❌ MongoDB is None!")
            return False
        
        print(f"  ✅ MongoDB connected")
        print(f"  Database: {db}")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"  Collections: {collections}")
        
        return True
    except Exception as e:
        print(f"  ❌ MongoDB check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("🧪 DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Clean up any .pyc and __pycache__
    print("\n🧹 Cleaning cached Python files...")
    import os
    import shutil
    
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                print(f"  Removed {pycache_path}")
            except:
                pass
    
    # Run checks
    results = {}
    
    results["Imports"] = check_imports()
    results["Routes"] = check_routes()
    results["MongoDB"] = asyncio.run(check_mongodb())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {check_name}")
    
    if all(results.values()):
        print("\n✅ All checks passed! Ready to start server.")
        print("\nStart server with: python main.py")
    else:
        print("\n❌ Some checks failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
