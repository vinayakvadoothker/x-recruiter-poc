"""
postgres_client.py - PostgreSQL client for relational data storage

This module provides a PostgreSQL client for storing non-graph data:
- Companies
- Teams
- Interviewers
- Positions
- Conversations (Grok position creation chats)
- Pipeline stages
- Position distribution flags

Implementation Rationale:

Why PostgreSQL over other databases:
1. **Relational data**: Teams, interviewers, positions have clear relationships
2. **ACID compliance**: Critical for multi-tenant data isolation
3. **Mature ecosystem**: Well-supported Python libraries (psycopg2, asyncpg)
4. **Local Docker**: Can run locally for development, persistent storage via volumes

Design Decisions:
- **Connection pooling**: Reuse connections for performance
- **Async support**: Use asyncpg for async operations (can switch to psycopg2 if needed)
- **Environment-based config**: Read DATABASE_URL from environment
- **Error handling**: Graceful connection failures with retries
"""

import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor

load_dotenv()
logger = logging.getLogger(__name__)


class PostgresClient:
    """
    PostgreSQL client with connection pooling for relational data storage.
    
    Handles connections to PostgreSQL database for storing:
    - Companies
    - Teams
    - Interviewers
    - Positions
    - Conversations
    - Pipeline stages
    - Position distribution flags
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL client with connection pool.
        
        Args:
            database_url: PostgreSQL connection string.
                         Defaults to DATABASE_URL env var.
        
        Raises:
            ConnectionError: If unable to connect to PostgreSQL
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Set it in .env file or pass database_url parameter."
            )
        
        # Create connection pool (min 2, max 10 connections)
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=self.database_url
            )
            
            if self.connection_pool:
                logger.info("PostgreSQL connection pool created successfully")
                # Test connection
                self._test_connection()
            else:
                raise ConnectionError("Failed to create PostgreSQL connection pool")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL client: {e}")
            raise ConnectionError(f"Cannot connect to PostgreSQL: {e}")
    
    def _test_connection(self):
        """Test database connection."""
        try:
            conn = self.connection_pool.getconn()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.connection_pool.putconn(conn)
                logger.info("PostgreSQL connection test successful")
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            raise ConnectionError(f"PostgreSQL connection test failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool (context manager).
        
        Usage:
            with postgres_client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM teams")
                results = cursor.fetchall()
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
        
        Returns:
            List of dictionaries (one per row)
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
        
        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
    
    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a SELECT query and return single result.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Single dictionary or None if no results
        """
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def close(self):
        """Close all connections in the pool."""
        if hasattr(self, 'connection_pool') and self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")

