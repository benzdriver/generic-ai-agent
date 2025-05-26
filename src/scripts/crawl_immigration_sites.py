#!/usr/bin/env python3
# src/scripts/crawl_immigration_sites.py

"""
移民网站爬虫：定期爬取指定的移民官方网站并更新知识库
"""

import sys
import os
import requests
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 尝试导入项目模块
try:
    from knowledge_ingestion.doc_parser import parse_html_content
    from vector_engine.embedding_router import get_embedding
    from qdrant_client import QdrantClient
    from config.env_manager import init_config
    from vector_engine.qdrant_client import DOCUMENT_COLLECTION
except ImportError as e:
    print(f"导入项目模块失败: {str(e)}")
    print("请确保您在正确的环境中运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{project_root}/logs/crawler_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建logs目录（如果不存在）
Path(f"{project_root}/logs").mkdir(exist_ok=True)

# 创建缓存目录（如果不存在）
CACHE_DIR = Path(f"{project_root}/cache/crawled_pages")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 初始化配置
config = init_config()
qdrant_config = config['qdrant']

# 默认爬取的移民官方网站列表
DEFAULT_SITES = [
    {
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada.html",
        "name": "IRCC_Immigrate",
        "domain": "canada_immigration",
        "lang": "en"
    },
    {
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada.html",
        "name": "IRCC_Study",
        "domain": "canada_immigration",
        "lang": "en"
    },
    {
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html",
        "name": "IRCC_Work",
        "domain": "canada_immigration",
        "lang": "en"
    }
]

def get_client() -> QdrantClient:
    """获取Qdrant客户端"""
    if qdrant_config['is_cloud']:
        return QdrantClient(
            url=qdrant_config['url'],
            api_key=qdrant_config['api_key']
        )
    return QdrantClient(url=qdrant_config['url'])

def upsert_documents_to_collection(paragraphs: list, metadata: dict = None):
    """上传文档到指定的向量数据库集合"""
    client = get_client()
    points = []
    
    for paragraph in paragraphs:
        embedding = get_embedding(paragraph)
        point_id = str(uuid.uuid4())
        payload = {
            "text": paragraph,
        }
        if metadata:
            payload.update(metadata)

        points.append({
            "id": point_id,
            "vector": embedding,
            "payload": payload
        })

    client.upsert(
        collection_name=DOCUMENT_COLLECTION,
        points=points
    )
    logger.info(f"成功将 {len(points)} 个向量点写入 {DOCUMENT_COLLECTION} 集合")

def load_site_list(file_path=None):
    """加载要爬取的网站列表"""
    if file_path and Path(file_path).exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载网站列表文件失败: {str(e)}")
    
    logger.info("使用默认网站列表")
    return DEFAULT_SITES

def get_page_hash(url, content):
    """计算页面内容的哈希值，用于检测变化"""
    return hashlib.md5((url + content).encode('utf-8')).hexdigest()

def has_page_changed(url, content):
    """检查页面内容是否已更改"""
    page_hash = get_page_hash(url, content)
    hash_file = CACHE_DIR / f"{hashlib.md5(url.encode('utf-8')).hexdigest()}.hash"
    
    if hash_file.exists():
        with open(hash_file, 'r') as f:
            old_hash = f.read().strip()
            if old_hash == page_hash:
                return False
    
    # 保存新的哈希值
    with open(hash_file, 'w') as f:
        f.write(page_hash)
    
    return True

def crawl_page(site):
    """爬取单个页面并处理内容"""
    url = site["url"]
    name = site["name"]
    domain = site.get("domain", "immigration")
    lang = site.get("lang", "en")
    
    logger.info(f"爬取页面: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        # 检查页面是否有变化
        if not has_page_changed(url, content):
            logger.info(f"页面未变化，跳过处理: {url}")
            return False
        
        # 解析HTML内容
        logger.info(f"处理页面内容: {url}")
        chunks = parse_html_content(content)
        
        if not chunks:
            logger.warning(f"未从页面提取到有效内容: {url}")
            return False
        
        # 准备元数据
        metadata = {
            "source": name,
            "url": url,
            "domain": domain,
            "language": lang,
            "crawled_at": datetime.now().isoformat()
        }
        
        # 将内容写入向量数据库的documents集合
        logger.info(f"提取了 {len(chunks)} 个段落，写入documents集合...")
        upsert_documents_to_collection(chunks, metadata)
        
        logger.info(f"成功处理页面: {url}")
        return True
        
    except Exception as e:
        logger.error(f"爬取或处理页面失败 {url}: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("🕸️ 移民网站爬虫")
    print("=" * 70)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='爬取移民官方网站并更新知识库')
    parser.add_argument('--sites', help='网站列表JSON文件路径')
    args = parser.parse_args()
    
    # 加载网站列表
    sites = load_site_list(args.sites)
    
    if not sites:
        logger.error("没有要爬取的网站")
        return
    
    logger.info(f"开始爬取 {len(sites)} 个网站...")
    
    # 爬取每个网站
    success_count = 0
    for site in sites:
        if crawl_page(site):
            success_count += 1
        # 添加延迟，避免请求过于频繁
        time.sleep(2)
    
    logger.info(f"爬取完成。成功: {success_count}/{len(sites)}")
    print(f"\n✅ 爬取完成。成功处理了 {success_count}/{len(sites)} 个网站")

if __name__ == "__main__":
    main() 