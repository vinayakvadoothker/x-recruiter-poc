"""
interview_prep_generator.py - Interview preparation generator using Grok API

This module generates comprehensive interview preparation materials for recruiters
and interviewers, including profile overviews, tailored questions, and focus areas.

Research Paper Citations:
[1] Frazzetto, P., et al. "Graph Neural Networks for Candidate‑Job Matching:
    An Inductive Learning Approach." Data Science and Engineering, 2025.
    - Used for: Profile matching concept (candidate-position alignment)
    - Our adaptation: Using profile alignment to generate relevant interview
      questions and identify focus areas for interview preparation

Our Novel Contribution:
AI-powered interview prep generation: Uses LLM (Grok) to generate tailored
interview questions and focus areas based on candidate profile, position requirements,
team context, and interviewer background. This creates personalized, high-quality
prep materials that help interviewers conduct more effective interviews.

Key functions:
- InterviewPrepGenerator: Main prep generation class
- generate_prep(): Generate complete prep materials (async)
- _summarize_candidate(): Summarize candidate profile
- _summarize_position(): Summarize position requirements
- _summarize_team(): Summarize team context
- _summarize_interviewer(): Summarize interviewer background
- _generate_profile_overview(): Generate combined overview
- _generate_questions(): Generate tailored interview questions
- _generate_focus_areas(): Identify focus areas (strengths, concerns, gaps)

Dependencies:
- backend.database.knowledge_graph: Profile retrieval
- backend.integrations.grok_api: Grok API client for LLM generation
- json: JSON parsing
- logging: Logging
"""

import logging
import json
from typing import Dict, List, Any, Optional
from backend.database.knowledge_graph import KnowledgeGraph
from backend.integrations.grok_api import GrokAPIClient

logger = logging.getLogger(__name__)


