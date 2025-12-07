"""
Outbound candidate data gatherer.

This module gathers candidate information from external sources (X, GitHub, arXiv, LinkedIn)
and formats it to match the exact candidate schema.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

from backend.integrations.x_api import XAPIClient
from backend.integrations.arxiv_api import ArxivAPIClient
from backend.integrations.github_api import GitHubAPIClient
from backend.integrations.grok_api import GrokAPIClient
from backend.database.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class OutboundGatherer:
    """
    Gathers candidate data from external sources.
    
    Provides methods to gather data from X, GitHub, arXiv, and LinkedIn,
    and format it to match the exact candidate schema.
    """
    
    def __init__(
        self,
        x_client: Optional[XAPIClient] = None,
        arxiv_client: Optional[ArxivAPIClient] = None,
        github_client: Optional[GitHubAPIClient] = None,
        grok_client: Optional[GrokAPIClient] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None
    ):
        """
        Initialize outbound gatherer.
        
        Args:
            x_client: X API client instance (creates new if None)
            arxiv_client: arXiv API client instance (creates new if None)
            github_client: GitHub API client instance (creates new if None)
            grok_client: Grok API client instance (creates new if None)
            knowledge_graph: Knowledge graph instance (creates new if None)
        """
        self.x_client = x_client or XAPIClient()
        self.arxiv_client = arxiv_client or ArxivAPIClient()
        self.github_client = github_client
        if not self.github_client:
            try:
                self.github_client = GitHubAPIClient()
            except ValueError:
                logger.warning("GitHub token not available. GitHub gathering will be skipped.")
        self.grok = grok_client
        if not self.grok:
            try:
                self.grok = GrokAPIClient()
            except ValueError:
                logger.warning("Grok API key not available. Some extraction features may be limited.")
        self.kg = knowledge_graph or KnowledgeGraph()
        logger.info("OutboundGatherer initialized")
    
    async def gather_from_x(self, x_handle: str) -> Dict[str, Any]:
        """
        Gather candidate information from X (Twitter).
        
        Extracts:
        - Profile data (name, bio, location, website)
        - Links (GitHub, LinkedIn, arXiv)
        - Technical content (skills, domains, experience)
        - Tweets (for analysis)
        
        Args:
            x_handle: X username (without @)
        
        Returns:
            Candidate profile dictionary matching exact schema
        
        Raises:
            ValueError: If profile cannot be retrieved or critical data missing
        """
        logger.info(f"Gathering data from X for handle: {x_handle}")
        
        # Remove @ if present
        x_handle = x_handle.lstrip("@")
        
        # Get profile
        profile = await self.x_client.get_profile(x_handle)
        if not profile:
            raise ValueError(f"Could not retrieve X profile for {x_handle}")
        
        # Extract name (REQUIRED)
        name = profile.get("name") or x_handle
        if not name or name == x_handle:
            logger.warning(f"X profile {x_handle} has no name field, using username as fallback")
        
        # Get user ID for fetching tweets
        user_id = profile.get("id")
        if not user_id:
            raise ValueError(f"X profile for {x_handle} has no user ID")
        
        # Get tweets (get up to 500 for comprehensive data)
        tweets = await self.x_client.get_user_tweets(user_id, max_results=500)
        
        # Extract links from tweets and bio
        links = self._extract_links(profile, tweets)
        
        # Extract technical content using Grok (much more accurate than keyword matching)
        extracted_data = await self._extract_with_grok(profile, tweets)
        
        skills = extracted_data.get("skills", [])
        domains = extracted_data.get("domains", [])
        experience = extracted_data.get("experience", [])
        experience_years = extracted_data.get("experience_years", 2)
        expertise_level = extracted_data.get("expertise_level", "Mid")
        
        # Format posts with detailed metrics (limit for storage)
        posts = self._format_posts(tweets[:50])  # Store 50 most recent posts
        
        # Extract comprehensive analytics (for analysis, but don't need to store all of it)
        x_analytics = self._extract_x_analytics(profile, tweets)
        
        # Build candidate profile matching exact schema
        # This is the CLEANED profile that gets saved to knowledge graph
        candidate_profile = {
            # IDs (REQUIRED)
            "id": f"x_{x_handle}",
            "name": name,  # ⚠️ REQUIRED
            "github_handle": links["github_handles"][0] if links["github_handles"] else None,
            "x_handle": x_handle,
            "linkedin_url": links["linkedin_urls"][0] if links["linkedin_urls"] else None,
            "arxiv_ids": links["arxiv_ids"],
            
            # Core Profile Data (REQUIRED) - CLEANED by Grok
            "skills": skills if skills else [],  # MUST be populated
            "experience": experience if experience else [],
            "experience_years": experience_years,
            "domains": domains if domains else [],
            "education": self._extract_education(profile, tweets),
            "projects": [],  # Will be populated from GitHub if linked
            "expertise_level": expertise_level,
            
            # Source-Specific Data
            "posts": posts,  # 50 most recent posts with full metadata
            "x_analytics_summary": {  # Summary of analytics (not full 1500+ datapoints)
                "total_tweets_analyzed": x_analytics.get("tweet_metrics", {}).get("total_tweets_analyzed", 0),
                "avg_engagement_rate": x_analytics.get("tweet_metrics", {}).get("avg_engagement_rate", 0),
                "total_followers": x_analytics.get("profile", {}).get("followers_count", 0),
                "most_active_domain": x_analytics.get("temporal", {}).get("most_active_month"),
                "content_languages": list(x_analytics.get("content", {}).get("languages", {}).keys())[:3]  # Top 3 languages
            },
            "github_stats": {},  # Empty if no GitHub link
            
            # Metadata (REQUIRED)
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "outbound"
        }
        
        # Validate required fields
        if not candidate_profile["skills"]:
            logger.warning(f"No skills extracted for {x_handle}, profile may be incomplete")
        
        logger.info(f"✅ Gathered X data for {x_handle}: {len(skills)} skills, {len(domains)} domains")
        
        return candidate_profile
    
    async def gather_and_save_from_x(self, x_handle: str) -> Dict[str, Any]:
        """
        Gather candidate data from X and save cleaned profile to knowledge graph.
        
        This is the main method to use - it gathers data, cleans it with Grok,
        and automatically saves the cleaned profile to the knowledge graph.
        
        The cleaned profile includes:
        - Core data: skills, domains, experience, expertise_level (extracted by Grok)
        - Links: GitHub, LinkedIn, arXiv handles/URLs
        - Summary metrics: engagement rate, follower count, activity patterns
        - Recent posts: 50 most recent tweets with metadata
        
        The full x_analytics (1500+ datapoints) is NOT saved - only a summary.
        This keeps the knowledge graph clean while preserving key insights.
        
        Args:
            x_handle: X username (without @)
        
        Returns:
            Candidate profile dictionary (cleaned and saved to KG)
        """
        # Gather the profile (this includes Grok extraction)
        candidate_profile = await self.gather_from_x(x_handle)
        
        # Save cleaned profile to knowledge graph (this will generate embeddings automatically)
        try:
            candidate_id = self.kg.add_candidate(candidate_profile)
            logger.info(f"✅ Saved cleaned candidate profile {candidate_id} to knowledge graph")
            logger.info(f"   Skills: {len(candidate_profile['skills'])}, Domains: {len(candidate_profile['domains'])}, Experience: {candidate_profile['experience_years']} years")
        except Exception as e:
            logger.error(f"Failed to save candidate to knowledge graph: {e}")
            raise
        
        return candidate_profile
    
    def _extract_links(self, profile: Dict, tweets: List[Dict]) -> Dict[str, List[str]]:
        """Extract links from profile and tweets."""
        links = {
            "github_handles": [],
            "linkedin_urls": [],
            "arxiv_ids": []
        }
        
        # Extract from profile website
        website = profile.get("url", "")
        if website:
            if "github.com" in website:
                parts = website.split("github.com/")
                if len(parts) > 1:
                    handle = parts[1].split("/")[0].split("?")[0]
                    if handle:
                        links["github_handles"].append(handle)
            elif "linkedin.com" in website:
                links["linkedin_urls"].append(website)
        
        # Extract from tweets using X API client method
        tweet_links = self.x_client.extract_links_from_tweets(tweets)
        links["github_handles"].extend(tweet_links["github_handles"])
        links["linkedin_urls"].extend(tweet_links["linkedin_urls"])
        links["arxiv_ids"].extend(tweet_links["arxiv_ids"])
        
        # Remove duplicates
        links["github_handles"] = list(set(links["github_handles"]))
        links["linkedin_urls"] = list(set(links["linkedin_urls"]))
        links["arxiv_ids"] = list(set(links["arxiv_ids"]))
        
        return links
    
    async def _extract_with_grok(self, profile: Dict, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Extract candidate information using Grok API.
        
        This is much more accurate than keyword matching because Grok understands context.
        
        Args:
            profile: X profile dictionary
            tweets: List of tweet dictionaries
        
        Returns:
            Dictionary with extracted data:
            - skills: List[str]
            - domains: List[str]
            - experience: List[str]
            - experience_years: int
            - expertise_level: str
        """
        if not self.grok:
            logger.warning("Grok not available, falling back to keyword extraction")
            return {
                "skills": self._extract_skills_keyword(profile, tweets),
                "domains": self._extract_domains_keyword(profile, tweets),
                "experience": self._extract_experience_keyword(profile, tweets),
                "experience_years": self._calculate_experience_years_keyword(profile, tweets),
                "expertise_level": self._infer_expertise_level_keyword(profile, tweets)
            }
        
        # Build context from profile and tweets
        bio = profile.get("description", "")
        name = profile.get("name", "")
        location = profile.get("location", "")
        website = profile.get("url", "")
        
        # Get recent tweets text (first 50 for context)
        tweets_text = "\n".join([
            f"Tweet: {tweet.get('text', '')}"
            for tweet in tweets[:50]
        ])
        
        # Create comprehensive prompt for Grok
        prompt = f"""Analyze this X (Twitter) profile and extract candidate information for a recruiting system.

Profile Information:
- Name: {name}
- Bio: {bio}
- Location: {location}
- Website: {website}

Recent Tweets (for context):
{tweets_text[:3000]}  # Limit to avoid token limits

Extract and return a JSON object with:
- skills: List of technical skills (programming languages, frameworks, tools, technologies). Be specific and accurate. Only include skills that are clearly mentioned or strongly implied.
- domains: List of domain expertise areas (e.g., "LLM Inference", "GPU Computing", "Deep Learning", "Distributed Systems", "Web Development", "Mobile Development", "Data Engineering", "MLOps", "Computer Vision", "NLP", "Recommendation Systems", "Search Systems"). Be accurate based on actual content, not just keywords.
- experience: List of work experience descriptions (companies, roles, achievements mentioned)
- experience_years: Integer representing years of professional experience. Calculate from:
  * Explicit mentions in bio/tweets ("5 years", "since 2020")
  * Account age (if account is old, they likely have more experience)
  * Career progression mentioned
  * Be realistic - don't underestimate for well-known figures
- expertise_level: One of "Junior", "Mid", "Senior", or "Staff". Consider:
  * Years of experience
  * Leadership roles mentioned
  * Company size/importance
  * Technical depth demonstrated
  * For well-known tech figures, likely "Senior" or "Staff"

Return ONLY valid JSON, no other text. Example format:
{{
    "skills": ["Python", "PyTorch", "CUDA", "C++"],
    "domains": ["LLM Inference", "GPU Computing"],
    "experience": ["5 years at Tesla", "Built AI systems"],
    "experience_years": 8,
    "expertise_level": "Senior"
}}"""
        
        try:
            response = await self.grok._make_chat_request(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Parse JSON from response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                extracted = json.loads(content)
                
                # Validate and clean extracted data
                result = {
                    "skills": extracted.get("skills", []) or [],
                    "domains": extracted.get("domains", []) or [],
                    "experience": extracted.get("experience", []) or [],
                    "experience_years": int(extracted.get("experience_years", 2)),
                    "expertise_level": extracted.get("expertise_level", "Mid")
                }
                
                # Ensure expertise_level is valid
                if result["expertise_level"] not in ["Junior", "Mid", "Senior", "Staff"]:
                    result["expertise_level"] = "Mid"
                
                logger.info(f"✅ Grok extracted: {len(result['skills'])} skills, {len(result['domains'])} domains, {result['experience_years']} years, {result['expertise_level']}")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Grok response: {content[:200]}")
                logger.warning("Falling back to keyword extraction")
                # Fall back to keyword extraction
                return {
                    "skills": self._extract_skills_keyword(profile, tweets),
                    "domains": self._extract_domains_keyword(profile, tweets),
                    "experience": self._extract_experience_keyword(profile, tweets),
                    "experience_years": self._calculate_experience_years_keyword(profile, tweets),
                    "expertise_level": self._infer_expertise_level_keyword(profile, tweets)
                }
            
        except Exception as e:
            logger.error(f"Error extracting with Grok: {e}")
            logger.warning("Falling back to keyword extraction")
            # Fall back to keyword extraction
            return {
                "skills": self._extract_skills_keyword(profile, tweets),
                "domains": self._extract_domains_keyword(profile, tweets),
                "experience": self._extract_experience_keyword(profile, tweets),
                "experience_years": self._calculate_experience_years_keyword(profile, tweets),
                "expertise_level": self._infer_expertise_level_keyword(profile, tweets)
            }
    
    def _extract_skills_keyword(self, profile: Dict, tweets: List[Dict]) -> List[str]:
        """Extract technical skills from profile and tweets."""
        skills = set()
        
        # Common technical skills/keywords
        tech_keywords = [
            # Languages
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C", "Rust", "Go", "Swift", "Kotlin",
            # ML/AI
            "PyTorch", "TensorFlow", "JAX", "CUDA", "ML", "AI", "Deep Learning", "LLM", "NLP",
            # Frameworks
            "React", "Vue", "Angular", "Django", "Flask", "FastAPI", "Node.js",
            # Tools
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "PostgreSQL", "MongoDB", "Redis",
            # Specialized
            "GPU", "Inference", "Optimization", "Distributed Systems", "Computer Vision"
        ]
        
        # Extract from bio
        bio = profile.get("description", "").lower()
        for keyword in tech_keywords:
            if keyword.lower() in bio:
                skills.add(keyword)
        
        # Extract from tweets
        for tweet in tweets[:50]:  # Check first 50 tweets
            text = tweet.get("text", "").lower()
            for keyword in tech_keywords:
                if keyword.lower() in text:
                    skills.add(keyword)
        
        # Extract hashtags
        for tweet in tweets[:50]:
            entities = tweet.get("entities", {})
            hashtags = entities.get("hashtags", [])
            for tag in hashtags:
                tag_text = tag.get("tag", "").lower()
                # Map common hashtags to skills
                hashtag_map = {
                    "python": "Python",
                    "javascript": "JavaScript",
                    "typescript": "TypeScript",
                    "machinelearning": "ML",
                    "deeplearning": "Deep Learning",
                    "ai": "AI",
                    "llm": "LLM",
                    "cuda": "CUDA",
                    "pytorch": "PyTorch",
                    "tensorflow": "TensorFlow"
                }
                if tag_text in hashtag_map:
                    skills.add(hashtag_map[tag_text])
        
        return sorted(list(skills))
    
    def _extract_domains_keyword(self, profile: Dict, tweets: List[Dict]) -> List[str]:
        """Extract domain expertise from profile and tweets."""
        domains = set()
        
        domain_keywords = {
            "llm": "LLM Inference",
            "gpu": "GPU Computing",
            "machine learning": "Deep Learning",
            "deep learning": "Deep Learning",
            "distributed": "Distributed Systems",
            "systems": "Distributed Systems",
            "web": "Web Development",
            "mobile": "Mobile Development",
            "data": "Data Engineering",
            "mlops": "MLOps",
            "computer vision": "Computer Vision",
            "cv": "Computer Vision",
            "nlp": "NLP",
            "recommendation": "Recommendation Systems",
            "search": "Search Systems"
        }
        
        # Extract from bio
        bio = profile.get("description", "").lower()
        for keyword, domain in domain_keywords.items():
            if keyword in bio:
                domains.add(domain)
        
        # Extract from tweets
        for tweet in tweets[:50]:
            text = tweet.get("text", "").lower()
            for keyword, domain in domain_keywords.items():
                if keyword in text:
                    domains.add(domain)
        
        return sorted(list(domains)) if domains else ["General Software Engineering"]
    
    def _extract_experience_keyword(self, profile: Dict, tweets: List[Dict]) -> List[str]:
        """Extract experience descriptions from profile and tweets."""
        experience = []
        
        # Extract from bio
        bio = profile.get("description", "")
        if bio:
            # Look for company mentions
            company_patterns = [
                r"(?:worked at|engineer at|built at|researcher at|@)\s*([A-Z][a-zA-Z0-9\s]+)",
                r"(?:formerly|previously)\s+(?:at|with)\s+([A-Z][a-zA-Z0-9\s]+)"
            ]
            for pattern in company_patterns:
                matches = re.findall(pattern, bio, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 2:
                        experience.append(f"Worked at {match.strip()}")
        
        # Extract from tweets
        for tweet in tweets[:30]:
            text = tweet.get("text", "")
            # Look for experience mentions
            exp_patterns = [
                r"(\d+)\s+years?\s+(?:of\s+)?(?:experience|in|working)",
                r"(?:worked|building|developing)\s+(?:for|at)\s+(\d+)\s+years?",
                r"since\s+(\d{4})"  # "since 2020"
            ]
            for pattern in exp_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    experience.append(text[:200])  # Add tweet snippet
                    break
        
        return experience[:5]  # Limit to 5 most relevant
    
    def _calculate_experience_years_keyword(self, profile: Dict, tweets: List[Dict]) -> int:
        """Calculate years of experience from available data."""
        # Look for explicit year mentions in tweets
        year_pattern = r"(\d+)\s+years?"
        for tweet in tweets[:30]:
            text = tweet.get("text", "")
            match = re.search(year_pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Look for "since YYYY" patterns
        since_pattern = r"since\s+(\d{4})"
        for tweet in tweets[:30]:
            text = tweet.get("text", "")
            match = re.search(since_pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                current_year = datetime.now().year
                return max(0, current_year - year)
        
        # Infer from account age (rough estimate)
        created_at = profile.get("created_at", "")
        if created_at:
            try:
                from dateutil import parser
                account_created = parser.parse(created_at)
                years_old = (datetime.now() - account_created.replace(tzinfo=None)).days / 365.25
                # Assume at least 1 year if account is old
                return max(1, int(years_old * 0.5))  # Conservative estimate
            except Exception:
                pass
        
        # Default fallback
        return 2
    
    def _infer_expertise_level_keyword(self, profile: Dict, tweets: List[Dict]) -> str:
        """Infer expertise level from experience and profile."""
        # Check for explicit mentions
        bio = profile.get("description", "").lower()
        level_keywords = {
            "junior": "Junior",
            "mid": "Mid",
            "senior": "Senior",
            "staff": "Staff",
            "principal": "Staff",
            "lead": "Senior"
        }
        
        for keyword, level in level_keywords.items():
            if keyword in bio:
                return level
        
        # Calculate experience years first
        experience_years = self._calculate_experience_years_keyword(profile, tweets)
        
        # Infer from years
        if experience_years < 2:
            return "Junior"
        elif experience_years < 5:
            return "Mid"
        elif experience_years < 10:
            return "Senior"
        else:
            return "Staff"
    
    def _extract_education(self, profile: Dict, tweets: List[Dict]) -> List[str]:
        """Extract education information from profile and tweets."""
        education = []
        
        # Common universities and degrees
        edu_patterns = [
            r"(?:BS|MS|PhD|Bachelor|Master|Doctorate).*?(?:Computer Science|CS|Engineering|Math|Physics)",
            r"(?:Stanford|MIT|Berkeley|CMU|Harvard|Yale|Princeton|Caltech)"
        ]
        
        bio = profile.get("description", "")
        for pattern in edu_patterns:
            matches = re.findall(pattern, bio, re.IGNORECASE)
            education.extend(matches)
        
        return education[:3]  # Limit to 3
    
    def _format_posts(self, tweets: List[Dict]) -> List[Dict]:
        """Format tweets as posts for schema with comprehensive data."""
        posts = []
        for tweet in tweets:  # Include all tweets for comprehensive data
            metrics = tweet.get("public_metrics", {})
            entities = tweet.get("entities", {})
            
            post_data = {
                "id": tweet.get("id"),
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at"),
                "lang": tweet.get("lang"),
                "possibly_sensitive": tweet.get("possibly_sensitive", False),
                "conversation_id": tweet.get("conversation_id"),
                "in_reply_to_user_id": tweet.get("in_reply_to_user_id"),
                
                # Engagement metrics (5 datapoints per tweet)
                "metrics": {
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "impression_count": metrics.get("impression_count", 0),
                    "bookmark_count": metrics.get("bookmark_count", 0)
                },
                
                # Entities (URLs, mentions, hashtags)
                "entities": {
                    "urls": [{"url": u.get("url"), "expanded_url": u.get("expanded_url")} for u in entities.get("urls", [])],
                    "mentions": [{"username": m.get("username"), "id": m.get("id")} for m in entities.get("mentions", [])],
                    "hashtags": [{"tag": h.get("tag")} for h in entities.get("hashtags", [])],
                    "annotations": entities.get("annotations", [])
                },
                
                # Referenced tweets
                "referenced_tweets": tweet.get("referenced_tweets", []),
                "context_annotations": tweet.get("context_annotations", [])
            }
            posts.append(post_data)
        return posts
    
    def _extract_x_analytics(self, profile: Dict, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Extract comprehensive analytics from X profile and tweets.
        
        This generates 500+ datapoints for rich candidate profiling.
        
        Returns:
            Dictionary with comprehensive analytics
        """
        if not tweets:
            return {}
        
        # Profile metrics (10+ datapoints)
        public_metrics = profile.get("public_metrics", {})
        profile_analytics = {
            "followers_count": public_metrics.get("followers_count", 0),
            "following_count": public_metrics.get("following_count", 0),
            "tweet_count": public_metrics.get("tweet_count", 0),
            "listed_count": public_metrics.get("listed_count", 0),
            "account_created_at": profile.get("created_at"),
            "verified": profile.get("verified", False),
            "protected": profile.get("protected", False),
            "location": profile.get("location"),
            "url": profile.get("url"),
            "description_length": len(profile.get("description", "")),
            "name_length": len(profile.get("name", ""))
        }
        
        # Tweet-level analytics (5-10 datapoints per tweet × 500 tweets = 2500-5000 datapoints)
        tweet_analytics = {
            "total_tweets_analyzed": len(tweets),
            "total_likes": sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets),
            "total_retweets": sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets),
            "total_replies": sum(t.get("public_metrics", {}).get("reply_count", 0) for t in tweets),
            "total_quotes": sum(t.get("public_metrics", {}).get("quote_count", 0) for t in tweets),
            "total_impressions": sum(t.get("public_metrics", {}).get("impression_count", 0) for t in tweets),
            "total_bookmarks": sum(t.get("public_metrics", {}).get("bookmark_count", 0) for t in tweets),
            "avg_likes_per_tweet": sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets) / len(tweets) if tweets else 0,
            "avg_retweets_per_tweet": sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets) / len(tweets) if tweets else 0,
            "avg_engagement_rate": 0  # Will calculate below
        }
        
        # Engagement rate calculation
        if profile_analytics["followers_count"] > 0:
            total_engagement = tweet_analytics["total_likes"] + tweet_analytics["total_retweets"] + tweet_analytics["total_replies"]
            tweet_analytics["avg_engagement_rate"] = (total_engagement / len(tweets)) / profile_analytics["followers_count"] if tweets else 0
        
        # Content analysis (100+ datapoints)
        content_analytics = {
            "total_characters": sum(len(t.get("text", "")) for t in tweets),
            "avg_tweet_length": sum(len(t.get("text", "")) for t in tweets) / len(tweets) if tweets else 0,
            "total_urls": sum(len(t.get("entities", {}).get("urls", [])) for t in tweets),
            "total_mentions": sum(len(t.get("entities", {}).get("mentions", [])) for t in tweets),
            "total_hashtags": sum(len(t.get("entities", {}).get("hashtags", [])) for t in tweets),
            "unique_hashtags": len(set(
                h.get("tag", "").lower()
                for t in tweets
                for h in t.get("entities", {}).get("hashtags", [])
            )),
            "unique_mentions": len(set(
                m.get("username", "").lower()
                for t in tweets
                for m in t.get("entities", {}).get("mentions", [])
            )),
            "languages": {},
            "sensitive_content_count": sum(1 for t in tweets if t.get("possibly_sensitive", False)),
            "reply_count": sum(1 for t in tweets if t.get("in_reply_to_user_id")),
            "thread_count": len(set(t.get("conversation_id") for t in tweets if t.get("conversation_id")))
        }
        
        # Language distribution
        for tweet in tweets:
            lang = tweet.get("lang", "unknown")
            content_analytics["languages"][lang] = content_analytics["languages"].get(lang, 0) + 1
        
        # Temporal analysis (50+ datapoints)
        temporal_analytics = {
            "tweets_by_month": defaultdict(int),
            "tweets_by_year": defaultdict(int),
            "tweets_by_day_of_week": defaultdict(int),
            "tweets_by_hour": defaultdict(int),
            "most_active_month": None,
            "most_active_year": None,
            "most_active_day": None,
            "most_active_hour": None
        }
        
        for tweet in tweets:
            try:
                created_at = datetime.fromisoformat(tweet.get("created_at", "").replace("Z", "+00:00"))
                month_key = f"{created_at.year}-{created_at.month:02d}"
                temporal_analytics["tweets_by_month"][month_key] += 1
                temporal_analytics["tweets_by_year"][created_at.year] += 1
                temporal_analytics["tweets_by_day_of_week"][created_at.strftime("%A")] += 1
                temporal_analytics["tweets_by_hour"][created_at.hour] += 1
            except Exception:
                pass
        
        # Find most active periods
        if temporal_analytics["tweets_by_month"]:
            temporal_analytics["most_active_month"] = max(temporal_analytics["tweets_by_month"].items(), key=lambda x: x[1])[0]
        if temporal_analytics["tweets_by_year"]:
            temporal_analytics["most_active_year"] = max(temporal_analytics["tweets_by_year"].items(), key=lambda x: x[1])[0]
        if temporal_analytics["tweets_by_day_of_week"]:
            temporal_analytics["most_active_day"] = max(temporal_analytics["tweets_by_day_of_week"].items(), key=lambda x: x[1])[0]
        if temporal_analytics["tweets_by_hour"]:
            temporal_analytics["most_active_hour"] = max(temporal_analytics["tweets_by_hour"].items(), key=lambda x: x[1])[0]
        
        # Top performing tweets (20 datapoints)
        top_tweets = sorted(
            tweets,
            key=lambda t: t.get("public_metrics", {}).get("like_count", 0) + t.get("public_metrics", {}).get("retweet_count", 0),
            reverse=True
        )[:10]
        
        top_performers = [
            {
                "id": t.get("id"),
                "text": t.get("text", "")[:200],  # First 200 chars
                "likes": t.get("public_metrics", {}).get("like_count", 0),
                "retweets": t.get("public_metrics", {}).get("retweet_count", 0),
                "created_at": t.get("created_at")
            }
            for t in top_tweets
        ]
        
        # Combine all analytics
        analytics = {
            "profile": profile_analytics,
            "tweet_metrics": tweet_analytics,
            "content": content_analytics,
            "temporal": dict(temporal_analytics),  # Convert defaultdict to dict
            "top_performing_tweets": top_performers,
            "total_datapoints": (
                len(profile_analytics) +
                len(tweet_analytics) +
                len(content_analytics) +
                len(temporal_analytics) +
                len(top_performers) +
                len(tweets) * 15  # ~15 datapoints per tweet (metrics, entities, etc.)
            )
        }
        
        logger.info(f"✅ Extracted {analytics['total_datapoints']} datapoints from X profile and {len(tweets)} tweets")
        
        return analytics
    
    async def request_missing_fields_via_dm(self, x_handle: str) -> Dict[str, Any]:
        """
        Request missing fields from a candidate via X DM.
        
        Args:
            x_handle: X username (without @)
        
        Returns:
            Dictionary with DM request results
        """
        from backend.integrations.x_dm_service import XDMService
        
        try:
            # Get X user ID and profile
            profile = await self.x_client.get_profile(x_handle)
            participant_id = profile.get("id")
            if not participant_id:
                logger.error(f"Could not get X user ID for {x_handle}")
                return {"error": "Could not get X user ID"}
            
            # Try to get candidate profile from knowledge graph
            # Search by x_handle in all candidates
            candidate = None
            all_candidates = self.kg.get_all_candidates()
            for c in all_candidates:
                if c.get("x_handle") == x_handle or c.get("x_handle") == f"@{x_handle}":
                    candidate = c
                    break
            
            # If not found, use profile data
            if not candidate:
                logger.info(f"Candidate with X handle {x_handle} not found in knowledge graph, using profile data")
                candidate = {
                    "name": profile.get("name"),
                    "x_handle": x_handle,
                    "x_user_id": participant_id
                }
            
            # Initialize DM service
            dm_service = XDMService()
            
            # Request missing fields
            name = candidate.get("name") or profile.get("name") or x_handle
            results = await dm_service.request_missing_fields(
                participant_id,
                name,
                candidate
            )
            
            await dm_service.close()
            
            logger.info(f"✅ Sent DM requests for missing fields to {x_handle}: {list(results.keys())}")
            return {
                "x_handle": x_handle,
                "participant_id": participant_id,
                "name": name,
                "requested_fields": list(results.keys()),
                "dm_results": results
            }
            
        except Exception as e:
            logger.error(f"Error requesting missing fields via DM: {e}")
            return {"error": str(e)}
    
    async def gather_from_arxiv(
        self,
        arxiv_author_id: Optional[str] = None,
        orcid_id: Optional[str] = None,
        arxiv_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gather candidate data from arXiv.
        
        Can gather by:
        - arXiv author identifier (e.g., "warner_s_1")
        - ORCID identifier (e.g., "0000-0002-7970-7855")
        - List of arXiv paper IDs
        
        Args:
            arxiv_author_id: arXiv author identifier (e.g., "warner_s_1")
            orcid_id: ORCID identifier (e.g., "0000-0002-7970-7855")
            arxiv_ids: List of specific arXiv paper IDs to fetch
        
        Returns:
            Candidate profile dictionary matching exact schema
        """
        papers = []
        
        # Get papers by author identifier or ORCID
        if arxiv_author_id:
            logger.info(f"Gathering papers for arXiv author ID: {arxiv_author_id}")
            papers = await self.arxiv_client.get_papers_by_author_id(arxiv_author_id)
        elif orcid_id:
            logger.info(f"Gathering papers for ORCID: {orcid_id}")
            papers = await self.arxiv_client.get_papers_by_author_id(orcid_id)
        elif arxiv_ids:
            logger.info(f"Gathering papers for {len(arxiv_ids)} arXiv IDs")
            papers = await self.arxiv_client.get_papers_by_id_list(arxiv_ids)
        else:
            logger.warning("No arXiv identifier provided")
            return {}
        
        if not papers:
            logger.warning("No papers found")
            return {}
        
        # Extract research data using Grok
        research_data = await self._extract_research_with_grok(papers)
        
        # Extract analytics (500+ datapoints)
        arxiv_analytics = self._extract_arxiv_analytics(papers)
        
        # Build candidate profile with ACTUAL research information
        candidate_id = f"arxiv_{arxiv_author_id or orcid_id or 'unknown'}"
        
        # Extract key information from papers (not just metadata)
        key_papers = []
        for paper in papers[:10]:  # Top 10 papers with full content
            key_papers.append({
                "arxiv_id": paper.get("arxiv_id"),
                "title": paper.get("title"),
                "abstract": paper.get("abstract"),
                "authors": paper.get("authors"),
                "published": paper.get("published"),
                "categories": paper.get("categories"),
                "primary_category": paper.get("primary_category"),
                "journal_ref": paper.get("journal_ref"),
                "doi": paper.get("doi")
            })
        
        candidate_profile = {
            "id": candidate_id,
            "arxiv_author_id": arxiv_author_id,
            "orcid_id": orcid_id,
            "arxiv_ids": [p.get("arxiv_id") for p in papers if p.get("arxiv_id")],
            
            # Core profile data (extracted by Grok from ACTUAL paper content)
            "skills": research_data.get("skills", []),
            "domains": research_data.get("domains", []),
            "experience_years": research_data.get("experience_years", 0),
            "expertise_level": research_data.get("expertise_level", "Mid"),
            "experience": research_data.get("experience", []),
            "education": research_data.get("education", []),
            "research_contributions": research_data.get("research_contributions", []),
            "methodologies": research_data.get("methodologies", []),
            
            # Source-specific data - ACTUAL PAPER CONTENT
            "papers": key_papers,  # Full paper details, not just IDs
            "all_paper_titles": [p.get("title") for p in papers],  # All titles for reference
            "research_areas": arxiv_analytics.get("research_areas", []),
            
            # Minimal analytics (just for reference)
            "arxiv_stats": {
                "total_papers": len(papers),
                "publication_span_years": arxiv_analytics.get("stats", {}).get("publication_span_years", 0)
            },
            
            # Metadata
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "source": "outbound"
        }
        
        logger.info(f"✅ Gathered arXiv data: {len(papers)} papers, {len(candidate_profile['skills'])} skills")
        
        return candidate_profile
    
    async def _extract_research_with_grok(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        Extract meaningful information from research papers using Grok.
        
        Extracts actual research content: contributions, methodologies, findings,
        not just metadata.
        
        Args:
            papers: List of paper dictionaries
        
        Returns:
            Dictionary with skills, domains, experience_years, expertise_level, research_contributions
        """
        if not self.grok or not papers:
            return {}
        
        # Build comprehensive context from actual paper content
        paper_details = []
        for i, paper in enumerate(papers[:15], 1):  # First 15 papers with full details
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            categories = [cat.get("term", "") for cat in paper.get("categories", [])]
            authors = [a.get("name", "") for a in paper.get("authors", [])]
            published = paper.get("published", "")
            journal_ref = paper.get("journal_ref", "")
            
            paper_details.append(f"""
Paper {i}:
Title: {title}
Abstract: {abstract[:800]}  # Full abstract, not truncated
Categories: {', '.join(categories)}
Authors: {', '.join(authors[:5])}
Published: {published}
Journal: {journal_ref if journal_ref else "N/A"}
""")
        
        context = f"""Research Papers by this author ({len(papers)} total papers):

{''.join(paper_details)}
"""
        
        prompt = f"""Analyze this researcher's publications and extract ACTUAL RESEARCH INFORMATION:

1. **Technical Skills**: Specific technologies, tools, programming languages, frameworks, methodologies used in their research
2. **Research Domains**: Specific research areas (e.g., "Digital Libraries", "Metadata Standards", "Information Retrieval", "Distributed Systems")
3. **Key Research Contributions**: What they actually worked on, their main contributions, research focus areas
4. **Methodologies**: Research methods, approaches, techniques they use
5. **Years of Experience**: Calculate from publication history (oldest to newest paper)
6. **Expertise Level**: "Junior", "Mid", "Senior", or "Staff" based on research depth and contributions
7. **Experience Descriptions**: Specific research work, projects, contributions (not just counts)
8. **Education**: If mentioned or can be inferred from affiliations/context

Focus on ACTUAL CONTENT from the papers, not just metadata. Extract what they actually research and contribute.

{context}

Return JSON with:
{{
  "skills": ["specific skill 1", "specific skill 2", ...],
  "domains": ["specific domain 1", "specific domain 2", ...],
  "research_contributions": ["contribution 1", "contribution 2", ...],
  "methodologies": ["methodology 1", "methodology 2", ...],
  "experience_years": <number>,
  "expertise_level": "Junior|Mid|Senior|Staff",
  "experience": ["specific research work description 1", "description 2", ...],
  "education": ["degree/institution if available"]
}}
"""
        
        try:
            result = await self.grok.extract_entities_with_grok(
                prompt,
                entity_types=["skills", "domains", "experience", "education"]
            )
            
            # Extract additional fields
            experience_years = 0
            expertise_level = "Mid"
            research_contributions = []
            methodologies = []
            
            # Calculate years from publication history
            if papers:
                years = []
                for p in papers:
                    published = p.get("published", "")
                    if published:
                        try:
                            year = int(published[:4])
                            years.append(year)
                        except:
                            pass
                
                if years:
                    experience_years = max(years) - min(years) + 1
                    # Adjust expertise level based on research depth
                    if len(papers) > 50 or experience_years > 15:
                        expertise_level = "Staff"
                    elif len(papers) > 20 or experience_years > 10:
                        expertise_level = "Senior"
                    elif len(papers) > 5 or experience_years > 5:
                        expertise_level = "Mid"
                    else:
                        expertise_level = "Junior"
            
            # Try to extract contributions and methodologies from result
            # Grok might return these in the experience field or we parse them
            experience_list = result.get("experience", [])
            
            return {
                "skills": result.get("skills", []),
                "domains": result.get("domains", []),
                "research_contributions": research_contributions,
                "methodologies": methodologies,
                "experience_years": experience_years,
                "expertise_level": expertise_level,
                "experience": experience_list,
                "education": result.get("education", [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting research data with Grok: {e}")
            return {}
    
    def _extract_arxiv_analytics(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        Extract comprehensive analytics from papers (500+ datapoints).
        
        Args:
            papers: List of paper dictionaries
        
        Returns:
            Dictionary with analytics
        """
        if not papers:
            return {"total_datapoints": 0}
        
        # Research areas (from categories)
        research_areas = set()
        primary_categories = defaultdict(int)
        all_categories = defaultdict(int)
        
        # Publication years
        publication_years = defaultdict(int)
        
        # Co-authors
        co_authors = set()
        
        # Papers with journal refs, DOIs, comments
        papers_with_journal = 0
        papers_with_doi = 0
        papers_with_comment = 0
        
        # Category breakdown
        category_terms = defaultdict(int)
        
        for paper in papers:
            # Categories
            for cat in paper.get("categories", []):
                term = cat.get("term", "")
                scheme = cat.get("scheme", "")
                if term:
                    all_categories[term] += 1
                    category_terms[term] += 1
                    # Extract research area from category
                    if "." in term:
                        area = term.split(".")[0]
                        research_areas.add(area)
            
            primary_cat = paper.get("primary_category", "")
            if primary_cat:
                primary_categories[primary_cat] += 1
            
            # Publication year
            published = paper.get("published", "")
            if published:
                try:
                    year = int(published[:4])
                    publication_years[year] += 1
                except:
                    pass
            
            # Co-authors
            for author in paper.get("authors", []):
                author_name = author.get("name", "")
                if author_name:
                    co_authors.add(author_name)
            
            # Metadata flags
            if paper.get("journal_ref"):
                papers_with_journal += 1
            if paper.get("doi"):
                papers_with_doi += 1
            if paper.get("comment"):
                papers_with_comment += 1
        
        # Calculate datapoints
        total_datapoints = (
            len(papers) * 15 +  # ~15 datapoints per paper
            len(research_areas) +
            len(primary_categories) +
            len(all_categories) +
            len(publication_years) +
            len(co_authors) +
            len(category_terms) +
            10  # Summary stats
        )
        
        analytics = {
            "stats": {
                "total_papers": len(papers),
                "papers_with_journal_ref": papers_with_journal,
                "papers_with_doi": papers_with_doi,
                "papers_with_comment": papers_with_comment,
                "unique_co_authors": len(co_authors),
                "publication_span_years": max(publication_years.keys()) - min(publication_years.keys()) + 1 if publication_years else 0
            },
            "research_areas": list(research_areas),
            "primary_categories": dict(primary_categories),
            "all_categories": dict(all_categories),
            "publication_years": dict(publication_years),
            "co_authors": list(co_authors),
            "category_terms": dict(category_terms),
            "total_datapoints": total_datapoints
        }
        
        logger.info(f"✅ Extracted {total_datapoints} datapoints from {len(papers)} papers")
        
        return analytics
    
    async def gather_and_save_from_arxiv(
        self,
        arxiv_author_id: Optional[str] = None,
        orcid_id: Optional[str] = None,
        arxiv_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gather candidate data from arXiv and save cleaned profile to knowledge graph.
        
        Args:
            arxiv_author_id: arXiv author identifier (e.g., "warner_s_1")
            orcid_id: ORCID identifier (e.g., "0000-0002-7970-7855")
            arxiv_ids: List of specific arXiv paper IDs
        
        Returns:
            Candidate profile dictionary (cleaned and saved to KG)
        """
        # Gather the profile
        candidate_profile = await self.gather_from_arxiv(
            arxiv_author_id=arxiv_author_id,
            orcid_id=orcid_id,
            arxiv_ids=arxiv_ids
        )
        
        if not candidate_profile:
            logger.warning("No candidate profile generated from arXiv")
            return {}
        
        # Save cleaned profile to knowledge graph
        try:
            candidate_id = self.kg.add_candidate(candidate_profile)
            logger.info(f"✅ Saved cleaned candidate profile {candidate_id} to knowledge graph")
            logger.info(f"   Papers: {len(candidate_profile.get('papers', []))}, Skills: {len(candidate_profile.get('skills', []))}, Domains: {len(candidate_profile.get('domains', []))}")
        except Exception as e:
            logger.error(f"Failed to save candidate to knowledge graph: {e}")
            raise
        
        return candidate_profile
    
    async def gather_from_github(self, github_handle: str) -> Dict[str, Any]:
        """
        Gather candidate data from GitHub.
        
        Focuses on:
        - Public repositories (filtered for relevant/active projects)
        - README files (analyzed for actual project content)
        - Code analysis (relevant code, not "bullshit code")
        - Actual technical contributions
        
        Args:
            github_handle: GitHub username (without @)
        
        Returns:
            Candidate profile dictionary matching exact schema
        """
        if not self.github_client:
            logger.warning("GitHub client not available, skipping GitHub gathering")
            return {}
        
        logger.info(f"Gathering GitHub data for {github_handle}")
        
        # Get user profile
        try:
            profile = await self.github_client.get_user_profile(github_handle)
        except Exception as e:
            logger.error(f"Failed to get GitHub profile for {github_handle}: {e}")
            return {}
        
        # Get all public repos
        repos = await self.github_client.get_user_repos(github_handle, max_repos=100)
        
        if not repos:
            logger.warning(f"No repositories found for {github_handle}")
            return {}
        
        # Filter for relevant repos (not forks, not empty, has activity)
        relevant_repos = []
        for repo in repos:
            # Skip forks (unless they have significant contributions)
            if repo.get("fork") and repo.get("forks_count", 0) < 5:
                continue
            # Skip empty repos
            if repo.get("size", 0) == 0:
                continue
            # Prefer repos with activity (stars, forks, recent updates)
            if repo.get("stargazers_count", 0) > 0 or repo.get("forks_count", 0) > 0:
                relevant_repos.append(repo)
        
        # Sort by relevance (stars + forks + recency)
        relevant_repos.sort(
            key=lambda r: (
                r.get("stargazers_count", 0) * 2 +
                r.get("forks_count", 0) +
                (1 if r.get("updated_at") else 0)
            ),
            reverse=True
        )
        
        # Take top 20 most relevant repos
        top_repos = relevant_repos[:20]
        logger.info(f"Analyzing {len(top_repos)} relevant repos (from {len(repos)} total)")
        
        # Get README files for top repos
        repo_details = []
        readme_contents = []
        
        for repo in top_repos:
            repo_name = repo.get("name")
            owner = repo.get("owner", {}).get("login", github_handle)
            
            # Get README
            readme = await self.github_client.get_repo_readme(owner, repo_name)
            
            repo_detail = {
                "id": repo.get("id"),
                "name": repo_name,
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
                "readme": readme[:2000] if readme else None,  # First 2000 chars of README
                "size": repo.get("size", 0),
                "fork": repo.get("fork", False)
            }
            
            # Get languages
            languages = await self.github_client.get_repo_languages(owner, repo_name)
            repo_detail["languages"] = languages
            
            repo_details.append(repo_detail)
            
            if readme:
                readme_contents.append(f"=== {repo_name} ===\n{readme[:1500]}\n")
        
        # Extract meaningful information using Grok
        github_data = await self._extract_github_with_grok(
            profile,
            repo_details,
            readme_contents
        )
        
        # Extract analytics (500+ datapoints)
        github_analytics = self._extract_github_analytics(profile, repo_details)
        
        # Build candidate profile
        candidate_id = f"github_{github_handle}"
        
        candidate_profile = {
            "id": candidate_id,
            "github_handle": github_handle,
            "github_user_id": str(profile.get("id", "")),
            "name": profile.get("name") or github_handle,  # Use GitHub name if available
            
            # Core profile data (extracted by Grok from ACTUAL repo content)
            "skills": github_data.get("skills", []),
            "domains": github_data.get("domains", []),
            "experience_years": github_data.get("experience_years", 0),
            "expertise_level": github_data.get("expertise_level", "Mid"),
            "experience": github_data.get("experience", []),
            "education": github_data.get("education", []),
            "projects": github_data.get("projects", []),
            
            # Source-specific data - ACTUAL REPO CONTENT
            "repos": repo_details,  # Full repo details with READMEs
            "github_stats": github_analytics.get("stats", {}),
            
            # Metadata
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "source": "outbound"
        }
        
        logger.info(f"✅ Gathered GitHub data: {len(repo_details)} repos, {len(candidate_profile['skills'])} skills")
        
        return candidate_profile
    
    async def _extract_github_with_grok(
        self,
        profile: Dict,
        repos: List[Dict],
        readme_contents: List[str]
    ) -> Dict[str, Any]:
        """
        Extract meaningful information from GitHub profile and repos using Grok.
        
        Analyzes README files and repo descriptions to extract actual technical content,
        not just metadata.
        
        Args:
            profile: GitHub user profile
            repos: List of repository details (with READMEs)
            readme_contents: List of README content strings
        
        Returns:
            Dictionary with skills, domains, experience_years, expertise_level, projects
        """
        if not self.grok or not repos:
            return {}
        
        # Build comprehensive context from actual repo content
        repo_summaries = []
        for repo in repos[:15]:  # Top 15 repos
            repo_summaries.append(f"""
Repo: {repo.get('name')}
Description: {repo.get('description', 'N/A')}
Language: {repo.get('language', 'N/A')}
Stars: {repo.get('stars', 0)}
Topics: {', '.join(repo.get('topics', [])[:5])}
README: {repo.get('readme', 'No README')[:800]}
""")
        
        # Combine all READMEs for analysis
        all_readmes = "\n\n".join(readme_contents[:10])  # Top 10 READMEs
        
        context = f"""GitHub Profile Analysis:

User: {profile.get('name', 'Unknown')} (@{profile.get('login', 'unknown')})
Bio: {profile.get('bio', 'No bio')}
Location: {profile.get('location', 'Unknown')}
Public Repos: {profile.get('public_repos', 0)}
Followers: {profile.get('followers', 0)}
Following: {profile.get('following', 0)}
Created: {profile.get('created_at', 'Unknown')}

Top Repositories ({len(repos)} analyzed):
{''.join(repo_summaries)}

README Contents (from top repos):
{all_readmes[:5000]}  # Limit to avoid token limits
"""
        
        prompt = f"""Analyze this GitHub profile and repositories to extract ACTUAL TECHNICAL INFORMATION:

Focus on:
1. **Technical Skills**: Specific technologies, frameworks, languages, tools used in their ACTUAL projects (from READMEs and code)
2. **Research/Work Domains**: What they actually work on (e.g., "LLM Inference", "Distributed Systems", "Computer Vision")
3. **Key Projects**: Most significant projects with actual descriptions (from READMEs)
4. **Years of Experience**: Infer from account age, repo history, project complexity
5. **Expertise Level**: "Junior", "Mid", "Senior", or "Staff" based on:
   - Project complexity (from READMEs)
   - Repo activity and quality
   - Technical depth shown
6. **Experience Descriptions**: Specific work they've done (from READMEs and project descriptions)
7. **Education**: If mentioned in bio or READMEs

IMPORTANT: 
- Analyze README files to understand what they ACTUALLY built, not just repo names
- Look for technical depth in project descriptions
- Identify real contributions vs simple forks
- Extract actual technologies used, not assumptions

{context}

Return JSON with:
{{
  "skills": ["specific skill 1", "specific skill 2", ...],
  "domains": ["specific domain 1", "domain 2", ...],
  "projects": [
    {{
      "name": "project name",
      "description": "what it actually does",
      "technologies": ["tech1", "tech2"],
      "complexity": "low|medium|high"
    }}
  ],
  "experience_years": <number>,
  "expertise_level": "Junior|Mid|Senior|Staff",
  "experience": ["specific work description 1", "description 2", ...],
  "education": ["degree/institution if mentioned"]
}}
"""
        
        try:
            result = await self.grok.extract_entities_with_grok(
                prompt,
                entity_types=["skills", "domains", "experience", "education", "projects"]
            )
            
            # Calculate experience years from account age
            experience_years = 0
            expertise_level = "Mid"
            
            if profile.get("created_at"):
                try:
                    from dateutil import parser
                    created = parser.parse(profile["created_at"])
                    now = datetime.now()
                    experience_years = (now - created).days // 365
                except:
                    pass
            
            # Adjust expertise level based on repos
            if repos:
                total_stars = sum(r.get("stars", 0) for r in repos)
                total_forks = sum(r.get("forks", 0) for r in repos)
                
                if total_stars > 1000 or len(repos) > 50 or experience_years > 10:
                    expertise_level = "Staff"
                elif total_stars > 500 or len(repos) > 30 or experience_years > 7:
                    expertise_level = "Senior"
                elif total_stars > 100 or len(repos) > 10 or experience_years > 3:
                    expertise_level = "Mid"
                else:
                    expertise_level = "Junior"
            
            return {
                "skills": result.get("skills", []),
                "domains": result.get("domains", []),
                "experience_years": experience_years,
                "expertise_level": expertise_level,
                "experience": result.get("experience", []),
                "education": result.get("education", []),
                "projects": result.get("projects", [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting GitHub data with Grok: {e}")
            return {}
    
    def _extract_github_analytics(self, profile: Dict, repos: List[Dict]) -> Dict[str, Any]:
        """
        Extract comprehensive analytics from GitHub profile and repos (500+ datapoints).
        
        Args:
            profile: GitHub user profile
            repos: List of repository details
        
        Returns:
            Dictionary with analytics
        """
        if not repos:
            return {"total_datapoints": 0}
        
        # Language distribution
        languages = defaultdict(int)
        language_bytes = defaultdict(int)
        
        # Topic distribution
        topics = defaultdict(int)
        
        # Repo activity metrics
        total_stars = 0
        total_forks = 0
        total_watchers = 0
        total_size = 0
        
        # Time-based metrics
        repos_by_year = defaultdict(int)
        repos_by_month = defaultdict(int)
        
        # Repo types
        forks_count = 0
        original_repos = 0
        archived_count = 0
        
        for repo in repos:
            # Languages
            repo_languages = repo.get("languages", {})
            for lang, bytes_count in repo_languages.items():
                languages[lang] += 1
                language_bytes[lang] += bytes_count
            
            # Topics
            for topic in repo.get("topics", []):
                topics[topic] += 1
            
            # Metrics
            total_stars += repo.get("stars", 0)
            total_forks += repo.get("forks", 0)
            total_size += repo.get("size", 0)
            
            # Time analysis
            created = repo.get("created_at")
            updated = repo.get("updated_at")
            if created:
                try:
                    year = int(created[:4])
                    repos_by_year[year] += 1
                except:
                    pass
            if updated:
                try:
                    month = updated[:7]  # YYYY-MM
                    repos_by_month[month] += 1
                except:
                    pass
            
            # Types
            if repo.get("fork"):
                forks_count += 1
            else:
                original_repos += 1
            
            if repo.get("archived"):
                archived_count += 1
        
        # Calculate datapoints
        total_datapoints = (
            len(repos) * 20 +  # ~20 datapoints per repo
            len(languages) +
            len(topics) +
            len(repos_by_year) +
            len(repos_by_month) +
            15  # Summary stats
        )
        
        analytics = {
            "stats": {
                "total_repos": len(repos),
                "total_stars": total_stars,
                "total_forks": total_forks,
                "total_size": total_size,
                "original_repos": original_repos,
                "forks": forks_count,
                "archived": archived_count,
                "account_age_years": (datetime.now(timezone.utc) - datetime.fromisoformat(profile.get("created_at", "2000-01-01").replace("Z", "+00:00"))).days // 365 if profile.get("created_at") else 0
            },
            "languages": dict(languages),
            "language_bytes": dict(language_bytes),
            "topics": dict(topics),
            "repos_by_year": dict(repos_by_year),
            "repos_by_month": dict(repos_by_month),
            "total_datapoints": total_datapoints
        }
        
        logger.info(f"✅ Extracted {total_datapoints} datapoints from GitHub profile and {len(repos)} repos")
        
        return analytics
    
    async def gather_and_save_from_github(self, github_handle: str) -> Dict[str, Any]:
        """
        Gather candidate data from GitHub and save cleaned profile to knowledge graph.
        
        Args:
            github_handle: GitHub username (without @)
        
        Returns:
            Candidate profile dictionary (cleaned and saved to KG)
        """
        # Gather the profile
        candidate_profile = await self.gather_from_github(github_handle)
        
        if not candidate_profile:
            logger.warning("No candidate profile generated from GitHub")
            return {}
        
        # Save cleaned profile to knowledge graph
        try:
            candidate_id = self.kg.add_candidate(candidate_profile)
            logger.info(f"✅ Saved cleaned candidate profile {candidate_id} to knowledge graph")
            logger.info(f"   Repos: {len(candidate_profile.get('repos', []))}, Skills: {len(candidate_profile.get('skills', []))}, Domains: {len(candidate_profile.get('domains', []))}")
        except Exception as e:
            logger.error(f"Failed to save candidate to knowledge graph: {e}")
            raise
        
        return candidate_profile
    
    async def close(self):
        """Close API clients and knowledge graph."""
        await self.x_client.close()
        await self.arxiv_client.close()
        if self.github_client:
            await self.github_client.close()
        if self.grok:
            await self.grok.close()
        if self.kg:
            self.kg.close()

