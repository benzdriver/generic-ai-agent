# 🔍 智能爬虫人类审查系统

## 📋 概述

设计一个人类可审查的报告系统，确保爬取的信息真正有用，避免垃圾数据进入知识库。

## 🎯 核心目标

1. **信息分类**：自动将爬取内容分类为不同类型
2. **质量评分**：对每个页面的有用性进行评分
3. **人类审查**：生成易于审查的报告
4. **批量处理**：支持快速批准/拒绝

## 📊 报告系统设计

### 1. 信息分类体系

```python
class ContentClassifier:
    """内容分类器"""
    
    CONTENT_TYPES = {
        'ELIGIBILITY_CRITERIA': {
            'keywords': ['eligible', 'requirements', 'qualify', 'criteria', 'must have'],
            'patterns': [r'you (must|need to|should) have', r'minimum requirements?'],
            'importance': 10
        },
        'APPLICATION_PROCESS': {
            'keywords': ['apply', 'application', 'process', 'steps', 'how to'],
            'patterns': [r'step \d+', r'how to apply', r'application process'],
            'importance': 9
        },
        'FEES_AND_COSTS': {
            'keywords': ['fee', 'cost', 'payment', 'price', 'charge'],
            'patterns': [r'\$\d+', r'processing fee', r'application fee'],
            'importance': 8
        },
        'PROCESSING_TIMES': {
            'keywords': ['processing time', 'wait', 'timeline', 'duration'],
            'patterns': [r'\d+ (days|weeks|months)', r'processing time'],
            'importance': 8
        },
        'REQUIRED_DOCUMENTS': {
            'keywords': ['document', 'proof', 'certificate', 'form', 'evidence'],
            'patterns': [r'required documents?', r'you (must|need to) provide'],
            'importance': 9
        },
        'SCORE_CALCULATION': {
            'keywords': ['points', 'score', 'calculation', 'crs', 'ranking'],
            'patterns': [r'\d+ points?', r'score calculation', r'point system'],
            'importance': 9
        },
        'PROGRAM_SPECIFIC': {
            'keywords': ['express entry', 'pnp', 'start-up visa', 'caregiver'],
            'patterns': [r'specific to', r'only for', r'program requirements'],
            'importance': 8
        },
        'GENERAL_INFO': {
            'keywords': ['overview', 'introduction', 'about', 'general'],
            'patterns': [],
            'importance': 3
        },
        'NEWS_UPDATE': {
            'keywords': ['news', 'update', 'announcement', 'change'],
            'patterns': [r'as of \d{4}', r'effective (from|date)'],
            'importance': 5
        },
        'CONTACT_HELP': {
            'keywords': ['contact', 'help', 'support', 'assistance'],
            'patterns': [],
            'importance': 2
        }
    }
    
    def classify_content(self, url: str, title: str, content: str) -> Dict:
        """对内容进行分类和评分"""
        classifications = []
        total_score = 0
        
        for content_type, rules in self.CONTENT_TYPES.items():
            score = self._calculate_type_score(content, rules)
            if score > 0:
                classifications.append({
                    'type': content_type,
                    'confidence': score,
                    'importance': rules['importance']
                })
                total_score += score * rules['importance']
        
        return {
            'primary_type': max(classifications, key=lambda x: x['confidence'])['type'] if classifications else 'UNKNOWN',
            'all_types': classifications,
            'usefulness_score': min(total_score / 100, 10),  # 0-10分
            'evidence': self._extract_evidence(content, classifications)
        }
```

### 2. 有用信息提取器

