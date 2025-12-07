"""
Test script for GitHub gathering.

Tests gathering candidate data from GitHub, focusing on README analysis
and extracting actual technical content.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integrations.github_api import GitHubAPIClient
from backend.orchestration.outbound_gatherer import OutboundGatherer


async def test_github_service():
    """Test GitHub API client and gathering."""
    
    print("=" * 60)
    print("Testing GitHub Gathering Service")
    print("=" * 60)
    print()
    
    # Test with vinayakvadoothker
    github_handle = "vinayakvadoothker"
    
    try:
        # Test 1: GitHub API client
        print("1. Testing GitHub API client...")
        github_client = GitHubAPIClient()
        
        print(f"   Getting profile for {github_handle}...")
        profile = await github_client.get_user_profile(github_handle)
        print(f"   ✅ Profile: {profile.get('name') or 'N/A'} ({profile.get('login')})")
        bio = profile.get('bio') or 'N/A'
        print(f"      Bio: {bio[:100] if bio != 'N/A' else bio}")
        print(f"      Public repos: {profile.get('public_repos', 0)}")
        print()
        
        # Test 2: Get repos
        print("2. Getting repositories...")
        repos = await github_client.get_user_repos(github_handle, max_repos=20)
        print(f"   ✅ Retrieved {len(repos)} repos")
        
        if repos:
            top_repo = repos[0]
            print(f"   Top repo: {top_repo.get('name')} ({top_repo.get('stargazers_count', 0)} stars)")
            desc = top_repo.get('description') or 'N/A'
            print(f"      Description: {desc[:100] if desc != 'N/A' else desc}")
            print(f"      Language: {top_repo.get('language') or 'N/A'}")
            print()
        
        # Test 3: Get README
        if repos:
            test_repo = repos[0]
            repo_name = test_repo.get('name')
            owner = test_repo.get('owner', {}).get('login', github_handle)
            
            print(f"3. Getting README for {repo_name}...")
            readme = await github_client.get_repo_readme(owner, repo_name)
            
            if readme:
                print(f"   ✅ README retrieved ({len(readme)} chars)")
                print(f"   Preview: {readme[:200]}...")
            else:
                print(f"   ⚠️  No README found")
            print()
        
        # Test 4: Full gathering with OutboundGatherer
        print("4. Testing full gathering with OutboundGatherer...")
        gatherer = OutboundGatherer()
        
        print(f"   Gathering profile for {github_handle}...")
        candidate_profile = await gatherer.gather_and_save_from_github(github_handle)
        
        if candidate_profile:
            print(f"   ✅ Profile gathered and saved!")
            print(f"      ID: {candidate_profile.get('id')}")
            print(f"      Name: {candidate_profile.get('name')}")
            print(f"      Repos analyzed: {len(candidate_profile.get('repos', []))}")
            print(f"      Skills: {len(candidate_profile.get('skills', []))}")
            print(f"      Domains: {len(candidate_profile.get('domains', []))}")
            print(f"      Experience: {candidate_profile.get('experience_years', 0)} years")
            print(f"      Level: {candidate_profile.get('expertise_level', 'N/A')}")
            print(f"      Projects: {len(candidate_profile.get('projects', []))}")
            
            # Show sample skills and domains
            skills = candidate_profile.get('skills', [])
            if skills:
                print(f"      Sample skills: {', '.join(skills[:5])}")
            
            domains = candidate_profile.get('domains', [])
            if domains:
                print(f"      Domains: {', '.join(domains[:5])}")
            
            # Show sample projects
            projects = candidate_profile.get('projects', [])
            if projects:
                print(f"      Sample projects:")
                for proj in projects[:3]:
                    print(f"        - {proj.get('name', 'N/A')}: {proj.get('description', 'N/A')[:80]}")
            
            # Show analytics
            stats = candidate_profile.get('github_stats', {})
            if stats:
                print(f"      Total stars: {stats.get('total_stars', 0)}")
                print(f"      Languages: {len(stats.get('languages', {}))}")
        else:
            print("   ❌ Failed to gather profile")
        
        print()
        
        # Cleanup
        await github_client.close()
        await gatherer.close()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_github_service())

