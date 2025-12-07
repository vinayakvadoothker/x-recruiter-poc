"""
migration_runner.py - Run database migrations

This module executes SQL migration files to set up database schema.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.postgres_client import PostgresClient

logger = logging.getLogger(__name__)


def run_migrations(postgres_client: PostgresClient, migration_dir: str = None):
    """
    Run all migration files in order.
    
    Args:
        postgres_client: PostgresClient instance
        migration_dir: Directory containing migration files. 
                      Defaults to backend/database/migrations/
    """
    if migration_dir is None:
        migration_dir = os.path.join(
            os.path.dirname(__file__),
            "migrations"
        )
    
    migration_path = Path(migration_dir)
    if not migration_path.exists():
        logger.warning(f"Migration directory not found: {migration_dir}")
        return
    
    # Get all SQL files, sorted by name (001_*, 002_*, etc.)
    migration_files = sorted(migration_path.glob("*.sql"))
    
    if not migration_files:
        logger.info("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration file(s)")
    
    for migration_file in migration_files:
        logger.info(f"Running migration: {migration_file.name}")
        try:
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute migration
            with postgres_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    conn.commit()
            
            logger.info(f"✅ Migration {migration_file.name} completed successfully")
        except Exception as e:
            logger.error(f"❌ Migration {migration_file.name} failed: {e}")
            raise


if __name__ == "__main__":
    # Run migrations when executed directly
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        client = PostgresClient()
        run_migrations(client)
        print("✅ All migrations completed successfully!")
        client.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