```python
class UsefulInfoExtractor:
    """提取页面中的有用信息"""
    
    def extract_useful_info(self, page_content: Dict) -> Dict:
        """提取关键信息"""
        extracted = {
            'eligibility_requirements': [],
            'fees': [],
            'processing_times': [],
            'required_documents': [],
            'important_dates': [],
            'score_calculations': [],
            'tables': [],
            'key_points': [],
            'warnings': [],
            'tips': []
        }
        
        # 1. 提取资格要求
        eligibility = self._extract_eligibility(page_content)
        if eligibility:
            extracted['eligibility_requirements'] = eligibility
            
        # 2. 提取费用信息
        fees = self._extract_fees(page_content)
        if fees:
            extracted['fees'] = fees
            
        # 3. 提取处理时间
        times = self._extract_processing_times(page_content)
        if times:
            extracted['processing_times'] = times
            
        # 4. 提取表格数据
        if 'tables' in page_content:
            extracted['tables'] = self._process_tables(page_content['tables'])
            
        # 5. 提取关键要点
        key_points = self._extract_key_points(page_content)
        if key_points:
            extracted['key_points'] = key_points
            
        return extracted
    
    def _extract_eligibility(self, content: Dict) -> List[Dict]:
        """提取资格要求"""
        requirements = []
        
        # 查找包含资格要求的段落
        patterns = [
            r'(you must|you need to|you should|must have|required to have)',
            r'(eligible if|qualify if|eligibility criteria)',
            r'(minimum requirements?|basic requirements?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content['text'], re.I)
            for match in matches:
                # 提取完整句子
                start = max(0, match.start() - 200)
                end = min(len(content['text']), match.end() + 200)
                context = content['text'][start:end]
                
                # 提取要点
                requirement = {
                    'text': self._extract_sentence(context, match.group()),
                    'type': 'eligibility',
                    'confidence': 0.8
                }
                requirements.append(requirement)
                
        return requirements
```

### 3. 人类审查报告生成器

```python
class HumanReviewReportGenerator:
    """生成人类可审查的报告"""
    
    def generate_review_report(self, crawl_results: List[Dict]) -> str:
        """生成Markdown格式的审查报告"""
        
        # 按有用性分组
        high_value = [r for r in crawl_results if r['usefulness_score'] >= 7]
        medium_value = [r for r in crawl_results if 4 <= r['usefulness_score'] < 7]
        low_value = [r for r in crawl_results if r['usefulness_score'] < 4]
        
        report = f"""# 🔍 爬虫内容审查报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**总页面数**: {len(crawl_results)}
**高价值页面**: {len(high_value)}
**中等价值页面**: {len(medium_value)}
**低价值页面**: {len(low_value)}

---

## 📌 高价值内容（建议全部保留）

"""
        
        # 高价值内容详情
        for idx, result in enumerate(high_value[:20], 1):  # 只显示前20个
            report += self._format_page_review(idx, result, detailed=True)
            
        # 中等价值内容摘要
        report += "\n## 📋 中等价值内容（需要人工筛选）\n\n"
        report += self._generate_summary_table(medium_value)
        
        # 低价值内容列表
        report += "\n## 🗑️ 低价值内容（建议排除）\n\n"
        report += self._generate_exclusion_list(low_value)
        
        # 统计摘要
        report += self._generate_statistics_summary(crawl_results)
        
        return report
    
    def _format_page_review(self, idx: int, result: Dict, detailed: bool = False) -> str:
        """格式化单个页面的审查信息"""
        
        review = f"""
### {idx}. {result['title']}

**URL**: {result['url']}
**分类**: {result['classification']['primary_type']}
**有用性评分**: {result['usefulness_score']:.1f}/10
**内容长度**: {len(result['content'])} 字符

"""
        
        if detailed and result.get('extracted_info'):
            info = result['extracted_info']
            
            # 显示提取的关键信息
            if info.get('eligibility_requirements'):
                review += "**📍 资格要求**:\n"
                for req in info['eligibility_requirements'][:3]:
                    review += f"- {req['text']}\n"
                review += "\n"
                
            if info.get('fees'):
                review += "**💰 费用信息**:\n"
                for fee in info['fees']:
                    review += f"- {fee['type']}: {fee['amount']}\n"
                review += "\n"
                
            if info.get('processing_times'):
                review += "**⏱️ 处理时间**:\n"
                for time in info['processing_times']:
                    review += f"- {time['stage']}: {time['duration']}\n"
                review += "\n"
                
            if info.get('tables'):
                review += f"**📊 包含 {len(info['tables'])} 个表格**\n\n"
                
        # 添加审查按钮（用于交互式工具）
        review += f"""
**审查决定**: 
- [ ] ✅ 保留 - 有用信息
- [ ] ⚠️ 修改 - 需要清理
- [ ] ❌ 排除 - 无关内容
- [ ] 🔄 重新爬取 - 内容不完整

**备注**: ____________________

---
"""
        
        return review
```

