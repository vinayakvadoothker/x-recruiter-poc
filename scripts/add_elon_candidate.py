"""
Script to add an exceptional "next Elon" candidate for Computer Vision Researcher role.
This candidate will pass all exceptional talent filters (0.0001% pass rate).
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.postgres_client import PostgresClient
from backend.database.knowledge_graph import KnowledgeGraph
from backend.orchestration.company_context import get_company_context

def create_elon_candidate():
    """Create an exceptional candidate profile that would pass all filters."""
    
    # Exceptional candidate profile - "Next Elon" for Computer Vision
    elon_candidate = {
        "id": "candidate_elon_001",
        "name": "Dr. Alex Vision",
        "phone_number": "+15103585699",  # Same number for phone screens
        "email": "alex.vision@example.com",
        "github_handle": "alexvision",
        "github_user_id": "123456789",
        "x_handle": "alexvision_cv",
        "x_user_id": "9876543210000000000",
        "linkedin_url": "https://linkedin.com/in/alexvision",
        "arxiv_author_id": "vision_a_1",
        "orcid_id": "0000-0000-0000-9999",
        
        # Core Profile - Computer Vision expertise
        "skills": [
            "PyTorch", "TensorFlow", "CUDA", "C++", "Python", "OpenCV",
            "Computer Vision", "Deep Learning", "Neural Networks", "CNN",
            "Transformer", "Vision Transformer", "Object Detection", "Image Segmentation",
            "3D Vision", "Multi-view Geometry", "SLAM", "Reinforcement Learning"
        ],
        "domains": ["Computer Vision", "Deep Learning", "Research", "ML Systems"],
        "experience_years": 15,
        "expertise_level": "Staff",
        
        # Experience
        "experience": [
            "Led computer vision research at top AI lab for 8 years",
            "Published 75+ papers in top-tier conferences (CVPR, ICCV, NeurIPS)",
            "Built production CV systems serving 100M+ users",
            "Invented novel vision transformer architecture",
            "Open source contributor with 200k+ GitHub stars"
        ],
        
        # Education
        "education": [
            "PhD in Computer Science, Stanford University",
            "MS in Computer Vision, MIT",
            "BS in Computer Science, UC Berkeley"
        ],
        
        # Projects
        "projects": [
            {
                "name": "Vision Transformer Framework",
                "description": "Open source framework for vision transformers",
                "stars": 50000
            },
            {
                "name": "Real-time Object Detection System",
                "description": "Production system for real-time detection",
                "stars": 30000
            }
        ],
        
        # GitHub Data - EXTREMELY HIGH (180k+ stars)
        "repos": [
            {
                "id": "repo_001",
                "name": "vision-transformer",
                "description": "State-of-the-art vision transformer implementation",
                "language": "Python",
                "stars": 50000,
                "forks": 5000,
                "created_at": "2020-01-15T00:00:00",
                "updated_at": "2024-12-01T00:00:00",
                "topics": ["computer-vision", "transformer", "deep-learning"],
                "contributors": ["alexvision"],
                "commits": 2000,
                "lines_of_code": 50000
            },
            {
                "id": "repo_002",
                "name": "cv-detection",
                "description": "Real-time object detection system",
                "language": "C++",
                "stars": 30000,
                "forks": 3000,
                "created_at": "2019-06-10T00:00:00",
                "updated_at": "2024-11-15T00:00:00",
                "topics": ["computer-vision", "object-detection", "cuda"],
                "contributors": ["alexvision"],
                "commits": 1500,
                "lines_of_code": 40000
            },
            {
                "id": "repo_003",
                "name": "3d-vision",
                "description": "3D computer vision algorithms",
                "language": "Python",
                "stars": 25000,
                "forks": 2500,
                "created_at": "2018-03-20T00:00:00",
                "updated_at": "2024-10-20T00:00:00",
                "topics": ["computer-vision", "3d", "geometry"],
                "contributors": ["alexvision"],
                "commits": 1200,
                "lines_of_code": 35000
            },
            {
                "id": "repo_004",
                "name": "slam-system",
                "description": "SLAM system for robotics",
                "language": "C++",
                "stars": 20000,
                "forks": 2000,
                "created_at": "2017-09-05T00:00:00",
                "updated_at": "2024-09-10T00:00:00",
                "topics": ["slam", "robotics", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 1000,
                "lines_of_code": 30000
            },
            {
                "id": "repo_005",
                "name": "cv-utils",
                "description": "Computer vision utilities library",
                "language": "Python",
                "stars": 15000,
                "forks": 1500,
                "created_at": "2016-05-12T00:00:00",
                "updated_at": "2024-08-05T00:00:00",
                "topics": ["computer-vision", "utilities", "opencv"],
                "contributors": ["alexvision"],
                "commits": 800,
                "lines_of_code": 25000
            },
            {
                "id": "repo_006",
                "name": "vision-ml",
                "description": "Machine learning for vision tasks",
                "language": "Python",
                "stars": 10000,
                "forks": 1000,
                "created_at": "2015-11-18T00:00:00",
                "updated_at": "2024-07-15T00:00:00",
                "topics": ["machine-learning", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 600,
                "lines_of_code": 20000
            },
            {
                "id": "repo_007",
                "name": "cv-datasets",
                "description": "Computer vision datasets",
                "language": "Python",
                "stars": 8000,
                "forks": 800,
                "created_at": "2014-08-22T00:00:00",
                "updated_at": "2024-06-20T00:00:00",
                "topics": ["datasets", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 500,
                "lines_of_code": 15000
            },
            {
                "id": "repo_008",
                "name": "vision-benchmarks",
                "description": "Benchmarking tools for vision models",
                "language": "Python",
                "stars": 7000,
                "forks": 700,
                "created_at": "2013-12-10T00:00:00",
                "updated_at": "2024-05-10T00:00:00",
                "topics": ["benchmarks", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 400,
                "lines_of_code": 12000
            },
            {
                "id": "repo_009",
                "name": "cv-training",
                "description": "Training pipelines for vision models",
                "language": "Python",
                "stars": 6000,
                "forks": 600,
                "created_at": "2012-09-15T00:00:00",
                "updated_at": "2024-04-05T00:00:00",
                "topics": ["training", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 350,
                "lines_of_code": 10000
            },
            {
                "id": "repo_010",
                "name": "vision-deploy",
                "description": "Deployment tools for vision models",
                "language": "Python",
                "stars": 5000,
                "forks": 500,
                "created_at": "2011-06-20T00:00:00",
                "updated_at": "2024-03-01T00:00:00",
                "topics": ["deployment", "computer-vision"],
                "contributors": ["alexvision"],
                "commits": 300,
                "lines_of_code": 8000
            }
        ],
        
        "github_stats": {
            "total_stars": 180000,  # EXTREMELY HIGH - exceeds 100k threshold
            "total_repos": 120,
            "languages": ["Python", "C++", "CUDA", "Rust", "Go", "TypeScript", "Julia"],
            "total_commits": 10000,
            "total_contributions": 50000
        },
        
        # arXiv Data - EXTREMELY HIGH (75+ papers)
        "papers": [
            {
                "id": f"paper_{i:04d}",
                "title": f"Breakthrough in Computer Vision: Novel Approach {i+1}",
                "abstract": f"This paper presents a novel approach to computer vision problem {i+1}, achieving state-of-the-art results.",
                "categories": [{"term": "cs.CV"}],
                "published": (datetime.now().replace(year=2020+i%5, month=1+(i%12), day=1)).isoformat(),
                "authors": ["Alex Vision", "Co-Author 1", "Co-Author 2"],
                "arxiv_id": f"2020.1234{i:04d}"
            }
            for i in range(75)  # 75 papers - EXTREMELY HIGH
        ],
        
        # arxiv_ids stored in papers array, not separate column
        
        "research_contributions": [
            "Novel vision transformer architecture",
            "Breakthrough in object detection",
            "Revolutionary 3D vision approach",
            "State-of-the-art SLAM system",
            "New multi-view geometry method",
            "Advanced image segmentation technique",
            "Cutting-edge real-time vision system"
        ],
        
        "research_areas": ["Computer Vision", "Deep Learning", "Neural Networks", "3D Vision", "SLAM", "Object Detection"],
        
        # X Data - EXTREMELY HIGH (1.2M+ followers)
        "posts": [
            {
                "id": f"post_{i}",
                "text": f"Exciting breakthrough in computer vision! New paper on vision transformers. #ComputerVision #AI #DeepLearning",
                "created_at": (datetime.now().replace(day=1+(i%28))).isoformat(),
                "likes": 10000 + i * 100,
                "retweets": 2000 + i * 50,
                "replies": 500 + i * 10
            }
            for i in range(50)
        ],
        
        "x_analytics_summary": {
            "followers_count": 1200000,  # 1.2M followers - EXTREMELY HIGH
            "following_count": 500,
            "tweet_count": 5000,
            "avg_engagement_rate": 0.15,  # 15% engagement - very high
            "verified": True,
            "influence_score": 0.98
        },
        
        # Phone Screen Results - EXTREMELY HIGH scores
        "phone_screen_results": {
            "technical_depth": 0.99,  # Near-perfect
            "problem_solving_ability": 0.97,
            "technical_communication": 0.96,
            "implementation_experience": 0.98,
            "motivation_score": 0.95,
            "communication_score": 0.94,
            "cultural_fit": 0.93
        },
        
        # Additional metadata
        "source": "outbound",
        "data_completeness": 0.99,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    return elon_candidate

def add_elon_candidate_to_db():
    """Add the exceptional candidate to both PostgreSQL and Weaviate."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("ADDING EXCEPTIONAL 'NEXT ELON' CANDIDATE")
    logger.info("=" * 60)
    
    # Get company context
    company_context = get_company_context()
    company_id = company_context.get_company_id()
    
    # Create candidate profile
    candidate = create_elon_candidate()
    candidate_id = candidate["id"]
    
    logger.info(f"Created candidate profile: {candidate['name']} ({candidate_id})")
    logger.info(f"  - arXiv papers: {len(candidate['papers'])}")
    logger.info(f"  - GitHub stars: {candidate['github_stats']['total_stars']:,}")
    logger.info(f"  - X followers: {candidate['x_analytics_summary']['followers_count']:,}")
    logger.info(f"  - Technical depth: {candidate['phone_screen_results']['technical_depth']}")
    
    # Add to PostgreSQL
    logger.info("\n📊 Adding to PostgreSQL...")
    postgres = PostgresClient()
    
    try:
        import json as json_module
        
        # Check if already exists
        existing = postgres.execute_one(
            "SELECT id FROM candidates WHERE id = %s AND company_id = %s",
            (candidate_id, company_id)
        )
        
        if existing:
            logger.info(f"  Candidate {candidate_id} already exists. Updating...")
            # Update existing
            postgres.execute_update(
                """
                UPDATE candidates SET
                    name = %s,
                    phone_number = %s,
                    email = %s,
                    github_handle = %s,
                    github_user_id = %s,
                    x_handle = %s,
                    x_user_id = %s,
                    linkedin_url = %s,
                    arxiv_author_id = %s,
                    orcid_id = %s,
                    skills = %s::jsonb,
                    domains = %s::jsonb,
                    experience_years = %s,
                    expertise_level = %s,
                    experience = %s::jsonb,
                    education = %s::jsonb,
                    projects = %s::jsonb,
                    repos = %s::jsonb,
                    papers = %s::jsonb,
                    github_stats = %s::jsonb,
                    arxiv_stats = %s::jsonb,
                    data_completeness = %s,
                    updated_at = NOW()
                WHERE id = %s AND company_id = %s
                """,
                (
                    candidate["name"],
                    candidate["phone_number"],
                    candidate["email"],
                    candidate["github_handle"],
                    candidate["github_user_id"],
                    candidate["x_handle"],
                    candidate["x_user_id"],
                    candidate["linkedin_url"],
                    candidate["arxiv_author_id"],
                    candidate["orcid_id"],
                    json_module.dumps(candidate["skills"]),
                    json_module.dumps(candidate["domains"]),
                    candidate["experience_years"],
                    candidate["expertise_level"],
                    json_module.dumps(candidate["experience"]),
                    json_module.dumps(candidate["education"]),
                    json_module.dumps(candidate["projects"]),
                    json_module.dumps(candidate["repos"]),
                    json_module.dumps(candidate["papers"]),
                    json_module.dumps(candidate["github_stats"]),
                    json_module.dumps({"paper_count": len(candidate["papers"]), "h_index": 45}),
                    candidate["data_completeness"],
                    candidate_id,
                    company_id
                )
            )
            logger.info("  ✅ Updated in PostgreSQL")
        else:
            # Insert new
            postgres.execute_update(
                """
                INSERT INTO candidates (
                    id, company_id, name, phone_number, email,
                    github_handle, github_user_id, x_handle, x_user_id,
                    linkedin_url, arxiv_author_id, orcid_id,
                    skills, domains, experience_years, expertise_level,
                    experience, education, projects,
                    repos, papers, github_stats, arxiv_stats,
                    source, data_completeness, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s, NOW(), NOW()
                )
                """,
                (
                    candidate_id, company_id,
                    candidate["name"],
                    candidate["phone_number"],
                    candidate["email"],
                    candidate["github_handle"],
                    candidate["github_user_id"],
                    candidate["x_handle"],
                    candidate["x_user_id"],
                    candidate["linkedin_url"],
                    candidate["arxiv_author_id"],
                    candidate["orcid_id"],
                    json_module.dumps(candidate["skills"]),
                    json_module.dumps(candidate["domains"]),
                    candidate["experience_years"],
                    candidate["expertise_level"],
                    json_module.dumps(candidate["experience"]),
                    json_module.dumps(candidate["education"]),
                    json_module.dumps(candidate["projects"]),
                    json_module.dumps(candidate["repos"]),
                    json_module.dumps(candidate["papers"]),
                    json_module.dumps(candidate["github_stats"]),
                    json_module.dumps({"paper_count": len(candidate["papers"]), "h_index": 45}),
                    candidate["source"],
                    candidate["data_completeness"]
                )
            )
            logger.info("  ✅ Inserted into PostgreSQL")
    except Exception as e:
        logger.error(f"  ❌ Error adding to PostgreSQL: {e}", exc_info=True)
        raise
    
    # Add to Knowledge Graph (Weaviate)
    logger.info("\n🔍 Adding to Knowledge Graph (Weaviate)...")
    kg = KnowledgeGraph()
    try:
        kg.add_candidate(candidate)
        logger.info("  ✅ Added to Knowledge Graph")
    except Exception as e:
        logger.warning(f"  ⚠️  Error adding to Knowledge Graph: {e}")
        # Continue even if Weaviate fails
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ EXCEPTIONAL CANDIDATE ADDED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info(f"\nCandidate ID: {candidate_id}")
    logger.info(f"Name: {candidate['name']}")
    logger.info(f"X Handle: @{candidate['x_handle']}")
    logger.info(f"\nThis candidate should pass all exceptional talent filters!")
    logger.info(f"  - 75 arXiv papers (exceeds 50+ threshold)")
    logger.info(f"  - 180,000 GitHub stars (exceeds 100k+ threshold)")
    logger.info(f"  - 1,200,000 X followers (exceeds 500k+ threshold)")
    logger.info(f"  - 0.99 technical depth (exceeds 0.98+ threshold)")
    logger.info(f"\nPerfect match for Computer Vision Researcher position!")

if __name__ == "__main__":
    add_elon_candidate_to_db()

