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
from weaviate.util import generate_uuid5
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
        # Schema creation happens automatically, but we don't need to store the result
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
        Internal method to store/update embedding in Weaviate.
        
        Uses deterministic UUIDs based on profile_id to prevent duplicates.
        If a record with the same profile_id exists, it will be skipped (no update).
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Unique profile identifier
            embedding: Normalized embedding vector
            metadata: Profile metadata as dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate deterministic UUID based on profile_id and class_name
            # This ensures the same profile_id always gets the same UUID, preventing duplicates
            # Format: "{class_name}:{profile_id}" to ensure uniqueness across classes
            unique_identifier = f"{class_name}:{profile_id}"
            obj_uuid = generate_uuid5(unique_identifier)
            
            # Get collection
            collection = self.client.collections.get(class_name)
            
            # Check if object already exists in Weaviate
            try:
                existing = collection.query.fetch_object_by_id(uuid=obj_uuid)
                if existing:
                    logger.debug(f"Skipping {class_name} profile {profile_id} - already exists in Weaviate (UUID: {obj_uuid})")
                    return True  # Already exists, consider it successful
            except Exception:
                # Object doesn't exist, continue to insert
                pass
            
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
            
            # Extract company_id from metadata (for multi-tenancy filtering)
            company_id = metadata.get('company_id', 'xai')  # Default to 'xai' for demo
            
            # Insert new object (we already checked it doesn't exist)
            try:
                collection.data.insert(
                    properties={
                        "profile_id": profile_id,
                        "company_id": company_id,
                        "metadata": metadata_json
                    },
                    vector=vector,
                    uuid=obj_uuid
                )
                logger.debug(f"Inserted {class_name} profile: {profile_id} (UUID: {obj_uuid})")
                return True
            except Exception as insert_error:
                # If insert fails, it might be a race condition (another process inserted it)
                # Check again if it exists now
                try:
                    existing = collection.query.fetch_object_by_id(uuid=obj_uuid)
                    if existing:
                        logger.debug(f"{class_name} profile {profile_id} was inserted by another process, skipping")
                        return True
                except Exception:
                    pass
                
                # If it still doesn't exist, log the error
                logger.warning(f"Failed to insert {class_name} profile {profile_id}: {insert_error}")
                return False
            
        except Exception as e:
            logger.warning(f"Failed to store {class_name} profile {profile_id}: {e}")
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
                company_id = obj.properties.get("company_id")
                distance = obj.metadata.distance if obj.metadata.distance else 0.0
                # Convert distance to similarity (1 - distance for cosine)
                similarity = 1.0 - distance if distance <= 1.0 else 0.0
                
                parsed_results.append({
                    "profile_id": obj.properties.get("profile_id"),
                    "company_id": company_id,
                    "metadata": metadata,
                    "similarity": similarity,
                    "distance": distance
                })
            
            return parsed_results
        except Exception as e:
            logger.error(f"Search failed for {class_name}: {e}")
            return []
    
    def get_all_embeddings(self, class_name: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a profile type.
        
        Uses the same pattern as _search - fetch objects via HTTP, then get vectors separately.
        This avoids gRPC requirements and matches our existing search implementation.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            limit: Maximum number of results to return
        
        Returns:
            List of embeddings with profile_id, embedding vector, and metadata
        """
        try:
            collection = self.client.collections.get(class_name)
            parsed_results = []
            
            # Use fetch_objects (HTTP only, same as _search method)
            # This matches our existing pattern and doesn't require gRPC
            results = collection.query.fetch_objects(limit=limit)
            
            for obj in results.objects:
                try:
                    profile_id = obj.properties.get("profile_id")
                    company_id = obj.properties.get("company_id")
                    metadata = json.loads(obj.properties.get("metadata", "{}"))
                    
                    # Fetch vector separately using fetch_object_by_id (HTTP only, no gRPC needed)
                    # This matches the pattern we use in _search method
                    vector = None
                    try:
                        obj_with_vector = collection.query.fetch_object_by_id(
                            uuid=obj.uuid,
                            include_vector=True
                        )
                        if obj_with_vector and hasattr(obj_with_vector, 'vector') and obj_with_vector.vector:
                            if isinstance(obj_with_vector.vector, dict):
                                vector = obj_with_vector.vector.get("default") or next(iter(obj_with_vector.vector.values()), None)
                            elif isinstance(obj_with_vector.vector, list):
                                vector = obj_with_vector.vector
                    except Exception as vec_error:
                        logger.debug(f"Could not fetch vector for {profile_id}: {vec_error}")
                        continue  # Skip this object if we can't get its vector
                    
                    if vector and len(vector) > 0:
                        parsed_results.append({
                            "profile_id": profile_id,
                            "company_id": company_id,
                            "embedding": vector,  # 768-dim vector
                            "metadata": metadata
                        })
                except Exception as e:
                    logger.warning(f"Error parsing object from {class_name}: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(parsed_results)} embeddings from {class_name}")
            return parsed_results
        except Exception as e:
            logger.error(f"Failed to get embeddings from {class_name}: {e}")
            return []
    
    def get_embedding(self, class_name: str, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single embedding by profile_id.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Profile identifier
        
        Returns:
            Dictionary with profile_id, embedding vector, and metadata, or None if not found
        """
        try:
            collection = self.client.collections.get(class_name)
            
            # Generate the same UUID that was used when storing
            unique_identifier = f"{class_name}:{profile_id}"
            obj_uuid = generate_uuid5(unique_identifier)
            
            # Fetch object with vector
            obj = collection.query.fetch_object_by_id(
                uuid=obj_uuid,
                include_vector=True
            )
            
            if not obj:
                return None
            
            # Extract vector
            vector = None
            if hasattr(obj, 'vector') and obj.vector:
                if isinstance(obj.vector, dict):
                    vector = obj.vector.get("default") or next(iter(obj.vector.values()), None)
                elif isinstance(obj.vector, list):
                    vector = obj.vector
            
            # Extract metadata
            metadata = json.loads(obj.properties.get("metadata", "{}"))
            company_id = obj.properties.get("company_id")
            
            if vector and len(vector) > 0:
                return {
                    "profile_id": profile_id,
                    "company_id": company_id,
                    "embedding": vector,  # 768-dim vector
                    "metadata": metadata
                }
            
            return None
        except Exception as e:
            logger.error(f"Failed to get embedding for {class_name} profile {profile_id}: {e}")
            return None
    
    def find_similar_embeddings(self, class_name: str, profile_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar embeddings to a given profile.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Profile identifier to find similarities for
            top_k: Number of similar results to return
        
        Returns:
            List of similar profiles with profile_id, metadata, similarity, and distance
        """
        try:
            # First, get the embedding for the given profile
            profile_embedding = self.get_embedding(class_name, profile_id)
            if not profile_embedding or not profile_embedding.get("embedding"):
                logger.warning(f"No embedding found for {class_name} profile {profile_id}")
                return []
            
            embedding_vector = profile_embedding.get("embedding")
            
            # Use the existing _search method to find similar embeddings
            # But exclude the original profile from results
            results = self._search(class_name, np.array(embedding_vector), top_k + 1)
            
            # Filter out the original profile
            filtered_results = [
                r for r in results 
                if r.get("profile_id") != profile_id
            ][:top_k]
            
            return filtered_results
        except Exception as e:
            logger.error(f"Failed to find similar embeddings for {class_name} profile {profile_id}: {e}")
            return []
    
    def delete_embedding(self, class_name: str, profile_id: str) -> bool:
        """
        Delete an embedding from Weaviate.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Profile identifier to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate deterministic UUID (same as used in _store)
            unique_identifier = f"{class_name}:{profile_id}"
            obj_uuid = generate_uuid5(unique_identifier)
            
            # Get collection
            collection = self.client.collections.get(class_name)
            
            # Delete by UUID
            collection.data.delete_by_id(uuid=obj_uuid)
            logger.debug(f"Deleted {class_name} profile: {profile_id} (UUID: {obj_uuid})")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete {class_name} profile {profile_id}: {e}")
            return False
    
    def find_similar_embeddings_across_types(self, class_name: str, profile_id: str, top_k_per_type: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find similar embeddings across all profile types.
        
        Args:
            class_name: Weaviate collection name (Candidate, Team, Interviewer, Position)
            profile_id: Profile identifier to find similarities for
            top_k_per_type: Number of similar results to return per profile type
        
        Returns:
            Dictionary mapping profile type to list of similar profiles
        """
        try:
            # First, get the embedding for the given profile
            profile_embedding = self.get_embedding(class_name, profile_id)
            if not profile_embedding or not profile_embedding.get("embedding"):
                logger.warning(f"No embedding found for {class_name} profile {profile_id}")
                return {
                    "candidates": [],
                    "teams": [],
                    "interviewers": [],
                    "positions": []
                }
            
            embedding_vector = np.array(profile_embedding.get("embedding"))
            
            # Search across all profile types
            all_results = {
                "candidates": [],
                "teams": [],
                "interviewers": [],
                "positions": []
            }
            
            # Map Weaviate class names to result keys
            class_to_key = {
                "Candidate": "candidates",
                "Team": "teams",
                "Interviewer": "interviewers",
                "Position": "positions"
            }
            
            for search_class_name in ["Candidate", "Team", "Interviewer", "Position"]:
                try:
                    # Search in this class
                    results = self._search(search_class_name, embedding_vector, top_k_per_type + 1)
                    
                    # Filter out the original profile if searching in the same class
                    filtered_results = [
                        r for r in results 
                        if not (search_class_name == class_name and r.get("profile_id") == profile_id)
                    ][:top_k_per_type]
                    
                    # Add profile_type to each result
                    for result in filtered_results:
                        result["profile_type"] = search_class_name.lower()
                    
                    result_key = class_to_key.get(search_class_name, search_class_name.lower() + "s")
                    all_results[result_key] = filtered_results
                except Exception as e:
                    logger.warning(f"Failed to search in {search_class_name}: {e}")
                    continue
            
            return all_results
        except Exception as e:
            logger.error(f"Failed to find similar embeddings across types for {class_name} profile {profile_id}: {e}")
            return {
                "candidates": [],
                "teams": [],
                "interviewers": [],
                "positions": []
            }
    
    def close(self):
        """Close Weaviate connection."""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Closed Weaviate connection")