### 4. 交互式审查工具

```python
class InteractiveReviewTool:
    """交互式审查工具"""
    
    def __init__(self, crawl_results: List[Dict]):
        self.results = crawl_results
        self.decisions = {}
        
    def start_review_session(self):
        """启动审查会话"""
        print("🔍 爬虫内容审查工具")
        print("=" * 50)
        
        # 1. 显示统计摘要
        self._show_summary()
        
        # 2. 批量审查高价值内容
        print("\n📌 高价值内容快速审查")
        high_value = [r for r in self.results if r['usefulness_score'] >= 7]
        
        if input(f"\n是否批量批准所有 {len(high_value)} 个高价值页面? (y/n): ").lower() == 'y':
            for result in high_value:
                self.decisions[result['url']] = 'APPROVED'
            print(f"✅ 已批准 {len(high_value)} 个页面")
        
        # 3. 逐个审查中等价值内容
        print("\n📋 中等价值内容详细审查")
        medium_value = [r for r in self.results if 4 <= r['usefulness_score'] < 7]
        
        for idx, result in enumerate(medium_value, 1):
            self._review_single_page(idx, result, len(medium_value))
            
        # 4. 生成最终报告
        self._generate_final_report()
    
    def _review_single_page(self, idx: int, result: Dict, total: int):
        """审查单个页面"""
        print(f"\n[{idx}/{total}] 审查页面")
        print("-" * 40)
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"分类: {result['classification']['primary_type']}")
        print(f"评分: {result['usefulness_score']:.1f}/10")
        
        # 显示关键信息
        if result.get('extracted_info'):
            print("\n提取的关键信息:")
            info = result['extracted_info']
            
            if info.get('key_points'):
                print("- 要点:", ', '.join(info['key_points'][:3]))
            if info.get('fees'):
                print("- 费用:", ', '.join([f"{f['type']}: {f['amount']}" for f in info['fees']]))
            if info.get('processing_times'):
                print("- 时间:", info['processing_times'][0]['duration'] if info['processing_times'] else 'N/A')
        
        # 获取决定
        while True:
            decision = input("\n决定 [A]批准 [R]拒绝 [S]跳过 [V]查看更多: ").upper()
            
            if decision == 'A':
                self.decisions[result['url']] = 'APPROVED'
                print("✅ 已批准")
                break
            elif decision == 'R':
                reason = input("拒绝原因: ")
                self.decisions[result['url']] = f'REJECTED: {reason}'
                print("❌ 已拒绝")
                break
            elif decision == 'S':
                self.decisions[result['url']] = 'SKIPPED'
                print("⏭️ 已跳过")
                break
            elif decision == 'V':
                # 显示更多内容
                print("\n内容预览:")
                print(result['content'][:500] + "...")
                continue
```

### 5. 自动化质量检查

