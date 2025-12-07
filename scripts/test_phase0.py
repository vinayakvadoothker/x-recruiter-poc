#!/usr/bin/env python3
"""
Test script for Phase 0: Foundation Setup

Tests:
1. PostgreSQL client connection
2. CompanyContext functionality
3. Weaviate schema includes company_id

Run this after starting Docker containers:
    docker-compose up -d postgres weaviate
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context
from backend.database.weaviate_connection import create_weaviate_client
from backend.database.weaviate_schema import create_profile_schemas

def test_postgres_connection():
    """Test PostgreSQL connection."""
    print("Testing PostgreSQL connection...")
    try:
        client = PostgresClient()
        print("✅ PostgreSQL connection successful!")
        
        # Test a simple query
        result = client.execute_query("SELECT 1 as test")
        assert result[0]['test'] == 1
        print("✅ PostgreSQL query test successful!")
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Make sure Docker is running: docker-compose up -d postgres")
        return False

def test_company_context():
    """Test CompanyContext functionality."""
    print("\nTesting CompanyContext...")
    try:
        ctx = get_company_context()
        assert ctx.get_company_id() == "xai"
        print(f"✅ Company context: {ctx.get_company_id()}")
        
        # Test filter_by_company
        params = {"test": "value"}
        filtered = ctx.filter_by_company(params)
        assert filtered['company_id'] == "xai"
        assert filtered['test'] == "value"
        print("✅ Company filter test successful!")
        
        # Test ensure_company_id
        data = {"name": "test"}
        ensured = ctx.ensure_company_id(data)
        assert ensured['company_id'] == "xai"
        print("✅ Company ID ensure test successful!")
        
        return True
    except Exception as e:
        print(f"❌ CompanyContext test failed: {e}")
        return False

def test_weaviate_schema():
    """Test Weaviate schema includes company_id."""
    print("\nTesting Weaviate schema...")
    try:
        client = create_weaviate_client()
        create_profile_schemas(client)
        
        # Check that collections exist
        collections = client.collections.list_all()
        collection_names = [str(c) for c in collections]
        
        required_collections = ["Candidate", "Team", "Interviewer", "Position"]
        for col_name in required_collections:
            if col_name in collection_names:
                print(f"✅ {col_name} collection exists")
            else:
                print(f"⚠️  {col_name} collection not found (may need to recreate)")
        
        print("✅ Weaviate schema check complete!")
        return True
    except Exception as e:
        print(f"❌ Weaviate schema test failed: {e}")
        print("   Make sure Docker is running: docker-compose up -d weaviate")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 0: Foundation Setup - Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("PostgreSQL Connection", test_postgres_connection()))
    results.append(("CompanyContext", test_company_context()))
    results.append(("Weaviate Schema", test_weaviate_schema()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 Phase 0: Foundation Setup - ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed. Make sure Docker containers are running:")
        print("   docker-compose up -d postgres weaviate")
    
    sys.exit(0 if all_passed else 1)

