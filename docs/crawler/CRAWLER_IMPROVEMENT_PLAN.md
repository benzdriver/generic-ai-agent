# 🕷️ 智能爬虫系统改进计划

## 📋 项目背景

当前爬虫系统在爬取加拿大移民官网（canada.ca）时存在覆盖率低、内容提取不完整等问题，导致知识库信息不全面，影响AI回答的准确性。

## 🎯 改进目标

1. **完整覆盖官网**：确保爬取所有移民相关页面，不遗漏重要信息
2. **结构化数据提取**：正确提取表格、列表、PDF等结构化内容
3. **智能内容识别**：准确识别不同类型的移民路径和要求
4. **增量更新支持**：高效更新变化的内容，避免重复爬取

## 🔧 技术改进方案

### 1. 增强爬取策略

#### 1.1 改进URL优先级算法
```python
class SmartURLPrioritizer:
    """智能URL优先级排序器"""
    
    # 高优先级路径模式
    HIGH_PRIORITY_PATTERNS = [
        # 移民项目
        r'/express-entry',
        r'/provincial-nominee',
        r'/start-up-visa',
        r'/self-employed',
        r'/family-sponsorship',
        r'/atlantic-immigration',
        r'/rural-northern',
        r'/caregivers',
        
        # 关键流程
        r'/how-to-apply',
        r'/eligibility',
        r'/requirements',
        r'/processing-times',
        r'/after-you-apply',
        r'/prepare-arrival',
        
        # 工具和指南
        r'/tools/',
        r'/guides/',
        r'/forms/',
        r'/fees/'
    ]
    
    def calculate_priority(self, url: str, parent_importance: float) -> float:
        """计算URL优先级分数"""
        score = 0.0
        
        # 1. URL路径匹配
        for pattern in self.HIGH_PRIORITY_PATTERNS:
            if re.search(pattern, url, re.I):
                score += 0.3
                
        # 2. 继承父页面重要性
        score += parent_importance * 0.3
        
        # 3. URL深度惩罚（但不要太严格）
        depth = len(urlparse(url).path.split('/'))
        score -= depth * 0.05
        
        # 4. 查询参数奖励（可能是筛选条件）
        if '?' in url:
            score += 0.1
            
        return min(max(score, 0), 1.0)
```

#### 1.2 实现站点地图优先爬取
```python
async def crawl_sitemap_first(self):
    """先爬取站点地图获取所有URL"""
    sitemap_urls = [
        "https://www.canada.ca/sitemap.xml",
        "https://www.canada.ca/en/immigration-refugees-citizenship/sitemap.xml"
    ]
    
    all_urls = []
    for sitemap_url in sitemap_urls:
        urls = await self.parse_sitemap(sitemap_url)
        # 过滤移民相关URL
        immigration_urls = [
            url for url in urls 
            if 'immigration' in url or 'visa' in url or 'permit' in url
        ]
        all_urls.extend(immigration_urls)
    
    return self.prioritize_urls(all_urls)
```

### 2. 增强内容提取

#### 2.1 表格数据提取器
```python
class TableExtractor:
    """表格数据提取器"""
    
    async def extract_tables(self, page):
        """提取页面中的所有表格"""
        tables = await page.query_selector_all('table')
        extracted_tables = []
        
        for table in tables:
            # 提取表格标题
            caption = await table.query_selector('caption')
            title = await caption.inner_text() if caption else ""
            
            # 提取表头
            headers = []
            header_cells = await table.query_selector_all('th')
            for cell in header_cells:
                headers.append(await cell.inner_text())
            
            # 提取数据行
            rows = []
            data_rows = await table.query_selector_all('tr')
            for row in data_rows:
                cells = await row.query_selector_all('td')
                if cells:
                    row_data = []
                    for cell in cells:
                        row_data.append(await cell.inner_text())
                    rows.append(row_data)
            
            extracted_tables.append({
                'title': title,
                'headers': headers,
                'data': rows,
                'markdown': self.table_to_markdown(headers, rows)
            })
            
        return extracted_tables
    
    def table_to_markdown(self, headers, rows):
        """将表格转换为Markdown格式"""
        if not headers:
            return ""
            
        # 构建Markdown表格
        md = "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["-" * len(h) for h in headers]) + " |\n"
        
        for row in rows:
            if len(row) == len(headers):
                md += "| " + " | ".join(row) + " |\n"
                
        return md
```

