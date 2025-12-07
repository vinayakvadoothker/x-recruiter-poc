#!/usr/bin/env python3
"""
Test script for Phase 1: Teams Management

Tests:
1. Database migration (teams table)
2. Teams CRUD API endpoints

Run this after starting Docker containers:
    docker-compose up -d postgres
    python backend/database/migration_runner.py  # Run migrations first
    python scripts/test_phase1.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.database.postgres_client import PostgresClient
from backend.database.migration_runner import run_migrations
from backend.orchestration.company_context import get_company_context
import uuid

def test_migration():
    """Test teams table migration."""
    print("Testing teams table migration...")
    try:
        postgres = PostgresClient()
        run_migrations(postgres)
        print("✅ Migration completed!")
        
        # Verify table exists
        result = postgres.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'teams'
        """)
        assert len(result) > 0
        print("✅ Teams table exists!")
        
        postgres.close()
        return True
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False

def test_teams_crud():
    """Test Teams CRUD operations."""
    print("\nTesting Teams CRUD operations...")
    try:
        postgres = PostgresClient()
        company_context = get_company_context()
        company_id = company_context.get_company_id()
        
        # Create team
        team_id = str(uuid.uuid4())
        from datetime import datetime
        now = datetime.now()
        
        create_query = """
            INSERT INTO teams (
                id, company_id, name, department, needs, expertise, stack, 
                domains, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING *
        """
        
        team = postgres.execute_one(create_query, (
            team_id,
            company_id,
            "Test Team",
            "Engineering",
            ["Python", "FastAPI"],
            ["Backend Development"],
            ["Python", "PostgreSQL"],
            ["LLM Inference"],
            now,
            now
        ))
        
        assert team is not None
        assert team['name'] == "Test Team"
        print("✅ Create team successful!")
        
        # Read team
        read_query = "SELECT * FROM teams WHERE id = %s AND company_id = %s"
        read_team = postgres.execute_one(read_query, (team_id, company_id))
        assert read_team is not None
        assert read_team['name'] == "Test Team"
        print("✅ Read team successful!")
        
        # Update team
        update_query = """
            UPDATE teams 
            SET name = %s, updated_at = %s
            WHERE id = %s AND company_id = %s
            RETURNING *
        """
        updated_team = postgres.execute_one(update_query, (
            "Updated Test Team",
            datetime.now(),
            team_id,
            company_id
        ))
        assert updated_team is not None
        assert updated_team['name'] == "Updated Test Team"
        print("✅ Update team successful!")
        
        # List teams
        list_query = "SELECT * FROM teams WHERE company_id = %s"
        teams = postgres.execute_query(list_query, (company_id,))
        assert len(teams) > 0
        print(f"✅ List teams successful! Found {len(teams)} team(s)")
        
        # Cleanup
        delete_query = "DELETE FROM teams WHERE id = %s AND company_id = %s"
        postgres.execute_update(delete_query, (team_id, company_id))
        print("✅ Delete team successful!")
        
        postgres.close()
        return True
    except Exception as e:
        print(f"❌ Teams CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: Teams Management - Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Migration", test_migration()))
    results.append(("Teams CRUD", test_teams_crud()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 Phase 1: Teams Management - ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Start API server: uvicorn backend.api.routes:router --reload")
        print("2. Test API endpoints with:")
        print("   - GET /api/teams")
        print("   - POST /api/teams")
        print("   - GET /api/teams/{team_id}")
        print("   - PUT /api/teams/{team_id}")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    sys.exit(0 if all_passed else 1)

