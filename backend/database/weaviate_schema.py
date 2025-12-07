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
    
    Returns:
        Dictionary with creation results: {
            'created': [list of created collection names],
            'existing': [list of existing collection names],
            'errors': [list of error messages]
        }
    
    Each profile type has:
    - Vector property (768 dimensions for MPNet embeddings)
    - Metadata properties (id, profile data as JSON)
    - Indexed for fast retrieval
    """
    results = {
        'created': [],
        'existing': [],
        'errors': []
    }
    
    try:
        # Check if collections already exist - improved detection
        existing_collections = []
        try:
            all_collections = client.collections.list_all()
            for col in all_collections:
                # Handle different return types from Weaviate
                if isinstance(col, str):
                    existing_collections.append(col)
                elif hasattr(col, 'name'):
                    existing_collections.append(col.name)
                elif hasattr(col, '__str__'):
                    existing_collections.append(str(col))
        except Exception as e:
            logger.warning(f"Error listing collections: {e}")
            # Continue anyway - will try to create and handle errors

        # Define collections to create
        collections_to_create = [
            {
                "name": "Candidate",
                "properties": [
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="company_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            },
            {
                "name": "Team",
                "properties": [
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="company_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            },
            {
                "name": "Interviewer",
                "properties": [
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="company_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            },
            {
                "name": "Position",
                "properties": [
                    Property(name="profile_id", data_type=DataType.TEXT),
                    Property(name="company_id", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.TEXT)
                ]
            }
        ]
        
        # Create each collection if it doesn't exist
        for collection_def in collections_to_create:
            collection_name = collection_def["name"]
            if collection_name in existing_collections:
                results['existing'].append(collection_name)
                logger.info(f"Collection {collection_name} already exists")
            else:
                try:
                    # Use vector_config instead of deprecated vectorizer_config
                    # Configure.Vectorizer.none() means no automatic vectorization (we provide our own vectors)
                    client.collections.create(
                        name=collection_name,
                        vectorizer_config=Configure.Vectorizer.none(),  # TODO: Update to vector_config when Weaviate client library is updated
                        replication_config=Configure.replication(factor=1),
                        properties=collection_def["properties"]
                    )
                    results['created'].append(collection_name)
                    logger.info(f"Created {collection_name} collection with company_id")
                except Exception as e:
                    error_msg = f"Failed to create {collection_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    # Check if it was created by another process
                    try:
                        # Try to get the collection to see if it exists now
                        client.collections.get(collection_name)
                        results['existing'].append(collection_name)
                        logger.info(f"Collection {collection_name} exists (created by another process)")
                    except:
                        pass  # Collection doesn't exist, error is valid
        
        if results['created']:
            logger.info(f"Weaviate schema created: {', '.join(results['created'])}")
        if results['existing']:
            logger.info(f"Weaviate schema existing: {', '.join(results['existing'])}")
        if results['errors']:
            logger.warning(f"Weaviate schema errors: {', '.join(results['errors'])}")
        
        logger.info("Weaviate schema ready for 4 profile types")
        return results
        
    except Exception as e:
        error_msg = f"Schema creation failed: {e}"
        logger.error(error_msg, exc_info=True)
        results['errors'].append(error_msg)
        return results

