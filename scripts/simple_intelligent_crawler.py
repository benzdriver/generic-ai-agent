#!/usr/bin/env python3
"""
简化版智能爬虫 - 使用Playwright和AI评估进行智能网站爬取
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse
from dataclasses import dataclass
import argparse

from playwright.async_api import async_playwright
from src.infrastructure.llm.factory import LLMFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrawlResult:
    """爬取结果"""
    url: str
    title: str
    content: str
    importance_score: float
    depth: int
    links_found: int
    summary: str = ""

class SimpleIntelligentCrawler:
    """简化版智能爬虫"""
    
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.target_domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.results = []  # 保存爬取结果
        self.stats = {}    # 保存统计信息
        self.llm = None
        
    def _get_llm(self):
        """延迟加载LLM"""
        if self.llm is None:
            try:
                from src.infrastructure.llm.factory import LLMFactory
                self.llm = LLMFactory.get_llm()
            except:
                logger.warning("无法加载LLM，将跳过AI功能")
        return self.llm
        
    async def crawl(self, max_depth: int = 3, max_pages: int = 100,
                   exclude_patterns: List[str] = None) -> List[CrawlResult]:
        """执行爬取"""
        self.results = []
        url_queue = [(self.start_url, 0)]
        pages_crawled = 0
        exclude_patterns = exclude_patterns or []
        
        # 初始化统计信息
        self.stats = {
            'total_pages': 0,
            'total_links': 0,
            'pages_by_depth': {},
            'pages_by_importance': {'high': 0, 'medium': 0, 'low': 0},
            'skipped_low_importance': 0
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                while url_queue and pages_crawled < max_pages:
                    current_url, depth = url_queue.pop(0)
                    
                    if current_url in self.visited_urls or depth > max_depth:
                        continue
                        
                    # 显示进度
                    queue_info = f"Queue: {len(url_queue)} | Visited: {len(self.visited_urls)}"
                    logger.info(f"Crawling: {current_url} (depth: {depth}) | {queue_info}")
                    
                    try:
                        page = await browser.new_page()
                        await page.goto(current_url, wait_until='domcontentloaded', timeout=30000)
                        
                        title = await page.title()
                        content = await page.content()
                        
                        # Extract text content
                        text_content = await page.evaluate("""
                            () => {
                                // Remove script and style elements
                                const scripts = document.querySelectorAll('script, style');
                                scripts.forEach(el => el.remove());
                                
                                // Get text content
                                return document.body.innerText || document.body.textContent || '';
                            }
                        """)
                        
                        # Extract links
                        links = await page.evaluate("""
                            () => {
                                const links = Array.from(document.querySelectorAll('a[href]'));
                                return links.map(link => ({
                                    href: link.href,
                                    text: link.textContent.trim()
                                }));
                            }
                        """)
                        
                        await page.close()
                        
                        # Evaluate importance
                        importance_score = await self._evaluate_importance(title, text_content[:3000])
                        
                        # Generate summary for important pages
                        summary = ""
                        if importance_score >= 0.6 and self._get_llm():
                            summary = await self._generate_summary(title, text_content[:3000])
                        
                        result = CrawlResult(
                            url=current_url,
                            title=title,
                            content=text_content,
                            importance_score=importance_score,
                            depth=depth,
                            links_found=len(links),
                            summary=summary
                        )
                        
                        self.results.append(result)
                        self.visited_urls.add(current_url)
                        pages_crawled += 1
                        
                        # 更新统计信息
                        self.stats['total_pages'] += 1
                        self.stats['total_links'] += len(links)
                        self.stats['pages_by_depth'][depth] = self.stats['pages_by_depth'].get(depth, 0) + 1
                        
                        if importance_score >= 0.8:
                            self.stats['pages_by_importance']['high'] += 1
                        elif importance_score >= 0.5:
                            self.stats['pages_by_importance']['medium'] += 1
                        else:
                            self.stats['pages_by_importance']['low'] += 1
                        
                        # 智能决定是否继续爬取子链接
                        if depth < max_depth and importance_score >= 0.6:
                            logger.info(f"  Page importance {importance_score:.2f} >= 0.6, will crawl child links")
                            
                            # 根据重要性动态调整要爬取的链接数量
                            max_links_to_add = int(30 * importance_score)
                            links_added = 0
                            
                            for link in links:
                                if links_added >= max_links_to_add:
                                    break
                                    
                                href = link['href']
                                if self._is_valid_url(href, exclude_patterns) and href not in self.visited_urls:
                                    # 评估链接文本的相关性
                                    link_text = link['text'].lower()
                                    
                                    # 高优先级关键词
                                    high_priority_keywords = ['visa', 'immigration', 'apply', 'eligibility', 
                                                            'requirement', 'process', 'permit', 'residency',
                                                            'start-up', 'entrepreneur']
                                    
                                    # 中等优先级关键词
                                    medium_priority_keywords = ['canada', 'program', 'application', 'form', 
                                                              'guide', 'document', 'fee', 'timeline']
                                    
                                    if any(kw in link_text for kw in high_priority_keywords):
                                        url_queue.insert(0, (href, depth + 1))  # 最高优先级
                                        links_added += 1
                                    elif any(kw in link_text for kw in medium_priority_keywords):
                                        insert_pos = min(len(url_queue) // 2, 10)
                                        url_queue.insert(insert_pos, (href, depth + 1))
                                        links_added += 1
                                    elif importance_score >= 0.8:
                                        url_queue.append((href, depth + 1))
                                        links_added += 1
                                        
                        elif importance_score < 0.6:
                            logger.info(f"  Page importance {importance_score:.2f} < 0.6, skipping child links")
                            self.stats['skipped_low_importance'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error crawling {current_url}: {e}")
                        continue
                        
            finally:
                await browser.close()
                
        # 显示最终统计
        logger.info("\n=== 爬取统计 ===")
        logger.info(f"总页面数: {len(self.results)}")
        logger.info(f"总链接数: {self.stats['total_links']}")
        logger.info(f"按深度分布: {self.stats['pages_by_depth']}")
        logger.info(f"按重要性分布: {self.stats['pages_by_importance']}")
        logger.info(f"跳过的低重要性页面: {self.stats['skipped_low_importance']}")
        
        return self.results
    
    async def _evaluate_importance(self, title: str, content: str) -> float:
        """评估页面重要性"""
        # 首先尝试使用AI评估
        if self._get_llm():
            prompt = f"""
