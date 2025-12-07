"""
Test script for X DM Service.

Tests sending DMs to request missing candidate information.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integrations.x_dm_service import XDMService
from backend.integrations.x_api import XAPIClient
from backend.orchestration.outbound_gatherer import OutboundGatherer


async def test_dm_service():
    """Test X DM service with @itsvinv."""
    
    print("=" * 60)
    print("Testing X DM Service")
    print("=" * 60)
    print()
    
    x_handle = "itsvinv"  # Test with @itsvinv
    
    try:
        # Initialize services
        print("1. Initializing services...")
        x_client = XAPIClient()
        dm_service = XDMService()
        
        # Get profile to get user ID
        print(f"2. Getting profile for @{x_handle}...")
        profile = await x_client.get_profile(x_handle)
        participant_id = profile.get("id")
        name = profile.get("name", x_handle)
        
        print(f"   ✅ Found: {name} (ID: {participant_id})")
        print()
        
        # Send real DMs to @itsvinv
        print("3. Sending real DMs to @itsvinv...")
        print("   (You'll receive these DMs and can respond to test parsing)")
        print()
        
        # Send resume request
        print("   📧 Sending resume request DM...")
        result = await dm_service.request_resume(participant_id, name)
        if result:
            print(f"   ✅ Resume request DM sent successfully!")
            print(f"      Message ID: {result.get('dm_event_id', 'N/A')}")
        else:
            print(f"   ❌ Failed to send resume request DM")
        print()
        
        # Send arXiv ID request
        print("   📧 Sending arXiv ID request DM...")
        result = await dm_service.request_arxiv_id(participant_id, name)
        if result:
            print(f"   ✅ arXiv ID request DM sent successfully!")
            print(f"      Message ID: {result.get('dm_event_id', 'N/A')}")
        else:
            print(f"   ❌ Failed to send arXiv ID request DM")
        print()
        
        # Send GitHub handle request
        print("   📧 Sending GitHub handle request DM...")
        result = await dm_service.request_github_handle(participant_id, name)
        if result:
            print(f"   ✅ GitHub handle request DM sent successfully!")
            print(f"      Message ID: {result.get('dm_event_id', 'N/A')}")
        else:
            print(f"   ❌ Failed to send GitHub handle request DM")
        print()
        
        # Send phone number request
        print("   📧 Sending phone number request DM...")
        result = await dm_service.request_phone_number(participant_id, name)
        if result:
            print(f"   ✅ Phone number request DM sent successfully!")
            print(f"      Message ID: {result.get('dm_event_id', 'N/A')}")
        else:
            print(f"   ❌ Failed to send phone number request DM")
        print()
        
        # Test using OutboundGatherer integration
        print("4. Testing OutboundGatherer integration...")
        gatherer = OutboundGatherer()
        
        # First, gather profile if not exists
        print(f"   Gathering profile for @{x_handle}...")
        try:
            candidate_profile = await gatherer.gather_and_save_from_x(x_handle)
            print(f"   ✅ Profile gathered and saved")
        except Exception as e:
            print(f"   ⚠️  Profile gathering error (may already exist): {e}")
        
        # Request missing fields
        print(f"   Requesting missing fields via DM...")
        dm_results = await gatherer.request_missing_fields_via_dm(x_handle)
        
        if "error" in dm_results:
            print(f"   ❌ Error: {dm_results['error']}")
        else:
            print(f"   ✅ DM requests sent:")
            print(f"      - X Handle: {dm_results['x_handle']}")
            print(f"      - Participant ID: {dm_results['participant_id']}")
            print(f"      - Name: {dm_results['name']}")
            print(f"      - Requested Fields: {', '.join(dm_results['requested_fields'])}")
        
        print()
        
        # Instructions for testing response parsing
        print("5. Next steps for testing response parsing:")
        print("   - Check your X DMs for the messages sent above")
        print("   - Reply to each DM with the requested information")
        print("   - Then run: python scripts/parse_dm_responses.py @itsvinv")
        print("   - This will parse your responses and update your candidate profile")
        print()
        
        # Cleanup
        await x_client.close()
        await dm_service.close()
        await gatherer.close()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Check X DMs for responses from @itsvinv")
        print("2. Use parse_dm_response() to extract information from replies")
        print("3. Update candidate profiles with extracted data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_dm_service())

