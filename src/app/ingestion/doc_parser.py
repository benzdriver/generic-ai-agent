# src/app/ingestion/doc_parser.py

"""
文档解析器：负责解析各种格式的文档
"""

import re
import html
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.infrastructure.config.env_manager import get_config

# 初始化配置
config = get_config()

def parse_html_content(html_content: str) -> List[Dict[str, Any]]:
    """解析HTML内容，提取文本段落
    
    Args:
        html_content: HTML内容字符串
        
    Returns:
        List[Dict[str, Any]]: 解析后的文档段落列表
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除脚本和样式标签
    for script in soup(["script", "style"]):
        script.decompose()
    
    # 提取文本段落
    paragraphs = []
    for element in soup.find_all(['p', 'div', 'section', 'article']):
        text = element.get_text(strip=True)
        if text and len(text) > 50:  # 过滤太短的段落
            paragraphs.append({
                'content': text,
                'type': 'paragraph',
                'source': 'html'
            })
    
    return paragraphs

def parse_ircc_html(html_content: str) -> List[str]:
    """解析IRCC网站的HTML内容"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除导航、页脚等无关内容
    for unwanted in soup.find_all(['nav', 'footer', 'header', 'aside']):
        unwanted.decompose()
    
    # 提取主要内容
    main_content = soup.find('main') or soup.find('div', class_='content') or soup
    
    paragraphs = []
    for p in main_content.find_all(['p', 'li', 'div']):
        text = p.get_text(strip=True)
        if text and len(text) > 30:
            # 清理文本
            text = re.sub(r'\s+', ' ', text)
            text = html.unescape(text)
            paragraphs.append(text)
    
    return paragraphs

def parse_ircc_text(text_content: str) -> List[str]:
    """解析纯文本内容"""
    # 按段落分割
    paragraphs = text_content.split('\n\n')
    
    cleaned_paragraphs = []
    for para in paragraphs:
        # 清理空白字符
        para = re.sub(r'\s+', ' ', para.strip())
        
        # 过滤太短的段落
        if len(para) > 30:
            cleaned_paragraphs.append(para)
    
    return cleaned_paragraphs

def extract_metadata(content: str, source_url: str = None) -> Dict[str, Any]:
    """提取文档元数据"""
    metadata = {
        'source_url': source_url,
        'content_length': len(content),
        'word_count': len(content.split()),
        'language': 'zh' if re.search(r'[\u4e00-\u9fff]', content) else 'en'
    }
    
    return metadata
