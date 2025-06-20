# Project Structure

Last Updated: June 2025

## Overview

Generic AI Agent is a domain-agnostic intelligent assistant system with web crawling, knowledge management, and QA capabilities.

## Directory Structure

```
generic-ai-agent/
├── README.md                    # Main project documentation
├── PROJECT_SUMMARY.md           # Business and technical overview
├── COMPLIANCE_GUIDE.md          # Data protection and compliance
├── IMPROVEMENT_TRACKER.md       # Development roadmap
├── LICENSE                      # Project license
├── requirements.txt             # Python dependencies
├── start_telegram_bot.py        # Telegram bot entry point
├── run_weekly_cleanup.sh        # Scheduled cleanup automation
│
├── src/                         # Main application source code
│   ├── app/                     # Application modules
│   │   ├── agent/              # Agent intelligence modules
│   │   ├── api/                # API endpoints
│   │   ├── ingestion/          # Data ingestion modules
│   │   ├── knowledge/          # Knowledge management
│   │   └── user/               # User management
│   ├── infrastructure/         # Infrastructure layer
│   │   ├── audit/              # Compliance and audit logging
│   │   ├── config/             # Configuration management
│   │   ├── llm/                # LLM client implementations
│   │   └── vector_store/       # Vector database interfaces
│   └── main.py                 # Main application entry
│
├── scripts/                     # Utility and management scripts
│   ├── README.md               # Scripts documentation
│   ├── SCRIPT_SUMMARY.md       # Script consolidation overview
│   ├── generic_knowledge_manager.py  # Main knowledge management tool
│   ├── initialize_collections.py     # Qdrant collection setup
│   ├── create_indexes.py            # Search index creation
│   ├── check_qdrant.py             # Qdrant health check
│   ├── data_retention_manager.py   # Compliance data management
│   ├── schedule_kb_updates.py      # Automated update scheduling
│   ├── monitor_updates.py          # Website change monitoring
│   ├── monitor_bot.py              # Telegram bot monitoring
│   ├── scrapy_intelligent_crawler.py    # High-speed static crawler
│   └── simple_intelligent_crawler.py    # JavaScript-enabled crawler
│
├── intelligent-crawler-service/  # Microservice crawler implementation
│   ├── README.md               # Service documentation
│   ├── DEPLOYMENT.md           # Deployment guide
│   ├── DEVELOPMENT_GUIDE.md    # Developer guide
│   ├── TASK_TRACKER.md         # Development tracking
│   ├── docker-compose.yml      # Service orchestration
│   ├── ai/                     # AI evaluation modules
│   ├── api/                    # REST API implementation
│   ├── crawler/                # Crawler core logic
│   ├── scripts/                # Service-specific tools
│   └── docker/                 # Dockerfiles
│
├── docs/                        # Documentation
│   ├── README.md               # Documentation index
│   ├── crawler/                # Crawler-specific docs
│   │   ├── README.md           # Crawler docs index
│   │   ├── CRAWLER_IMPROVEMENT_PLAN.md
│   │   ├── AI_AUTONOMOUS_CRAWLER_SYSTEM.md
│   │   ├── AI_INCREMENTAL_UPDATE_SYSTEM.md
│   │   ├── CRAWLER_HUMAN_REVIEW_SYSTEM.md
│   │   └── DOCKER_CRAWLER_SERVICE_DESIGN.md
│   ├── compliance_docs/        # Compliance documentation
│   ├── crawl_reports/          # Crawl execution reports
│   ├── archived/               # Historical documents
│   ├── domain_integration_guide.md
│   ├── web_crawler_guide.md
│   ├── boundary_detection_best_practices.md
│   └── GENERIC_KNOWLEDGE_BEST_PRACTICES.md
│
├── config/                      # Configuration files
│   ├── domains.yaml            # Domain configurations
│   └── domains/                # Domain-specific configs
│
├── data/                        # Data storage
│   ├── kb_sites.json           # Knowledge base sites
│   └── needs_review/           # Content requiring review
│
├── cache/                       # Temporary cache
│   ├── knowledge/              # Knowledge cache
│   └── page_content/           # Page content cache
│
├── audit_logs/                  # Compliance audit logs
│   ├── audit.jsonl
│   ├── pii_access.jsonl
│   └── system.jsonl
│
├── domains/                     # Domain definitions
├── tags/                        # Tag definitions
└── tests/                       # Test suites
```

## Key Components

### 1. Core Application (`src/`)
- **app/**: Business logic and features
- **infrastructure/**: Technical infrastructure and integrations
- **main.py**: Application entry point

### 2. Scripts (`scripts/`)
- **generic_knowledge_manager.py**: Primary management tool for crawling, testing, and quality control
- Infrastructure scripts for setup and maintenance
- Specialized crawlers for different website types

### 3. Intelligent Crawler Service (`intelligent-crawler-service/`)
- Dockerized microservice implementation
- REST API for crawler operations
- AI-powered content evaluation
- Distributed task processing with Celery

### 4. Documentation (`docs/`)
- Comprehensive guides and best practices
- Crawler architecture documents
- Compliance and regulatory documentation
- Historical/archived documents

### 5. Configuration (`config/`)
- Domain-specific configurations
- Crawling rules and patterns
- System settings

## Entry Points

1. **start_telegram_bot.py** - Telegram bot interface
2. **src/main.py** - Main application server
3. **intelligent-crawler-service/api/main.py** - Crawler service API
4. **scripts/generic_knowledge_manager.py** - CLI management tool

## Data Flow

1. **Input**: User queries via Telegram bot or API
2. **Processing**: 
   - Query normalization and routing
   - Vector similarity search
   - LLM-based response generation
3. **Knowledge Update**:
   - Automated crawling via intelligent-crawler-service
   - Content evaluation and quality control
   - Vector database updates
4. **Output**: Contextual responses with source citations

## Recent Changes

- Consolidated crawler documentation into `docs/crawler/`
- Merged crawler collection initialization into main script
- Removed redundant scripts and documentation
- Organized root directory for cleaner structure
- Archived historical/completed documents