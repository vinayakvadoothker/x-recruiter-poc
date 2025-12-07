"""
weaviate_connection.py - Weaviate connection handling

This module handles Weaviate client connection logic.
Separated from vector_db_client.py to keep files under 200 lines.

Implementation Rationale:

Why separate connection module:
- Connection logic is independent of storage/search operations
- Can be reused by other modules if needed
- Easier to test connection separately
- Keeps vector_db_client.py focused on core functionality
"""

import os
import logging
import weaviate
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def create_weaviate_client(url: Optional[str] = None):
    """
    Create and connect to Weaviate client.
    
    Args:
        url: Weaviate server URL. Defaults to WEAVIATE_URL env var or http://localhost:8080
    
    Returns:
        Connected Weaviate client instance
    
    Raises:
        ConnectionError: If unable to connect to Weaviate
    """
    weaviate_url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    try:
        # Extract host and port from URL
        if "://" in weaviate_url:
            url_parts = weaviate_url.split("://")[1]
            if ":" in url_parts:
                host, port_str = url_parts.split(":")
                port = int(port_str)
            else:
                host = url_parts
                port = 8080
        else:
            host = "localhost"
            port = 8080
        
        # Weaviate v4 API - use connect_to_local for localhost, connect_to_custom for Docker service names
        if host == "localhost" or host == "127.0.0.1":
            # Try to connect with gRPC first, but skip checks if not available
            try:
                client = weaviate.connect_to_local(
                    host=host,
                    port=port,
                    grpc_port=50051,
                    skip_init_checks=True  # Skip gRPC checks if gRPC is not available
                )
            except Exception as e:
                logger.warning(f"Failed to connect with gRPC, trying HTTP only: {e}")
                # Fall back to HTTP only if gRPC fails
                client = weaviate.connect_to_local(
                    host=host,
                    port=port,
                    skip_init_checks=True
                )
        else:
            # For Docker service names (e.g., "weaviate")
            try:
                client = weaviate.connect_to_custom(
                    http_host=host,
                    http_port=port,
                    http_secure=False,
                    grpc_host=host,
                    grpc_port=50051,
                    grpc_secure=False
                )
            except Exception as e:
                logger.warning(f"Failed to connect with gRPC, trying HTTP only: {e}")
                # Fall back to HTTP only
                client = weaviate.connect_to_custom(
                    http_host=host,
                    http_port=port,
                    http_secure=False
                )
        
        logger.info(f"Connected to Weaviate at {weaviate_url}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        raise ConnectionError(f"Cannot connect to Weaviate at {weaviate_url}: {e}")

