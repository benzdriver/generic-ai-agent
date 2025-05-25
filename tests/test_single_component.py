#!/usr/bin/env python3
# tests/test_single_component.py

"""
单个组件测试脚本：用于快速测试单个组件的功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.config.env_manager import init_config
from src.config.domain_manager import domain_manager
from src.llm.factory import LLMFactory
from src.vector_engine.embedding_router import get_embedding
from src.agent_core.response_router import generate_response

def test_llm():
    """测试LLM生成功能"""
    print("\n🧪 测试LLM生成功能")
    llm = LLMFactory.get_llm()
    
    prompt = input("\n请输入测试提示词 (或按回车使用默认提示词): ")
    if not prompt:
        prompt = "请用一句话回答：加拿大有多少个省？"
    
    print(f"\n提示词: {prompt}")
    print("\n生成中...")
    
    response = llm.generate(prompt)
    print(f"\n回答: {response}")

def test_embedding():
    """测试嵌入向量生成"""
    print("\n🧪 测试嵌入向量生成")
    
    text = input("\n请输入测试文本 (或按回车使用默认文本): ")
    if not text:
        text = "这是一个测试文本，用于生成嵌入向量"
    
    print(f"\n文本: {text}")
    print("\n生成嵌入向量中...")
    
    embedding = get_embedding(text)
    print(f"\n向量维度: {len(embedding)}")
    print(f"向量前5个元素: {embedding[:5]}")

def test_domain_config():
    """测试领域配置"""
    print("\n🧪 测试领域配置")
    
    domains = domain_manager.list_domains()
    print(f"\n可用领域: {domains}")
    
    if domains:
        domain = input(f"\n请选择要查看的领域 (或按回车使用第一个领域): ")
        if not domain or domain not in domains:
            domain = domains[0]
        
        config = domain_manager.get_domain_config(domain)
        print(f"\n领域 '{domain}' 配置:")
        for key, value in config.items():
            if key != "prompt_template":  # 提示词模板可能很长，只打印前100个字符
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value[:100]}...")

def test_response_generation():
    """测试回答生成"""
    print("\n🧪 测试回答生成")
    
    domains = domain_manager.list_domains()
    print(f"\n可用领域: {domains}")
    
    domain = input(f"\n请选择要使用的领域 (或按回车使用默认领域): ")
    if domain and domain not in domains:
        print(f"⚠️ 领域 '{domain}' 不存在，使用默认领域")
        domain = None
    
    query = input("\n请输入测试问题 (或按回车使用默认问题): ")
    if not query:
        query = "在加拿大，Express Entry最低分数线是多少？"
    
    print(f"\n问题: {query}")
    print(f"使用领域: {domain or '默认'}")
    print("\n生成回答中...")
    
    response = generate_response(query, domain=domain)
    print(f"\n回答: {response}")

def main():
    """主函数"""
    print("=" * 70)
    print("🧪 AI移民助手组件测试")
    print("=" * 70)
    
    # 初始化配置，使用真实API
    init_config(test_mode=False)
    
    while True:
        print("\n请选择要测试的组件:")
        print("1. LLM生成功能")
        print("2. 嵌入向量生成")
        print("3. 领域配置")
        print("4. 回答生成")
        print("0. 退出")
        
        choice = input("\n请输入选项编号: ")
        
        if choice == "1":
            test_llm()
        elif choice == "2":
            test_embedding()
        elif choice == "3":
            test_domain_config()
        elif choice == "4":
            test_response_generation()
        elif choice == "0":
            print("\n👋 测试结束")
            break
        else:
            print("\n⚠️ 无效选项，请重新选择")
        
        input("\n按回车继续...")

if __name__ == "__main__":
    main() 