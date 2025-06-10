#!/usr/bin/env python3
"""
通用知识库管理系统 (Generic Knowledge Management System)
支持任何领域的知识库构建和管理
通过YAML配置驱动，实现真正的领域无关性
"""

import os
import sys
import yaml
import json
import time
import hashlib
import asyncio
import argparse
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Type, Tuple
from dataclasses import dataclass, asdict
import importlib.util
import logging
import uuid # 导入uuid库
import re # 导入正则表达式库
from collections import Counter # 导入Counter
import numpy as np # Import numpy for cosine similarity
import shutil # Import shutil for file operations
from urllib.parse import urlparse, urljoin
# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.infrastructure.vector_store.embedding_router import get_embedding

def get_embedding_batch(texts: List[str]) -> List[List[float]]:
    """批量获取文本的embedding向量"""
    try:
        # 逐个处理，因为embedding_router可能不支持批量
        return [get_embedding(text) for text in texts if text]
    except Exception as e:
        logger.error(f"批量获取embedding失败: {e}")
        return [[] for _ in texts]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not v1 or not v2:
        return 0.0
    v1_np = np.array(v1)
    v2_np = np.array(v2)
    dot_product = np.dot(v1_np, v2_np)
    norm_v1 = np.linalg.norm(v1_np)
    norm_v2 = np.linalg.norm(v2_np)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

try:
    from playwright.async_api import async_playwright, Browser, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DomainConfig:
    """领域配置"""
    name: str
    description: str
    collection_name: str
    sources: List[Dict[str, Any]]
    parser_class: Optional[str] = None
    quality_rules: Optional[Dict[str, Any]] = None
    test_queries: Optional[List[Dict[str, Any]]] = None
    update_frequency_days: int = 7
    enabled: bool = True

@dataclass
class SourceConfig:
    """数据源配置"""
    name: str
    url: str
    type: str  # website, api, file, database
    parser_config: Optional[Dict[str, Any]] = None
    selectors: Optional[Dict[str, str]] = None
    priority: int = 1
    last_updated: Optional[str] = None
    content_hash: Optional[str] = None

class ContentParser(ABC):
    """内容解析器基类"""
    
    @abstractmethod
    def parse(self, content: str, config: Dict[str, Any]) -> List[str]:
        """解析内容，返回段落列表"""
        pass
    
    @abstractmethod
    def extract_metadata(self, content: str, url: str) -> Dict[str, Any]:
        """提取元数据"""
        pass

class GenericHTMLParser(ContentParser):
    """通用HTML解析器"""
    
    def parse(self, content: str, config: Dict[str, Any]) -> List[str]:
        """通用HTML解析"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 使用配置中的选择器
        selectors = config.get('selectors', {})
        
        # 移除不需要的元素
        exclude_selectors = selectors.get('exclude', 'script, style, nav, footer, header')
        for element in soup.select(exclude_selectors):
            element.decompose()
        
        # 提取内容
        content_selector = selectors.get('content', 'p, div.content, article, section')
        paragraphs = []
        
        for element in soup.select(content_selector):
            text = element.get_text(strip=True)
            min_length = config.get('min_paragraph_length', 50)
            if len(text) >= min_length:
                paragraphs.append(text)
        
        max_paragraphs = config.get('max_paragraphs', 50)
        return paragraphs[:max_paragraphs]
    
    def extract_metadata(self, content: str, url: str) -> Dict[str, Any]:
        """提取通用元数据"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        
        metadata = {
            'url': url,
            'scraped_at': datetime.now().isoformat()
        }
        
        # 尝试提取标题
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # 尝试提取描述
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')
        
        # 尝试提取关键词
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = [k.strip() for k in meta_keywords.get('content', '').split(',')]
        
        return metadata

