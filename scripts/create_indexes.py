#!/usr/bin/env python3
# scripts/create_indexes.py

"""
为Qdrant集合创建索引：为集合中的字段创建索引，以支持过滤搜索
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PayloadSchemaType

# 定义集合名称
CANONICAL_COLLECTION = "canonical_queries"  # 规范化查询集合
CONVERSATION_COLLECTION = "conversations"   # 对话历史集合
DOCUMENT_COLLECTION = "documents"          # 文档知识库集合
MERGED_COLLECTION = "merged_knowledge"     # 合并知识点集合

def main():
    """为集合创建索引"""
    print("=" * 70)
    print("🔍 为Qdrant集合创建索引")
    print("=" * 70)
    
    # 加载环境变量
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"加载环境变量文件: {env_path}")
        load_dotenv(env_path)
    else:
        print("⚠️ 未找到.env文件，使用默认值")
    
    # 从环境变量获取URL和API密钥
    url = os.environ.get('QDRANT_URL')
    api_key = os.environ.get('QDRANT_API_KEY')
    
    if not api_key:
        print("⚠️ 未设置QDRANT_API_KEY环境变量，请确保已设置正确的API密钥")
        return
    
    try:
        # 创建客户端
        client = QdrantClient(url=url, api_key=api_key)
        print(f"✅ 成功连接到Qdrant: {url}")
        
        # 为每个集合创建索引
        collections = [
            (DOCUMENT_COLLECTION, [
                ("text", PayloadSchemaType.TEXT),
                ("source", PayloadSchemaType.KEYWORD),
                ("category", PayloadSchemaType.KEYWORD),
                ("is_metadata", PayloadSchemaType.BOOL),
                ("collection_info", PayloadSchemaType.BOOL)
            ]),
            (CANONICAL_COLLECTION, [
                ("text", PayloadSchemaType.TEXT),
                ("is_metadata", PayloadSchemaType.BOOL),
                ("collection_info", PayloadSchemaType.BOOL)
            ]),
            (CONVERSATION_COLLECTION, [
                ("user_id", PayloadSchemaType.KEYWORD),
                ("session_id", PayloadSchemaType.KEYWORD),
                ("timestamp", PayloadSchemaType.INTEGER),
                ("is_metadata", PayloadSchemaType.BOOL),
                ("collection_info", PayloadSchemaType.BOOL)
            ]),
            (MERGED_COLLECTION, [
                ("text", PayloadSchemaType.TEXT),
                ("source", PayloadSchemaType.KEYWORD),
                ("category", PayloadSchemaType.KEYWORD),
                ("is_metadata", PayloadSchemaType.BOOL),
                ("collection_info", PayloadSchemaType.BOOL)
            ])
        ]
        
        for collection_name, indexes in collections:
            print(f"\n为集合 {collection_name} 创建索引...")
            
            # 检查集合是否存在
            if not client.collection_exists(collection_name):
                print(f"⚠️ 集合 {collection_name} 不存在，跳过")
                continue
            
            # 获取当前索引
            try:
                current_schema = client.get_collection(collection_name).payload_schema
                print(f"当前索引: {current_schema}")
            except Exception as e:
                print(f"⚠️ 获取当前索引失败: {str(e)}")
                current_schema = {}
            
            # 创建索引
            for field_name, field_type in indexes:
                try:
                    # 检查索引是否已存在
                    if field_name in current_schema:
                        print(f"  ℹ️ 字段 {field_name} 的索引已存在")
                        continue
                    
                    # 创建索引
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_type
                    )
                    print(f"  ✅ 成功为字段 {field_name} 创建 {field_type} 类型的索引")
                except Exception as e:
                    print(f"  ❌ 为字段 {field_name} 创建索引失败: {str(e)}")
        
    except Exception as e:
        print(f"❌ 创建索引失败: {str(e)}")
    
    print("\n索引创建完成")

if __name__ == "__main__":
    main() 