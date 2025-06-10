# AI Agent Scripts Documentation

This directory contains utility scripts for managing the AI agent system's knowledge base, infrastructure, and data lifecycle. The scripts are designed to be modular, scalable, and configuration-driven.

## 🏗️ Core Scripts Architecture

### 🚀 **Generic Knowledge Manager (`generic_knowledge_manager.py`)**

This is the **primary tool** for all knowledge-related operations. It is designed to be domain-agnostic, driven by YAML configurations.

**Key Features:**
- 🌐 **Multi-Domain Knowledge Ingestion**: Scrapes and processes information from various sources (websites, APIs, files) based on YAML configurations.
- 🔌 **Pluggable Parsers**: Supports custom content parsers for domain-specific data extraction.
- ✅ **Data Quality Assurance**: Implements configurable quality checks to ensure the knowledge base is accurate and reliable.
- 🔄 **Incremental Updates**: Uses content hashing to efficiently update only the information that has changed.
- 🎯 **Integrated Testing**: Allows defining and running domain-specific relevance tests directly from the configuration file.

**Usage:**
```bash
# Initialize with an example configuration
python scripts/generic_knowledge_manager.py init

# Update all enabled domains
python scripts/generic_knowledge_manager.py update --force

# Update a specific domain
python scripts/generic_knowledge_manager.py update-domain --domain immigration

# Run tests for a specific domain
python scripts/generic_knowledge_manager.py test --domain immigration

# Get statistics for all domains
python scripts/generic_knowledge_manager.py stats
```

### 📋 **Infrastructure & Setup**
Scripts for one-time setup and system configuration.

- **`initialize_collections.py`**: Creates vector collections in Qdrant.
- **`create_indexes.py`**: Adds filtered search indexes to collections.
- **`check_qdrant.py`**: Verifies connectivity and system health.

### ⚙️ **System & Lifecycle Management**
Specialized tools for ongoing maintenance.

- **`schedule_kb_updates.py`**: Schedules periodic knowledge base updates using the generic manager.
- **`data_retention_manager.py`**: Manages data lifecycle and retention policies, cleaning up old data.

## 🗂️ Configuration-Driven Workflow

The entire system is driven by `config/domains.yaml`. This file allows you to define multiple knowledge domains, their data sources, quality rules, and tests.

```yaml
# config/domains.yaml
domains:
  immigration:
    description: "Immigration and visa information"
    collection_name: "immigration_docs"
    update_frequency_days: 7
    quality_rules:
      min_length: 50
      required_patterns: ["immigration", "visa"]
    sources:
      - name: "Canada_Express_Entry"
        url: "https://www.canada.ca/en/..."
        type: "website"
    test_queries:
      - query: "How to apply for Express Entry?"
        relevant: true
      - query: "What is the best car to buy?"
        relevant: false
```

## 🚀 Quick Start Guide

1.  **Initialize**:
    ```bash
    python scripts/generic_knowledge_manager.py init
    ```
    This creates `config/domains.yaml`. Customize it for your needs.

2.  **Setup Infrastructure**:
    ```bash
    python scripts/initialize_collections.py
    python scripts/create_indexes.py
    ```

3.  **Populate Knowledge Base**:
    ```bash
    python scripts/generic_knowledge_manager.py update --force
    ```

4.  **Test a Domain**:
    ```bash
    python scripts/generic_knowledge_manager.py test --domain immigration
    ```

5.  **Schedule Updates**:
    ```bash
    # See schedule_kb_updates.py for examples
    # (e.g., using cron or a Python scheduler)
    ```
    
## 🧹 Final Script Cleanup Summary

- **DELETED**: `unified_knowledge_manager.py`, `test_boundary_detection.py`, and 9 other legacy scripts.
- **PROMOTED**: `generic_knowledge_manager.py` is the new primary tool.
- **RESULT**: A cleaner, more powerful, and genuinely generic knowledge management system.

## 🗂️ Configuration Files

### `data/immigration_sites.json`
Website configurations for knowledge base updates:
```json
[
  {
    "name": "IRCC_PNP",
    "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/provincial-nominees.html",
    "domain": "canada_immigration",
    "lang": "en",
    "description": "Provincial Nominee Program",
    "priority": 1,
    "update_frequency": 3,
    "enabled": true
  }
]
```

