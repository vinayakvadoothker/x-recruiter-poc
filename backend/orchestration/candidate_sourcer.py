"""
Candidate sourcing from GitHub and X.

Searches for candidates based on role requirements and extracts candidate data.
"""

import logging
from typing import List, Dict, Optional
from backend.integrations.github_api import GitHubAPIClient
from backend.integrations.grok_api import GrokAPIClient
from backend.integrations.x_api import XAPIClient

logger = logging.getLogger(__name__)


class CandidateSourcer:
    """
    Sources candidates from GitHub and X based on role requirements.
    
    Extracts candidate profiles, analyzes repositories, and ranks candidates.
    """
    
    def __init__(
        self,
        github_client: Optional[GitHubAPIClient] = None,
        grok_client: Optional[GrokAPIClient] = None,
        x_client: Optional[XAPIClient] = None
    ):
        """
        Initialize candidate sourcer with API clients.
        
        Args:
            github_client: GitHub API client instance
            grok_client: Grok API client instance
            x_client: X API client instance (optional)
        """
        self.github = github_client or GitHubAPIClient()
        self.grok = grok_client or GrokAPIClient()
        self.x = x_client or XAPIClient()
    
    async def source_candidates(
        self,
        role_description: str,
        max_candidates: int = 50
    ) -> List[Dict]:
        """
        Source candidates from GitHub and X based on role description.
        
        Args:
            role_description: Text description of the role and requirements
            max_candidates: Maximum number of candidates to return
        
        Returns:
            List of candidate dictionaries with profile data, skills, etc.
        """
        candidates = []
        
        # Source from GitHub
        github_candidates = await self.source_from_github(role_description, max_candidates)
        candidates.extend(github_candidates)
        
        # Source from X (stub for now)
        x_candidates = await self.source_from_x(role_description)
        candidates.extend(x_candidates)
        
        # Remove duplicates based on github_handle
        seen_handles = set()
        unique_candidates = []
        for candidate in candidates:
            handle = candidate.get('github_handle')
            if handle and handle not in seen_handles:
                seen_handles.add(handle)
                unique_candidates.append(candidate)
        
        logger.info(f"Sourced {len(unique_candidates)} unique candidates")
        return unique_candidates[:max_candidates]
    
    async def source_from_github(
        self,
        role_description: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Source candidates from GitHub.
        
        Args:
            role_description: Role description text
            max_results: Maximum number of candidates to return
        
        Returns:
            List of candidate dictionaries
        """
        try:
            # Extract key terms from role using Grok
            role_entities = await self.grok.extract_entities_with_grok(
                role_description,
                entity_types=['skills']
            )
            
            # Extract skills and languages from role
            skills = role_entities.get('skills', [])
            languages = self._extract_languages_from_skills(skills)
            
            # Search GitHub users
            query_parts = []
            if languages:
                # Search by primary language
                query_parts.append(f"language:{languages[0]}")
            
            # Add skill-related topics
            topics = self._extract_topics_from_skills(skills)
            
            # Build search query
            search_query = " ".join(query_parts) if query_parts else "developer"
            
            users = await self.github.search_users(
                query=search_query,
                language=languages[0] if languages else None,
                topics=topics[:3] if topics else None,
                per_page=min(max_results, 100)
            )
            
            # Process each user
            candidates = []
            for user in users[:max_results]:
                try:
                    username = user.get('login')
                    if not username:
                        continue
                    
                    candidate = await self.extract_candidate_data(username)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.warning(f"Error processing user {username}: {e}")
                    continue
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error sourcing from GitHub: {e}")
            return []
    
    async def source_from_x(
        self,
        role_description: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Source candidates from X (Twitter).
        
        Args:
            role_description: Role description text
            max_results: Maximum number of candidates to return
        
        Returns:
            List of candidate dictionaries (empty for now - stub)
        
        Note: This is a stub - X API integration not yet implemented
        """
        # TODO: Implement when X API is available
        logger.info("X sourcing not yet implemented - returning empty list")
        return []
    
    async def extract_candidate_data(self, github_username: str) -> Optional[Dict]:
        """
        Extract comprehensive candidate data from GitHub profile.
        
        Args:
            github_username: GitHub username
        
        Returns:
            Candidate dictionary with profile data, repos, skills, etc.
        """
        try:
            # Get user profile
            profile = await self.github.get_user_profile(github_username)
            
            # Get user repositories
            repos = await self.github.get_user_repos(github_username, per_page=20)
            
            # Extract skills from repositories
            repo_texts = []
            languages_used = set()
            
            for repo in repos:
                # Collect repository information
                repo_info = {
                    'name': repo.get('name', ''),
                    'description': repo.get('description', ''),
                    'language': repo.get('language', ''),
                    'topics': repo.get('topics', [])
                }
                repo_texts.append(f"{repo_info['name']}: {repo_info['description']}")
                
                if repo_info['language']:
                    languages_used.add(repo_info['language'])
                
                # Get detailed language stats
                owner = profile.get('login', '')
                repo_name = repo.get('name', '')
                if owner and repo_name:
                    lang_stats = await self.github.get_repo_languages(owner, repo_name)
                    languages_used.update(lang_stats.keys())
            
            # Combine profile and repo information for entity extraction
            candidate_text = f"""
            Profile: {profile.get('bio', '')}
            Company: {profile.get('company', '')}
            Location: {profile.get('location', '')}
            
            Repositories:
            {' '.join(repo_texts[:10])}
            """
            
            # Extract entities using Grok
            entities = await self.grok.extract_entities_with_grok(
                candidate_text,
                entity_types=['skills', 'experience', 'education', 'projects']
            )
            
            # Build candidate dictionary
            candidate = {
                'github_handle': github_username,
                'x_handle': None,  # Will be populated if found
                'profile_data': {
                    'name': profile.get('name', ''),
                    'bio': profile.get('bio', ''),
                    'company': profile.get('company', ''),
                    'location': profile.get('location', ''),
                    'followers': profile.get('followers', 0),
                    'public_repos': profile.get('public_repos', 0),
                    'created_at': profile.get('created_at', ''),
                    'avatar_url': profile.get('avatar_url', '')
                },
                'repos': repos[:10],  # Top 10 repos
                'skills': entities.get('skills', []) + list(languages_used),
                'experience': entities.get('experience', []),
                'education': entities.get('education', []),
                'projects': entities.get('projects', [])
            }
            
            return candidate
            
        except Exception as e:
            logger.error(f"Error extracting candidate data for {github_username}: {e}")
            return None
    
    async def rank_candidates(
        self,
        candidates: List[Dict],
        role_description: str
    ) -> List[Dict]:
        """
        Rank candidates based on role requirements.
        
        Args:
            candidates: List of candidate dictionaries
            role_description: Role description text
        
        Returns:
            Ranked list of candidates (sorted by relevance)
        
        Note: This is a basic implementation. Will use Vin's graph similarity later.
        """
        # Extract role requirements
        role_entities = await self.grok.extract_entities_with_grok(
            role_description,
            entity_types=['skills']
        )
        required_skills = set(skill.lower() for skill in role_entities.get('skills', []))
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            candidate_skills = set(skill.lower() for skill in candidate.get('skills', []))
            
            # Calculate match score (simple keyword matching)
            matching_skills = required_skills.intersection(candidate_skills)
            match_score = len(matching_skills) / len(required_skills) if required_skills else 0.0
            
            # Add score to candidate
            candidate['match_score'] = match_score
            candidate['matching_skills'] = list(matching_skills)
            scored_candidates.append(candidate)
        
        # Sort by match score (descending)
        ranked = sorted(scored_candidates, key=lambda x: x.get('match_score', 0), reverse=True)
        
        return ranked
    
    def _extract_languages_from_skills(self, skills: List[str]) -> List[str]:
        """
        Extract programming languages from skills list.
        
        Args:
            skills: List of skill strings
        
        Returns:
            List of programming language names
        """
        common_languages = [
            'python', 'javascript', 'java', 'typescript', 'go', 'rust', 'c++', 'c#',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'c', 'cuda'
        ]
        
        languages = []
        skills_lower = [s.lower() for s in skills]
        
        for lang in common_languages:
            if lang in skills_lower or any(lang in skill for skill in skills_lower):
                languages.append(lang.capitalize())
        
        return languages
    
    def _extract_topics_from_skills(self, skills: List[str]) -> List[str]:
        """
        Extract GitHub topics from skills list.
        
        Args:
            skills: List of skill strings
        
        Returns:
            List of topic keywords for GitHub search
        """
        common_topics = [
            'machine-learning', 'deep-learning', 'ai', 'nlp', 'computer-vision',
            'tensorflow', 'pytorch', 'transformer', 'llm', 'inference',
            'distributed-systems', 'kubernetes', 'docker', 'microservices',
            'react', 'vue', 'angular', 'nodejs', 'django', 'flask', 'fastapi'
        ]
        
        topics = []
        skills_lower = [s.lower() for s in skills]
        
        for topic in common_topics:
            if topic in skills_lower or any(topic in skill for skill in skills_lower):
                topics.append(topic)
        
        return topics

