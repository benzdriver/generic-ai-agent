# Scripts Directory Documentation

This document explains the purpose and functionality of the scripts in this project, which are organized in two different directories.

## Main Scripts Directory (`/scripts`)

The main scripts directory contains utility scripts for setting up and managing the Qdrant vector database. These scripts are primarily used for system setup, configuration, and testing.

### Scripts:

1. **`check_qdrant.py`**
   - **Purpose**: Verify connectivity to the Qdrant vector database
   - **Functionality**: Tests connection using API key, lists existing collections, and checks if required collections exist
   - **Usage**: `python scripts/check_qdrant.py`

2. **`initialize_collections.py`**
   - **Purpose**: Create all necessary vector collections in Qdrant
   - **Functionality**: Sets up four collections (canonical_queries, conversations, documents, merged_knowledge) with proper configurations
   - **Usage**: `python scripts/initialize_collections.py`

3. **`create_indexes.py`**
   - **Purpose**: Create field indexes for Qdrant collections
   - **Functionality**: Adds text, keyword, and boolean field indexes to support filtered searches
   - **Usage**: `python scripts/create_indexes.py`

4. **`test_collections.py`**
   - **Purpose**: Test vector insertion and search functionality
   - **Functionality**: Adds test vectors with metadata and performs both regular and filtered searches
   - **Usage**: `python scripts/test_collections.py`

## Application Scripts Directory (`/src/scripts`)

The `/src/scripts` directory contains operational scripts that are part of the application's regular workflow. These scripts are used during normal operation of the system rather than during setup.

### Scripts:

1. **`weekly_cleanup.py`**
   - **Purpose**: Perform regular maintenance on the knowledge base
   - **Functionality**: Executes knowledge clustering/merging and cleans up old data points
   - **Usage**: Typically scheduled to run weekly via cron job or similar scheduler

2. **`load_and_index.py`**
   - **Purpose**: Parse and index document content into the vector database
   - **Functionality**: Processes HTML or text files, chunks content, and inserts into vector database
   - **Usage**: `python src/scripts/load_and_index.py <file_path> [html|txt]`

## Key Differences Between Script Directories

1. **Purpose**:
   - `/scripts`: System setup, configuration, and testing tools
   - `/src/scripts`: Operational scripts for regular system usage

2. **When to Use**:
   - `/scripts`: During initial setup, troubleshooting, or when reconfiguring the system
   - `/src/scripts`: During normal operation as part of data ingestion and maintenance workflows

3. **Integration**:
   - `/scripts`: Standalone utilities that primarily interact with Qdrant directly
   - `/src/scripts`: Integrated with the application's core modules and business logic

## Environment Setup

All scripts require proper environment variables to be set, particularly:
- `QDRANT_URL`: The URL of your Qdrant instance
- `QDRANT_API_KEY`: API key with appropriate permissions

These can be set in a `.env` file at the project root. 