# CliniMatch Database Setup Guide

This guide explains how to set up the Supabase database for the CliniMatch application.

## Prerequisites

- Supabase project created and configured
- Environment variables set in `.env` file:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SUPABASE_PROJECT_ID`

## Setup Process

### 1. Verify Connection

First, run the database setup script to verify your connection and get the SQL schema:

```bash
cd backend
python setup_database.py
```

This script will:
- Test the Supabase connection
- Check if tables exist
- Display the SQL schema that needs to be executed
- Run basic tests if tables are already set up

### 2. Create Database Schema

If tables don't exist yet, you'll see the SQL schema output. Copy this SQL and execute it in your Supabase SQL editor:

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Paste the provided SQL schema
4. Execute the SQL commands

The schema creates:
- `trials_cache` table for caching clinical trial data
- `user_sessions` table for optional analytics
- Proper indexes for performance
- Row Level Security policies

### 3. Verify Setup

After creating the tables, run the setup script again to verify everything is working:

```bash
python setup_database.py
```

You should see successful tests for:
- Database connection
- Cache operations (store, retrieve, stats)
- Table structure verification

## Database Schema Details

### trials_cache Table

Stores cached clinical trial data with TTL support:

- `id`: Primary key
- `search_key`: Unique hash of search parameters
- `trial_data`: JSONB data containing trial information
- `created_at`: Timestamp when cached
- `expires_at`: Expiration timestamp for TTL

### user_sessions Table

Optional table for analytics (not used in current implementation):

- `id`: Primary key
- `session_id`: Unique session identifier
- `search_count`: Number of searches in session
- `created_at`: Session creation time
- `last_activity`: Last activity timestamp

## Usage in Code

### Database Connection

```python
from utils.database import get_db_connection

# Get database connection
db_conn = get_db_connection()

# Test connection
if db_conn.test_connection():
    print("Connected!")
```

### Cache Service

```python
from utils.database import get_cache_service

# Get cache service
cache = get_cache_service()

# Cache trial data
search_params = {"age": 30, "condition": "diabetes"}
trial_data = [{"nct_id": "NCT123", "title": "Test Trial"}]
cache.cache_trials(search_params, trial_data)

# Retrieve cached data
cached_data = cache.get_cached_trials(search_params)

# Get cache statistics
stats = cache.get_cache_stats()
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_database.py -v
```

This runs 21 test cases covering:
- Database connection handling
- Cache operations (CRUD)
- Error handling
- TTL functionality
- Integration workflows

## Troubleshooting

### Connection Issues

1. Verify environment variables are set correctly
2. Check Supabase project status
3. Ensure API keys have proper permissions

### Table Issues

1. Make sure SQL schema was executed successfully
2. Check Row Level Security policies are enabled
3. Verify table permissions in Supabase dashboard

### Cache Issues

1. Check if tables exist and are accessible
2. Verify JSONB data format is valid
3. Monitor cache expiration times

## Performance Considerations

- The cache uses MD5 hashing for search keys
- Indexes are created on frequently queried columns
- TTL cleanup happens automatically during operations
- Consider running periodic cleanup for expired entries

## Security

- Row Level Security (RLS) is enabled on all tables
- Public access policies are configured for the application
- No sensitive user data is stored permanently
- All data is session-based and expires automatically