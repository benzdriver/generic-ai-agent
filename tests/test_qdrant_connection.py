#!/usr/bin/env python3
# tests/test_qdrant_connection.py

"""
Qdrant连接测试：使用正确的URL和API密钥测试Qdrant连接
"""

import sys
import os
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

def main():
    """测试Qdrant连接"""
    print("=" * 70)
    print("🔍 Qdrant连接测试")
    print("=" * 70)
    
    # 加载环境变量
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # 从环境变量获取URL和API密钥
    url = os.environ.get('QDRANT_URL', 'https://23b33ab7-02d1-4a51-b52a-967c3c5d7e0c.us-west-1-0.aws.cloud.qdrant.io:6333')
    api_key = os.environ.get('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ErhUqQTU')
    
    print(f"\n连接到Qdrant: {url}")
    print("使用API密钥进行认证...")
    
    try:
        # 创建客户端
        client = QdrantClient(url=url, api_key=api_key)
        
        # 尝试获取集合列表
        try:
            print("\n尝试获取集合列表...")
            collections = client.get_collections()
            
            # 检查响应
            print(f"✅ 成功获取集合列表！")
            print(f"发现 {len(collections.collections)} 个集合:")
            for collection in collections.collections:
                print(f"  - {collection.name}")
                
            # 尝试创建一个测试集合
            test_collection_name = "test_connection"
            print(f"\n尝试创建测试集合: {test_collection_name}...")
            
            # 检查集合是否已存在
            if client.collection_exists(test_collection_name):
                print(f"集合 {test_collection_name} 已存在，正在删除...")
                client.delete_collection(test_collection_name)
            
            # 创建集合
            client.create_collection(
                collection_name=test_collection_name,
                vectors_config=models.VectorParams(
                    size=4,  # 小维度用于测试
                    distance=models.Distance.COSINE
                )
            )
            
            # 验证集合已创建
            if client.collection_exists(test_collection_name):
                print(f"✅ 成功创建测试集合！")
                
                # 删除测试集合
                client.delete_collection(test_collection_name)
                print(f"✅ 成功删除测试集合！")
            else:
                print(f"❌ 创建测试集合失败！")
            
        except Exception as e:
            print(f"❌ 获取集合列表失败: {str(e)}")
            
            # 尝试健康检查
            try:
                print("\n尝试健康检查...")
                health = client.http.health_check()
                if health and hasattr(health, 'result') and health.result:
                    print("✅ 健康检查通过，服务器正常运行")
                else:
                    print("❌ 健康检查未通过")
            except Exception as e2:
                print(f"❌ 健康检查失败: {str(e2)}")
    
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
    
    print("\n测试完成")

if __name__ == "__main__":
    main() 