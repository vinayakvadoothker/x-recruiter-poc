"""
arXiv API client for candidate data gathering.

This module provides integration with arXiv API for gathering
candidate research papers, author information, and extracting
research areas and expertise.
"""

import os
import logging
import urllib.parse
from typing import List, Dict, Optional
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv

from backend.integrations.api_utils import retry_with_backoff, handle_api_error

load_dotenv()
logger = logging.getLogger(__name__)

# XML namespaces
ATOM_NS = "{http://www.w3.org/2005/Atom}"
OPENSEARCH_NS = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivAPIClient:
    """
    Client for interacting with arXiv API.
    
    Supports:
    - Author identifier lookup (e.g., https://arxiv.org/a/warner_s_1)
    - ORCID identifier lookup (e.g., https://arxiv.org/a/0000-0002-7970-7855)
    - Paper search and retrieval
    - Metadata extraction
    """
    
    def __init__(self):
        """Initialize arXiv API client."""
        self.base_url = "http://export.arxiv.org/api"
        self.author_base_url = "https://arxiv.org/a"
        # Follow redirects for author identifier URLs
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        logger.info("ArxivAPIClient initialized")
    
    async def get_papers_by_author_id(self, author_id: str) -> List[Dict]:
        """
        Get all papers by an arXiv author identifier.
        
        Uses the author identifier feed: https://arxiv.org/a/{author_id}
        This returns an Atom feed with all papers by that author.
        
        Args:
            author_id: arXiv author identifier (e.g., "warner_s_1" or ORCID "0000-0002-7970-7855")
        
        Returns:
            List of paper dictionaries with full metadata
        """
        # Try both .atom and .atom2 formats, and also try without extension
        urls_to_try = [
            f"{self.author_base_url}/{author_id}.atom2",  # Combined authors feed (preferred)
            f"{self.author_base_url}/{author_id}.atom",   # Separate authors feed
            f"{self.author_base_url}/{author_id}"         # HTML (will redirect)
        ]
        
        for url in urls_to_try:
            try:
                response = await retry_with_backoff(
                    self._make_get_request,
                    url=url
                )
                
                # Check if we got XML (Atom feed)
                if response.strip().startswith('<?xml') or '<feed' in response:
                    # Parse Atom XML
                    papers = self._parse_atom_feed(response)
                    if papers:
                        logger.info(f"Retrieved {len(papers)} papers for author {author_id}")
                        return papers
                
            except Exception as e:
                logger.debug(f"Failed to get papers from {url}: {e}")
                continue
        
        logger.warning(f"No papers found for author {author_id} (tried {len(urls_to_try)} URL formats)")
        return []
    
    async def get_papers_by_author_name(self, author_name: str, max_results: int = 100) -> List[Dict]:
        """
        Get papers by author name using search.
        
        Args:
            author_name: Author name (e.g., "Simeon Warner")
            max_results: Maximum number of results (default: 100, max: 2000 per request)
        
        Returns:
            List of paper dictionaries
        """
        # Replace spaces with underscores for arXiv search
        author_search = author_name.replace(" ", "_")
        search_query = f"au:{author_search}"
        
        url = f"{self.base_url}/query"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(max_results, 2000)
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            papers = self._parse_atom_feed(response)
            logger.info(f"Retrieved {len(papers)} papers for author {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error getting papers by author name {author_name}: {e}")
            return []
    
    async def get_papers_by_id_list(self, arxiv_ids: List[str]) -> List[Dict]:
        """
        Get papers by arXiv ID list.
        
        Args:
            arxiv_ids: List of arXiv IDs (e.g., ["2301.12345", "cs/9901002"])
        
        Returns:
            List of paper dictionaries
        """
        if not arxiv_ids:
            return []
        
        # arXiv API accepts comma-delimited list
        id_list = ",".join(arxiv_ids)
        
        url = f"{self.base_url}/query"
        params = {
            "id_list": id_list
        }
        
        try:
            response = await retry_with_backoff(
                self._make_get_request,
                url=url,
                params=params
            )
            
            papers = self._parse_atom_feed(response)
            logger.info(f"Retrieved {len(papers)} papers for {len(arxiv_ids)} IDs")
            return papers
            
        except Exception as e:
            logger.error(f"Error getting papers by ID list: {e}")
            return []
    
    def _parse_atom_feed(self, xml_content: str) -> List[Dict]:
        """
        Parse Atom XML feed and extract paper metadata.
        
        Args:
            xml_content: XML content from arXiv API
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Find all entry elements
            entries = root.findall(f".//{ATOM_NS}entry")
            
            for entry in entries:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            
        except ET.ParseError as e:
            logger.error(f"Error parsing Atom XML: {e}")
        except Exception as e:
            logger.error(f"Error processing Atom feed: {e}")
        
        return papers
    
    def _parse_entry(self, entry: ET.Element) -> Optional[Dict]:
        """
        Parse a single Atom entry element into a paper dictionary.
        
        Args:
            entry: XML entry element
        
        Returns:
            Paper dictionary or None if parsing fails
        """
        try:
            # Extract basic fields
            title_elem = entry.find(f"{ATOM_NS}title")
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
            
            id_elem = entry.find(f"{ATOM_NS}id")
            arxiv_url = id_elem.text if id_elem is not None else ""
            # Extract arXiv ID from URL (e.g., "http://arxiv.org/abs/2301.12345" -> "2301.12345")
            arxiv_id = arxiv_url.replace("http://arxiv.org/abs/", "").replace("https://arxiv.org/abs/", "") if arxiv_url else ""
            
            published_elem = entry.find(f"{ATOM_NS}published")
            published = published_elem.text if published_elem is not None else ""
            
            updated_elem = entry.find(f"{ATOM_NS}updated")
            updated = updated_elem.text if updated_elem is not None else ""
            
            summary_elem = entry.find(f"{ATOM_NS}summary")
            abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
            
            # Extract authors
            authors = []
            author_elems = entry.findall(f"{ATOM_NS}author")
            for author_elem in author_elems:
                name_elem = author_elem.find(f"{ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    author_name = name_elem.text.strip()
                    # Check for affiliation
                    affiliation_elem = author_elem.find(f"{ARXIV_NS}affiliation")
                    affiliation = affiliation_elem.text.strip() if affiliation_elem is not None and affiliation_elem.text else None
                    authors.append({
                        "name": author_name,
                        "affiliation": affiliation
                    })
            
            # Extract categories
            categories = []
            category_elems = entry.findall(f"{ATOM_NS}category")
            for cat_elem in category_elems:
                term = cat_elem.get("term", "")
                scheme = cat_elem.get("scheme", "")
                if term:
                    categories.append({
                        "term": term,
                        "scheme": scheme
                    })
            
            # Primary category
            primary_cat_elem = entry.find(f"{ARXIV_NS}primary_category")
            primary_category = primary_cat_elem.get("term", "") if primary_cat_elem is not None else ""
            
            # Extract links
            links = {}
            link_elems = entry.findall(f"{ATOM_NS}link")
            for link_elem in link_elems:
                rel = link_elem.get("rel", "")
                href = link_elem.get("href", "")
                title = link_elem.get("title", "")
                
                if rel == "alternate":
                    links["abstract"] = href
                elif rel == "related" and title == "pdf":
                    links["pdf"] = href
                elif rel == "related" and title == "doi":
                    links["doi"] = href
            
            # Extract arXiv-specific fields
            comment_elem = entry.find(f"{ARXIV_NS}comment")
            comment = comment_elem.text.strip() if comment_elem is not None and comment_elem.text else None
            
            journal_ref_elem = entry.find(f"{ARXIV_NS}journal_ref")
            journal_ref = journal_ref_elem.text.strip() if journal_ref_elem is not None and journal_ref_elem.text else None
            
            doi_elem = entry.find(f"{ARXIV_NS}doi")
            doi = doi_elem.text if doi_elem is not None else None
            
            paper = {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published,
                "updated": updated,
                "categories": categories,
                "primary_category": primary_category,
                "links": links,
                "comment": comment,
                "journal_ref": journal_ref,
                "doi": doi
            }
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None
    
    async def _make_get_request(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Make a GET request to arXiv API.
        
        Args:
            url: Full URL to request
            params: Query parameters
        
        Returns:
            Response text (XML content)
        """
        response = await self.client.get(url, params=params)
        handle_api_error(response, "arXiv API request failed")
        return response.text
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

