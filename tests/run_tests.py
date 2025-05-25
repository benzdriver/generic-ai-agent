#!/usr/bin/env python3
# tests/run_tests.py

"""
测试运行脚本：自动加载环境变量并运行测试
"""

import sys
import os
import unittest
from pathlib import Path
import subprocess

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def load_env_from_file():
    """从.env文件加载环境变量"""
    env_path = project_root / '.env'
    local_env_path = project_root / '.env.local'
    
    env_file = local_env_path if local_env_path.exists() else env_path
    
    if not env_file.exists():
        print(f"⚠️ 环境变量文件不存在: {env_file}")
        return False
    
    print(f"📝 从 {env_file} 加载环境变量...")
    
    # 环境变量名称映射，用于处理不一致的命名
    var_mapping = {
        'OPEN_API_KEY': 'OPENAI_API_KEY'  # 将OPEN_API_KEY映射为OPENAI_API_KEY
    }
    
    # 读取环境变量文件
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # 如果值包含引号，去掉引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # 设置环境变量，使用映射后的名称
            env_key = var_mapping.get(key, key)
            os.environ[env_key] = value
            print(f"  设置环境变量: {env_key}=***")
            
            # 如果有映射，同时设置原始名称的环境变量
            if key in var_mapping:
                os.environ[key] = value
                print(f"  同时设置原始环境变量: {key}=***")
    
    return True

def run_specific_test(test_path):
    """运行指定的测试文件"""
    if not Path(test_path).exists():
        print(f"⚠️ 测试文件不存在: {test_path}")
        return False
    
    print(f"🧪 运行测试: {test_path}")
    result = subprocess.run([sys.executable, test_path])
    return result.returncode == 0

def run_all_tests():
    """运行所有集成测试"""
    print("🧪 运行所有集成测试...")
    result = subprocess.run([sys.executable, str(project_root / "tests" / "run_integration_tests.py")])
    return result.returncode == 0

def main():
    """主函数"""
    print("=" * 70)
    print("🧪 AI移民助手测试运行器")
    print("=" * 70)
    
    # 加载环境变量
    if not load_env_from_file():
        print("⚠️ 无法加载环境变量，测试可能会失败")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        success = run_specific_test(test_path)
    else:
        # 显示菜单
        print("\n请选择要运行的测试:")
        print("1. API密钥测试")
        print("2. 单个组件测试")
        print("3. 所有集成测试")
        print("0. 退出")
        
        choice = input("\n请输入选项编号: ")
        
        success = False
        if choice == "1":
            success = run_specific_test(str(project_root / "tests" / "test_api_keys.py"))
        elif choice == "2":
            success = run_specific_test(str(project_root / "tests" / "test_single_component.py"))
        elif choice == "3":
            success = run_all_tests()
        elif choice == "0":
            print("\n👋 测试结束")
            return 0
        else:
            print("\n⚠️ 无效选项")
            return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 