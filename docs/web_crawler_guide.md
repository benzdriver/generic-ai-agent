# Web Crawler Integration Guide

## 现在的正确架构

感谢您的反馈！现在 `generic_knowledge_manager.py` 已经内置了深层爬取功能，无需额外的脚本。

## 深层爬取功能

### 在配置中启用深层爬取

只需在 `parser_config` 中添加 `deep_crawl: true`：

```yaml
# config/domains/immigration_deep.yaml
description: 'Canadian immigration information with deep crawling'
collection_name: 'immigration_deep_docs'
sources:
  - name: 'IRCC_Deep_Crawl'
    url: 'https://www.canada.ca/en/immigration-refugees-citizenship.html'
    type: 'website'
    parser_config:
      deep_crawl: true  # 启用深层爬取
      max_depth: 3      # 最大爬取深度
      max_pages: 100    # 最大页面数
      selectors:
        content: 'main, article, .content, #content, p, section'
        exclude: 'script, style, nav, footer, header'
```

### 运行深层爬取

```bash
# 使用深层爬取更新移民知识库
python scripts/generic_knowledge_manager.py update-domain --domain immigration_deep

# 查看统计信息
python scripts/generic_knowledge_manager.py stats
```

## 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `deep_crawl` | 是否启用深层爬取 | false |
| `max_depth` | 最大爬取深度（从起始URL开始） | 3 |
| `max_pages` | 最大爬取页面数 | 50 |

## 工作原理

1. **自动发现链接**：从起始 URL 开始，自动发现所有可见链接
2. **深度优先爬取**：按深度优先策略访问页面
3. **视觉过滤**：只爬取视觉可见的链接（宽高大于0，非hidden）
4. **同域名限制**：只爬取同一域名下的页面
5. **批量存储**：收集所有内容后批量存入向量数据库

## 与 browser-use 的关系

虽然 browser-use 是一个强大的工具，但对于知识库构建场景：
- 我们的集成方案更轻量级，直接使用 Playwright
- 无需额外安装和配置 browser-use
- 与现有的质量检查和审查流程完美集成

## 使用建议

### 场景 1：官网完整爬取
```yaml
parser_config:
  deep_crawl: true
  max_depth: 3
  max_pages: 100
```

### 场景 2：特定栏目爬取
```yaml
# 只爬取 SUV 相关页面
url: 'https://www.canada.ca/.../start-visa.html'
parser_config:
  deep_crawl: true
  max_depth: 2  # 较浅的深度
  max_pages: 30
```

### 场景 3：单页面爬取（默认）
```yaml
# 不设置 deep_crawl 或设为 false
parser_config:
  selectors:
    content: 'main, article'
```

## 优势

1. **统一管理**：所有功能集成在 generic_knowledge_manager 中
2. **质量控制**：深层爬取的内容也经过相同的质量检查
3. **增量更新**：支持 content_hash 检测，避免重复爬取
4. **灵活配置**：可以混合使用深层和单页爬取

## 监控和调试

查看深层爬取的进度：
```bash
# 使用 DEBUG 级别查看详细日志
python scripts/generic_knowledge_manager.py update-domain --domain immigration_deep --log-level DEBUG
```

## 总结

- ✅ 深层爬取功能已集成到 `generic_knowledge_manager.py`
- ✅ 通过配置文件即可启用，无需额外脚本
- ✅ 支持灵活的爬取策略配置
- ✅ 与现有的质量检查和存储流程无缝集成

这样的设计保持了系统的简洁性，同时提供了强大的深层爬取能力！ 