## 🔧 Requirements

### Core Dependencies
- Python 3.8+
- Qdrant client library
- Valid Qdrant API key with cluster-wide write permissions

### Optional Dependencies
- `playwright` - For web scraping functionality
- `beautifulsoup4` - For HTML parsing
- `schedule` - For automated updates

### Installation
```bash
# Install core requirements
pip install qdrant-client python-dotenv

# Install web scraping dependencies
pip install playwright beautifulsoup4
playwright install

# Install scheduling dependencies
pip install schedule
```

## ⚙️ Environment Setup

Create a `.env` file in the project root:
```env
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
OPENAI_API_KEY=your_openai_key  # For embeddings
```

## 🚀 Quick Start Guide

### 1. Initial Setup
```bash
# Check system connectivity
python scripts/check_qdrant.py

# Initialize collections
python scripts/initialize_collections.py

# Create indexes
python scripts/create_indexes.py
```

### 2. Knowledge Base Management
```bash
# Interactive management (recommended for first-time users)
python scripts/generic_knowledge_manager.py init

# Or run specific operations
python scripts/generic_knowledge_manager.py update --force
python scripts/generic_knowledge_manager.py update-domain --domain immigration
python scripts/generic_knowledge_manager.py test --domain immigration
```

### 3. Ongoing Maintenance
```bash
# Set up automated updates
python scripts/schedule_kb_updates.py

# Regular quality checks
python scripts/generic_knowledge_manager.py stats
```

## 📊 Data Quality Features

The generic manager includes sophisticated data quality detection:

### Problem Patterns Detected
- **Automotive Content**: Car-related content misclassified as immigration
- **Real Estate**: Property investment content not related to immigration
- **General Chat**: Non-immigration conversational content
- **Empty Records**: Incomplete or invalid data entries

### Confidence Scoring
- **High Confidence (>0.7)**: Automatically flagged for cleanup
- **Medium Confidence (0.3-0.7)**: Manual review recommended
- **Low Confidence (<0.3)**: Preserved with monitoring

### Boundary Detection Testing
Automated testing with predefined query sets:
- ✅ Immigration-related: PNP, Express Entry, SUV (Start-up Visa)
- ❌ Non-immigration: Car recommendations, real estate, weather

## 🔄 Automated Workflows

### Daily Operations
1. **Health Check**: System connectivity and collection status
2. **Data Quality Scan**: Identify problematic records
3. **Boundary Testing**: Verify classification accuracy

### Weekly Operations
1. **Knowledge Base Update**: Scrape latest content from official sites
2. **Data Cleanup**: Remove identified problematic records
3. **Performance Analysis**: Generate quality reports

### Monthly Operations
1. **Deep Quality Analysis**: Comprehensive data quality assessment
2. **Configuration Review**: Update website configurations
3. **Retention Management**: Archive or remove outdated content

## 🧹 Migration from Legacy Scripts

The following legacy scripts have been **consolidated** into `generic_knowledge_manager.py`:

### Removed Scripts
- ~~`smart_knowledge_updater.py`~~ → Knowledge base updates
- ~~`comprehensive_data_cleaner.py`~~ → Data quality management
- ~~`analyze_false_positive.py`~~ → Analysis capabilities
- ~~`clean_canonical_queries.py`~~ → Specific cleanup operations
- ~~`kb_updater.py`~~ → Web scraping functionality
- ~~`intelligent_knowledge_pipeline.py`~~ → Pipeline management
- ~~`force_clean_problems.py`~~ → Problem resolution

### Migration Benefits
- **Single Point of Control**: All knowledge management in one tool
- **Consistent Interface**: Unified command structure across operations
- **Reduced Complexity**: Eliminated script overlap and redundancy
- **Better Testing**: Integrated validation and verification
- **Improved Logging**: Centralized reporting and monitoring

## 🛠️ Troubleshooting

### Common Issues

**Connection Problems**
```bash
python scripts/check_qdrant.py  # Verify connectivity
```

**Missing Collections**
```bash
python scripts/initialize_collections.py  # Recreate collections
```

