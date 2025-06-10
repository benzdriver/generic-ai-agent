#!/usr/bin/env python3
"""
基于Scrapy的智能爬虫 - 针对静态网站的高速爬取
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import scrapy
import scrapy.signals
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor

logger = logging.getLogger(__name__)

@dataclass
class CrawlResult:
    """爬取结果"""
    url: str
    title: str
    content: str
    depth: int
    importance_score: float
    summary: str = ""
    
@dataclass
class CrawlStatistics:
    """爬取统计"""
    total_pages: int = 0
    total_links: int = 0
    pages_by_depth: Dict[int, int] = field(default_factory=dict)
    pages_by_importance: Counter = field(default_factory=Counter)
    skipped_low_importance: int = 0


class IntelligentSpider(scrapy.Spider):
    """智能Scrapy爬虫"""
    
    name = 'intelligent_spider'
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 32,  # 高并发
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'DOWNLOAD_DELAY': 0.25,  # 小延迟
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.25,
        'AUTOTHROTTLE_MAX_DELAY': 1,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 16,
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'INFO'
    }
    
    def __init__(self, start_url: str, max_depth: int = 3, max_pages: int = 100,
                 exclude_patterns: List[str] = None, keywords: List[str] = None,
                 importance_threshold: float = 0.6, crawler_instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.exclude_patterns = exclude_patterns or []
        self.keywords = keywords or ['immigration', 'visa', 'permit', 'canada']
        self.importance_threshold = importance_threshold
        
        self.visited_urls: Set[str] = set()
        self.results: List[CrawlResult] = []
        self.stats = CrawlStatistics()
        
        # 保存crawler实例引用
        self.crawler_instance = crawler_instance
        
        # 配置链接提取器
        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            deny=self.exclude_patterns,
            unique=True
        )
        
        # LLM接口（延迟加载）
        self._llm = None
        
    @property
    def llm(self):
        """延迟初始化LLM"""
        if self._llm is None:
            try:
                from src.infrastructure.llm.factory import LLMFactory
                self._llm = LLMFactory.get_llm()
            except:
                logger.warning("无法加载LLM，将跳过AI摘要功能")
        return self._llm
        
    def start_requests(self):
        """生成初始请求"""
        for url in self.start_urls:
            yield Request(url, meta={'depth': 0})
            
    def parse(self, response: Response):
        """解析页面"""
        url = response.url
        depth = response.meta['depth']
        
        # 检查是否已访问或达到限制
        if url in self.visited_urls or len(self.results) >= self.max_pages:
            return
            
        self.visited_urls.add(url)
        self.stats.total_pages += 1
        self.stats.pages_by_depth[depth] = self.stats.pages_by_depth.get(depth, 0) + 1
        
        # 提取标题
        title = response.css('title::text').get() or 'No Title'
        
        # 提取主要内容 - 使用多种选择器
        content_selectors = [
            'main ::text',
            'article ::text', 
            '.content ::text',
            '#content ::text',
            'section ::text',
            'div.container ::text',
            'p::text',
            'li::text'
        ]
        
        content_parts = []
        for selector in content_selectors:
            texts = response.css(selector).getall()
            if texts:
                content_parts.extend(texts)
                
        # 清理和合并内容
        content = ' '.join(content_parts)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 跳过内容太少的页面
        if not content or len(content) < 100:
            logger.debug(f"页面内容太少，跳过: {url}")
            return
            
        # 快速评估页面重要性
        importance_score = self._evaluate_importance_fast(title, content, url)
        
        if importance_score < 0.2:
            self.stats.skipped_low_importance += 1
            logger.debug(f"页面重要性太低 ({importance_score:.2f}), 跳过: {url}")
            return
            
        # 获取AI摘要（仅对高重要性页面）
        summary = ""
        if importance_score >= self.importance_threshold and self.llm:
            try:
                summary = self._get_ai_summary(title, content[:1500])
            except Exception as e:
                logger.debug(f"生成摘要失败: {e}")
                
        # 保存结果
        result = CrawlResult(
            url=url,
            title=title,
            content=content,
            depth=depth,
            importance_score=importance_score,
            summary=summary
        )
        self.results.append(result)
        
        # 更新统计
        if importance_score >= 0.8:
            self.stats.pages_by_importance['high'] += 1
        elif importance_score >= 0.5:
            self.stats.pages_by_importance['medium'] += 1
        else:
            self.stats.pages_by_importance['low'] += 1
            
        logger.info(f"已爬取 [{depth}] {url} | 重要性: {importance_score:.2f} | 进度: {len(self.results)}/{self.max_pages}")
        
        # 继续爬取子链接（如果满足条件）
        if importance_score >= self.importance_threshold and depth < self.max_depth:
            links = self.link_extractor.extract_links(response)
            self.stats.total_links += len(links)
            
            # 优先级排序
            prioritized_links = self._prioritize_links(links)
            
            for link in prioritized_links[:30]:  # 每页最多30个链接
                if len(self.results) >= self.max_pages:
                    break
                    
                yield Request(
                    link.url,
                    meta={'depth': depth + 1},
                    priority=-depth  # Scrapy优先级（负数更高）
                )
                
    def _evaluate_importance_fast(self, title: str, content: str, url: str) -> float:
        """快速评估页面重要性（不使用LLM）"""
        score = 0.0
        
        # URL评分
        url_lower = url.lower()
        url_keywords = ['immigrate', 'visa', 'permit', 'eligibility', 'apply', 
                       'requirements', 'process', 'guide', 'how-to']
        for keyword in url_keywords:
            if keyword in url_lower:
                score += 0.15
                
        # 标题评分
        title_lower = title.lower()
        for keyword in self.keywords:
            if keyword in title_lower:
                score += 0.2
                
        # 内容关键词密度
        content_lower = content.lower()
        keyword_count = sum(content_lower.count(kw) for kw in self.keywords)
        word_count = len(content_lower.split())
        if word_count > 0:
            keyword_density = keyword_count / word_count
            score += min(keyword_density * 10, 0.4)
            
        # 内容长度奖励
        if len(content) > 1000:
            score += 0.1
        if len(content) > 3000:
            score += 0.1
            
        return min(score, 1.0)
        
    def _get_ai_summary(self, title: str, content_preview: str) -> str:
        """获取AI摘要"""
        prompt = f"""
        Based on this immigration webpage, provide a 2-3 sentence summary:
        
        Title: {title}
        Content: {content_preview}
        
        Focus on key immigration information. Be concise and factual.
        """
        
        try:
            summary = self.llm.generate(prompt)
            return summary.strip()
        except:
            return ""
            
    def _prioritize_links(self, links) -> List:
        """对链接进行优先级排序"""
        scored_links = []
        
        priority_paths = ['apply', 'eligibility', 'requirements', 'guide', 'process']
        
        for link in links:
            score = 0
            url_lower = link.url.lower()
            
            # 关键词匹配
            for keyword in self.keywords:
                if keyword in url_lower:
                    score += 2
                    
            # 优先路径
            for path in priority_paths:
                if path in url_lower:
                    score += 3
                    
            # 排除外部链接
            if urlparse(link.url).netloc != self.allowed_domains[0]:
                score -= 10
                
            scored_links.append((score, link))
            
        scored_links.sort(key=lambda x: x[0], reverse=True)
        return [link for _, link in scored_links]


class ScrapyIntelligentCrawler:
    """Scrapy智能爬虫管理器"""
    
    def __init__(self):
        self.spider_results = []
        self.spider_stats = None
    
    def crawl(self, start_url: str, max_depth: int = 3, max_pages: int = 100,
              exclude_patterns: List[str] = None, keywords: List[str] = None,
              importance_threshold: float = 0.6) -> Tuple[List[CrawlResult], CrawlStatistics]:
        """执行爬取"""
        
        # 创建自定义设置
        custom_settings = {
            'USER_AGENT': 'Mozilla/5.0 (compatible; IntelligentCrawler/1.0)',
        }
        
        # 创建爬虫进程
        process = CrawlerProcess(custom_settings)
        
        # 启动爬取
        logger.info(f"开始Scrapy爬取: {start_url}")
        logger.info(f"配置: 深度={max_depth}, 最大页面={max_pages}, 重要性阈值={importance_threshold}")
        
        # 创建一个回调来捕获结果
        def spider_closed(spider):
            self.spider_results = spider.results
            self.spider_stats = spider.stats
        
        # 获取crawler对象并连接信号
        crawler = process.create_crawler(IntelligentSpider)
        crawler.signals.connect(spider_closed, signal=scrapy.signals.spider_closed)
        
        # 启动爬虫
        process.crawl(
            crawler,
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            exclude_patterns=exclude_patterns or [],
            keywords=keywords or [],
            importance_threshold=importance_threshold,
            crawler_instance=self
        )
        
        process.start()  # 阻塞直到完成
        
        # 生成报告
        if self.spider_stats:
            self._print_statistics(self.spider_stats, len(self.spider_results))
            self._save_report(start_url, self.spider_results, self.spider_stats)
        
        return self.spider_results, self.spider_stats or CrawlStatistics()
        
    def _print_statistics(self, stats: CrawlStatistics, result_count: int):
        """打印统计信息"""
        logger.info("\n" + "="*50)
        logger.info("Scrapy爬取统计")
        logger.info("="*50)
        logger.info(f"总页面数: {stats.total_pages}")
        logger.info(f"成功爬取: {result_count}")
        logger.info(f"总链接数: {stats.total_links}")
        logger.info(f"按深度分布: {dict(stats.pages_by_depth)}")
        logger.info(f"按重要性分布: {dict(stats.pages_by_importance)}")
        logger.info(f"跳过的低重要性页面: {stats.skipped_low_importance}")
        
    def _save_report(self, start_url: str, results: List[CrawlResult], stats: CrawlStatistics):
        """保存爬取报告"""
        report_dir = Path("docs/crawl_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # 生成Markdown格式报告
        domain_name = urlparse(start_url).netloc.replace('.', '_')
        report_file_md = report_dir / f"scrapy_report_{domain_name}_{timestamp_str}.md"
        
        with open(report_file_md, 'w', encoding='utf-8') as f:
            # 写入标题和元信息
            f.write("# 智能爬取审查报告\n\n")
            f.write(f"**生成日期:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**目标网站:** {start_url}\n")
            f.write(f"**爬取方式:** Scrapy高速爬虫\n")
            f.write(f"**总计页面:** {len(results)}\n")
            f.write(f"**成功率:** {(len(results) / stats.total_pages * 100) if stats.total_pages > 0 else 0:.1f}%\n\n")
            
            # 写入统计信息
            f.write("## 爬取统计\n\n")
            f.write(f"- **总访问页面:** {stats.total_pages}\n")
            f.write(f"- **总发现链接:** {stats.total_links}\n")
            f.write(f"- **跳过低重要性:** {stats.skipped_low_importance}\n")
            f.write(f"- **深度分布:** {dict(stats.pages_by_depth)}\n")
            f.write(f"- **重要性分布:** 高({stats.pages_by_importance.get('high', 0)}) / 中({stats.pages_by_importance.get('medium', 0)}) / 低({stats.pages_by_importance.get('low', 0)})\n\n")
            
            # 写入页面详情表格
            f.write("## 爬取页面详情\n\n")
            f.write("| 重要性 | 深度 | 链接 | 标题 | AI 生成摘要 |\n")
            f.write("|:---:|:---:|:---|:---|:---|\n")
            
            # 按重要性排序
            sorted_results = sorted(results, key=lambda x: x.importance_score, reverse=True)
            
            for result in sorted_results:
                # 重要性星级
                if result.importance_score >= 0.8:
                    importance = "⭐⭐⭐"
                elif result.importance_score >= 0.5:
                    importance = "⭐⭐"
                else:
                    importance = "⭐"
                
                # 截断过长的URL和标题
                url_display = result.url
                if len(url_display) > 80:
                    url_display = url_display[:77] + "..."
                    
                title_display = result.title[:50] + "..." if len(result.title) > 50 else result.title
                
                # 摘要处理
                summary_display = result.summary if result.summary else "无摘要"
                if len(summary_display) > 150:
                    summary_display = summary_display[:147] + "..."
                
                # 写入表格行
                f.write(f"| {importance} | {result.depth} | [{title_display}]({result.url}) | {title_display} | {summary_display} |\n")
            
            f.write("\n---\n")
            f.write(f"*报告生成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        logger.info(f"\n📄 Markdown报告已保存至: {report_file_md}")
        
        # 同时保存JSON格式（用于程序处理）
        report_file_json = report_dir / f"scrapy_report_{domain_name}_{timestamp_str}.json"
        report_data = {
            "start_url": start_url,
            "timestamp": timestamp_str,
            "crawler_type": "scrapy",
            "statistics": {
                "total_pages": stats.total_pages,
                "successful_pages": len(results),
                "total_links": stats.total_links,
                "pages_by_depth": dict(stats.pages_by_depth),
                "pages_by_importance": dict(stats.pages_by_importance),
                "skipped_low_importance": stats.skipped_low_importance
            },
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "depth": r.depth,
                    "importance_score": r.importance_score,
                    "content_length": len(r.content),
                    "summary": r.summary
                }
                for r in results
            ]
        }
        
        with open(report_file_json, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📊 JSON数据已保存至: {report_file_json}")


def main():
    """测试爬虫"""
    crawler = ScrapyIntelligentCrawler()
    
    # 测试爬取
    results, stats = crawler.crawl(
        start_url="https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/start-visa.html",
        max_depth=2,
        max_pages=20,
        exclude_patterns=["/fr/", "/news/", ".pdf", "/contact/"],
        keywords=['start-up', 'visa', 'entrepreneur', 'business', 'immigration'],
        importance_threshold=0.5
    )
    
    print(f"\n爬取完成! 共获取 {len(results)} 个页面")
    
    # 显示最重要的页面
    print("\n最重要的5个页面:")
    for i, result in enumerate(sorted(results, key=lambda x: x.importance_score, reverse=True)[:5], 1):
        print(f"{i}. [{result.importance_score:.2f}] {result.title}")
        print(f"   URL: {result.url}")
        if result.summary:
            print(f"   摘要: {result.summary[:100]}...")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main() 