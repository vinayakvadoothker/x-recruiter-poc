"""
Parse DM responses from a candidate and update their profile.

Usage: python scripts/parse_dm_responses.py <x_handle>
Example: python scripts/parse_dm_responses.py itsvinv
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integrations.x_dm_service import XDMService
from backend.integrations.x_api import XAPIClient
from backend.orchestration.outbound_gatherer import OutboundGatherer
from backend.database.knowledge_graph import KnowledgeGraph


async def parse_and_update(x_handle: str):
    """Parse DM responses and update candidate profile."""
    
    print("=" * 60)
    print(f"Parsing DM Responses for @{x_handle}")
    print("=" * 60)
    print()
    
    try:
        # Initialize services
        x_client = XAPIClient()
        dm_service = XDMService()
        gatherer = OutboundGatherer()
        kg = KnowledgeGraph()
        
        # Get profile
        print(f"1. Getting profile for @{x_handle}...")
        profile = await x_client.get_profile(x_handle)
        participant_id = profile.get("id")
        name = profile.get("name", x_handle)
        
        print(f"   ✅ Found: {name} (ID: {participant_id})")
        print()
        
        # Get candidate from knowledge graph
        print("2. Finding candidate in knowledge graph...")
        all_candidates = kg.get_all_candidates()
        candidate = None
        candidate_id = None
        
        for c in all_candidates:
            if c.get("x_handle") == x_handle or c.get("x_handle") == f"@{x_handle}":
                candidate = c
                candidate_id = c.get("id")
                break
        
        if not candidate:
            print(f"   ⚠️  Candidate not found in knowledge graph")
            print(f"   Creating new profile...")
            candidate_profile = await gatherer.gather_and_save_from_x(x_handle)
            candidate_id = candidate_profile.get("id")
            candidate = candidate_profile
        else:
            print(f"   ✅ Found candidate: {candidate_id}")
        
        print()
        
        # Get DM conversation (this is a simplified version - in production you'd track conversation IDs)
        print("3. Checking for DM responses...")
        print("   (Note: Full implementation requires conversation state tracking)")
        print()
        
        # For now, we'll manually parse responses
        # In production, you'd poll for new messages or use webhooks
        print("4. To parse responses:")
        print("   - Get the DM conversation ID from X API")
        print("   - Retrieve messages from the conversation")
        print("   - Parse each response with Grok")
        print("   - Update candidate profile")
        print()
        
        # Example: Parse a response if you provide it
        if len(sys.argv) > 2:
            response_text = " ".join(sys.argv[2:])
            requested_field = sys.argv[2] if len(sys.argv) > 2 else "resume"
            
            print(f"5. Parsing response for '{requested_field}'...")
            print(f"   Response: {response_text}")
            
            parsed = await dm_service.parse_dm_response(response_text, requested_field)
            
            if parsed:
                print(f"   ✅ Parsed data: {parsed}")
                
                # Update candidate profile
                print(f"6. Updating candidate profile...")
                updates = {}
                
                if "resume_url" in parsed:
                    updates["resume_url"] = parsed["resume_url"]
                if "resume_text" in parsed:
                    updates["resume_text"] = parsed["resume_text"]
                if "arxiv_id" in parsed or "arxiv_author_id" in parsed:
                    updates["arxiv_author_id"] = parsed.get("arxiv_id") or parsed.get("arxiv_author_id")
                if "github_handle" in parsed:
                    updates["github_handle"] = parsed["github_handle"]
                if "linkedin_url" in parsed:
                    updates["linkedin_url"] = parsed["linkedin_url"]
                if "phone_number" in parsed:
                    updates["phone_number"] = parsed["phone_number"]
                if "email" in parsed:
                    updates["email"] = parsed["email"]
                
                if updates:
                    kg.update_candidate(candidate_id, updates)
                    print(f"   ✅ Updated candidate profile with: {list(updates.keys())}")
                else:
                    print(f"   ⚠️  No valid fields to update")
            else:
                print(f"   ❌ Failed to parse response")
        else:
            print("5. Usage:")
            print("   python scripts/parse_dm_responses.py <x_handle> <field> <response_text>")
            print("   Example: python scripts/parse_dm_responses.py itsvinv github_handle 'My GitHub is @username'")
        
        print()
        
        # Cleanup
        await x_client.close()
        await dm_service.close()
        await gatherer.close()
        
        print("=" * 60)
        print("✅ Done!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_dm_responses.py <x_handle> [field] [response_text]")
        print("Example: python scripts/parse_dm_responses.py itsvinv")
        sys.exit(1)
    
    x_handle = sys.argv[1].lstrip("@")
    asyncio.run(parse_and_update(x_handle))

