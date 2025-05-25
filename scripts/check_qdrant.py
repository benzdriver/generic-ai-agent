#!/usr/bin/env python3
# scripts/check_qdrant.py

"""
Qdrant连接检查：仅检查Qdrant连接，不需要其他API密钥
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

def main():
    """检查Qdrant连接"""
    print("=" * 70)
    print("🔍 Qdrant连接检查")
    print("=" * 70)
    
    # 加载环境变量
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"加载环境变量文件: {env_path}")
        load_dotenv(env_path)
    else:
        print("⚠️ 未找到.env文件，使用默认值")
    
    # 从环境变量获取URL和API密钥，设置默认值
    url = os.environ.get('QDRANT_URL')
    api_key = os.environ.get('QDRANT_API_KEY')
    
    if not api_key:
        print("⚠️ 未设置QDRANT_API_KEY环境变量，请确保已设置正确的API密钥")
        return
    
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
                
            # 定义我们需要的集合
            required_collections = [
                "canonical_queries",  # 规范化查询集合
                "conversations",      # 对话历史集合
                "documents",          # 文档知识库集合
                "merged_knowledge"    # 合并知识点集合
            ]
            
            # 检查是否缺少必需的集合
            existing_collections = [c.name for c in collections.collections]
            missing_collections = [c for c in required_collections if c not in existing_collections]
            
            if missing_collections:
                print(f"\n⚠️ 缺少以下集合: {', '.join(missing_collections)}")
                print("您可以运行 'python scripts/initialize_collections.py' 来创建这些集合")
            else:
                print("\n✅ 所有必需的集合都已存在")
            
        except Exception as e:
            print(f"❌ 获取集合列表失败: {str(e)}")
            
            # 尝试健康检查
            try:
                print("\n尝试健康检查...")
                health = client.health()
                print(f"✅ 健康检查通过: {health}")
            except Exception as e2:
                print(f"❌ 健康检查失败: {str(e2)}")
    
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
    
    print("\n检查完成")

if __name__ == "__main__":
    main() 