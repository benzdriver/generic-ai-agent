# Operational Scripts

This directory contains scripts that are part of the application's regular workflow, used during normal operation of the AI agent system.

## Available Scripts

### `load_and_index.py`
- **Purpose**: Parse and index document content into the vector database
- **Usage**: `python src/scripts/load_and_index.py <file_path> [html|txt]`
- **Parameters**:
  - `file_path`: Path to the document file to be processed
  - `file_type`: Optional, either "html" or "txt" (defaults to "txt")
- **Description**: This script processes document files, chunks the content into manageable segments, and inserts them into the vector database with appropriate metadata.

### `weekly_cleanup.py`
- **Purpose**: Perform regular maintenance on the knowledge base
- **Usage**: Typically scheduled to run weekly via cron job or similar scheduler
- **Operations**:
  1. Executes knowledge clustering and merging
  2. Cleans up old/redundant data points
- **Description**: This script helps maintain the quality and efficiency of the knowledge base by consolidating similar information and removing outdated entries.

### `crawl_immigration_sites.py`
- **Purpose**: Crawl immigration official websites and update the knowledge base
- **Usage**: `python src/scripts/crawl_immigration_sites.py [--sites SITES_JSON_FILE]`
- **Parameters**:
  - `--sites`: Optional, path to a JSON file containing website list (defaults to built-in list)
- **Description**: This script crawls specified immigration websites, extracts content, and updates the vector database with the latest information.

### `schedule_crawler.py`
- **Purpose**: Schedule periodic crawling of immigration websites
- **Usage**: `python src/scripts/schedule_crawler.py [options]`
- **Parameters**:
  - `--sites`: Optional, path to a JSON file containing website list
  - `--daily`: Run crawler daily (at 2:00 AM)
  - `--weekly`: Run crawler weekly (Monday at 3:00 AM)
  - `--interval HOURS`: Run crawler at specified hour intervals
  - `--now`: Run crawler immediately
- **Description**: This script sets up a scheduler to periodically run the crawler script, ensuring the knowledge base stays up-to-date with the latest information from immigration websites.

## Integration with Core Modules

These scripts integrate with the application's core modules:
- `knowledge_ingestion`: For document parsing and processing
- `vector_engine`: For interaction with the vector database
- `knowledge_manager`: For knowledge clustering and cleanup

## When to Use

- Use `load_and_index.py` when you have new documents to add to the knowledge base
- Schedule `weekly_cleanup.py` to run automatically for regular maintenance
- Use `crawl_immigration_sites.py` to manually update the knowledge base from websites
- Use `schedule_crawler.py` to set up automatic periodic updates from websites

## Requirements

These scripts require:
- All core application modules to be properly installed
- Proper environment configuration (see project root README)
- Appropriate permissions for the vector database
- Additional libraries: `requests`, `beautifulsoup4`, `schedule` (for crawling and scheduling)

## Configuration Files

- `data/immigration_sites.json`: Contains the list of immigration websites to crawl

For system setup and configuration scripts, see the `/scripts` directory. 