#### 2.2 PDF内容提取
```python
class PDFExtractor:
    """PDF文档提取器"""
    
    async def should_download_pdf(self, pdf_url: str, title: str) -> bool:
        """判断是否应该下载PDF"""
        important_pdfs = [
            'guide', 'checklist', 'form', 'instruction',
            'requirement', 'eligibility', 'process'
        ]
        
        # 检查URL或标题是否包含重要关键词
        url_lower = pdf_url.lower()
        title_lower = title.lower()
        
        for keyword in important_pdfs:
            if keyword in url_lower or keyword in title_lower:
                return True
                
        return False
    
    async def extract_pdf_content(self, pdf_url: str) -> Dict:
        """提取PDF内容"""
        try:
            # 下载PDF
            pdf_content = await self.download_pdf(pdf_url)
            
            # 使用 PyPDF2 或 pdfplumber 提取文本
            text = self.extract_text_from_pdf(pdf_content)
            
            # 提取表单字段（如果是可填写表单）
            form_fields = self.extract_form_fields(pdf_content)
            
            return {
                'url': pdf_url,
                'type': 'pdf',
                'text': text,
                'form_fields': form_fields,
                'summary': self.generate_pdf_summary(text)
            }
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return None
```

#### 2.3 交互式内容处理
```python
class InteractiveContentHandler:
    """处理JavaScript动态内容"""
    
    async def handle_accordions(self, page):
        """展开所有折叠内容"""
        # 查找所有可展开元素
        accordions = await page.query_selector_all('[data-toggle="collapse"], .accordion-button')
        
        for accordion in accordions:
            try:
                await accordion.click()
                await page.wait_for_timeout(500)  # 等待动画完成
            except:
                pass
    
    async def handle_tabs(self, page):
        """切换所有标签页获取内容"""
        tabs = await page.query_selector_all('[role="tab"]')
        all_tab_content = []
        
        for tab in tabs:
            try:
                await tab.click()
                await page.wait_for_timeout(500)
                
                # 获取当前标签内容
                content = await page.evaluate('''
                    () => {
                        const activePanel = document.querySelector('[role="tabpanel"][aria-hidden="false"]');
                        return activePanel ? activePanel.innerText : '';
                    }
                ''')
                
                all_tab_content.append(content)
            except:
                pass
                
        return all_tab_content
```

### 3. 不同移民路径的专门处理

#### 3.1 移民项目识别器
```python
class ImmigrationProgramDetector:
    """识别页面所属的移民项目"""
    
    PROGRAM_PATTERNS = {
        'express_entry': {
            'keywords': ['express entry', 'federal skilled worker', 'canadian experience class', 'federal skilled trades'],
            'urls': ['/express-entry/', '/ee/']
        },
        'pnp': {
            'keywords': ['provincial nominee', 'pnp', 'nomination certificate'],
            'urls': ['/provincial-nominees/', '/pnp/']
        },
        'start_up_visa': {
            'keywords': ['start-up visa', 'suv', 'letter of support', 'designated organization'],
            'urls': ['/start-visa/', '/suv/']
        },
        'family_sponsorship': {
            'keywords': ['sponsor', 'spouse', 'common-law', 'conjugal', 'dependent child', 'parent', 'grandparent'],
            'urls': ['/sponsor/', '/family/']
        },
        'caregiver': {
            'keywords': ['caregiver', 'home child care', 'home support worker'],
            'urls': ['/caregivers/']
        }
    }
    
    def detect_program(self, url: str, title: str, content: str) -> List[str]:
        """检测页面涉及的移民项目"""
        detected_programs = []
        
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:1000]  # 只检查前1000字符
        
        for program, patterns in self.PROGRAM_PATTERNS.items():
            # URL匹配
            for url_pattern in patterns['urls']:
                if url_pattern in url_lower:
                    detected_programs.append(program)
                    break
                    
            # 关键词匹配
            for keyword in patterns['keywords']:
                if keyword in title_lower or keyword in content_lower:
                    detected_programs.append(program)
                    break
                    
        return list(set(detected_programs))
```

