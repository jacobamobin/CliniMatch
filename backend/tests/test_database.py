import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import with mocking to avoid global initialization
with patch('utils.database.create_client'):
    from utils.database import DatabaseConnection, CacheService, DatabaseError
    from config import Config

class TestDatabaseConnection:
    """Test cases for DatabaseConnection class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_client = Mock()
        
    @patch('utils.database.create_client')
    def test_successful_initialization(self, mock_create_client):
        """Test successful database connection initialization"""
        # Mock the create_client function
        mock_create_client.return_value = self.mock_client
        
        # Mock successful connection test (auth.get_session succeeds)
        self.mock_client.auth.get_session.return_value = Mock()
        
        # Test initialization
        db_conn = DatabaseConnection()
        
        assert db_conn.client is not None
        mock_create_client.assert_called_once_with(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    @patch('utils.database.create_client')
    def test_missing_credentials_error(self, mock_create_client):
        """Test error handling when Supabase credentials are missing"""
        with patch.object(Config, 'SUPABASE_URL', None):
            with pytest.raises(DatabaseError) as exc_info:
                DatabaseConnection()
            
            assert "Supabase URL and Key must be configured" in str(exc_info.value)
    
    @patch('utils.database.create_client')
    def test_connection_failure(self, mock_create_client):
        """Test handling of connection failures"""
        mock_create_client.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            DatabaseConnection()
        
        assert "Database initialization failed" in str(exc_info.value)
    
    @patch('utils.database.create_client')
    def test_get_client_with_reinitialization(self, mock_create_client):
        """Test get_client method with reinitialization"""
        mock_create_client.return_value = self.mock_client
        
        # Mock successful connection test (auth.get_session succeeds)
        self.mock_client.auth.get_session.return_value = Mock()
        
        db_conn = DatabaseConnection()
        db_conn.client = None  # Simulate lost connection
        
        client = db_conn.get_client()
        assert client is not None
    
    @patch('utils.database.create_client')
    def test_connection_test_success(self, mock_create_client):
        """Test successful connection test"""
        mock_create_client.return_value = self.mock_client
        
        # Mock successful connection test (auth.get_session succeeds)
        self.mock_client.auth.get_session.return_value = Mock()
        
        db_conn = DatabaseConnection()
        assert db_conn.test_connection() is True
    
    @patch('utils.database.create_client')
    def test_connection_test_failure(self, mock_create_client):
        """Test connection test failure"""
        mock_create_client.return_value = self.mock_client
        
        # Mock failed connection test (auth.get_session fails)
        self.mock_client.auth.get_session.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseError):
            DatabaseConnection()

class TestCacheService:
    """Test cases for CacheService class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_db_connection = Mock()
        self.mock_client = Mock()
        self.mock_db_connection.get_client.return_value = self.mock_client
        self.cache_service = CacheService(self.mock_db_connection)
    
    def test_generate_search_key(self):
        """Test search key generation"""
        search_params1 = {"age": 30, "condition": "diabetes"}
        search_params2 = {"condition": "diabetes", "age": 30}  # Same params, different order
        search_params3 = {"age": 31, "condition": "diabetes"}  # Different params
        
        key1 = self.cache_service._generate_search_key(search_params1)
        key2 = self.cache_service._generate_search_key(search_params2)
        key3 = self.cache_service._generate_search_key(search_params3)
        
        # Same parameters should generate same key regardless of order
        assert key1 == key2
        # Different parameters should generate different keys
        assert key1 != key3
        # Keys should be strings
        assert isinstance(key1, str)
    
    def test_is_expired_true(self):
        """Test expiry check for expired entries"""
        from datetime import timezone
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert self.cache_service._is_expired(past_time) is True
    
    def test_is_expired_false(self):
        """Test expiry check for non-expired entries"""
        from datetime import timezone
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        assert self.cache_service._is_expired(future_time) is False
    
    def test_is_expired_invalid_format(self):
        """Test expiry check with invalid date format"""
        invalid_time = "invalid-date-format"
        assert self.cache_service._is_expired(invalid_time) is True
    
    def test_get_cached_trials_success(self):
        """Test successful retrieval of cached trials"""
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        from datetime import timezone
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        # Mock database response
        mock_table = Mock()
        mock_result = Mock()
        mock_result.data = [{"trial_data": trial_data, "expires_at": future_time}]
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.get_cached_trials(search_params)
        
        assert result == trial_data
        mock_table.select.assert_called_once_with('trial_data, expires_at')
    
    def test_get_cached_trials_not_found(self):
        """Test retrieval when no cached data exists"""
        search_params = {"age": 30, "condition": "diabetes"}
        
        # Mock empty database response
        mock_table = Mock()
        mock_result = Mock()
        mock_result.data = []
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.get_cached_trials(search_params)
        
        assert result is None
    
    def test_get_cached_trials_expired(self):
        """Test retrieval of expired cached data"""
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        from datetime import timezone
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        # Mock database response with expired data
        mock_table = Mock()
        mock_result = Mock()
        mock_result.data = [{"trial_data": trial_data, "expires_at": past_time}]
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        
        # Mock delete operation for cleanup
        mock_delete_result = Mock()
        mock_delete_result.data = []
        mock_table.delete.return_value.lt.return_value.execute.return_value = mock_delete_result
        
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.get_cached_trials(search_params)
        
        assert result is None
    
    def test_cache_trials_new_entry(self):
        """Test caching new trial data"""
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        
        # Mock update operation (no existing entry)
        mock_table = Mock()
        mock_update_result = Mock()
        mock_update_result.data = []  # No existing entry to update
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        
        # Mock insert operation
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": 1}]  # Successful insert
        mock_table.insert.return_value.execute.return_value = mock_insert_result
        
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.cache_trials(search_params, trial_data)
        
        assert result is True
        mock_table.insert.assert_called_once()
    
    def test_cache_trials_update_existing(self):
        """Test updating existing cached trial data"""
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        
        # Mock update operation (existing entry found)
        mock_table = Mock()
        mock_update_result = Mock()
        mock_update_result.data = [{"id": 1}]  # Existing entry updated
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.cache_trials(search_params, trial_data)
        
        assert result is True
        mock_table.update.assert_called_once()
    
    def test_cache_trials_insert_failure(self):
        """Test handling of cache insertion failure"""
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        
        # Mock update operation (no existing entry)
        mock_table = Mock()
        mock_update_result = Mock()
        mock_update_result.data = []
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        
        # Mock insert operation failure
        mock_insert_result = Mock()
        mock_insert_result.data = []  # Failed insert
        mock_table.insert.return_value.execute.return_value = mock_insert_result
        
        self.mock_client.table.return_value = mock_table
        
        with pytest.raises(DatabaseError) as exc_info:
            self.cache_service.cache_trials(search_params, trial_data)
        
        assert "Failed to insert cache entry" in str(exc_info.value)
    
    def test_clear_cache_success(self):
        """Test successful cache clearing"""
        mock_table = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]  # Mock deleted entries
        mock_table.delete.return_value.neq.return_value.execute.return_value = mock_result
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.clear_cache()
        
        assert result is True
        mock_table.delete.assert_called_once()
    
    def test_clear_cache_failure(self):
        """Test cache clearing failure"""
        mock_table = Mock()
        mock_table.delete.return_value.neq.return_value.execute.side_effect = Exception("Delete failed")
        self.mock_client.table.return_value = mock_table
        
        with pytest.raises(DatabaseError) as exc_info:
            self.cache_service.clear_cache()
        
        assert "Cache clearing failed" in str(exc_info.value)
    
    def test_get_cache_stats_success(self):
        """Test successful cache statistics retrieval"""
        # Mock total entries query
        mock_table = Mock()
        mock_total_result = Mock()
        mock_total_result.count = 10
        
        # Mock expired entries query
        mock_expired_result = Mock()
        mock_expired_result.count = 3
        
        # Setup the mock chain for total entries
        mock_table.select.return_value.execute.return_value = mock_total_result
        
        # Setup the mock chain for expired entries
        mock_expired_table = Mock()
        mock_expired_table.select.return_value.lt.return_value.execute.return_value = mock_expired_result
        
        # Configure the table mock to return different mocks for different calls
        self.mock_client.table.side_effect = [mock_table, mock_expired_table]
        
        result = self.cache_service.get_cache_stats()
        
        expected = {
            'total_entries': 10,
            'expired_entries': 3,
            'active_entries': 7
        }
        assert result == expected
    
    def test_get_cache_stats_error(self):
        """Test cache statistics retrieval error handling"""
        mock_table = Mock()
        mock_table.select.side_effect = Exception("Query failed")
        self.mock_client.table.return_value = mock_table
        
        result = self.cache_service.get_cache_stats()
        
        assert 'error' in result
        assert 'Query failed' in result['error']