Rate the importance of this webpage for someone interested in Canadian immigration.
Title: {title}
Content preview: {content[:1000]}...

Rate from 0.0 to 1.0. Respond with ONLY the number.
"""
            try:
                response = self.llm.generate(prompt)
                return float(response.strip())
            except:
                pass
        
        # 如果AI不可用，使用基于规则的评估
        score = 0.0
        keywords = ['visa', 'immigration', 'permit', 'canada', 'apply', 'eligibility', 'requirement']
        
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 标题中的关键词
        for kw in keywords:
            if kw in title_lower:
                score += 0.15
                
        # 内容中的关键词密度
        keyword_count = sum(content_lower.count(kw) for kw in keywords)
        word_count = len(content_lower.split())
        if word_count > 0:
            keyword_density = keyword_count / word_count
            score += min(keyword_density * 10, 0.4)
            
        return min(score, 1.0)
            
    async def _generate_summary(self, title: str, content: str) -> str:
        """生成摘要"""
        prompt = f"""
Summarize this immigration webpage in 2-3 sentences.
Title: {title}
Content: {content[:2000]}...

Focus on key immigration information. Be concise and factual.
"""
        try:
            return self.llm.generate(prompt).strip()
        except:
            return ""
            
    def _is_valid_url(self, url: str, exclude_patterns: List[str]) -> bool:
        """检查URL是否有效"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            if self.target_domain not in parsed.netloc:
                return False
            
            # 默认排除模式
            default_exclude = ['/fr/', '/fra/', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                             'mailto:', 'javascript:', 'tel:', '#', '/news/', '/videos/']
            
            # 合并默认和自定义排除模式
            all_exclude = default_exclude + exclude_patterns
            
            # 检查URL是否匹配任何排除模式
            url_lower = url.lower()
            for pattern in all_exclude:
                if pattern in url_lower:
                    return False
                    
            return True
        except:
            return False
            
    def save_report(self, results: List[CrawlResult], output_file: Path):
        """保存报告"""
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 智能爬取报告\n\n")
            f.write(f"**日期:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**主题:** {self.topic}\n")
            f.write(f"**页面数:** {len(results)}\n\n")
            
            # Sort by importance
            sorted_results = sorted(results, key=lambda x: x.importance_score, reverse=True)
            
            f.write("## 页面列表\n\n")
            for i, result in enumerate(sorted_results, 1):
                f.write(f"### {i}. {result.title}\n")
                f.write(f"- **URL:** {result.url}\n")
                f.write(f"- **重要性:** {result.importance_score:.2f}\n")
                f.write(f"- **深度:** {result.depth}\n")
                f.write(f"- **链接数:** {result.links_found}\n")
                f.write(f"- **摘要:** {result.summary}\n\n")

    def generate_report(self, domain_name: str, source_name: str) -> Path:
        """生成爬取报告"""
        report_dir = Path("docs/crawl_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # 生成Markdown格式报告
        report_file_md = report_dir / f"playwright_report_{domain_name}_{source_name}_{timestamp_str}.md"
        
        with open(report_file_md, 'w', encoding='utf-8') as f:
            # 写入标题和元信息
            f.write("# 智能爬取审查报告\n\n")
            f.write(f"**生成日期:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**目标主题:** {domain_name} - {source_name}\n")
            f.write(f"**目标网站:** {self.start_url}\n")
            f.write(f"**爬取方式:** Playwright智能爬虫\n")
            f.write(f"**总计页面:** {len(self.results)}\n\n")
            
            # 写入统计信息
            f.write("## 爬取统计\n\n")
            f.write(f"- **总访问页面:** {self.stats.get('total_pages', 0)}\n")
            f.write(f"- **总发现链接:** {self.stats.get('total_links', 0)}\n")
            f.write(f"- **跳过低重要性:** {self.stats.get('skipped_low_importance', 0)}\n")
            f.write(f"- **深度分布:** {self.stats.get('pages_by_depth', {})}\n")
            
            pages_by_importance = self.stats.get('pages_by_importance', {})
            high = pages_by_importance.get('high', 0)
            medium = pages_by_importance.get('medium', 0) 
            low = pages_by_importance.get('low', 0)
            f.write(f"- **重要性分布:** 高({high}) / 中({medium}) / 低({low})\n\n")
            
            # 写入页面详情表格
            f.write("## 爬取页面详情\n\n")
            f.write("| 重要性 | 深度 | 链接 | 标题 | AI 生成摘要 |\n")
            f.write("|:---:|:---:|:---|:---|:---|\n")
            
            # 按重要性排序
            sorted_results = sorted(self.results, key=lambda x: x.importance_score, reverse=True)
            
            for result in sorted_results:
                # 重要性星级
                if result.importance_score >= 0.8:
                    importance = "⭐⭐⭐"
                elif result.importance_score >= 0.5:
                    importance = "⭐⭐"
                else:
                    importance = "⭐"
                
                # 截断过长的URL和标题
                title_display = result.title[:50] + "..." if len(result.title) > 50 else result.title
                
                # 摘要处理
                summary_display = result.summary if result.summary else "无摘要"
                if len(summary_display) > 150:
                    summary_display = summary_display[:147] + "..."
                
                # 写入表格行
                f.write(f"| {importance} | {result.depth} | [{title_display}]({result.url}) | {title_display} | {summary_display} |\n")
            
            f.write("\n---\n")
            f.write(f"*报告生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        logger.info(f"📄 Markdown报告已保存至: {report_file_md}")
        
        # 同时保存JSON格式（用于程序处理）
        report_file_json = report_dir / f"playwright_report_{domain_name}_{source_name}_{timestamp_str}.json"
        report_data = {
            "domain": domain_name,
            "source": source_name,
            "start_url": self.start_url,
            "timestamp": timestamp_str,
            "crawler_type": "playwright",
            "statistics": self.stats,
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "depth": r.depth,
                    "importance_score": r.importance_score,
                    "content_length": len(r.content),
                    "summary": r.summary
                }
                for r in self.results
            ]
        }
        
        with open(report_file_json, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📊 JSON数据已保存至: {report_file_json}")
        
        return report_file_md

async def main():
    parser = argparse.ArgumentParser(description="简化版智能爬虫")
    parser.add_argument("--url", required=True, help="起始URL")
    parser.add_argument("--domain", default="immigration", help="领域名称")
    parser.add_argument("--topic", default="Canadian immigration", help="主题")
    parser.add_argument("--max-pages", type=int, default=10, help="最大页面数")
    parser.add_argument("--max-depth", type=int, default=2, help="最大深度")
    
    args = parser.parse_args()
    
    crawler = SimpleIntelligentCrawler(
        start_url=args.url
    )
    
    print(f"🚀 开始爬取...")
    print(f"   URL: {args.url}")
    print(f"   最大页面数: {args.max_pages}")
    print(f"   最大深度: {args.max_depth}")
    
    results = await crawler.crawl(max_depth=args.max_depth, max_pages=args.max_pages)
    
    # Save report
    report_path = crawler.generate_report(args.domain, args.topic)
    
    print(f"✅ 爬取完成！找到 {len(results)} 个页面")
    print(f"📄 报告已保存至: {report_path}")

if __name__ == "__main__":
    asyncio.run(main()) 