#### 3.2 特定内容增强提取
```python
class ProgramSpecificExtractor:
    """针对不同移民项目的特定内容提取"""
    
    async def extract_express_entry_content(self, page, content):
        """提取Express Entry特定内容"""
        extracted = {
            'program': 'express_entry',
            'crs_score_table': None,
            'noc_requirements': None,
            'language_requirements': None,
            'education_assessment': None
        }
        
        # 查找CRS分数表
        crs_tables = await self.find_tables_by_keywords(page, ['comprehensive ranking system', 'crs', 'points'])
        if crs_tables:
            extracted['crs_score_table'] = crs_tables[0]
            
        # 提取语言要求
        language_section = await self.find_section_by_heading(page, ['language', 'clb', 'ielts', 'celpip'])
        if language_section:
            extracted['language_requirements'] = language_section
            
        return extracted
    
    async def extract_pnp_content(self, page, content):
        """提取PNP特定内容"""
        extracted = {
            'program': 'pnp',
            'provinces': [],
            'streams': [],
            'requirements_by_province': {}
        }
        
        # 识别省份
        provinces = ['alberta', 'british columbia', 'manitoba', 'ontario', 'quebec', 'saskatchewan']
        for province in provinces:
            if province in content.lower():
                extracted['provinces'].append(province)
                
                # 查找该省份的具体要求
                province_section = await self.find_section_by_heading(page, [province])
                if province_section:
                    extracted['requirements_by_province'][province] = province_section
                    
        return extracted
```

### 4. 智能去重和增量更新

#### 4.1 内容指纹生成
```python
class ContentFingerprint:
    """生成内容指纹用于去重"""
    
    def generate_fingerprint(self, content: str) -> str:
        """生成内容指纹"""
        # 1. 规范化文本
        normalized = self.normalize_text(content)
        
        # 2. 提取关键句子
        key_sentences = self.extract_key_sentences(normalized)
        
        # 3. 生成哈希
        content_hash = hashlib.sha256(
            ''.join(key_sentences).encode()
        ).hexdigest()
        
        return content_hash
    
    def normalize_text(self, text: str) -> str:
        """规范化文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s]', '', text)
        # 转小写
        return text.lower().strip()
```

#### 4.2 增量更新检测
```python
class IncrementalUpdateDetector:
    """检测页面是否有更新"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        
    async def has_content_changed(self, url: str, new_content: str) -> bool:
        """检查内容是否有实质性变化"""
        # 获取已存储的内容
        existing = await self.vector_store.get_by_url(url)
        if not existing:
            return True
            
        # 比较内容指纹
        old_fingerprint = existing.get('fingerprint')
        new_fingerprint = ContentFingerprint().generate_fingerprint(new_content)
        
        if old_fingerprint != new_fingerprint:
            # 进一步检查是否只是小改动
            similarity = self.calculate_similarity(
                existing.get('content'), 
                new_content
            )
            
            # 如果相似度低于90%，认为有实质性更新
            return similarity < 0.9
            
        return False
```

### 5. 爬虫调度优化

#### 5.1 并行爬取管理
```python
class CrawlerScheduler:
    """爬虫调度器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def crawl_batch(self, urls: List[str]):
        """批量爬取URL"""
        tasks = []
        
        for url in urls:
            task = self.crawl_with_limit(url)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理失败的URL，加入重试队列
        failed_urls = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                failed_urls.append(url)
                
        return results, failed_urls
    
    async def crawl_with_limit(self, url: str):
        """限流爬取"""
        async with self.semaphore:
            return await self.crawl_single_url(url)
```