class QualityChecker:
    """内容质量检查器"""
    
    def __init__(self, rules: Dict[str, Any]):
        self.rules = self._default_rules()
        if rules:
            self.rules.update(rules)
    
    def _default_rules(self) -> Dict[str, Any]:
        """默认质量规则"""
        return {
            'min_length': 10,
            'max_length': 5000,
            'min_unique_words': 5,
            'max_duplicate_ratio': 0.3,
            'forbidden_patterns': [],
            'required_patterns': [],
            'enable_semantic_check': False,
            'semantic_relevance_threshold': 0.4,
            'required_patterns': [],
            'forbidden_patterns': []
        }
    
    def _check_basic_rules(self, text: str) -> Tuple[bool, float, str]:
        """执行基本的、不依赖AI的规则检查"""
        # Length check
        if not (self.rules['min_length'] <= len(text) <= self.rules['max_length']):
            reason = f"长度不符 (is {len(text)}, should be {self.rules['min_length']}-{self.rules['max_length']})"
            return False, 0.0, reason
        
        # Required patterns check
        required_patterns = self.rules.get('required_patterns', [])
        if required_patterns:
            if not any(re.search(r'\\b' + re.escape(p.lower()) + r'\\b', text.lower()) for p in required_patterns):
                reason = f"缺少必需的模式: {required_patterns}"
                return False, 0.4, reason

        # Forbidden patterns check
        for pattern in self.rules.get('forbidden_patterns', []):
            if re.search(r'\\b' + re.escape(pattern.lower()) + r'\\b', text.lower()):
                reason = f"包含禁止的模式: '{pattern}'"
                return False, 0.0, reason
        
        return True, 0.6, "通过基本检查" # Return a base score

    def check_quality(self, text: str, relevance_vector: Optional[List[float]] = None) -> Tuple[bool, float, str]:
        """检查单个文本的质量"""
        is_valid, score, reason = self._check_basic_rules(text)
        if not is_valid:
            return False, score, reason

        # Smart semantic check
        if self.rules.get('enable_semantic_check', False) and relevance_vector:
            para_vector = get_embedding(text)
            if not para_vector:
                 return False, 0.0, "无法生成 embedding"

            similarity = cosine_similarity(relevance_vector, para_vector)
            
            if similarity < self.rules['semantic_relevance_threshold']:
                reason = f"语义相关性低 (得分: {similarity:.2f}, 阈值: >{self.rules['semantic_relevance_threshold']})"
                logger.debug(f"[Quality Fail] {reason} | Content: '{text[:60]}...'")
                return False, similarity, reason
        
        quality_score = self._calculate_quality_score(text, text.split(), len(set(text.split())))
        return True, quality_score, "通过质量检查"
    
    def _calculate_quality_score(self, text: str, words: List[str], unique_words: int) -> float:
        """计算质量分数"""
        score = 0.5  # 基础分
        
        # 长度奖励
        ideal_length = 500
        length_diff = abs(len(text) - ideal_length)
        length_score = max(0, 1 - length_diff / ideal_length)
        score += length_score * 0.2
        
        # 词汇丰富度奖励
        if len(words) > 0:
            richness = unique_words / len(words)
            score += richness * 0.3
        
        return min(1.0, score)

    def batch_check_quality(self, paragraphs: List[str], relevance_vector: Optional[List[float]] = None) -> List[Tuple[bool, float, str]]:
        """批量检查段落质量"""
        if not self.rules.get('enable_semantic_check', False) or relevance_vector is None:
            # 如果不进行语义检查，则只进行基本检查
            results = []
            for p in paragraphs:
                is_valid, score, reason = self._check_basic_rules(p)
                results.append((is_valid, score, reason))
            return results

        try:
            # 批量获取 embedding
            para_vectors = get_embedding_batch(paragraphs)
            results = []
            semantic_threshold = self.rules.get('semantic_relevance_threshold', 0.4)

            for i, para_vector in enumerate(para_vectors):
                text = paragraphs[i]
                is_valid, _, reason = self._check_basic_rules(text)
                if not is_valid:
                    results.append((False, 0.0, reason))
                    continue

                if not para_vector: # Check if embedding failed for this item
                    results.append((False, 0.0, "Embedding generation failed"))
                    continue

                similarity = cosine_similarity(relevance_vector, para_vector)
                
                if similarity < semantic_threshold:
                    reason = f"语义相关性低 (得分: {similarity:.2f}, 阈值: >{semantic_threshold})"
                    logger.debug(f"[Quality Fail] {reason} | Content: '{text[:60]}...'")
                    results.append((False, similarity, reason))
                else:
                    quality_score = self._calculate_quality_score(text, text.split(), len(set(text.split())))
                    results.append((True, quality_score, "通过质量检查"))
            
            return results
        except Exception as e:
            logger.error(f"批量质量检查失败: {e}")
            return [(False, 0.0, "检查异常") for _ in paragraphs]

    def should_send_for_review(self, score: float) -> bool:
        """判断是否应该将内容送审"""
        # 分数较高的内容（可能是边缘情况）送审
        return score > 0.2

UPDATE_QUEUE_FILE = project_root / "cache" / "update_queue.json"
PAGE_CONTENT_CACHE_DIR = project_root / "cache" / "page_content"

