#!/usr/bin/env python3
"""
generate_datasets.py - Generate and save sample datasets to JSON files

This script generates sample datasets for all 4 profile types and saves them
to JSON files in the data/ directory. Useful for inspection, debugging, and
sharing datasets without regenerating them each time.

Usage:
    python scripts/generate_datasets.py [--count CANDIDATES TEAMS INTERVIEWERS POSITIONS]
    python scripts/generate_datasets.py --count 100 50 100 80  # Small test dataset
    python scripts/generate_datasets.py  # Full 1,000x scale (default: 15000 8000 15000 12000)

Default counts (1,000x scale):
    - Candidates: 15,000
    - Teams: 8,000
    - Interviewers: 15,000
    - Positions: 12,000
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.datasets import (
    generate_candidates,
    generate_teams,
    generate_interviewers,
    generate_positions
)


def save_datasets(
    candidate_count: int = 15000,
    team_count: int = 8000,
    interviewer_count: int = 15000,
    position_count: int = 12000,
    output_dir: Path = Path("data")
):
    """
    Generate and save all datasets to JSON files.
    
    Args:
        candidate_count: Number of candidates to generate
        team_count: Number of teams to generate
        interviewer_count: Number of interviewers to generate
        position_count: Number of positions to generate
        output_dir: Directory to save JSON files
    """
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print(f"Generating datasets...")
    print(f"  Candidates: {candidate_count}")
    print(f"  Teams: {team_count}")
    print(f"  Interviewers: {interviewer_count}")
    print(f"  Positions: {position_count}")
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # Generate and save candidates
    print("Generating candidates...")
    candidates = list(generate_candidates(candidate_count))
    candidates_file = output_dir / "candidates.json"
    with open(candidates_file, 'w') as f:
        json.dump(candidates, f, indent=2, default=str)
    print(f"  ✅ Saved {len(candidates)} candidates to {candidates_file}")
    
    # Generate and save teams
    print("Generating teams...")
    teams = list(generate_teams(team_count))
    teams_file = output_dir / "teams.json"
    with open(teams_file, 'w') as f:
        json.dump(teams, f, indent=2, default=str)
    print(f"  ✅ Saved {len(teams)} teams to {teams_file}")
    
    # Generate and save interviewers
    print("Generating interviewers...")
    interviewers = list(generate_interviewers(interviewer_count, teams_count=team_count))
    interviewers_file = output_dir / "interviewers.json"
    with open(interviewers_file, 'w') as f:
        json.dump(interviewers, f, indent=2, default=str)
    print(f"  ✅ Saved {len(interviewers)} interviewers to {interviewers_file}")
    
    # Generate and save positions
    print("Generating positions...")
    positions = list(generate_positions(position_count, teams_count=team_count))
    positions_file = output_dir / "positions.json"
    with open(positions_file, 'w') as f:
        json.dump(positions, f, indent=2, default=str)
    print(f"  ✅ Saved {len(positions)} positions to {positions_file}")
    
    # Create metadata file
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "counts": {
            "candidates": len(candidates),
            "teams": len(teams),
            "interviewers": len(interviewers),
            "positions": len(positions),
            "total": len(candidates) + len(teams) + len(interviewers) + len(positions)
        },
        "files": {
            "candidates": str(candidates_file),
            "teams": str(teams_file),
            "interviewers": str(interviewers_file),
            "positions": str(positions_file)
        }
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✅ Saved metadata to {metadata_file}")
    
    print()
    print(f"✅ All datasets generated successfully!")
    print(f"   Total profiles: {metadata['counts']['total']}")
    print(f"   Location: {output_dir.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate and save sample datasets to JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--count',
        nargs=4,
        type=int,
        metavar=('CANDIDATES', 'TEAMS', 'INTERVIEWERS', 'POSITIONS'),
        default=[15000, 8000, 15000, 12000],
        help='Number of profiles to generate for each type (default: 15000 8000 15000 12000 - 1,000x scale)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path("data"),
        help='Output directory for JSON files (default: data/)'
    )
    
    args = parser.parse_args()
    
    candidate_count, team_count, interviewer_count, position_count = args.count
    
    save_datasets(
        candidate_count=candidate_count,
        team_count=team_count,
        interviewer_count=interviewer_count,
        position_count=position_count,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()

