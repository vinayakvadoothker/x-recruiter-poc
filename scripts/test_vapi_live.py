#!/usr/bin/env python3
"""
Live test script for Vapi phone screen integration.

This script:
1. Loads a candidate and position into the knowledge graph
2. Conducts a real phone screen interview via Vapi
3. Shows the results

Usage:
    python scripts/test_vapi_live.py [candidate_id] [position_id]
    
Example:
    python scripts/test_vapi_live.py candidate_0000 position_0000
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.knowledge_graph import KnowledgeGraph
from backend.datasets.dataset_loader import DatasetLoader
from backend.interviews.phone_screen_interviewer import PhoneScreenInterviewer


async def main():
    """Run live Vapi phone screen test."""
    
    print("=" * 80)
    print("VAPI PHONE SCREEN LIVE TEST")
    print("=" * 80)
    print()
    
    # Get candidate and position IDs from command line or use defaults
    candidate_id = sys.argv[1] if len(sys.argv) > 1 else "candidate_0000"
    position_id = sys.argv[2] if len(sys.argv) > 2 else "position_0000"
    
    print(f"Test Configuration:")
    print(f"  Candidate ID: {candidate_id}")
    print(f"  Position ID: {position_id}")
    print()
    
    # Initialize knowledge graph
    print("Step 1: Initializing knowledge graph...")
    kg = KnowledgeGraph()
    
    # Load a few candidates and positions (if not already loaded)
    print("Step 2: Loading test data...")
    loader = DatasetLoader(kg)
    
    # Load just a few for testing
    candidates_loaded = loader.load_candidates(count=10, batch_size=5)
    positions_loaded = loader.load_positions(count=10, batch_size=5)
    
    print(f"  Loaded {candidates_loaded} candidates")
    print(f"  Loaded {positions_loaded} positions")
    print()
    
    # Verify candidate and position exist
    candidate = kg.get_candidate(candidate_id)
    position = kg.get_position(position_id)
    
    if not candidate:
        print(f"❌ ERROR: Candidate {candidate_id} not found!")
        print(f"   Available candidates: {[c['id'] for c in kg.get_all_candidates()][:5]}...")
        return
    
    if not position:
        print(f"❌ ERROR: Position {position_id} not found!")
        print(f"   Available positions: {[p['id'] for p in kg.get_all_positions()][:5]}...")
        return
    
    # Show candidate and position info
    print("Step 3: Test Data Preview")
    print(f"  Candidate: {candidate.get('name', candidate.get('github_handle', 'N/A'))}")
    print(f"    GitHub: {candidate.get('github_handle', 'N/A')}")
    print(f"    Phone: {candidate.get('phone_number', 'N/A')}")
    print(f"    Skills: {', '.join(candidate.get('skills', [])[:5])}")
    print(f"  Position: {position.get('title', 'N/A')}")
    print(f"    Must-haves: {', '.join(position.get('must_haves', [])[:5])}")
    print()
    
    # Confirm before making call
    phone_number = candidate.get('phone_number')
    if not phone_number:
        print(f"❌ ERROR: Candidate {candidate_id} has no phone number!")
        return
    
    print("⚠️  WARNING: This will make a REAL phone call!")
    print(f"   Calling: {phone_number}")
    print(f"   Position: {position.get('title', 'N/A')}")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Test cancelled.")
        return
    
    print()
    print("Step 4: Conducting phone screen interview...")
    print("  This may take 10-15 minutes (waiting for call to complete)...")
    print()
    
    try:
        # Initialize interviewer
        interviewer = PhoneScreenInterviewer(knowledge_graph=kg)
        
        # Conduct phone screen
        result = await interviewer.conduct_phone_screen(
            candidate_id=candidate_id,
            position_id=position_id
        )
        
        print("✅ Phone screen completed!")
        print()
        
        # Display results
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()
        
        print(f"Call ID: {result['call_id']}")
        print()
        
        print("Decision:")
        decision = result['decision']
        print(f"  Result: {decision['decision'].upper()}")
        print(f"  Confidence: {decision['confidence']:.2%}")
        print(f"  Reasoning: {decision.get('reasoning', 'N/A')}")
        print()
        
        print("Extracted Information:")
        extracted = result['extracted_info']
        print(f"  Motivation Score: {extracted.get('motivation_score', 0):.2f}")
        print(f"  Communication Score: {extracted.get('communication_score', 0):.2f}")
        print(f"  Technical Depth: {extracted.get('technical_depth', 0):.2f}")
        print(f"  Cultural Fit: {extracted.get('cultural_fit', 0):.2f}")
        if extracted.get('skills'):
            print(f"  Skills Mentioned: {', '.join(extracted['skills'][:5])}")
        print()
        
        print("Transcript Summary:")
        transcript = result['conversation']
        if transcript.get('summary'):
            print(f"  {transcript['summary']}")
        elif transcript.get('transcript'):
            # Show first 500 chars
            transcript_text = transcript['transcript']
            print(f"  {transcript_text[:500]}...")
        else:
            print("  (No transcript available)")
        print()
        
        # Save results to file
        results_file = Path("vapi_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"✅ Full results saved to: {results_file}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        kg.close()
        print()
        print("Test complete.")


if __name__ == "__main__":
    asyncio.run(main())

