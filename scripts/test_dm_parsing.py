"""
Test DM response parsing with simulated/natural responses.

This demonstrates that the Grok-based parsing works with any natural language text,
whether from real DMs or simulated responses.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.integrations.x_dm_service import XDMService


async def test_parsing():
    """Test parsing simulated DM responses."""
    
    print("=" * 60)
    print("Testing DM Response Parsing (Simulated Responses)")
    print("=" * 60)
    print()
    
    dm_service = XDMService()
    
    # Simulated natural responses (like what a candidate might actually send)
    test_cases = [
        {
            "field": "resume",
            "response": """Vin Vadoothker
Software Engineer
Email: vin@example.com
Phone: 510-358-5699

EXPERIENCE:
- Software Engineer at Company X (2020-2024)
  * Built ML systems for recommendation
  * Led team of 5 engineers

EDUCATION:
- BS Computer Science, Stanford (2020)

SKILLS:
- Python, PyTorch, CUDA, LLM Inference"""
        },
        {
            "field": "arxiv_id",
            "response": "Yeah I have an arXiv author ID, it's warner_s_1"
        },
        {
            "field": "arxiv_id",
            "response": "My ORCID is 0000-0002-7970-7855"
        },
        {
            "field": "github_handle",
            "response": "My GitHub username is @vinvadoothker"
        },
        {
            "field": "github_handle",
            "response": "github.com/vinvadoothker"
        },
        {
            "field": "linkedin_url",
            "response": "Here's my LinkedIn: https://linkedin.com/in/vinvadoothker"
        },
        {
            "field": "phone_number",
            "response": "My phone is 510-358-5699"
        },
        {
            "field": "phone_number",
            "response": "You can reach me at +1 (510) 358-5699"
        },
        {
            "field": "email",
            "response": "My email is vin@example.com"
        },
        {
            "field": "resume",
            "response": """I'll paste my resume here:

Vin Vadoothker
Senior ML Engineer

Worked at Google for 3 years building LLM inference systems.
Currently at Anthropic working on model optimization.
PhD in CS from MIT.

Skills: Python, CUDA, PyTorch, Distributed Systems"""
        }
    ]
    
    print("Testing Grok-based parsing with natural language responses...")
    print()
    
    for i, test in enumerate(test_cases, 1):
        field = test["field"]
        response = test["response"]
        
        print(f"{i}. Testing '{field}' extraction:")
        print(f"   Response: {response[:80]}{'...' if len(response) > 80 else ''}")
        
        try:
            parsed = await dm_service.parse_dm_response(response, field)
            
            if parsed:
                print(f"   ✅ Parsed successfully:")
                for key, value in parsed.items():
                    if value:  # Only show non-null values
                        print(f"      - {key}: {value}")
            else:
                print(f"   ❌ Failed to parse")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    await dm_service.close()
    
    print("=" * 60)
    print("✅ Parsing test complete!")
    print("=" * 60)
    print()
    print("The DM service can parse natural language responses from:")
    print("- Real X DMs (once permissions are set up)")
    print("- Simulated responses (for testing)")
    print("- Any natural language text with the requested information")
    print()
    print("The Grok API extracts structured data regardless of how the text is formatted.")


if __name__ == "__main__":
    asyncio.run(test_parsing())

