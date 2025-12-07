"""
vector_db_client.py - Vector database client for storing embeddings

This module provides a Weaviate-based vector database client for storing and
retrieving embeddings for all 4 profile types (candidates, teams, interviewers, positions).

Implementation Rationale:

Why Weaviate over other vector databases:
1. **Self-hosted and free**: No API costs or rate limits for hackathon
   - Alternative: Pinecone (cloud) - Rejected because:
     * API costs for high-volume operations
     * Rate limits could block during demos
     * Requires internet connection
   - Trade-off: Need to run Docker container, but full control

2. **Native vector support**: Built for vector similarity search
   - Alternative: PostgreSQL with pgvector - Rejected because:
     * More complex setup and configuration
     * Less optimized for pure vector operations
     * Weaviate is purpose-built for this use case
   - Trade-off: Less general-purpose, but perfect for our needs

3. **Schema-based organization**: Separate classes for each profile type
   - Alternative: Single class with type field - Rejected because:
     * Harder to query specific profile types
     * Can't set different properties per type
     * Schema validation is weaker
   - Our approach: 4 separate Weaviate classes (Candidate, Team, Interviewer, Position)

4. **Metadata + vectors**: Store both embedding and metadata together
   - Alternative: Separate storage for metadata - Rejected because:
     * Requires joins or multiple queries
     * Data consistency issues
     * More complex code
   - Trade-off: Slightly larger storage, but simpler queries

Design Decisions:
- **Separate classes per profile type**: Better organization and querying
- **Store metadata as properties**: Enables filtering and retrieval without re-querying
- **Use cosine similarity**: Standard for normalized embeddings
- **Batch operations**: Support batch insert for performance
"""

import logging
import json
from typing import List, Dict, Any, Optional
import numpy as np
from backend.database.weaviate_connection import create_weaviate_client
from backend.database.weaviate_schema import create_profile_schemas

logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    Vector database client for storing embeddings and fast similarity search.
    
    Uses Weaviate for vector storage and retrieval. Supports 4 profile types:
    - Candidates: Technical profiles with skills, experience, projects
    - Teams: Team profiles with needs, expertise, culture
    - Interviewers: Interviewer profiles with expertise, success rates
    - Positions: Position profiles with requirements, must-haves
    
    All embeddings are 768-dimensional (from MPNet model) and normalized.
    """
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Weaviate client.
        
        Args:
            url: Weaviate server URL. Defaults to WEAVIATE_URL env var or http://localhost:8080
        
        Raises:
            ConnectionError: If unable to connect to Weaviate
        """
        self.url = url
        self.client = create_weaviate_client(url)
        create_profile_schemas(self.client)
    
    def store_candidate(self, candidate_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """
        Store candidate embedding with metadata.
        
        Args:
            candidate_id: Unique candidate identifier
            embedding: 768-dimensional normalized embedding vector
            metadata: Candidate profile data (skills, experience, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        return self._store("Candidate", candidate_id, embedding, metadata)
    
    def store_team(self, team_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """Store team embedding with metadata."""
        return self._store("Team", team_id, embedding, metadata)
    
    def store_interviewer(self, interviewer_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """Store interviewer embedding with metadata."""
        return self._store("Interviewer", interviewer_id, embedding, metadata)
    
    def store_position(self, position_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """Store position embedding with metadata."""
        return self._store("Position", position_id, embedding, metadata)
    
    def _store(self, class_name: str, profile_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> bool:
        """
        Internal method to store embedding in Weaviate.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Unique profile identifier
            embedding: Normalized embedding vector
            metadata: Profile metadata as dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert embedding to list
            vector = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
            # Convert metadata to JSON string (handle datetime objects)
            def json_serializer(obj):
                """JSON serializer for objects not serializable by default json code"""
                from datetime import datetime
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            metadata_json = json.dumps(metadata, default=json_serializer)
            
            # Get collection and insert
            collection = self.client.collections.get(class_name)
            collection.data.insert(
                properties={
                    "profile_id": profile_id,
                    "metadata": metadata_json
                },
                vector=vector
            )
            
            logger.debug(f"Stored {class_name} profile: {profile_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store {class_name} profile {profile_id}: {e}")
            return False
    
    def search_similar_candidates(self, query_embedding: np.ndarray, top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Search for similar candidates using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector (768-dim, normalized)
            top_k: Number of results to return
        
        Returns:
            List of candidate results with similarity scores and metadata
        """
        return self._search("Candidate", query_embedding, top_k)
    
    def search_similar_teams(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar teams."""
        return self._search("Team", query_embedding, top_k)
    
    def search_similar_interviewers(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Dict[str, Any]]:
        """Search for similar interviewers."""
        return self._search("Interviewer", query_embedding, top_k)
    
    def search_similar_positions(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar positions."""
        return self._search("Position", query_embedding, top_k)
    
    def _search(self, class_name: str, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """
        Internal method to search for similar profiles.
        
        Args:
            class_name: Weaviate collection name
            query_embedding: Query embedding vector
            top_k: Number of results
        
        Returns:
            List of results with profile_id, metadata, and similarity score
        """
        try:
            # Convert embedding to list
            vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
            
            # Get collection and perform vector search
            collection = self.client.collections.get(class_name)
            results = collection.query.near_vector(
                near_vector=vector,
                limit=top_k,
                return_metadata=["distance"]
            )
            
            # Parse results
            parsed_results = []
            for obj in results.objects:
                metadata = json.loads(obj.properties.get("metadata", "{}"))
                distance = obj.metadata.distance if obj.metadata.distance else 0.0
                # Convert distance to similarity (1 - distance for cosine)
                similarity = 1.0 - distance if distance <= 1.0 else 0.0
                
                parsed_results.append({
                    "profile_id": obj.properties.get("profile_id"),
                    "metadata": metadata,
                    "similarity": similarity,
                    "distance": distance
                })
            
            return parsed_results
        except Exception as e:
            logger.error(f"Search failed for {class_name}: {e}")
            return []
    
    def close(self):
        """Close Weaviate connection."""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Closed Weaviate connection")

