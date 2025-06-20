"""
Core data models
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class CrawlStatus(str, Enum):
    """Crawl job status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ContentType(str, Enum):
    """Content type classification"""
    GUIDE = "guide"
    FAQ = "faq"
    REFERENCE = "reference"
    TUTORIAL = "tutorial"
    NEWS = "news"
    POLICY = "policy"
    FORM = "form"
    TOOL = "tool"
    UNKNOWN = "unknown"

class CrawlConfig(BaseModel):
    """Crawl configuration"""
    max_depth: int = Field(default=3, ge=0, le=10)
    max_pages: int = Field(default=100, ge=1, le=10000)
    max_concurrent: int = Field(default=5, ge=1, le=20)
    page_timeout: int = Field(default=30, ge=5, le=120)  # seconds
    
    # AI Features
    ai_evaluation: bool = Field(default=True)
    min_quality_score: float = Field(default=0.6, ge=0, le=1)
    intelligent_extraction: bool = Field(default=True)
    
    # Content Processing
    extract_tables: bool = Field(default=True)
    extract_images: bool = Field(default=False)
    extract_pdfs: bool = Field(default=True)
    handle_javascript: bool = Field(default=True)
    wait_for_dynamic: bool = Field(default=True)
    
    # URL Filtering
    allowed_domains: Optional[List[str]] = Field(default=None)
    exclude_patterns: Optional[List[str]] = Field(default=None)
    include_patterns: Optional[List[str]] = Field(default=None)
    respect_robots_txt: bool = Field(default=True)
    
    # Extraction Schema
    extraction_schema: Optional[Dict[str, Any]] = Field(default=None)
    
    # Performance
    max_links_per_page: int = Field(default=50)
    cache_enabled: bool = Field(default=True)
    
class PageContent(BaseModel):
    """Extracted page content"""
    url: str
    title: str
    description: Optional[str] = None
    text: str
    html: Optional[str] = None
    markdown: Optional[str] = None
    
    # Extracted data
    tables: List[Dict] = Field(default_factory=list)
    images: List[Dict] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    
    # Metadata
    content_hash: str
    extracted_at: datetime
    
    # AI Analysis
    ai_evaluation: Optional['ContentEvaluation'] = None
    structured_data: Optional[Dict[str, Any]] = None
    key_information: Optional[Dict[str, Any]] = None

class ContentEvaluation(BaseModel):
    """AI content evaluation results"""
    url: str
    quality_score: float = Field(ge=0, le=1)
    relevance_score: float = Field(ge=0, le=1)
    completeness_score: float = Field(ge=0, le=1)
    freshness_score: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    
    topics: List[str] = Field(default_factory=list)
    content_type: str = ContentType.UNKNOWN
    target_audience: Optional[str] = None
    quality_issues: List[str] = Field(default_factory=list)
    recommendation: str = Field(default="neutral")  # keep, skip, review
    
    evaluated_at: datetime

class CrawlResult(BaseModel):
    """Result of crawling a single page"""
    url: str
    depth: int
    success: bool
    
    # Content
    content: Optional[PageContent] = None
    
    # Discovery
    links: List[str] = Field(default_factory=list)
    new_domains: List[str] = Field(default_factory=list)
    
    # Metadata
    crawled_at: datetime
    duration_ms: Optional[int] = None
    
    # Error info
    error: Optional[str] = None
    error_type: Optional[str] = None

class CrawlJob(BaseModel):
    """Crawl job definition"""
    job_id: str
    urls: List[str]
    config: CrawlConfig
    collection_name: str = "default"
    
    # Status
    status: CrawlStatus = CrawlStatus.QUEUED
    progress: float = Field(default=0, ge=0, le=100)
    
    # Results
    urls_crawled: int = 0
    pages_discovered: int = 0
    pages_processed: int = 0
    errors: List[Dict] = Field(default_factory=list)
    
    # Timing
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Callback
    callback_url: Optional[str] = None
    
    # Results preview
    results_preview: Optional[List[Dict]] = None

class VectorDocument(BaseModel):
    """Document ready for vectorization"""
    id: str
    collection: str
    
    # Content
    text: str
    metadata: Dict[str, Any]
    
    # Chunking
    chunk_id: Optional[int] = None
    chunk_total: Optional[int] = None
    
    # Source
    source_url: str
    source_title: str
    
    # Timestamps
    crawled_at: datetime
    vectorized_at: Optional[datetime] = None

class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    collection: str = "default"
    
    # Search parameters
    top_k: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.7, ge=0, le=1)
    
    # Filters
    metadata_filters: Optional[Dict[str, Any]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Options
    include_metadata: bool = True
    include_scores: bool = True
    rerank: bool = True

class SearchResult(BaseModel):
    """Search result model"""
    id: str
    score: float
    
    # Content
    text: str
    metadata: Dict[str, Any]
    
    # Source
    source_url: str
    source_title: str
    
    # Highlights
    highlights: Optional[List[str]] = None

class UpdateCheck(BaseModel):
    """Incremental update check result"""
    url: str
    has_changed: bool
    change_type: Optional[str] = None  # content, removed, error
    
    # Change details
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    change_summary: Optional[str] = None
    
    # Priority
    update_priority: float = Field(default=0.5, ge=0, le=1)
    
    checked_at: datetime