class InterviewPrepGenerator:
    """
    Generates interview preparation materials using Grok API.
    
    Creates tailored prep materials including:
    - Profile overviews (candidate, position, team, interviewer)
    - Interview questions (technical, experience, cultural fit)
    - Focus areas (strengths, concerns, gaps to explore)
    """
    
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        grok_client: Optional[GrokAPIClient] = None
    ):
        """
        Initialize interview prep generator.
        
        Args:
            knowledge_graph: Knowledge graph instance (creates new if None)
            grok_client: Grok API client instance (creates new if None)
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        self.grok = grok_client
        if not self.grok:
            try:
                self.grok = GrokAPIClient()
            except ValueError:
                logger.warning("Grok API key not available. Some features may be limited.")
        
        logger.info("Initialized InterviewPrepGenerator")
    
    async def generate_prep(
        self,
        candidate_id: str,
        team_id: str,
        interviewer_id: str,
        position_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete interview prep materials.
        
        Args:
            candidate_id: Candidate identifier
            team_id: Team identifier
            interviewer_id: Interviewer identifier
            position_id: Optional position identifier (if None, uses team's position)
        
        Returns:
            Dictionary with:
            - profile_overview: Combined overview
            - candidate_summary: Candidate summary
            - position_summary: Position summary
            - team_context: Team context
            - interviewer_context: Interviewer background
            - questions: List of interview questions
            - focus_areas: List of focus areas
        
        Raises:
            ValueError: If any profile is missing
        """
        logger.info(f"Generating prep for candidate {candidate_id}, team {team_id}, interviewer {interviewer_id}")
        
        # Retrieve profiles
        candidate = self.kg.get_candidate(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        team = self.kg.get_team(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        
        interviewer = self.kg.get_interviewer(interviewer_id)
        if not interviewer:
            raise ValueError(f"Interviewer {interviewer_id} not found")
        
        # Get position (from team or provided)
        if position_id:
            position = self.kg.get_position(position_id)
        else:
            # Try to get position from team
            position_ids = team.get('position_ids', [])
            if position_ids:
                position = self.kg.get_position(position_ids[0])
            else:
                raise ValueError(f"No position found for team {team_id} and no position_id provided")
        
        if not position:
            raise ValueError(f"Position not found")
        
        logger.info(f"Retrieved all profiles: candidate={candidate.get('id')}, position={position.get('id')}, team={team.get('id')}, interviewer={interviewer.get('id')}")
        
        # Generate summaries
        candidate_summary = await self._summarize_candidate(candidate, position)
        position_summary = await self._summarize_position(position, candidate)
        team_context = await self._summarize_team(team, position)
        interviewer_context = await self._summarize_interviewer(interviewer, candidate, position)
        
        # Generate prep materials
        profile_overview = await self._generate_profile_overview(
            candidate_summary, position_summary, team_context, interviewer_context
        )
        questions = await self._generate_questions(candidate, position, team)
        focus_areas = await self._generate_focus_areas(candidate, position, team)
        
        return {
            "profile_overview": profile_overview,
            "candidate_summary": candidate_summary,
            "position_summary": position_summary,
            "team_context": team_context,
            "interviewer_context": interviewer_context,
            "questions": questions,
            "focus_areas": focus_areas,
            "metadata": {
                "candidate_id": candidate_id,
                "team_id": team_id,
                "interviewer_id": interviewer_id,
                "position_id": position.get('id'),
                "generated_at": self._get_timestamp()
            }
        }
    
    async def _summarize_candidate(self, candidate: Dict, position: Dict) -> str:
        """Summarize candidate profile for interview prep."""
        if not self.grok:
            return self._fallback_candidate_summary(candidate)
        
        skills = candidate.get('skills', [])
        experience = candidate.get('experience', [])
        experience_years = candidate.get('experience_years', 0)
        domains = candidate.get('domains', [])
        projects = candidate.get('projects', [])
        education = candidate.get('education', [])
        
        prompt = f"""Summarize this candidate profile for interview preparation.

Candidate Profile:
- Skills: {', '.join(skills[:10]) if skills else 'Not specified'}
- Experience: {experience_years} years
- Domains: {', '.join(domains) if domains else 'Not specified'}
- Education: {', '.join(education) if education else 'Not specified'}
- Recent Experience: {experience[0] if experience else 'Not specified'}

Position Applied For: {position.get('title', 'Unknown')}
Position Requirements: {', '.join(position.get('required_skills', [])[:5]) if position.get('required_skills') else 'Not specified'}

Generate a concise 3-4 sentence summary focusing on:
1. Key technical strengths relevant to the position
2. Experience level and background
3. Notable projects or achievements
4. How their profile aligns with the position requirements

Return only the summary text, no additional formatting."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.debug(f"Generated candidate summary: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating candidate summary: {e}")
            return self._fallback_candidate_summary(candidate)
    
    async def _summarize_position(self, position: Dict, candidate: Dict) -> str:
        """Summarize position requirements for interview prep."""
        if not self.grok:
            return self._fallback_position_summary(position)
        
        title = position.get('title', 'Unknown')
        required_skills = position.get('required_skills', [])
        experience_level = position.get('experience_level', 'Not specified')
        domain = position.get('domain', 'Not specified')
        description = position.get('description', '')
        
        prompt = f"""Summarize this position for interview preparation.

Position: {title}
Domain: {domain}
Experience Level: {experience_level}
Required Skills: {', '.join(required_skills[:10]) if required_skills else 'Not specified'}
Description: {description[:200] if description else 'Not specified'}

Candidate Profile:
- Skills: {', '.join(candidate.get('skills', [])[:5]) if candidate.get('skills') else 'Not specified'}

Generate a concise 3-4 sentence summary focusing on:
1. Key requirements and must-have skills
2. Experience level expected
3. Domain and context
4. What the role entails

Return only the summary text, no additional formatting."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.debug(f"Generated position summary: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating position summary: {e}")
            return self._fallback_position_summary(position)
    
    async def _summarize_team(self, team: Dict, position: Dict) -> str:
        """Summarize team context for interview prep."""
        if not self.grok:
            return self._fallback_team_summary(team)
        
        name = team.get('name', 'Unknown')
        domain = team.get('domain', 'Not specified')
        current_projects = team.get('current_projects', [])
        expertise_areas = team.get('expertise_areas', [])
        
        prompt = f"""Summarize this team context for interview preparation.

Team: {name}
Domain: {domain}
Expertise Areas: {', '.join(expertise_areas[:5]) if expertise_areas else 'Not specified'}
Current Projects: {', '.join([p.get('name', '') if isinstance(p, dict) else str(p) for p in current_projects[:3]]) if current_projects else 'Not specified'}

Position: {position.get('title', 'Unknown')}

Generate a concise 2-3 sentence summary focusing on:
1. Team's focus and expertise
2. Current projects or initiatives
3. Team culture and working style (if available)

Return only the summary text, no additional formatting."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.debug(f"Generated team summary: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating team summary: {e}")
            return self._fallback_team_summary(team)
    
    async def _summarize_interviewer(self, interviewer: Dict, candidate: Dict, position: Dict) -> str:
        """Summarize interviewer background for interview prep."""
        if not self.grok:
            return self._fallback_interviewer_summary(interviewer)
        
        name = interviewer.get('name', 'Unknown')
        expertise_areas = interviewer.get('expertise_areas', [])
        experience_years = interviewer.get('experience_years', 0)
        role = interviewer.get('role', 'Not specified')
        
        prompt = f"""Summarize this interviewer's background for interview preparation.

Interviewer: {name}
Role: {role}
Experience: {experience_years} years
Expertise Areas: {', '.join(expertise_areas[:5]) if expertise_areas else 'Not specified'}

Candidate Profile:
- Skills: {', '.join(candidate.get('skills', [])[:5]) if candidate.get('skills') else 'Not specified'}
- Experience: {candidate.get('experience_years', 0)} years

Position: {position.get('title', 'Unknown')}

Generate a concise 2-3 sentence summary focusing on:
1. Interviewer's expertise and background
2. What they're likely to focus on in the interview
3. How their expertise relates to the candidate and position

Return only the summary text, no additional formatting."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.debug(f"Generated interviewer summary: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating interviewer summary: {e}")
            return self._fallback_interviewer_summary(interviewer)
    
    async def _generate_profile_overview(
        self,
        candidate_summary: str,
        position_summary: str,
        team_context: str,
        interviewer_context: str
    ) -> str:
        """Generate combined profile overview."""
        if not self.grok:
            return f"{candidate_summary}\n\n{position_summary}\n\n{team_context}\n\n{interviewer_context}"
        
        prompt = f"""Create a comprehensive interview preparation overview by combining these summaries:

Candidate Summary:
{candidate_summary}

Position Summary:
{position_summary}

Team Context:
{team_context}

Interviewer Context:
{interviewer_context}

Generate a cohesive 5-6 sentence overview that:
1. Introduces the candidate and their background
2. Describes the position and requirements
3. Provides team context
4. Notes the interviewer's perspective
5. Sets the stage for the interview

Return only the overview text, no additional formatting."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.debug(f"Generated profile overview: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"Error generating profile overview: {e}")
            return f"{candidate_summary}\n\n{position_summary}\n\n{team_context}\n\n{interviewer_context}"
    
    async def _generate_questions(
        self,
        candidate: Dict,
        position: Dict,
        team: Dict
    ) -> List[Dict[str, str]]:
        """Generate tailored interview questions."""
        if not self.grok:
            return self._fallback_questions(candidate, position)
        
        candidate_skills = candidate.get('skills', [])
        position_skills = position.get('required_skills', [])
        candidate_experience = candidate.get('experience_years', 0)
        position_level = position.get('experience_level', 'Not specified')
        
        prompt = f"""Generate 7-10 tailored interview questions for this candidate and position.

Candidate Profile:
- Skills: {', '.join(candidate_skills[:10]) if candidate_skills else 'Not specified'}
- Experience: {candidate_experience} years
- Domains: {', '.join(candidate.get('domains', [])[:3]) if candidate.get('domains') else 'Not specified'}

Position Requirements:
- Title: {position.get('title', 'Unknown')}
- Required Skills: {', '.join(position_skills[:10]) if position_skills else 'Not specified'}
- Experience Level: {position_level}
- Domain: {position.get('domain', 'Not specified')}

Team Context:
- Domain: {team.get('domain', 'Not specified')}
- Expertise: {', '.join(team.get('expertise_areas', [])[:3]) if team.get('expertise_areas') else 'Not specified'}

Generate questions across these categories:
1. Technical (3-4 questions): Deep dive into key skills
2. Experience (2-3 questions): Past projects and achievements
3. Problem-solving (1-2 questions): How they approach challenges
4. Cultural fit (1-2 questions): Team collaboration and values

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "category": "Technical" | "Experience" | "Problem-solving" | "Cultural fit",
    "question": "<question text>",
    "rationale": "<why this question matters>"
  }},
  ...
]

