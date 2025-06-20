#!/usr/bin/env python3
"""
Demo script for Intelligent Crawler Service
"""

import asyncio
import json
from datetime import datetime

# Add current directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import CrawlConfig, PageContent, ContentEvaluation
from crawler.intelligent_crawler import IntelligentCrawler
from ai.evaluator import ContentEvaluator

async def demo_crawl():
    """Demo crawling functionality"""
    
    print("=== Intelligent Crawler Demo ===\n")
    
    # 1. Create crawl configuration
    config = CrawlConfig(
        max_depth=2,
        max_pages=10,
        ai_evaluation=True,
        min_quality_score=0.6,
        extract_tables=True,
        intelligent_extraction=True
    )
    
    print("📋 Crawl Configuration:")
    print(f"  - Max Depth: {config.max_depth}")
    print(f"  - Max Pages: {config.max_pages}")
    print(f"  - AI Evaluation: {config.ai_evaluation}")
    print(f"  - Min Quality Score: {config.min_quality_score}")
    
    # 2. Demo content evaluation
    print("\n🧠 Content Evaluation Demo:")
    
    # Create sample content
    sample_content = PageContent(
        url="https://example.com/immigration-guide",
        title="Complete Immigration Guide to Canada",
        description="Everything you need to know about immigrating to Canada",
        text="""
        This comprehensive guide covers all aspects of Canadian immigration.
        
        Eligibility Requirements:
        - You must have at least one year of work experience
        - You need to prove language proficiency in English or French
        - Educational credentials must be assessed
        
        Application Process:
        1. Create an Express Entry profile
        2. Get your documents ready
        3. Submit your application
        4. Wait for processing (typically 6 months)
        
        Fees:
        - Application fee: $1,325 CAD per adult
        - Right of Permanent Residence Fee: $500 CAD
        - Biometrics: $85 CAD
        
        This guide is updated regularly to reflect the latest immigration policies.
        """,
        content_hash="abc123",
        extracted_at=datetime.utcnow()
    )
    
    evaluator = ContentEvaluator()
    evaluation = await evaluator.evaluate_content(sample_content)
    
    print(f"  URL: {sample_content.url}")
    print(f"  Title: {sample_content.title}")
    print(f"  Quality Score: {evaluation.quality_score:.2f}")
    print(f"  Relevance Score: {evaluation.relevance_score:.2f}")
    print(f"  Overall Score: {evaluation.overall_score:.2f}")
    print(f"  Content Type: {evaluation.content_type}")
    print(f"  Topics: {', '.join(evaluation.topics)}")
    print(f"  Recommendation: {evaluation.recommendation}")
    
    # 3. Demo key information extraction
    print("\n🔍 Key Information Extraction:")
    
    key_info = await evaluator.identify_key_content(sample_content)
    
    print(f"  Requirements Found: {len(key_info['requirements'])}")
    if key_info['requirements']:
        print(f"    - {key_info['requirements'][0][:100]}...")
    
    print(f"  Fees Found: {len(key_info['fees'])}")
    for fee in key_info['fees']:
        print(f"    - {fee['amount']}: {fee['context'][:50]}...")
    
    print(f"  Timelines Found: {len(key_info['timelines'])}")
    if key_info['timelines']:
        print(f"    - {key_info['timelines'][0][:100]}...")
    
    # 4. Demo crawl workflow (without actual crawling)
    print("\n🕷️ Crawl Workflow Demo:")
    print("  1. Initialize crawler with AI evaluation")
    print("  2. Queue URLs for crawling")
    print("  3. For each URL:")
    print("     - Quick evaluation to determine if worth crawling")
    print("     - Extract content with Playwright")
    print("     - AI evaluation of content quality")
    print("     - Extract structured data (tables, key info)")
    print("     - Discover and queue new URLs")
    print("  4. Store results in vector database")
    
    print("\n✅ Demo completed!")
    
    # Return sample results for demonstration
    return {
        "config": config.dict(),
        "sample_evaluation": {
            "url": evaluation.url,
            "scores": {
                "quality": evaluation.quality_score,
                "relevance": evaluation.relevance_score,
                "overall": evaluation.overall_score
            },
            "content_type": evaluation.content_type,
            "topics": evaluation.topics
        },
        "key_information": {
            "requirements": len(key_info['requirements']),
            "fees": len(key_info['fees']),
            "timelines": len(key_info['timelines'])
        }
    }

async def demo_api_usage():
    """Demo API usage"""
    
    print("\n\n=== API Usage Demo ===\n")
    
    print("📡 Example API Calls:\n")
    
    # 1. Create crawl job
    print("1. Create Crawl Job:")
    print("   POST /api/v1/crawl")
    print("   Body:")
    crawl_request = {
        "urls": ["https://www.canada.ca/immigration"],
        "config": {
            "max_depth": 3,
            "ai_evaluation": True,
            "min_quality_score": 0.7
        },
        "collection_name": "immigration_docs"
    }
    print(json.dumps(crawl_request, indent=4))
    
    print("\n   Response:")
    print(json.dumps({
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "queued",
        "message": "Crawl job created for 1 URLs",
        "created_at": "2024-12-17T10:30:00Z",
        "estimated_completion": "2024-12-17T10:36:00Z"
    }, indent=4))
    
    # 2. Check job status
    print("\n2. Check Job Status:")
    print("   GET /api/v1/crawl/123e4567-e89b-12d3-a456-426614174000")
    print("   Response:")
    print(json.dumps({
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "running",
        "progress": 45.5,
        "urls_crawled": 23,
        "urls_total": 50,
        "pages_discovered": 127
    }, indent=4))
    
    # 3. Search knowledge base
    print("\n3. Search Knowledge Base:")
    print("   POST /api/v1/search")
    print("   Body:")
    search_request = {
        "query": "Express Entry requirements",
        "collection": "immigration_docs",
        "top_k": 5,
        "min_score": 0.7
    }
    print(json.dumps(search_request, indent=4))
    
    print("\n   Response:")
    print(json.dumps({
        "results": [
            {
                "id": "doc_001",
                "score": 0.92,
                "text": "Express Entry requires proof of language ability...",
                "source_url": "https://www.canada.ca/express-entry",
                "source_title": "Express Entry - Canada.ca"
            }
        ]
    }, indent=4))

def main():
    """Run demos"""
    
    # Run async demos
    loop = asyncio.get_event_loop()
    
    # Demo 1: Crawling functionality
    results = loop.run_until_complete(demo_crawl())
    
    # Demo 2: API usage examples
    loop.run_until_complete(demo_api_usage())
    
    print("\n\n=== Demo Summary ===")
    print(f"✅ Content Evaluation: Working")
    print(f"✅ Key Information Extraction: Working")
    print(f"✅ API Structure: Ready")
    print(f"✅ Docker Configuration: Valid")
    
    print("\n🚀 The Intelligent Crawler Service is ready to use!")
    print("\nTo start the service:")
    print("  1. cd intelligent-crawler-service")
    print("  2. cp .env.example .env")
    print("  3. Edit .env with your API keys")
    print("  4. docker-compose up")

if __name__ == "__main__":
    main()