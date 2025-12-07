"""
Test script for arXiv gathering.

Tests gathering candidate data from arXiv using author identifier and ORCID.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integrations.arxiv_api import ArxivAPIClient
from backend.orchestration.outbound_gatherer import OutboundGatherer


async def test_arxiv_service():
    """Test arXiv API client and gathering."""
    
    print("=" * 60)
    print("Testing arXiv Gathering Service")
    print("=" * 60)
    print()
    
    # Test with Simeon Warner
    # Author ID: warner_s_1
    # ORCID: 0000-0002-7970-7855
    
    try:
        # Test 1: Get papers by author identifier
        print("1. Testing arXiv API client...")
        arxiv_client = ArxivAPIClient()
        
        print("   Testing with author ID: warner_s_1")
        papers = await arxiv_client.get_papers_by_author_id("warner_s_1")
        print(f"   ✅ Retrieved {len(papers)} papers")
        
        if papers:
            print(f"   Sample paper: {papers[0].get('title', 'N/A')[:80]}...")
            print(f"   Authors: {', '.join([a.get('name', '') for a in papers[0].get('authors', [])[:3]])}")
            print(f"   Categories: {', '.join([c.get('term', '') for c in papers[0].get('categories', [])[:3]])}")
        
        print()
        
        # Test 2: Get papers by ORCID
        print("2. Testing with ORCID: 0000-0002-7970-7855")
        papers_orcid = await arxiv_client.get_papers_by_author_id("0000-0002-7970-7855")
        print(f"   ✅ Retrieved {len(papers_orcid)} papers via ORCID")
        print()
        
        # Test 3: Full gathering with OutboundGatherer
        print("3. Testing full gathering with OutboundGatherer...")
        gatherer = OutboundGatherer()
        
        print("   Gathering profile for warner_s_1...")
        candidate_profile = await gatherer.gather_and_save_from_arxiv(
            arxiv_author_id="warner_s_1"
        )
        
        if candidate_profile:
            print(f"   ✅ Profile gathered and saved!")
            print(f"      ID: {candidate_profile.get('id')}")
            print(f"      Papers: {len(candidate_profile.get('papers', []))}")
            print(f"      Skills: {len(candidate_profile.get('skills', []))}")
            print(f"      Domains: {len(candidate_profile.get('domains', []))}")
            print(f"      Experience: {candidate_profile.get('experience_years', 0)} years")
            print(f"      Level: {candidate_profile.get('expertise_level', 'N/A')}")
            print(f"      Research Areas: {', '.join(candidate_profile.get('research_areas', [])[:5])}")
            
            analytics = candidate_profile.get('arxiv_analytics_summary', {})
            print(f"      Total Datapoints: {analytics.get('total_datapoints', 0)}")
            print(f"      Co-authors: {analytics.get('co_authors', 0)}")
        else:
            print("   ❌ Failed to gather profile")
        
        print()
        
        # Test 4: Test with ORCID
        print("4. Testing gathering with ORCID...")
        candidate_profile_orcid = await gatherer.gather_and_save_from_arxiv(
            orcid_id="0000-0002-7970-7855"
        )
        
        if candidate_profile_orcid:
            print(f"   ✅ Profile gathered via ORCID!")
            print(f"      Papers: {len(candidate_profile_orcid.get('papers', []))}")
        else:
            print("   ❌ Failed to gather profile via ORCID")
        
        print()
        
        # Cleanup
        await arxiv_client.close()
        await gatherer.close()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_arxiv_service())

