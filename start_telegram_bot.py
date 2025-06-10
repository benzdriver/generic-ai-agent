#!/usr/bin/env python3
"""
快速启动 Telegram Bot 脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_prerequisites():
    """检查先决条件"""
    print("🔍 检查运行环境...")
    
    # 检查 .env 文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ .env 文件不存在！")
        return False
    
    # 检查配置
    try:
        from src.infrastructure.config.env_manager import get_config
        config = get_config()
        
        # 检查 Telegram Token
        if not config.telegram.token:
            print("❌ TELEGRAM_TOKEN 未配置！")
            return False
        print(f"✅ Telegram Token: {config.telegram.token[:20]}...")
        
        # 检查 OpenAI API Key
        if not config.openai.api_key:
            print("❌ OPENAI_API_KEY 未配置！")
            return False
        print(f"✅ OpenAI API Key: {config.openai.api_key[:20]}...")
        
        # 检查 Qdrant 连接
        print(f"✅ Qdrant URL: {config.qdrant.url}")
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False
    
    return True

def check_qdrant():
    """检查 Qdrant 连接"""
    print("🔍 检查 Qdrant 连接...")
    try:
        from src.infrastructure.vector_store.qdrant import QdrantVectorStore
        vector_store = QdrantVectorStore()
        collections = vector_store.client.get_collections()
        print(f"✅ Qdrant 连接成功，找到 {len(collections.collections)} 个集合")
        return True
    except Exception as e:
        print(f"❌ Qdrant 连接失败: {e}")
        print("💡 请先启动 Qdrant Docker 容器:")
        print("   docker run -d --name qdrant-local -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return False

def start_bot():
    """启动 Bot"""
    print("🚀 启动 Telegram Bot...")
    try:
        from src.main import main
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot 已停止")
    except Exception as e:
        print(f"❌ Bot 启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Generic AI Agent - Telegram Bot 启动器")
    print("=" * 60)
    
    # 检查先决条件
    if not check_prerequisites():
        print("\n❌ 先决条件检查失败，请修复配置后重试")
        sys.exit(1)
    
    # 检查 Qdrant
    if not check_qdrant():
        print("\n❌ Qdrant 服务不可用，请启动后重试")
        sys.exit(1)
    
    print("\n✅ 所有检查通过，启动 Bot...")
    print("💡 按 Ctrl+C 停止 Bot")
    print("-" * 60)
    
    # 启动 Bot
    start_bot()

if __name__ == "__main__":
    main() 