```python
class QualityChecker:
    """自动化质量检查"""
    
    def check_content_quality(self, content: Dict) -> Dict:
        """检查内容质量"""
        issues = []
        quality_score = 100
        
        # 1. 检查内容完整性
        if len(content['text']) < 200:
            issues.append({
                'type': 'CONTENT_TOO_SHORT',
                'severity': 'HIGH',
                'message': '内容过短，可能不完整'
            })
            quality_score -= 30
            
        # 2. 检查是否包含错误页面标志
        error_indicators = ['404', 'not found', 'page does not exist', 'error occurred']
        for indicator in error_indicators:
            if indicator in content['text'].lower():
                issues.append({
                    'type': 'ERROR_PAGE',
                    'severity': 'CRITICAL',
                    'message': f'可能是错误页面: 包含"{indicator}"'
                })
                quality_score -= 50
                
        # 3. 检查是否是登录页面
        if 'sign in' in content['text'].lower() and 'password' in content['text'].lower():
            issues.append({
                'type': 'LOGIN_PAGE',
                'severity': 'HIGH',
                'message': '可能是登录页面'
            })
            quality_score -= 40
            
        # 4. 检查重复内容
        if self._is_duplicate_content(content):
            issues.append({
                'type': 'DUPLICATE_CONTENT',
                'severity': 'MEDIUM',
                'message': '内容可能与其他页面重复'
            })
            quality_score -= 20
            
        # 5. 检查关键信息密度
        info_density = self._calculate_info_density(content)
        if info_density < 0.1:
            issues.append({
                'type': 'LOW_INFO_DENSITY',
                'severity': 'MEDIUM',
                'message': '有用信息密度低'
            })
            quality_score -= 15
            
        return {
            'quality_score': max(0, quality_score),
            'issues': issues,
            'passed': quality_score >= 60
        }
```

### 6. 最终审查报告格式

```markdown
# 🔍 爬虫内容最终审查报告

## 📊 审查统计

| 类别 | 数量 | 百分比 |
|------|------|---------|
| 总页面数 | 2,847 | 100% |
| 已批准 | 1,923 | 67.5% |
| 已拒绝 | 724 | 25.4% |
| 待定 | 200 | 7.1% |

## ✅ 已批准的高价值内容

### 移民项目信息 (423页)
- Express Entry 完整指南: 156页
- 省提名计划详情: 89页
- Start-up Visa 要求: 45页
- 家庭团聚移民: 78页
- 护理人员项目: 55页

### 申请流程和要求 (387页)
- 资格评估工具: 23页
- 申请步骤指南: 145页
- 文件清单: 89页
- 费用明细: 67页
- 处理时间: 63页

### 重要表格和计算 (298页)
- CRS分数计算表: 12页
- NOC职业分类: 156页
- 语言测试要求: 45页
- 教育认证指南: 85页

## ❌ 已拒绝的内容

### 拒绝原因分析
1. **重复内容** (312页) - 相同信息的不同语言版本
2. **过时信息** (156页) - 2020年前的旧政策
3. **无关内容** (89页) - 新闻稿、媒体报道
4. **错误页面** (45页) - 404错误、维护页面
5. **低质量** (122页) - 内容过短或无实质信息

## 🔍 需要注意的发现

### 1. 缺失的重要信息
- [ ] 魁北克移民单独系统（需要特别爬取）
- [ ] 某些省份的PNP详细要求在PDF中
- [ ] 最新的政策更新在新闻稿中

### 2. 数据质量问题
- 部分表格数据提取不完整
- JavaScript渲染的内容需要特殊处理
- 一些重要PDF文档需要手动下载

### 3. 建议的后续行动
1. 对PDF文档进行专门爬取
2. 定期检查政策更新页面
3. 建立内容版本追踪系统

## 📈 知识库影响评估

**预期改进**:
- 问答准确率: 65% → 92%
- 内容覆盖率: 35% → 95%
- 信息时效性: 提升80%

**下一步**:
1. 导入已批准内容到向量数据库
2. 建立内容更新监控
3. 定期质量审查流程

---
*报告生成时间: 2024-12-17 15:30:00*
*审查人: [Your Name]*
*审查工具版本: 1.0*
```

### 7. 实施建议

1. **分阶段爬取**
   - 第一阶段：爬取主要移民项目页面（~500页）
   - 第二阶段：深度爬取具体要求（~2000页）
   - 第三阶段：补充PDF和动态内容

2. **人工审查流程**
   - 每批次审查200-300页
   - 使用自动分类预筛选
   - 重点审查中等价值内容

3. **质量保证**
   - 建立内容指纹避免重复
   - 定期抽查已批准内容
   - 用户反馈驱动的改进

通过这个系统，我们可以确保：
- 爬取的内容真正有用
- 人类可以高效审查大量页面
- 知识库质量得到保证
- 持续改进爬取策略