class TestIntegration:
    """Integration tests for database components"""
    
    @patch('utils.database.create_client')
    def test_full_cache_workflow(self, mock_create_client):
        """Test complete cache workflow: store, retrieve, expire"""
        # Setup mocks
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock successful connection test (auth.get_session succeeds)
        mock_client.auth.get_session.return_value = Mock()
        
        # Mock table operations
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        # Initialize components
        db_conn = DatabaseConnection()
        cache_service = CacheService(db_conn)
        
        # Test data
        search_params = {"age": 30, "condition": "diabetes"}
        trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
        
        # Mock cache storage (insert new entry)
        mock_update_result = Mock()
        mock_update_result.data = []
        mock_insert_result = Mock()
        mock_insert_result.data = [{"id": 1}]
        
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        mock_table.insert.return_value.execute.return_value = mock_insert_result
        
        # Test caching
        cache_result = cache_service.cache_trials(search_params, trial_data)
        assert cache_result is True
        
        # Mock cache retrieval
        from datetime import timezone
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        mock_get_result = Mock()
        mock_get_result.data = [{"trial_data": trial_data, "expires_at": future_time}]
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_get_result
        
        # Test retrieval
        retrieved_data = cache_service.get_cached_trials(search_params)
        assert retrieved_data == trial_data

if __name__ == '__main__':
    pytest.main([__file__])