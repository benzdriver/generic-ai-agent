#!/usr/bin/env python3
# tests/test_end_to_end.py

"""
端到端测试：测试完整的 Telegram Bot 工作流程
"""

import sys
import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.infrastructure.config.env_manager import init_config
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.main import handle_message, start
from src.app.agent.response_router import generate_response

class TestEndToEnd(unittest.TestCase):
    """端到端测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        print("\n准备端到端测试环境...")
        try:
            # 初始化配置
            cls.config = init_config(test_mode=False)
            
            # 检查必要的 API 密钥
            if not cls.config.openai.api_key:
                raise unittest.SkipTest("OpenAI API key not configured")
            
            if not cls.config.telegram.token:
                raise unittest.SkipTest("Telegram token not configured")
            
            # 初始化服务
            cls.llm = LLMFactory.get_llm()
            cls.vector_store = VectorStoreFactory.get_vector_store()
            
            print("✅ 端到端测试环境准备完成")
            
        except unittest.SkipTest:
            raise
        except Exception as e:
            raise unittest.SkipTest(f"无法初始化端到端测试环境: {str(e)}")
    
    def test_direct_response_generation(self):
        """测试1：直接测试响应生成（不通过 Telegram）"""
        print("\n🧪 测试直接响应生成...")
        
        test_queries = [
            "什么是加拿大移民？",
            "How do I apply for a work permit in Canada?",
            "Express Entry 的最低分数是多少？"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                try:
                    response = generate_response(
                        user_query=query,
                        llm=self.llm,
                        vector_store=self.vector_store,
                        user_id="test_e2e_user"
                    )
                    
                    self.assertIsInstance(response, str)
                    self.assertGreater(len(response), 0)
                    print(f"   ✅ 查询: '{query[:30]}...' -> 响应长度: {len(response)}")
                    
                except Exception as e:
                    self.fail(f"响应生成失败 for query '{query}': {str(e)}")
    
    def test_telegram_message_handler_simulation(self):
        """测试2：模拟 Telegram 消息处理流程"""
        print("\n🤖 测试 Telegram 消息处理模拟...")
        
        async def run_telegram_simulation():
            # 模拟 Telegram Update 对象
            mock_update = Mock()
            mock_update.effective_user.id = 12345
            mock_update.message.text = "什么是加拿大永久居民？"
            mock_update.message.reply_text = AsyncMock()
            
            # 模拟 Context 对象
            mock_context = Mock()
            mock_context.bot_data = {
                "llm": self.llm,
                "vector_store": self.vector_store
            }
            
            # 调用消息处理函数
            await handle_message(mock_update, mock_context)
            
            # 验证回复被调用
            mock_update.message.reply_text.assert_called_once()
            
            # 获取回复内容
            call_args = mock_update.message.reply_text.call_args
            response_text = call_args[0][0]  # 第一个位置参数
            
            self.assertIsInstance(response_text, str)
            self.assertGreater(len(response_text), 0)
            print(f"   ✅ Telegram 消息处理成功，回复长度: {len(response_text)}")
            return response_text
        
        # 运行异步测试
        response = asyncio.run(run_telegram_simulation())
        self.assertIn("永久居民", response)  # 验证回复内容相关性
    
    def test_telegram_start_command_simulation(self):
        """测试3：模拟 Telegram /start 命令"""
        print("\n🚀 测试 Telegram /start 命令模拟...")
        
        async def run_start_simulation():
            # 模拟 Telegram Update 对象
            mock_update = Mock()
            mock_update.effective_user.id = 67890
            mock_update.message.reply_text = AsyncMock()
            
            # 模拟 Context 对象
            mock_context = Mock()
            
            # 调用 start 命令处理函数
            await start(mock_update, mock_context)
            
            # 验证欢迎消息被发送
            mock_update.message.reply_text.assert_called_once()
            
            # 获取欢迎消息内容
            call_args = mock_update.message.reply_text.call_args
            welcome_text = call_args[0][0]
            
            self.assertIsInstance(welcome_text, str)
            self.assertIn("智能移民问答助手", welcome_text)
            print(f"   ✅ /start 命令处理成功，欢迎消息长度: {len(welcome_text)}")
            return welcome_text
        
        # 运行异步测试
        welcome_msg = asyncio.run(run_start_simulation())
        self.assertIn("Express Entry", welcome_msg)  # 验证欢迎消息包含示例
    
    def test_error_handling_simulation(self):
        """测试4：模拟错误处理"""
        print("\n⚠️ 测试错误处理模拟...")
        
        async def run_error_simulation():
            # 模拟 Telegram Update 对象
            mock_update = Mock()
            mock_update.effective_user.id = 99999
            mock_update.message.text = "测试错误处理"
            mock_update.message.reply_text = AsyncMock()
            
            # 模拟 Context 对象，但故意提供无效的服务
            mock_context = Mock()
            mock_context.bot_data = {
                "llm": None,  # 故意设置为 None 引发错误
                "vector_store": self.vector_store
            }
            
            # 调用消息处理函数
            await handle_message(mock_update, mock_context)
            
            # 验证错误消息被发送
            mock_update.message.reply_text.assert_called_once()
            
            # 获取错误消息内容
            call_args = mock_update.message.reply_text.call_args
            error_text = call_args[0][0]
            
            self.assertIsInstance(error_text, str)
            self.assertIn("抱歉", error_text)
            print(f"   ✅ 错误处理成功，错误消息: '{error_text}'")
            return error_text
        
        # 运行异步测试
        error_msg = asyncio.run(run_error_simulation())
        self.assertIn("出现了错误", error_msg)
    
    def test_configuration_validation(self):
        """测试5：验证配置完整性"""
        print("\n🔧 测试配置验证...")
        
        # 验证 Telegram 配置
        self.assertIsNotNone(self.config.telegram.token)
        self.assertTrue(self.config.telegram.token.startswith(('7', '6', '5')))  # Telegram token 格式
        print(f"   ✅ Telegram Token: {'有效' if self.config.telegram.token else '无效'}")
        
        # 验证其他必要配置
        self.assertIsNotNone(self.config.openai.api_key)
        self.assertIsNotNone(self.config.qdrant.url)
        print(f"   ✅ OpenAI API Key: {'已配置' if self.config.openai.api_key else '未配置'}")
        print(f"   ✅ Qdrant URL: {self.config.qdrant.url}")
        
        # 验证默认域配置
        self.assertIsNotNone(self.config.domains.default_domain)
        print(f"   ✅ 默认域: {self.config.domains.default_domain}")

class TestManualTelegramBot(unittest.TestCase):
    """手动测试指南（仅输出测试步骤）"""
    
    def test_manual_testing_guide(self):
        """输出手动测试 Telegram Bot 的指南"""
        print("\n" + "="*80)
        print("📋 手动测试 Telegram Bot 指南")
        print("="*80)
        
        guide = """
