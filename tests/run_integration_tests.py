#!/usr/bin/env python3
# tests/run_integration_tests.py

"""
运行所有集成测试
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_all_tests():
    """运行所有集成测试"""
    # 查找所有测试文件
    test_dir = Path(__file__).parent / "integration"
    test_files = [f for f in test_dir.glob("test_*.py")]
    
    if not test_files:
        print("⚠️ 未找到测试文件！")
        return
    
    print(f"📋 发现 {len(test_files)} 个测试文件:")
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {file.name}")
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试
    for test_file in test_files:
        # 将文件路径转换为模块名
        module_name = f"tests.integration.{test_file.stem}"
        try:
            # 动态导入测试模块
            test_module = __import__(module_name, fromlist=["*"])
            # 添加模块中的所有测试
            tests = loader.loadTestsFromModule(test_module)
            suite.addTests(tests)
        except Exception as e:
            print(f"⚠️ 加载测试模块 {module_name} 失败: {str(e)}")
    
    # 运行测试
    print("🚀 开始运行集成测试...\n")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试结果摘要
    print("\n📊 测试结果摘要:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 AI移民助手集成测试")
    print("=" * 70)
    
    result = run_all_tests()
    
    # 根据测试结果设置退出码
    if result and (result.failures or result.errors):
        sys.exit(1)
    sys.exit(0) 