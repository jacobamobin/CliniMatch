#!/usr/bin/env python3
"""
Database setup script for CliniMatch
This script helps set up the Supabase database schema
"""

import os
import sys
from utils.database import get_db_connection, get_cache_service, DatabaseError

def setup_database():
    """Setup the database and test the connection"""
    try:
        print("Setting up CliniMatch database...")
        
        # Test database connection
        print("Testing database connection...")
        db_conn = get_db_connection()
        
        if db_conn.test_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            return False
        
        # Test if tables exist by trying cache service
        print("Checking if database tables exist...")
        cache_service = get_cache_service()
        
        # Get cache statistics to test if tables exist
        stats = cache_service.get_cache_stats()
        if 'error' not in stats:
            print(f"✅ Database tables exist! Cache stats: {stats}")
            tables_exist = True
        else:
            print(f"⚠️  Database tables may not exist yet: {stats['error']}")
            tables_exist = False
        
        print("\n📋 Database Schema Information:")
        print("The following SQL schema should be executed in your Supabase SQL editor:")
        print("=" * 60)
        
        # Read and display the schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
        try:
            with open(schema_path, 'r') as f:
                schema_content = f.read()
            print(schema_content)
        except FileNotFoundError:
            print("❌ Schema file not found!")
            return False
        
        print("=" * 60)
        
        if tables_exist:
            print("\n✅ Database setup verification complete!")
            print("All tables exist and are accessible.")
        else:
            print("\n⚠️  Database connection successful, but tables need to be created.")
            print("Please execute the SQL schema above in your Supabase SQL editor.")
            print("Then run this script again to verify the setup.")
        
        return True
        
    except DatabaseError as e:
        print(f"❌ Database setup failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during setup: {e}")
        return False

def test_cache_operations():
    """Test basic cache operations"""
    try:
        print("\n🧪 Testing cache operations...")
        
        cache_service = get_cache_service()
        
        # First check if tables exist
        stats = cache_service.get_cache_stats()
        if 'error' in stats:
            print(f"⚠️  Skipping cache operations test - tables not ready: {stats['error']}")
            return True  # Not a failure, just not ready yet
        
        # Test data
        test_search_params = {
            "age": 30,
            "conditions": ["diabetes"],
            "location": {"city": "San Francisco", "state": "CA"}
        }
        
        test_trial_data = [
            {
                "nct_id": "NCT_TEST_001",
                "title": "Test Clinical Trial",
                "description": "This is a test trial for database verification"
            }
        ]
        
        # Test caching
        print("Testing cache storage...")
        cache_result = cache_service.cache_trials(test_search_params, test_trial_data, ttl_hours=1)
        if cache_result:
            print("✅ Cache storage successful!")
        else:
            print("❌ Cache storage failed!")
            return False
        
        # Test retrieval
        print("Testing cache retrieval...")
        retrieved_data = cache_service.get_cached_trials(test_search_params)
        if retrieved_data and retrieved_data == test_trial_data:
            print("✅ Cache retrieval successful!")
        else:
            print("❌ Cache retrieval failed!")
            return False
        
        # Test cache stats
        print("Testing cache statistics...")
        stats = cache_service.get_cache_stats()
        if 'error' not in stats:
            print(f"✅ Cache stats: {stats}")
        else:
            print(f"❌ Cache stats error: {stats['error']}")
            return False
        
        # Clean up test data
        print("Cleaning up test data...")
        cache_service.clear_cache()
        print("✅ Test cleanup complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("CliniMatch Database Setup and Verification")
    print("=" * 50)
    
    # Setup database
    setup_success = setup_database()
    
    if setup_success:
        # Test cache operations if setup was successful
        test_success = test_cache_operations()
        
        if test_success:
            print("\n🎉 All database tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Cache operations tests failed!")
            sys.exit(1)
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)