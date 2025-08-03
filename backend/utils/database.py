import os
from supabase import create_client, Client
from config import Config
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import hashlib

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class DatabaseConnection:
    """Supabase database connection utility with enhanced error handling"""
    
    def __init__(self):
        self.client: Client = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Supabase client connection with comprehensive error handling"""
        try:
            if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
                raise DatabaseError("Supabase URL and Key must be configured in environment variables")
            
            self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            logger.info("Supabase connection initialized successfully")
            
            # Test the connection immediately
            if not self._test_connection():
                raise DatabaseError("Failed to establish connection to Supabase")
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase connection: {e}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    
    def get_client(self) -> Client:
        """Get the Supabase client instance with connection validation"""
        if not self.client:
            self._initialize_connection()
        return self.client
    
    def _test_connection(self) -> bool:
        """Internal method to test the database connection"""
        try:
            # Try a simple query that doesn't depend on our tables existing
            # This tests the basic Supabase connection
            result = self.client.auth.get_session()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Public method to test the database connection"""
        return self._test_connection()
    
    def execute_schema(self, schema_file_path: str) -> bool:
        """Execute SQL schema file (for setup purposes)"""
        try:
            with open(schema_file_path, 'r') as file:
                schema_sql = file.read()
            
            # Note: Supabase Python client doesn't support raw SQL execution
            # This method is for documentation purposes
            # Schema should be executed via Supabase dashboard or SQL editor
            logger.info(f"Schema file {schema_file_path} should be executed via Supabase SQL editor")
            return True
            
        except Exception as e:
            logger.error(f"Failed to read schema file: {e}")
            raise DatabaseError(f"Schema execution failed: {str(e)}")

class CacheService:
    """Service class for cache operations with TTL support"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.table_name = 'trials_cache'
    
    def _generate_search_key(self, search_params: Dict[str, Any]) -> str:
        """Generate a unique search key from search parameters"""
        # Sort parameters for consistent key generation
        sorted_params = json.dumps(search_params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()
    
    def _is_expired(self, expires_at: str) -> bool:
        """Check if a cache entry has expired"""
        try:
            # Parse the expiry time
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            # Get current UTC time for comparison
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
            
            return current_time > expiry_time
        except Exception as e:
            logger.error(f"Error checking expiry time: {e}")
            return True  # Assume expired if we can't parse the date
    
    def get_cached_trials(self, search_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached trial data if not expired"""
        try:
            search_key = self._generate_search_key(search_params)
            
            result = self.db.get_client().table(self.table_name)\
                .select('trial_data, expires_at')\
                .eq('search_key', search_key)\
                .execute()
            
            if not result.data:
                logger.info(f"No cached data found for search key: {search_key}")
                return None
            
            cache_entry = result.data[0]
            
            # Check if the cache entry has expired
            if self._is_expired(cache_entry['expires_at']):
                logger.info(f"Cache entry expired for search key: {search_key}")
                # Clean up expired entry
                self._delete_expired_entries()
                return None
            
            logger.info(f"Retrieved cached data for search key: {search_key}")
            return cache_entry['trial_data']
            
        except Exception as e:
            logger.error(f"Error retrieving cached trials: {e}")
            raise DatabaseError(f"Cache retrieval failed: {str(e)}")
    
    def cache_trials(self, search_params: Dict[str, Any], trial_data: List[Dict[str, Any]], 
                    ttl_hours: int = None) -> bool:
        """Cache trial data with TTL support"""
        try:
            search_key = self._generate_search_key(search_params)
            ttl_hours = ttl_hours or Config.CACHE_TTL_HOURS
            
            # Use UTC time for consistency
            from datetime import timezone
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            
            # Try to update existing entry first
            update_result = self.db.get_client().table(self.table_name)\
                .update({
                    'trial_data': trial_data,
                    'expires_at': expires_at.isoformat()
                })\
                .eq('search_key', search_key)\
                .execute()
            
            # If no rows were updated, insert new entry
            if not update_result.data:
                insert_result = self.db.get_client().table(self.table_name)\
                    .insert({
                        'search_key': search_key,
                        'trial_data': trial_data,
                        'expires_at': expires_at.isoformat()
                    })\
                    .execute()
                
                if not insert_result.data:
                    raise DatabaseError("Failed to insert cache entry")
            
            logger.info(f"Successfully cached trial data for search key: {search_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching trials: {e}")
            raise DatabaseError(f"Cache storage failed: {str(e)}")
    
    def _delete_expired_entries(self) -> int:
        """Clean up expired cache entries"""
        try:
            from datetime import timezone
            current_time = datetime.now(timezone.utc).isoformat()
            
            result = self.db.get_client().table(self.table_name)\
                .delete()\
                .lt('expires_at', current_time)\
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    def clear_cache(self) -> bool:
        """Clear all cached data (for testing/maintenance)"""
        try:
            result = self.db.get_client().table(self.table_name)\
                .delete()\
                .neq('id', 0)\
                .execute()  # Delete all entries
            
            logger.info("Successfully cleared all cache data")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise DatabaseError(f"Cache clearing failed: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Get total entries
            total_result = self.db.get_client().table(self.table_name)\
                .select('id', count='exact')\
                .execute()
            
            total_entries = total_result.count if total_result.count is not None else 0
            
            # Get expired entries
            from datetime import timezone
            current_time = datetime.now(timezone.utc).isoformat()
            expired_result = self.db.get_client().table(self.table_name)\
                .select('id', count='exact')\
                .lt('expires_at', current_time)\
                .execute()
            
            expired_entries = expired_result.count if expired_result.count is not None else 0
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}

# Global database instance (lazy initialization)
_db_connection = None
_cache_service = None

def get_db_connection() -> DatabaseConnection:
    """Get or create the global database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection

def get_cache_service() -> CacheService:
    """Get or create the global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(get_db_connection())
    return _cache_service