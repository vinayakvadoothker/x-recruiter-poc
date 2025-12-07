"""
weaviate_schema.py - Weaviate schema creation for 4 profile types

This module handles schema creation for Weaviate collections.
Separated from vector_db_client.py to keep files under 200 lines.

Implementation Rationale:

Why separate schema module:
- Keeps vector_db_client.py focused on storage/search operations
- Schema logic is independent and can be reused
- Easier to test schema creation separately
- Follows single responsibility principle
"""

import logging
from weaviate.classes.config import Configure, Property, DataType

logger = logging.getLogger(__name__)


def create_profile_schemas(client):
    """
    Create Weaviate schema for 4 profile types.
    
    Args:
        client: Weaviate client instance
    
    Each profile type has:
    - Vector property (768 dimensions for MPNet embeddings)
    - Metadata properties (id, profile data as JSON)
    - Indexed for fast retrieval
    """
    try:
        # Check if collections already exist
        existing_collections = []
        for col in client.collections.list_all():
            if hasattr(col, 'name'):
                existing_collections.append(col.name)
            else:
                # Fallback: treat as string if it's already a name
                existing_collections.append(str(col))
        
        # Define Candidate collection
        if "Candidate" not in existing_collections:
            client.collections.create(
                name="Candidate",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            )
            logger.info("Created Candidate collection")
        
        # Define Team collection
        if "Team" not in existing_collections:
            client.collections.create(
                name="Team",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            )
            logger.info("Created Team collection")
        
        # Define Interviewer collection
        if "Interviewer" not in existing_collections:
            client.collections.create(
                name="Interviewer",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            )
            logger.info("Created Interviewer collection")
        
        # Define Position collection
        if "Position" not in existing_collections:
            client.collections.create(
                name="Position",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            )
            logger.info("Created Position collection")
        
        logger.info("Weaviate schema ready for 4 profile types")
    except Exception as e:
        logger.warning(f"Schema creation failed (may already exist): {e}")