Do not include any explanation, only the JSON array."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            questions = json.loads(content)
            logger.info(f"Generated {len(questions)} interview questions")
            return questions
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._fallback_questions(candidate, position)
    
    async def _generate_focus_areas(
        self,
        candidate: Dict,
        position: Dict,
        team: Dict
    ) -> List[Dict[str, Any]]:
        """Generate focus areas (strengths, concerns, gaps)."""
        if not self.grok:
            return self._fallback_focus_areas(candidate, position)
        
        candidate_skills = candidate.get('skills', [])
        position_skills = position.get('required_skills', [])
        candidate_experience = candidate.get('experience_years', 0)
        position_level = position.get('experience_level', 'Not specified')
        
        # Identify gaps
        missing_skills = set(position_skills) - set(candidate_skills)
        matching_skills = set(candidate_skills) & set(position_skills)
        
        prompt = f"""Identify 4-6 focus areas for this interview.

Candidate Profile:
- Skills: {', '.join(candidate_skills[:10]) if candidate_skills else 'Not specified'}
- Experience: {candidate_experience} years
- Domains: {', '.join(candidate.get('domains', [])[:3]) if candidate.get('domains') else 'Not specified'}

Position Requirements:
- Required Skills: {', '.join(position_skills[:10]) if position_skills else 'Not specified'}
- Experience Level: {position_level}

Analysis:
- Matching Skills: {', '.join(list(matching_skills)[:5]) if matching_skills else 'None'}
- Missing Skills: {', '.join(list(missing_skills)[:5]) if missing_skills else 'None'}

Generate focus areas identifying:
1. Strengths to highlight (2-3 areas)
2. Concerns to probe (1-2 areas)
3. Gaps to explore (1-2 areas)

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "area": "<focus area name>",
    "type": "strength" | "concern" | "gap",
    "description": "<why this matters>",
    "questions_to_ask": ["<question 1>", "<question 2>"],
    "rationale": "<why focus on this>"
  }},
  ...
]

Do not include any explanation, only the JSON array."""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            focus_areas = json.loads(content)
            logger.info(f"Generated {len(focus_areas)} focus areas")
            return focus_areas
        except Exception as e:
            logger.error(f"Error generating focus areas: {e}")
            return self._fallback_focus_areas(candidate, position)
    
    # Fallback methods (when Grok is unavailable)
    def _fallback_candidate_summary(self, candidate: Dict) -> str:
        """Fallback candidate summary."""
        skills = ', '.join(candidate.get('skills', [])[:5]) or 'Not specified'
        exp_years = candidate.get('experience_years', 0)
        return f"Candidate with {exp_years} years of experience. Key skills: {skills}."
    
    def _fallback_position_summary(self, position: Dict) -> str:
        """Fallback position summary."""
        title = position.get('title', 'Unknown')
        skills = ', '.join(position.get('required_skills', [])[:5]) or 'Not specified'
        return f"Position: {title}. Required skills: {skills}."
    
    def _fallback_team_summary(self, team: Dict) -> str:
        """Fallback team summary."""
        name = team.get('name', 'Unknown')
        domain = team.get('domain', 'Not specified')
        return f"Team: {name}. Domain: {domain}."
    
    def _fallback_interviewer_summary(self, interviewer: Dict) -> str:
        """Fallback interviewer summary."""
        name = interviewer.get('name', 'Unknown')
        role = interviewer.get('role', 'Not specified')
        return f"Interviewer: {name}. Role: {role}."
    
    def _fallback_questions(self, candidate: Dict, position: Dict) -> List[Dict[str, str]]:
        """Fallback questions."""
        return [
            {
                "category": "Technical",
                "question": f"Tell me about your experience with {position.get('required_skills', ['relevant technologies'])[0] if position.get('required_skills') else 'relevant technologies'}.",
                "rationale": "Assess technical depth"
            },
            {
                "category": "Experience",
                "question": "Walk me through a challenging project you've worked on.",
                "rationale": "Understand problem-solving approach"
            }
        ]
    
    def _fallback_focus_areas(self, candidate: Dict, position: Dict) -> List[Dict[str, Any]]:
        """Fallback focus areas."""
        return [
            {
                "area": "Technical Skills",
                "type": "strength",
                "description": "Verify alignment with position requirements",
                "questions_to_ask": ["What technologies have you used?", "Tell me about your experience."],
                "rationale": "Core requirement"
            }
        ]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Close knowledge graph connection."""
        self.kg.close()

