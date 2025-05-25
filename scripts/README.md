# Setup and Configuration Scripts

This directory contains utility scripts for setting up, configuring, and testing the Qdrant vector database for the AI agent system.

## Available Scripts

### `check_qdrant.py`
- **Purpose**: Verify connectivity to Qdrant and check required collections
- **Usage**: `python scripts/check_qdrant.py`
- **When to use**: When setting up the system or troubleshooting connection issues

### `initialize_collections.py`
- **Purpose**: Create all necessary vector collections in Qdrant
- **Usage**: `python scripts/initialize_collections.py`
- **Collections created**:
  - `canonical_queries`: Stores standardized user queries
  - `conversations`: Stores conversation history
  - `documents`: Stores official documentation content
  - `merged_knowledge`: Stores deduplicated knowledge

### `create_indexes.py`
- **Purpose**: Create field indexes for collections to support filtered searches
- **Usage**: `python scripts/create_indexes.py`
- **Indexes created**: Text, keyword, and boolean field indexes

### `test_collections.py`
- **Purpose**: Test vector insertion and search functionality
- **Usage**: `python scripts/test_collections.py`
- **Features**: Tests both regular vector search and filtered search

## Requirements

These scripts require:
- Python 3.8+
- Qdrant client library
- Valid Qdrant API key with cluster-wide write permissions

## Environment Setup

All scripts read configuration from a `.env` file in the project root. Make sure to set:
```
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
```

## Typical Setup Workflow

1. Run `check_qdrant.py` to verify connectivity
2. Run `initialize_collections.py` to create collections
3. Run `create_indexes.py` to set up proper field indexes
4. Run `test_collections.py` to verify functionality

For operational scripts used during normal system operation, see the `/src/scripts` directory. 