"""
neo4j_client.py - Neo4j database connection and session management

This module handles Neo4j database connections, session management,
and provides a context manager for safe database operations.

Key functions:
- connect(): Establish connection to Neo4j
- get_session(): Get database session
- close(): Close connection

Dependencies:
- neo4j: Neo4j Python driver
- python-dotenv: Load environment variables
- os: Access environment variables
"""

import os
from typing import Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jClient:
    """
    Neo4j database client for managing connections and sessions.
    
    Handles connection to Neo4j database using credentials from
    environment variables. Provides session management for safe
    database operations.
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI (defaults to NEO4J_URI env var)
            user: Neo4j username (defaults to NEO4J_USER env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
        """
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        self.driver: Optional[GraphDatabase.driver] = None
    
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database.
        
        Returns:
            True if connection successful, False otherwise
        
        Raises:
            Exception: If connection fails
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {str(e)}")
    
    def get_session(self):
        """
        Get a Neo4j session for database operations.
        
        Returns:
            Neo4j session object
        
        Raises:
            RuntimeError: If not connected
        """
        if self.driver is None:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        return self.driver.session()
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver is not None:
            self.driver.close()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

