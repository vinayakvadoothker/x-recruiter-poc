#!/usr/bin/env python3
"""
reset_database.py - Clear and reset entire database and Weaviate

This script:
1. Drops all tables in PostgreSQL
2. Deletes all collections in Weaviate
3. Re-runs migrations to recreate schema
4. Recreates Weaviate schema

Usage:
    python scripts/reset_database.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.postgres_client import PostgresClient
from backend.database.migration_runner import run_migrations
from backend.database.weaviate_connection import create_weaviate_client
from backend.database.weaviate_schema import create_profile_schemas

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def drop_all_postgres_tables(postgres_client: PostgresClient):
    """Drop all tables in PostgreSQL."""
    logger.info("🗑️  Dropping all PostgreSQL tables...")
    
    # Get all table names
    with postgres_client.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                logger.info("  No tables found to drop")
                return
            
            logger.info(f"  Found {len(tables)} table(s): {', '.join(tables)}")
            
            # Disable foreign key checks temporarily
            cursor.execute("SET session_replication_role = 'replica';")
            
            # Drop all tables with CASCADE to handle foreign keys
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    logger.info(f"  ✅ Dropped table: {table}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to drop table {table}: {e}")
            
            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = 'origin';")
            
            conn.commit()
    
    logger.info("✅ All PostgreSQL tables dropped")


def delete_all_weaviate_collections(weaviate_client):
    """Delete all collections in Weaviate."""
    logger.info("🗑️  Deleting all Weaviate collections...")
    
    try:
        # Get all collections
        collections = weaviate_client.collections.list_all()
        
        if not collections:
            logger.info("  No collections found to delete")
            return
        
        logger.info(f"  Found {len(collections)} collection(s): {', '.join(collections)}")
        
        # Delete each collection
        for collection_name in collections:
            try:
                weaviate_client.collections.delete(collection_name)
                logger.info(f"  ✅ Deleted collection: {collection_name}")
            except Exception as e:
                logger.warning(f"  ⚠️  Failed to delete collection {collection_name}: {e}")
        
        logger.info("✅ All Weaviate collections deleted")
    except Exception as e:
        logger.error(f"❌ Error deleting Weaviate collections: {e}")
        raise


def reset_database():
    """Reset entire database and Weaviate."""
    logger.info("=" * 60)
    logger.info("RESETTING DATABASE AND WEAVIATE")
    logger.info("=" * 60)
    
    # Step 1: Clear PostgreSQL
    logger.info("\n📊 Step 1: Clearing PostgreSQL...")
    postgres_client = PostgresClient()
    try:
        drop_all_postgres_tables(postgres_client)
    except Exception as e:
        logger.error(f"❌ Failed to clear PostgreSQL: {e}")
        raise
    finally:
        postgres_client.close()
    
    # Step 2: Clear Weaviate
    logger.info("\n🔍 Step 2: Clearing Weaviate...")
    try:
        weaviate_client = create_weaviate_client()
        delete_all_weaviate_collections(weaviate_client)
    except Exception as e:
        logger.error(f"❌ Failed to clear Weaviate: {e}")
        raise
    
    # Step 3: Re-run migrations
    logger.info("\n🔧 Step 3: Re-running PostgreSQL migrations...")
    postgres_client = PostgresClient()
    try:
        run_migrations(postgres_client)
        logger.info("✅ PostgreSQL migrations completed")
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}")
        raise
    finally:
        postgres_client.close()
    
    # Step 4: Recreate Weaviate schema
    logger.info("\n🔧 Step 4: Recreating Weaviate schema...")
    try:
        weaviate_client = create_weaviate_client()
        create_profile_schemas(weaviate_client)
        logger.info("✅ Weaviate schema recreated")
    except Exception as e:
        logger.error(f"❌ Failed to recreate Weaviate schema: {e}")
        raise
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ DATABASE AND WEAVIATE RESET COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        reset_database()
    except Exception as e:
        logger.error(f"❌ Reset failed: {e}", exc_info=True)
        sys.exit(1)