class GenericKnowledgeManager:
    """通用知识库管理器"""
    
    def __init__(self, config_dir: str = "config/domains"):
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.project_root = project_root
        self.config_dir = self.project_root / config_dir
        self.cache_dir = self.project_root / "cache" / "knowledge"
        self.review_dir = self.project_root / "data" / "needs_review"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        PAGE_CONTENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.domains = self._load_domains_config()
        self.parsers = self._load_parsers()
        
        self.browser = None
        self.playwright = None
    
    def _load_domains_config(self) -> Dict[str, DomainConfig]:
        """从目录加载所有领域配置"""
        if not self.config_dir.exists() or not self.config_dir.is_dir():
            logger.warning(f"配置目录不存在: {self.config_dir}")
            return self._create_example_config_structure()
        
        domains = {}
        for config_file in self.config_dir.glob("*.yaml"):
            domain_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    domain_data = yaml.safe_load(f)

                if not domain_data:
                    logger.warning(f"配置文件为空: {config_file}")
                    continue

                sources = []
                for source_data in domain_data.get('sources', []):
                    sources.append(SourceConfig(**source_data))
                
                domain = DomainConfig(
                    name=domain_name,
                    description=domain_data.get('description', ''),
                    collection_name=domain_data.get('collection_name', f"{domain_name}_docs"),
                    sources=sources,
                    parser_class=domain_data.get('parser_class'),
                    quality_rules=domain_data.get('quality_rules'),
                    test_queries=domain_data.get('test_queries'),
                    update_frequency_days=domain_data.get('update_frequency_days', 7),
                    enabled=domain_data.get('enabled', True)
                )
                domains[domain_name] = domain
            except Exception as e:
                logger.error(f"加载领域配置文件失败 {config_file}: {e}")
        
        return domains
    
    def _create_example_config_structure(self) -> Dict[str, DomainConfig]:
        """创建示例配置目录和文件"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        example_file = self.config_dir / "immigration.yaml.example"
        
        example_config = {
            'description': 'Immigration and visa information',
            'collection_name': 'immigration_docs',
            'sources': [
                {
                    'name': 'IRCC_PNP',
                    'url': 'https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/provincial-nominees.html',
                    'type': 'website'
                }
            ],
            'quality_rules': {
                'min_length': 50,
                'required_patterns': ['immigration', 'visa', 'canada']
            },
            'test_queries': [
                {'query': 'How to apply for Express Entry?', 'relevant': True}
            ],
            'update_frequency_days': 7
        }
        
        with open(example_file, 'w', encoding='utf-8') as f:
            yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已创建示例配置目录和文件: {example_file}")
        return {}
    
    def _load_parsers(self) -> Dict[str, ContentParser]:
        """加载解析器"""
        parsers = {
            'generic': GenericHTMLParser()
        }
        
        # 加载自定义解析器
        custom_parsers_dir = self.project_root / "parsers"
        if custom_parsers_dir.exists():
            for parser_file in custom_parsers_dir.glob("*.py"):
                if parser_file.name.startswith("_"):
                    continue
                
                try:
                    # 动态导入解析器
                    module_name = parser_file.stem
                    spec = importlib.util.spec_from_file_location(module_name, parser_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找ContentParser子类
                    for name, obj in module.__dict__.items():
                        if (isinstance(obj, type) and 
                            issubclass(obj, ContentParser) and 
                            obj != ContentParser):
                            parsers[module_name] = obj()
                            logger.info(f"加载自定义解析器: {module_name}")
                            
                except Exception as e:
                    logger.error(f"加载解析器失败 {parser_file}: {e}")
        
        return parsers
    
    async def update_all_domains(self, force_update: bool = False):
        """更新所有启用的领域"""
        for domain_name, domain in self.domains.items():
            if domain.enabled:
                await self.update_domain(domain_name, force_update)
    
    async def update_domain(self, domain_name: str, force_update: bool = False):
        """更新特定领域的知识库"""
        if domain_name not in self.domains:
            logger.error(f"未找到领域配置: {domain_name}")
            return
        
        domain = self.domains[domain_name]
        if not domain.enabled:
            logger.info(f"领域 {domain_name} 已禁用，跳过更新")
            return
        
        logger.info(f"🚀 更新领域: {domain_name}")
        
        if not HAS_PLAYWRIGHT:
            logger.error("❌ Playwright未安装. 请运行: pip install playwright && playwright install")
            return
        
        await self._initialize_browser()
        
        updated_count = 0
        for source_dict in domain.sources:
            # Convert dict to SourceConfig if needed
            if isinstance(source_dict, dict):
                source_config = SourceConfig(**source_dict)
            else:
                source_config = source_dict
                
            if source_config.type == 'website':
                success = await self._scrape_website(domain, source_config, force_update)
                if success:
                    updated_count += 1
            elif source_config.type == 'api':
                # TODO: 实现API数据源
                logger.warning(f"API数据源暂未实现: {source_config.name}")
            elif source_config.type == 'file':
                # TODO: 实现文件数据源
                logger.warning(f"文件数据源暂未实现: {source_config.name}")
        
        await self._close_browser()
        
        logger.info(f"✅ 领域 {domain_name} 更新完成! 更新了 {updated_count} 个数据源")
    
    async def _scrape_website(self, domain: DomainConfig, source: SourceConfig, 
                            force_update: bool) -> bool:
        """抓取网站内容"""
        if not force_update and not self._should_update_source(source, domain.update_frequency_days):
            logger.info(f"⏭️ {source.name}: 无需更新，跳过。")
            return False
        
        logger.info(f"🌐 开始抓取: {source.name} ({source.url})")
        
        # 检查是否需要深层爬取
        deep_crawl = source.parser_config and source.parser_config.get('deep_crawl', False)
        max_depth = source.parser_config.get('max_depth', 3) if source.parser_config else 3
        max_pages = source.parser_config.get('max_pages', 50) if source.parser_config else 50
        
        if deep_crawl:
            logger.info(f"  - 启用深层爬取模式 (深度: {max_depth}, 最大页面数: {max_pages})")
            return await self._deep_crawl_website(domain, source, force_update, max_depth, max_pages)
        else:
            # 原有的单页爬取逻辑
            return await self._single_page_scrape(domain, source, force_update)
    
    async def _single_page_scrape(self, domain: DomainConfig, source: SourceConfig, 
                                 force_update: bool) -> bool:
        """抓取单个网页"""
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            logger.debug(f"  - 正在导航到页面...")
            try:
                await page.goto(source.url, wait_until="networkidle", timeout=60000)
            except Exception as e: # Catch potential Playwright errors (like TimeoutError)
                logger.error(f"  - ❌ 页面导航失败: {type(e).__name__}. 网站可能无法访问或响应缓慢。")
                await context.close()
                return False

            await asyncio.sleep(2)
            
            html_content = await page.content()
            logger.debug(f"  - 页面HTML内容获取成功 (大小: {len(html_content)} bytes)。")
            await context.close()
            
            # --- Get Page Title for Semantic Context ---
            parser_name = domain.parser_class or 'generic'
            parser = self.parsers.get(parser_name, self.parsers['generic'])
            metadata = parser.extract_metadata(html_content, source.url)
            page_title = metadata.get('title')

            # --- Create Relevance Vector ---
            relevance_vector = None
            quality_rules = domain.quality_rules or {}
            if quality_rules.get('enable_semantic_check', False) and page_title:
                relevance_vector = get_embedding(page_title)
                logger.debug(f"  - 语义相关性检查已启用。基准标题: '{page_title}'")

            logger.debug("  - 开始使用解析器提取内容...")
            parser_config = source.parser_config or source.selectors or {}
            paragraphs = parser.parse(html_content, parser_config)
            logger.info(f"  - 解析器提取了 {len(paragraphs)} 个初始段落。")
            
            if not paragraphs:
                logger.warning(f"   ⚠️ 解析器未能从页面提取任何有效段落。请检查源网页结构和配置中的CSS选择器。")
                return False
            
            # --- Perform Quality Check with Semantic Context & Human Review ---
            logger.debug("  - 开始进行段落质量检查...")
            quality_checker = QualityChecker(quality_rules)
            filtered_paragraphs = []
            paragraphs_for_review = []
            failure_reasons = Counter()

            # 批量检查
            quality_results = quality_checker.batch_check_quality(paragraphs, relevance_vector)

            # 批量处理
            for paragraph, (passed, score, reason) in zip(paragraphs, quality_results):
                if passed:
                    filtered_paragraphs.append((paragraph, score))
                else:
                    # 对于未通过质量检查的内容，根据分数决定是否送审
                    if score > 0.2:  # 分数较高的内容送审
                        review_item = {
                            'url': source.url,
                            'content': paragraph,
                            'reason_for_filtering': reason,
                            'similarity_score': round(score, 4)
                        }
                        paragraphs_for_review.append(review_item)
                        
                        failure_type = reason.split('(')[0].strip()
                        failure_reasons[failure_type] += 1
                        logger.debug(f"    - [送往审查] (原因: {reason}): '{paragraph[:100]}...'")
            
            if paragraphs_for_review:
                self._save_for_review(domain.name, source.name, paragraphs_for_review)

            logger.info(f"  - {len(filtered_paragraphs)}/{len(paragraphs)} 个段落通过质量检查。")
            logger.info(f"  - {len(paragraphs_for_review)} 个段落已保存供人工审查。")

            if not filtered_paragraphs:
                logger.warning(f"   ⚠️ 没有段落直接通过质量检查，无法继续处理此源。")
                top_3_reasons = failure_reasons.most_common(3)
                reasons_str = ", ".join([f"'{k}' ({v}次)" for k, v in top_3_reasons])
                logger.warning(f"     - 主要过滤原因: {reasons_str}")
                return False
            
            content_text = '\n'.join([p[0] for p in filtered_paragraphs])
            content_hash = hashlib.md5(content_text.encode()).hexdigest()
            
            if source.content_hash == content_hash and not force_update:
                logger.info(f"   ✅ 内容无变化，无需更新。")
                source.last_updated = datetime.now().isoformat()
                return True
            
            logger.debug(f"  - 内容有变化或被强制更新，准备存入向量数据库...")
            await self._store_content(domain, source, filtered_paragraphs, metadata)
            
            source.content_hash = content_hash
            source.last_updated = datetime.now().isoformat()
            
            logger.info(f"   ✅ 成功处理并存储了 {len(filtered_paragraphs)} 个段落。")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ 抓取或处理页面时发生严重错误: {source.name} - {type(e).__name__}: {e}", exc_info=True)
            return False
    
    async def _deep_crawl_website(self, domain: DomainConfig, source: SourceConfig, 
                                force_update: bool, max_depth: int, max_pages: int) -> bool:
        """深层爬取网站 - 智能选择爬虫类型"""
        logger.info(f"  - 开始深层爬取: {source.url}")
        
        # 检查是否应该使用Scrapy（对于静态网站）
        use_scrapy = source.parser_config and source.parser_config.get('use_scrapy', False)
        
        # 初始化爬取结果
        results = []
        
        if use_scrapy:
            # 使用Scrapy爬虫（速度快，适合静态网站）
            logger.info(f"  - 使用Scrapy爬虫进行高速爬取")
            from scrapy_intelligent_crawler import ScrapyIntelligentCrawler
            
            try:
                # 获取排除模式
                parser_config = source.parser_config or {}
                exclude_patterns = parser_config.get('exclude_link_patterns', [])
                
                # 准备关键词
                keywords = parser_config.get('keywords', ['immigration', 'visa', 'canada', 'permit'])
                
                # 创建Scrapy爬虫
                crawler = ScrapyIntelligentCrawler()
                
                # 执行爬取
                results, stats = crawler.crawl(
                    start_url=source.url,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    exclude_patterns=exclude_patterns,
                    keywords=keywords,
                    importance_threshold=0.6
                )
                
                logger.info(f"  - Scrapy爬取完成，找到 {len(results)} 个页面")
                
            except Exception as e:
                logger.error(f"  - Scrapy爬取失败: {e}")
                logger.info(f"  - 回退到Playwright爬虫")
                use_scrapy = False
                results = []
                
        if not use_scrapy:
            # 使用Playwright爬虫（功能全面，适合动态网站）
            logger.info(f"  - 使用Playwright爬虫进行智能爬取")
            
            # 导入简化版智能爬虫
            from simple_intelligent_crawler import SimpleIntelligentCrawler
            
            # 获取排除模式
            parser_config = source.parser_config or {}
            exclude_patterns = parser_config.get('exclude_link_patterns', [])
            
            # 创建爬虫实例
            crawler = SimpleIntelligentCrawler(start_url=source.url)
            
            # 执行爬取
            results = await crawler.crawl(
                max_depth=max_depth,
                max_pages=max_pages,
                exclude_patterns=exclude_patterns
            )
            
            logger.info(f"  - 爬取完成，找到 {len(results)} 个页面")
            
            # 生成爬取报告
            report_path = crawler.generate_report(domain.name, source.name)
            logger.info(f"  - 爬取报告已保存至: {report_path}")
        
        # 处理爬取结果（无论使用哪种爬虫）
        try:
            # 准备质量检查
            quality_rules = domain.quality_rules or {}
            quality_checker = QualityChecker(quality_rules)
            relevance_vector = None
            
            if quality_rules.get('enable_semantic_check'):
                relevance_text = f"{domain.description} {source.name}".strip()
                relevance_vector = get_embedding(relevance_text)
                logger.info(f"  - 已为领域 '{domain.name}' 生成相关性基准向量")
            
            # 处理爬取结果
            all_filtered_paragraphs = []
            
            for result in results:
                # 使用解析器处理内容
                parser_name = domain.parser_class or 'generic'
                parser = self.parsers.get(parser_name, self.parsers['generic'])
                
                # 将纯文本内容分段并包装成HTML段落
                # 按照换行符分割文本，创建真正的HTML段落
                text_paragraphs = result.content.split('\n\n')  # 双换行符分段
                html_paragraphs = []
                for para in text_paragraphs:
                    para = para.strip()
                    if para:  # 忽略空段落
                        html_paragraphs.append(f"<p>{para}</p>")
                
                # 生成包含真正段落的HTML
                html_content = f"""
                <html>
                <head><title>{result.title}</title></head>
                <body>
                {''.join(html_paragraphs)}
                </body>
                </html>
                """
                
                paragraphs = parser.parse(html_content, source.parser_config or {})
                if not paragraphs:
                    # 如果解析器仍然没有提取到段落，直接使用原始文本段落
                    paragraphs = [para for para in text_paragraphs if para.strip() and len(para.strip()) >= 50]
                    logger.debug(f"  - 解析器未提取到HTML段落，使用原始文本段落: {len(paragraphs)} 个")
                
                if not paragraphs:
                    logger.warning(f"  - 页面 {result.url} 没有提取到任何段落")
                    continue
                
                logger.info(f"  - 从页面 {result.url} 提取到 {len(paragraphs)} 个段落")
                
                metadata = {
                    'title': result.title,
                    'crawl_depth': result.depth,
                    'importance_score': result.importance_score,
                    'ai_summary': getattr(result, 'summary', '')  # 兼容两种爬虫的结果格式
                }
                
                # 批量质量检查
                quality_results = quality_checker.batch_check_quality(paragraphs, relevance_vector)
                
                passed_count = 0
                failed_count = 0
                review_count = 0
                
                for paragraph, (passed, score, reason) in zip(paragraphs, quality_results):
                    if passed:
                        all_filtered_paragraphs.append((paragraph, score, result.url, metadata))
                        passed_count += 1
                    else:
                        failed_count += 1
                        if quality_checker.should_send_for_review(score):
                            review_count += 1
                            logger.debug(f"    - 段落未通过 (分数: {score:.3f}, 原因: {reason}): {paragraph[:50]}...")
                
                logger.info(f"  - 质量检查结果: {passed_count} 通过, {failed_count} 失败, {review_count} 待审查")
            
            # 存储所有收集的内容
            if all_filtered_paragraphs:
                logger.info(f"  - 共收集 {len(all_filtered_paragraphs)} 个高质量段落")
                
                # 批量存储到向量数据库
                collection_name = domain.collection_name
                self._ensure_collection(collection_name)
                
                points = []
                for paragraph, quality_score, url, metadata in all_filtered_paragraphs:
                    vector = get_embedding(paragraph)
                    point_id = str(uuid.uuid4())
                    
                    point_data = {
                        "id": point_id,
                        "vector": vector,
                        "payload": {
                            "content": paragraph,
                            "domain": domain.name,
                            "source": source.name,
                            "url": url,
                            "quality_score": quality_score,
                            "created_at": datetime.now().isoformat(),
                            **metadata
                        }
                    }
                    points.append(point_data)
                
                # 批量插入
                self.vector_store.upsert(collection_name, points)
                
                # 更新source状态
                source.last_updated = datetime.now().isoformat()
                crawler_type = "scrapy_crawl" if use_scrapy else "deep_crawl"
                content_summary = f"{crawler_type}_{len(results)}_{len(all_filtered_paragraphs)}"
                source.content_hash = hashlib.md5(content_summary.encode()).hexdigest()
                
                logger.info(f"   ✅ 成功存储 {len(all_filtered_paragraphs)} 个段落到知识库")
                return True
            else:
                logger.warning(f"   ⚠️ 深层爬取未能收集到任何有效内容")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ 深层爬取失败: {e}", exc_info=True)
            return False
    
    def _save_for_review(self, domain_name: str, source_name: str, review_items: List[Dict]):
        """将需要审查的段落保存为YAML快照文件"""
        # The filename will now be a .yaml file
        review_filename = f"{domain_name}_{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        review_path = self.review_dir / review_filename

        # Add a 'status' field for the human reviewer
        for item in review_items:
            item['status'] = 'pending' # options: pending, approved, rejected

        snapshot_data = {
            'metadata': {
                'domain': domain_name,
                'source': source_name,
                'url': review_items[0]['url'] if review_items else 'N/A',
                'creation_date': datetime.now().isoformat(),
                'item_count': len(review_items)
            },
            'review_items': review_items
        }

        try:
            with open(review_path, 'w', encoding='utf-8') as f:
                # Use yaml.dump for a much more human-readable format
                yaml.dump(snapshot_data, f, allow_unicode=True, sort_keys=False, indent=2)
            logger.info(f"  - 已将 {len(review_items)} 个待审段落保存为快照: {review_path}")
        except Exception as e:
            logger.error(f"   ❌ 保存待审快照文件失败: {e}")
    
    async def _store_content(self, domain: DomainConfig, source: SourceConfig, 
                           paragraphs: List[Tuple[str, float]], metadata: Dict[str, Any]):
        """存储内容到向量数据库"""
        collection_name = domain.collection_name
        
        # 确保集合存在
        self._ensure_collection(collection_name)
        
        points = []
        
        for i, (paragraph, quality_score) in enumerate(paragraphs):
            vector = get_embedding(paragraph)
            
            # 使用UUID作为ID
            point_id = str(uuid.uuid4())
            
            point_data = {
                "id": point_id,
                "vector": vector,
                "payload": {
                    "content": paragraph,
                    "domain": domain.name,
                    "source": source.name,
                    "url": source.url,
                    "quality_score": quality_score,
                    "created_at": datetime.now().isoformat(),
                    **metadata  # 包含解析器提取的元数据
                }
            }
            points.append(point_data)
        
        # 批量插入
        self.vector_store.upsert(collection_name, points)
    
    def _ensure_collection(self, collection_name: str):
        """确保集合存在"""
        try:
            self.vector_store.client.get_collection(collection_name)
        except:
            # 创建集合
            self.vector_store.client.recreate_collection(
                collection_name=collection_name,
                vectors_config={
                    "size": 1536,  # OpenAI embedding size
                    "distance": "Cosine"
                }
            )
            logger.info(f"创建集合: {collection_name}")
    
    def _should_update_source(self, source: SourceConfig, update_frequency_days: int) -> bool:
        """判断是否需要更新数据源"""
        if not source.last_updated:
            return True
        
        try:
            last_update = datetime.fromisoformat(source.last_updated)
            days_since_update = (datetime.now() - last_update).days
            return days_since_update >= update_frequency_days
        except:
            return True
    
    async def _initialize_browser(self):
        """初始化浏览器"""
        if self.browser:
            return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    def test_all_domains(self):
        """测试所有已配置的领域"""
        logger.info("🔬 开始测试所有领域...")
        for domain_name, domain in self.domains.items():
            if domain.enabled and domain.test_queries:
                self.test_domain_queries(domain_name)
            else:
                logger.info(f"⏭️ 跳过领域 {domain_name} (未启用或无测试用例)")

    def test_domain_queries(self, domain_name: str):
        """测试领域特定的查询"""
        if domain_name not in self.domains:
            logger.error(f"未找到领域: {domain_name}")
            return
        
        domain = self.domains[domain_name]
        collection_name = domain.collection_name
        
        test_queries_config = domain.test_queries
        if not test_queries_config:
            logger.warning(f"领域 {domain_name} 没有配置测试用例")
            return
            
        logger.info(f"🔬 测试领域 {domain_name} 的查询...")
        
        correct_count = 0
        test_queries = [(item['query'], item['relevant']) for item in test_queries_config]
        
        for query, expected_relevant in test_queries:
            query_vector = get_embedding(query)
            
            try:
                results = self.vector_store.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=1
                )
                
                if results:
                    score = results[0].score
                    is_relevant = score > 0.5  # 可配置的阈值
                else:
                    score = 0.0
                    is_relevant = False
                
                is_correct = is_relevant == expected_relevant
                if is_correct:
                    correct_count += 1
                
                status = "✅" if is_correct else "❌"
                logger.info(f"{status} {query}: 分数={score:.3f}, 相关={is_relevant}")
                
            except Exception as e:
                logger.error(f"❌ {query}: 测试失败 - {e}")
        
        accuracy = correct_count / len(test_queries) if test_queries else 0
        logger.info(f"📊 准确率: {accuracy:.1%} ({correct_count}/{len(test_queries)})")
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有领域的统计信息"""
        stats = {}
        
        for domain_name, domain in self.domains.items():
            try:
                collection_info = self.vector_store.client.get_collection(domain.collection_name)
                stats[domain_name] = {
                    'collection': domain.collection_name,
                    'description': domain.description,
                    'enabled': domain.enabled,
                    'sources_count': len(domain.sources),
                    'documents_count': collection_info.points_count,
                    'update_frequency_days': domain.update_frequency_days
                }
            except:
                stats[domain_name] = {
                    'collection': domain.collection_name,
                    'description': domain.description,
                    'enabled': domain.enabled,
                    'sources_count': len(domain.sources),
                    'documents_count': 0,
                    'update_frequency_days': domain.update_frequency_days,
                    'error': 'Collection not found'
                }
        
        return stats

    def process_reviews(self, dry_run: bool = True):
        """处理人工审查过的快照文件"""
        logger.info(f"🔍 开始处理审查文件... (模式: {'模拟' if dry_run else '生产'})")
        
        processed_dir = self.review_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        items_ingested = 0
        files_processed = 0

        for review_file in self.review_dir.glob("*.yaml"):
            logger.info(f"  - 正在处理文件: {review_file.name}")
            try:
                with open(review_file, 'r', encoding='utf-8') as f:
                    snapshot_data = yaml.safe_load(f)

                approved_items = [
                    item for item in snapshot_data.get('review_items', [])
                    if item.get('status') == 'approved'
                ]

                if not approved_items:
                    logger.info("    - 未发现 'approved' 状态的条目，跳过。")
                    continue

                logger.info(f"    - 发现 {len(approved_items)} 个已批准的条目。")
                domain_name = snapshot_data['metadata']['domain']
                domain = self.domains.get(domain_name)

                if not domain:
                    logger.error(f"    - ❌ 领域 '{domain_name}' 的配置未找到，无法处理。")
                    continue

                # 将批准的条目转换为存储格式
                paragraphs_to_store = [(item['content'], item.get('similarity_score', 0.5)) for item in approved_items]
                metadata = snapshot_data['metadata']

                if not dry_run:
                    # 使用asyncio.run来调用异步的存储函数
                    asyncio.run(self._store_content(domain, SourceConfig(name=metadata['source'], url=metadata['url'], type='manual'), paragraphs_to_store, metadata))
                
                items_ingested += len(approved_items)
                files_processed += 1

                if not dry_run:
                    # 将已处理的文件移动到 processed 文件夹
                    shutil.move(str(review_file), str(processed_dir / review_file.name))
                    logger.info(f"    - ✅ 文件已处理并移动至: {processed_dir.name}")

            except Exception as e:
                logger.error(f"  - ❌ 处理审查文件失败 {review_file.name}: {e}", exc_info=True)

        logger.info(f"✅ 审查处理完成。共处理 {files_processed} 个文件， ingest 了 {items_ingested} 个条目。")

    async def _is_change_significant(self, url: str, old_content: str, new_content: str) -> Tuple[bool, str]:
        """使用LLM判断页面变化是否重大"""
        from src.infrastructure.llm.factory import LLMFactory
        llm = LLMFactory.get_llm()

        # Simple hash check first to avoid LLM calls for identical content
        if hashlib.md5(old_content.encode()).hexdigest() == hashlib.md5(new_content.encode()).hexdigest():
            return False, "内容哈希值未变"

        prompt = f"""
        Analyze the difference between the two versions of the webpage content below.
        A "significant" change involves updates to policy, numbers, dates, application requirements, or the addition/removal of key steps.
        Ignore minor changes like typo fixes, sentence restructuring, or formatting adjustments.

        OLD VERSION (summary):
        {old_content[:1500]}...

        NEW VERSION (summary):
        {new_content[:1500]}...

        Is the change significant? Respond in JSON format.
        Example:
        {{
          "is_significant": true,
          "reason": "The deadline was updated from 2024 to 2025."
        }}
        """
        try:
            response = llm.generate(prompt)
            result = json.loads(response.strip())
            is_significant = result.get("is_significant", False)
            reason = result.get("reason", "No specific reason provided.")
            logger.info(f"Semantic diff for {url}: Significant: {is_significant}, Reason: {reason}")
            return is_significant, reason
        except Exception as e:
            logger.error(f"Semantic diff failed for {url}: {e}")
            # Fallback to simple hash comparison on error
            return old_content != new_content, "LLM diff failed, fell back to hash comparison."

    def _get_cached_page_content(self, url: str) -> Optional[str]:
        """获取缓存的页面内容"""
        cache_file = PAGE_CONTENT_CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.html"
        if cache_file.exists():
            return cache_file.read_text(encoding='utf-8')
        return None

    def _cache_page_content(self, url: str, content: str):
        """缓存页面内容"""
        cache_file = PAGE_CONTENT_CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.html"
        cache_file.write_text(content, encoding='utf-8')

    async def update_incremental(self, force: bool = False):
        """
        执行增量更新。
        只处理在 `update_queue.json` 中被标记为有更新的页面。
        """
        logger.info("🚀 Starting incremental update...")
        if not UPDATE_QUEUE_FILE.exists():
            logger.info("✅ No update queue found. All content is up-to-date.")
            return

        with open(UPDATE_QUEUE_FILE, 'r') as f:
            update_queue = json.load(f)

        if not update_queue:
            logger.info("✅ Update queue is empty. No work to do.")
            # Clean up empty queue file
            UPDATE_QUEUE_FILE.unlink()
            return
            
        await self._initialize_browser()
        
        updated_count = 0
        processed_urls = set()

        for item in update_queue:
            url = item['url']
            source_name = item['source_name']
            
            if url in processed_urls:
                continue

            logger.info(f"Processing updated URL from queue: {url}")
            
            # Find the corresponding domain and source config
            domain, source = None, None
            for d in self.domains.values():
                for s in d.sources:
                    # A bit loose, but should work for now.
                    if s.name == source_name:
                        domain, source = d, s
                        break
                if domain:
                    break
            
            if not domain or not source:
                logger.warning(f"Could not find matching domain/source for {source_name}. Skipping {url}.")
                continue

            try:
                page = await self.browser.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                new_content = await page.content()
                await page.close()
                
                old_content = self._get_cached_page_content(url)

                should_update = True
                if old_content and not force:
                    is_significant, reason = await self._is_change_significant(url, old_content, new_content)
                    if not is_significant:
                        should_update = False
                
                if should_update:
                    logger.info(f"✅ Change is significant. Updating knowledge base for {url}.")
                    # Use existing parsing and storing logic
                    parser = self.parsers.get(domain.parser_class or 'generic', self.parsers['generic'])
                    paragraphs = parser.parse(new_content, source.parser_config or {})
                    metadata = parser.extract_metadata(new_content, url)
                    
                    quality_checker = QualityChecker(domain.quality_rules or {})
                    # Create relevance vector from domain desc/source name for better consistency
                    relevance_text = f"{domain.description} {source.name}".strip()
                    relevance_vector = get_embedding(relevance_text)
                    
                    quality_results = quality_checker.batch_check_quality(paragraphs, relevance_vector)
                    
                    filtered_paragraphs = [(p, score) for p, (passed, score, _) in zip(paragraphs, quality_results) if passed]

                    if filtered_paragraphs:
                        # We need a way to remove old docs for this URL before adding new ones
                        logger.info(f"UPSERTING: {len(filtered_paragraphs)} paragraphs for {url}")
                        await self._store_content(domain, source, filtered_paragraphs, metadata, specific_url=url)
                        updated_count += 1
                    
                    self._cache_page_content(url, new_content)
                else:
                    logger.info(f"Skipping update for {url}: change not significant.")

                processed_urls.add(url)

            except Exception as e:
                logger.error(f"Failed to process page {url}: {e}", exc_info=True)

        await self._close_browser()
        
        # Clean up the queue file after processing
        logger.info(f"Incremental update finished. Updated {updated_count} pages.")
        UPDATE_QUEUE_FILE.unlink()

    async def _store_content(self, domain: DomainConfig, source: SourceConfig, 
                           paragraphs: List[Tuple[str, float]], metadata: Dict[str, Any], specific_url: str = None):
        """存储内容到向量数据库，可选择性地先删除特定URL的旧内容"""
        collection_name = domain.collection_name
        self._ensure_collection(collection_name)
        
        target_url = specific_url or source.url

        # **CRITICAL STEP**: Delete old entries for this specific URL to avoid duplicates
        self.vector_store.delete(
            collection_name=collection_name,
            filter_conditions={"must": [{"key": "payload.url", "match": {"value": target_url}}]}
        )
        logger.info(f"Deleted old vector entries for URL: {target_url}")

        points = []
        for i, (paragraph, quality_score) in enumerate(paragraphs):
            vector = get_embedding(paragraph)
            
            # 使用UUID作为ID
            point_id = str(uuid.uuid4())
            
            point_data = {
                "id": point_id,
                "vector": vector,
                "payload": {
                    "content": paragraph,
                    "domain": domain.name,
                    "source": source.name,
                    "url": target_url, # Use the specific URL
                    "quality_score": quality_score,
                    "created_at": datetime.now().isoformat(),
                    **metadata
                }
            }
            points.append(point_data)
        self.vector_store.upsert(collection_name, points)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="通用知识库管理系统")
    parser.add_argument("command", choices=['update', 'update-domain', 'test', 'stats', 'init', 'process-reviews', 'update-incremental'], help="要执行的命令")
    parser.add_argument("--domain", help="指定领域名称")
    parser.add_argument("--config-dir", default="config/domains", help="配置目录路径")
    parser.add_argument("--force", action="store_true", help="强制更新")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="设置日志级别")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不执行实际的数据库写入或文件移动")
    
    args = parser.parse_args()
    
    # 配置日志级别
    log_level = args.log_level.upper()
    logging.getLogger().setLevel(log_level)
    # 控制第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    manager = GenericKnowledgeManager(config_dir=args.config_dir)
    
    if args.command == "init":
        # The init command already creates an example structure, so it's fine
        pass
            
    elif args.command == "update":
        await manager.update_all_domains(force_update=args.force)
        
    elif args.command == "update-domain":
        if not args.domain:
            print("❌ 请使用 --domain 指定领域名称")
            return
        await manager.update_domain(args.domain, force_update=args.force)
        
    elif args.command == "test":
        if not args.domain:
            print("❌ 请使用 --domain 指定领域名称")
            manager.test_all_domains()
        else:
            manager.test_domain_queries(args.domain)

    elif args.command == "stats":
        stats = manager.get_statistics()
        print("📊 知识库统计信息:\n")
        for domain_name, domain_stats in stats.items():
            print(f"领域: {domain_name}")
            print(f"  描述: {domain_stats['description']}")
            print(f"  状态: {'启用' if domain_stats['enabled'] else '禁用'}")
            print(f"  数据源数: {domain_stats['sources_count']}")
            print(f"  文档数: {domain_stats.get('documents_count', 0)}")
            print(f"  更新频率: 每{domain_stats['update_frequency_days']}天")
            if 'error' in domain_stats:
                print(f"  ⚠️ 错误: {domain_stats['error']}")
            print()

    elif args.command == "process-reviews":
        manager.process_reviews(dry_run=args.dry_run)

    elif args.command == "update-incremental":
        await manager.update_incremental(force_update=args.force)

if __name__ == "__main__":
    asyncio.run(main()) 