#!/usr/bin/env python3
"""
Test script for X API gathering functionality.

Tests the X API client and outbound gatherer with a real X handle.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.integrations.x_api import XAPIClient
from backend.orchestration.outbound_gatherer import OutboundGatherer


async def test_x_api_client():
    """Test X API client basic functionality."""
    print("=" * 60)
    print("Testing X API Client")
    print("=" * 60)
    
    try:
        client = XAPIClient()
        print("✅ X API client initialized")
        
        # Test with a real handle
        test_handle = "Ishaanbansal77"  # Testing with @Ishaanbansal77
        
        print(f"\n📋 Testing get_profile for: {test_handle}")
        profile = await client.get_profile(test_handle)
        
        if profile:
            print(f"✅ Profile retrieved successfully")
            print(f"   Name: {profile.get('name', 'N/A')}")
            print(f"   Username: {profile.get('username', 'N/A')}")
            print(f"   Bio: {profile.get('description', 'N/A')[:100]}...")
            print(f"   Followers: {profile.get('public_metrics', {}).get('followers_count', 0):,}")
        else:
            print("❌ Profile retrieval returned empty")
            return False
        
        # Test getting tweets
        user_id = profile.get("id")
        if user_id:
            print(f"\n📋 Testing get_user_tweets for user ID: {user_id}")
            tweets = await client.get_user_tweets(user_id, max_results=10)
            print(f"✅ Retrieved {len(tweets)} tweets")
            if tweets:
                print(f"   First tweet: {tweets[0].get('text', '')[:100]}...")
        
        # Test link extraction
        if tweets:
            print(f"\n📋 Testing link extraction from tweets")
            links = client.extract_links_from_tweets(tweets)
            print(f"✅ Extracted links:")
            print(f"   GitHub handles: {links['github_handles']}")
            print(f"   LinkedIn URLs: {len(links['linkedin_urls'])} found")
            print(f"   arXiv IDs: {links['arxiv_ids']}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing X API client: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gather_from_x():
    """Test gather_from_x method."""
    print("\n" + "=" * 60)
    print("Testing gather_from_x()")
    print("=" * 60)
    
    try:
        gatherer = OutboundGatherer()
        
        # Test with a real X handle
        test_handle = "Ishaanbansal77"  # Testing with @Ishaanbansal77
        
        print(f"\n📋 Gathering data from X for: {test_handle}")
        candidate_profile = await gatherer.gather_from_x(test_handle)
        
        if candidate_profile:
            print(f"✅ Candidate profile gathered successfully")
            print(f"\n📊 Profile Summary:")
            print(f"   ID: {candidate_profile.get('id')}")
            print(f"   Name: {candidate_profile.get('name')} ⚠️ REQUIRED")
            print(f"   X Handle: {candidate_profile.get('x_handle')}")
            print(f"   Skills: {len(candidate_profile.get('skills', []))} found")
            print(f"   Domains: {candidate_profile.get('domains', [])}")
            print(f"   Experience Years: {candidate_profile.get('experience_years')}")
            print(f"   Expertise Level: {candidate_profile.get('expertise_level')}")
            print(f"   GitHub Handle: {candidate_profile.get('github_handle', 'None')}")
            print(f"   LinkedIn URL: {candidate_profile.get('linkedin_url', 'None')}")
            print(f"   arXiv IDs: {len(candidate_profile.get('arxiv_ids', []))} found")
            print(f"   Posts: {len(candidate_profile.get('posts', []))} found")
            
            # Validate required fields
            print(f"\n✅ Schema Validation:")
            required_fields = [
                "id", "name", "x_handle", "skills", "experience_years",
                "domains", "expertise_level", "created_at", "updated_at", "source"
            ]
            missing_fields = [field for field in required_fields if field not in candidate_profile or not candidate_profile[field]]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
            else:
                print(f"   ✅ All required fields present")
            
            # Check name field specifically
            if candidate_profile.get("name"):
                print(f"   ✅ Name field present: '{candidate_profile['name']}'")
            else:
                print(f"   ❌ Name field missing (REQUIRED)")
            
            # Save to file for inspection
            output_file = project_root / "test_x_gathering_output.json"
            with open(output_file, "w") as f:
                json.dump(candidate_profile, f, indent=2, default=str)
            print(f"\n💾 Full profile saved to: {output_file}")
            
            await gatherer.close()
            return True
        else:
            print("❌ gather_from_x returned empty profile")
            return False
            
    except Exception as e:
        print(f"❌ Error testing gather_from_x: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing X API Gathering Implementation")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("X_BEARER_TOKEN"):
        print("❌ X_BEARER_TOKEN environment variable not set")
        print("   Please add it to your .env file")
        return
    
    results = []
    
    # Test 1: X API Client
    results.append(await test_x_api_client())
    
    # Test 2: Gather from X
    results.append(await test_gather_from_x())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    if all(results):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