### 6. 配置文件优化

```yaml
# improved_immigration_crawler.yaml
crawler_config:
  # 基础设置
  max_depth: 10  # 适中的深度
  max_pages: 5000  # 足够覆盖整个网站
  concurrent_requests: 20  # 提高并发
  
  # 内容提取
  extract_tables: true
  extract_pdfs: true
  handle_javascript: true
  
  # 智能爬取
  use_sitemap: true
  smart_url_priority: true
  detect_programs: true
  
  # 质量控制
  min_content_length: 100
  max_content_length: 50000
  importance_threshold: 0.2
  
  # 特定程序配置
  program_specific:
    express_entry:
      priority_boost: 0.3
      extract_crs_table: true
      extract_noc_codes: true
    pnp:
      priority_boost: 0.3
      extract_provincial_requirements: true
    start_up_visa:
      priority_boost: 0.25
      extract_designated_orgs: true
      
  # 排除模式（优化后）
  exclude_patterns:
    - '/fr/'  # 法语页面
    - '/news-releases/'  # 新闻稿
    - '/media/'  # 媒体资源
    - '/video/'  # 视频
    - '/(contact|help|search)/'  # 功能页面
    
  # 包含模式（新增）
  include_patterns:
    - '/services/immigrate'
    - '/immigration-refugees-citizenship'
    - '/en/immigration'
    - '/apply/'
    - '/tools/'
    - '/guides/'
```

## 📊 实施计划

### 第一阶段：核心改进（1周）
1. ✅ 实现智能URL优先级算法
2. ✅ 添加表格数据提取器
3. ✅ 实现基础的程序识别器

### 第二阶段：内容增强（2周）
1. ✅ PDF内容提取
2. ✅ JavaScript动态内容处理
3. ✅ 特定程序内容提取器

### 第三阶段：优化和测试（1周）
1. ✅ 内容去重机制
2. ✅ 增量更新支持
3. ✅ 性能优化和测试

## 🎯 预期效果

1. **覆盖率提升**：从20页提升到2000+页，覆盖95%以上的移民相关内容
2. **内容质量**：正确提取所有表格、要求列表、PDF指南
3. **更新效率**：增量更新只处理变化内容，减少90%的重复爬取
4. **查询准确性**：AI能够准确回答各种移民路径的具体要求

## 🔍 监控指标

```python
class CrawlerMetrics:
    """爬虫性能指标"""
    
    def __init__(self):
        self.metrics = {
            'total_urls_discovered': 0,
            'total_pages_crawled': 0,
            'relevant_pages_found': 0,
            'tables_extracted': 0,
            'pdfs_processed': 0,
            'programs_detected': Counter(),
            'content_duplicates': 0,
            'crawl_speed': 0,  # pages per minute
            'error_rate': 0
        }
    
    def generate_report(self):
        """生成爬虫效果报告"""
        return {
            'coverage': {
                'total_pages': self.metrics['total_pages_crawled'],
                'relevant_pages': self.metrics['relevant_pages_found'],
                'relevance_rate': self.metrics['relevant_pages_found'] / max(self.metrics['total_pages_crawled'], 1)
            },
            'content_extraction': {
                'tables': self.metrics['tables_extracted'],
                'pdfs': self.metrics['pdfs_processed'],
                'programs': dict(self.metrics['programs_detected'])
            },
            'efficiency': {
                'speed': self.metrics['crawl_speed'],
                'duplicate_rate': self.metrics['content_duplicates'] / max(self.metrics['total_pages_crawled'], 1),
                'error_rate': self.metrics['error_rate']
            }
        }
```

---

通过这些改进，爬虫系统将能够：
1. 完整爬取加拿大移民官网的所有相关内容
2. 正确提取各种格式的数据（表格、PDF、动态内容）
3. 智能识别不同的移民项目和路径
4. 高效进行增量更新，保持知识库的时效性

这将显著提升AI助手回答的准确性和完整性。