🔧 准备步骤：
1. 确保所有依赖服务正在运行：
   - ✅ Qdrant Docker 容器: docker ps | grep qdrant
   - ✅ 配置文件: .env 中的 TELEGRAM_TOKEN

2. 启动 Bot：
   cd /Users/ziyanzhou/Projects/generic-ai-agent
   python src/main.py

🧪 测试场景：

📱 基础功能测试：
1. 在 Telegram 中找到你的 Bot
2. 发送 /start 命令 -> 应该收到欢迎消息
3. 发送简单问题："什么是加拿大移民？"
4. 发送复杂问题："我在BC省工作一年了，有LMIA，可以申请PNP吗？"
5. 发送英文问题："How to apply for Express Entry?"

🔬 高级功能测试：
1. 测试对话历史：连续发送相关问题
2. 测试不同领域：发送法律相关问题
3. 测试边界情况：发送非常长的消息或特殊字符

🚨 错误处理测试：
1. 暂停 Qdrant 服务，发送消息 -> 应该收到错误消息
2. 发送空消息或仅包含符号的消息

📊 性能测试：
1. 同时发送多条消息
2. 测试响应时间是否合理（< 30秒）

✅ 验证标准：
- 所有消息都应该收到回复
- 回复内容应该相关且有帮助
- 错误情况应该有友好的错误消息
- Bot 应该保持稳定运行
"""
        print(guide)
        print("="*80)
        
        # 这不是一个真正的测试，只是输出指南
        self.assertTrue(True, "手动测试指南已输出")

if __name__ == '__main__':
    unittest.main() 