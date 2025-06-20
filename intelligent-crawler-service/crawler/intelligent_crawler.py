"""
Core Intelligent Crawler Implementation
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib

from playwright.async_api import async_playwright, Page, Browser
import aiohttp

from ai.evaluator import ContentEvaluator
from ai.extractor import IntelligentExtractor
from core.models import CrawlResult, CrawlConfig, PageContent
from utils.url_utils import normalize_url, is_valid_url, should_crawl_url

logger = logging.getLogger(__name__)

class IntelligentCrawler:
    """
    AI-powered web crawler with intelligent content extraction
    """
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.evaluator = ContentEvaluator()
        self.extractor = IntelligentExtractor()
        self.visited_urls: Set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.results: List[CrawlResult] = []
        self.browser: Optional[Browser] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize crawler resources"""
        # Start browser
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # Create HTTP session for quick checks
        self.session = aiohttp.ClientSession()
        
        logger.info("Crawler initialized")
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.session:
            await self.session.close()
            
    async def crawl(self, urls: List[str]) -> List[CrawlResult]:
        """
        Main crawl method
        """
        try:
            await self.initialize()
            
            # Add initial URLs to queue
            for url in urls:
                normalized = normalize_url(url)
                if normalized:
                    await self.url_queue.put((normalized, 0))  # (url, depth)
            
            # Start crawler workers
            workers = []
            for i in range(self.config.max_concurrent):
                worker = asyncio.create_task(self._crawl_worker(i))
                workers.append(worker)
            
            # Wait for queue to be empty
            await self.url_queue.join()
            
            # Cancel workers
            for worker in workers:
                worker.cancel()
            
            # Wait for all workers to finish
            await asyncio.gather(*workers, return_exceptions=True)
            
            logger.info(f"Crawl completed. Total pages: {len(self.results)}")
            return self.results
            
        finally:
            await self.cleanup()
    
    async def _crawl_worker(self, worker_id: int):
        """Worker coroutine for crawling"""
        logger.info(f"Worker {worker_id} started")
        
        try:
            while True:
                try:
                    url, depth = await asyncio.wait_for(
                        self.url_queue.get(), 
                        timeout=10.0
                    )
                    
                    if url in self.visited_urls or depth > self.config.max_depth:
                        self.url_queue.task_done()
                        continue
                    
                    logger.info(f"Worker {worker_id} crawling: {url} (depth: {depth})")
                    
                    # Crawl the page
                    result = await self._crawl_page(url, depth)
                    
                    if result:
                        self.results.append(result)
                        
                        # Add discovered URLs to queue
                        if result.links and depth < self.config.max_depth:
                            for link in result.links[:self.config.max_links_per_page]:
                                normalized = normalize_url(link)
                                if normalized and normalized not in self.visited_urls:
                                    await self.url_queue.put((normalized, depth + 1))
                    
                    self.url_queue.task_done()
                    
                except asyncio.TimeoutError:
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
            raise
    
    async def _crawl_page(self, url: str, depth: int) -> Optional[CrawlResult]:
        """Crawl a single page"""
        
        # Mark as visited
        self.visited_urls.add(url)
        
        try:
            # Quick pre-check with HTTP HEAD
            if self.config.ai_evaluation:
                should_crawl = await self._quick_evaluation(url)
                if not should_crawl:
                    logger.info(f"Skipping {url} - failed quick evaluation")
                    return None
            
            # Create browser page
            page = await self.browser.new_page()
            
            try:
                # Navigate to page
                response = await page.goto(
                    url, 
                    wait_until='domcontentloaded',
                    timeout=self.config.page_timeout * 1000
                )
                
                if not response or response.status >= 400:
                    logger.warning(f"Failed to load {url}: status {response.status if response else 'None'}")
                    return None
                
                # Wait for dynamic content if needed
                if self.config.wait_for_dynamic:
                    await page.wait_for_load_state('networkidle', timeout=self.config.page_timeout * 1000)
                
                # Extract page content
                page_content = await self._extract_page_content(page, url)
                
                # AI evaluation
                if self.config.ai_evaluation:
                    evaluation = await self.evaluator.evaluate_content(page_content)
                    
                    if evaluation.quality_score < self.config.min_quality_score:
                        logger.info(f"Skipping {url} - low quality score: {evaluation.quality_score}")
                        return None
                    
                    page_content.ai_evaluation = evaluation
                
                # Intelligent extraction
                if self.config.intelligent_extraction:
                    extracted_data = await self.extractor.extract_structured_data(
                        page, 
                        page_content,
                        self.config.extraction_schema
                    )
                    page_content.structured_data = extracted_data
                
                # Extract links
                links = await self._extract_links(page, url)
                
                # Create result
                result = CrawlResult(
                    url=url,
                    depth=depth,
                    content=page_content,
                    links=links,
                    crawled_at=datetime.utcnow(),
                    success=True
                )
                
                logger.info(f"Successfully crawled {url}")
                return result
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return CrawlResult(
                url=url,
                depth=depth,
                error=str(e),
                crawled_at=datetime.utcnow(),
                success=False
            )
    
    async def _quick_evaluation(self, url: str) -> bool:
        """Quick evaluation using HTTP HEAD and URL analysis"""
        try:
            # URL pattern analysis
            url_score = self._evaluate_url_pattern(url)
            if url_score < 0.3:
                return False
            
            # HTTP HEAD check
            async with self.session.head(url, timeout=5) as response:
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if not any(ct in content_type for ct in ['text/html', 'application/xhtml']):
                    return False
                
                # Check content length
                content_length = int(response.headers.get('Content-Length', 0))
                if content_length > 0 and content_length < 1000:  # Too small
                    return False
                    
            return True
            
        except Exception as e:
            logger.debug(f"Quick evaluation failed for {url}: {e}")
            return True  # Give it a chance
    
    def _evaluate_url_pattern(self, url: str) -> float:
        """Evaluate URL pattern for relevance"""
        score = 0.5  # Base score
        
        url_lower = url.lower()
        
        # Positive indicators
        positive_patterns = [
            'guide', 'how-to', 'tutorial', 'documentation',
            'requirements', 'eligibility', 'process', 'apply',
            'faq', 'help', 'support', 'resources'
        ]
        
        for pattern in positive_patterns:
            if pattern in url_lower:
                score += 0.1
        
        # Negative indicators
        negative_patterns = [
            'login', 'signin', 'register', 'account',
            'cart', 'checkout', 'payment',
            'privacy', 'terms', 'cookie',
            'contact', 'about', 'career'
        ]
        
        for pattern in negative_patterns:
            if pattern in url_lower:
                score -= 0.2
                
        return max(0, min(1, score))
    
    async def _extract_page_content(self, page: Page, url: str) -> PageContent:
        """Extract content from page"""
        
        # Get title
        title = await page.title()
        
        # Get meta description
        description = await page.evaluate('''
            () => {
                const meta = document.querySelector('meta[name="description"]');
                return meta ? meta.content : '';
            }
        ''')
        
        # Get main content
        content = await page.evaluate('''
            () => {
                // Remove script and style elements
                const scripts = document.querySelectorAll('script, style, noscript');
                scripts.forEach(el => el.remove());
                
                // Try to find main content area
                const mainSelectors = ['main', 'article', '#content', '.content', '[role="main"]'];
                let mainContent = null;
                
                for (const selector of mainSelectors) {
                    mainContent = document.querySelector(selector);
                    if (mainContent) break;
                }
                
                // Fall back to body if no main content found
                if (!mainContent) {
                    mainContent = document.body;
                }
                
                return {
                    text: mainContent.innerText,
                    html: mainContent.innerHTML
                };
            }
        ''')
        
        # Extract tables if configured
        tables = []
        if self.config.extract_tables:
            tables = await self._extract_tables(page)
        
        # Extract images info if configured
        images = []
        if self.config.extract_images:
            images = await self._extract_images(page)
        
        # Generate content hash
        content_hash = hashlib.sha256(content['text'].encode()).hexdigest()
        
        return PageContent(
            url=url,
            title=title,
            description=description,
            text=content['text'],
            html=content['html'],
            tables=tables,
            images=images,
            content_hash=content_hash,
            extracted_at=datetime.utcnow()
        )
    
    async def _extract_tables(self, page: Page) -> List[Dict]:
        """Extract tables from page"""
        return await page.evaluate('''
            () => {
                const tables = document.querySelectorAll('table');
                const results = [];
                
                tables.forEach((table, index) => {
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                    const rows = [];
                    
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim());
                        if (cells.length > 0) {
                            rows.push(cells);
                        }
                    });
                    
                    if (headers.length > 0 || rows.length > 0) {
                        results.push({
                            index: index,
                            headers: headers,
                            rows: rows,
                            caption: table.querySelector('caption')?.innerText || ''
                        });
                    }
                });
                
                return results;
            }
        ''')
    
    async def _extract_images(self, page: Page) -> List[Dict]:
        """Extract image information"""
        return await page.evaluate('''
            () => {
                const images = document.querySelectorAll('img');
                const results = [];
                
                images.forEach((img, index) => {
                    if (img.width > 100 && img.height > 100) {  // Skip small images
                        results.push({
                            src: img.src,
                            alt: img.alt,
                            width: img.width,
                            height: img.height
                        });
                    }
                });
                
                return results;
            }
        ''')
    
    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """Extract and normalize links from page"""
        
        raw_links = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('a[href]');
                return Array.from(links).map(link => link.href);
            }
        ''')
        
        # Normalize and filter links
        valid_links = []
        base_domain = urlparse(base_url).netloc
        
        for link in raw_links:
            try:
                # Make absolute URL
                absolute_url = urljoin(base_url, link)
                
                # Check if should crawl
                if should_crawl_url(absolute_url, base_domain, self.config):
                    valid_links.append(absolute_url)
                    
            except Exception as e:
                logger.debug(f"Error processing link {link}: {e}")
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in valid_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links