**Poor Boundary Detection**
```bash
python scripts/generic_knowledge_manager.py test --domain immigration  # Check accuracy
python scripts/generic_knowledge_manager.py update --force  # Clean bad data
```

**Outdated Knowledge Base**
```bash
python scripts/generic_knowledge_manager.py update --force  # Force update
```

### Performance Optimization

**Large Collections**
- Use batch operations for bulk updates
- Monitor memory usage during operations
- Consider collection partitioning for very large datasets

**Network Issues**
- Configure appropriate timeouts for web scraping
- Implement retry logic for failed operations
- Use rate limiting to avoid being blocked

## 📈 Monitoring & Analytics

### Key Metrics
- **Collection Sizes**: Number of records per collection
- **Data Quality Score**: Percentage of clean vs problematic records
- **Boundary Detection Accuracy**: Classification correctness rate
- **Update Frequency**: How often content changes

### Reporting
The generic manager generates comprehensive reports including:
- Data quality analysis results
- Boundary detection test outcomes
- Knowledge base statistics
- Cleaning operation summaries

## 🤝 Contributing

When adding new functionality:

1. **Use Generic Manager**: Add features to `generic_knowledge_manager.py`
2. **Follow Patterns**: Maintain consistent code structure and interfaces
3. **Add Tests**: Include boundary detection test cases for new features
4. **Update Documentation**: Keep this README current with changes

## 📚 Related Documentation

- **System Architecture**: See `/docs` for overall system design
- **API Documentation**: Vector store and embedding interfaces
- **Configuration Guide**: Detailed setup and configuration options
- **Deployment Guide**: Production deployment considerations

# Knowledge Base Management Scripts

This directory contains scripts for managing the Generic AI Agent's knowledge base.

## Core Scripts

### 1. generic_knowledge_manager.py
The main knowledge management system that handles:
- Multi-domain knowledge organization
- Quality control and filtering
- Deep web crawling with AI evaluation using Playwright
- Incremental updates
- Human review workflow

**Key Features:**
- **Domain-based organization**: Separate collections for different topics
- **Quality filtering**: Semantic similarity checks and content validation
- **Smart crawling**: Uses AI to evaluate page importance during deep crawls
- **Review system**: Saves borderline content for human review

### 2. simple_intelligent_crawler.py
A simplified intelligent web crawler that:
- Uses Playwright for robust web scraping
- Employs AI to evaluate page relevance and importance
- Generates summaries for each crawled page
- Creates detailed crawl reports

**Usage:**
```bash
python scripts/simple_intelligent_crawler.py \
  --url https://example.com \
  --topic "Your topic of interest" \
  --max-pages 10 \
  --max-depth 2
```

### 3. monitor_updates.py
Monitors configured websites for updates using sitemaps:
- Lightweight monitoring without full page downloads
- Detects new and updated pages
- Creates update queues for incremental processing

### 4. schedule_kb_updates.py
Sets up cron jobs for automated knowledge base maintenance:
- Daily monitoring for updates
- Weekly full updates
- Monthly data cleanup

### 5. data_retention_manager.py
Manages data lifecycle and compliance:
- Removes outdated content
- Handles right-to-be-forgotten requests
- Maintains audit logs

## Setup and Configuration

1. **Install dependencies:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Configure domains:**
   Create YAML files in `config/domains/` for each knowledge domain.

3. **Run initial setup:**
   ```bash
   python scripts/generic_knowledge_manager.py init
   ```

## Common Workflows

### Adding a New Knowledge Source
1. Create/edit domain configuration in `config/domains/`
2. Run deep crawl:
   ```bash
   python scripts/generic_knowledge_manager.py update-domain --domain your_domain
   ```

### Monitoring for Updates
```bash
# One-time check
python scripts/monitor_updates.py check-all

# Setup automated monitoring
python scripts/schedule_kb_updates.py setup
```

### Processing Human Reviews
```bash
# Review files in kb_review/ directory
# Mark items as 'approved' or 'rejected'
# Then process:
python scripts/generic_knowledge_manager.py process-reviews
```

## Architecture Notes

- **No browser-use dependency**: We use Playwright directly for better stability and control
- **Custom LLM integration**: Works with the project's own LLM infrastructure
- **Modular design**: Each script handles a specific aspect of knowledge management 