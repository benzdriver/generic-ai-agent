"""
LLM工厂：负责创建和管理不同的LLM实现
"""

from typing import Dict, Type, Optional, List, Any
from .base import BaseLLM
from .openai_llm import OpenAILLM
from .anthropic_llm import AnthropicLLM

class LLMFactory:
    """LLM工厂类，支持垂直领域定制"""
    
    _instances: Dict[str, BaseLLM] = {}
    _implementations = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
    }
    

    
    @classmethod
    def get_llm(cls, provider: str = "openai", fallback_providers: Optional[List[str]] = None, **kwargs) -> BaseLLM:
        """获取LLM实例
        
        Args:
            provider: 首选LLM提供商名称
            fallback_providers: 备选LLM提供商列表，按优先级排序
            **kwargs: 其他参数，将传递给LLM实例
            
        Returns:
            BaseLLM: LLM实例
            
        Raises:
            ValueError: 当所有提供商都不可用时抛出
        """
        # 设置默认的 fallback
        if fallback_providers is None:
            fallback_providers = ["anthropic"]
        
        # 尝试首选提供商
        try:
            if provider not in cls._instances:
                if provider not in cls._implementations:
                    raise ValueError(f"不支持的LLM提供商：{provider}")
                cls._instances[provider] = cls._implementations[provider](**kwargs)
            return cls._instances[provider]
        except Exception as e:
            print(f"⚠️ 主要提供商 {provider} 初始化失败: {str(e)}")
        
        # 尝试 fallback 提供商
        for fallback in fallback_providers:
            try:
                if fallback not in cls._instances:
                    if fallback not in cls._implementations:
                        continue
                    cls._instances[fallback] = cls._implementations[fallback](**kwargs)
                print(f"✅ 使用备选提供商：{fallback}")
                return cls._instances[fallback]
            except Exception as e:
                print(f"⚠️ 备选提供商 {fallback} 初始化失败: {str(e)}")
        
        raise ValueError("所有LLM提供商都不可用")

class FallbackLLM(BaseLLM):
    """带有自动fallback功能的LLM封装类"""
    
    def __init__(self, primary_provider: str = "openai", fallback_providers: Optional[List[str]] = None, **kwargs):
        self.primary = primary_provider
        self.fallbacks = fallback_providers or ["anthropic"]
        self.kwargs = kwargs
    
    def _execute_with_fallback(self, method_name: str, *args, **kwargs) -> str:
        """执行LLM方法，失败时自动尝试fallback"""
        providers = [self.primary] + self.fallbacks
        last_error = None
        
        # 合并实例参数和方法调用参数
        merged_kwargs = self.kwargs.copy()
        merged_kwargs.update(kwargs)
        
        for provider in providers:
            try:
                llm = LLMFactory.get_llm(provider, **merged_kwargs)
                method = getattr(llm, method_name)
                return method(*args, **merged_kwargs)
            except Exception as e:
                last_error = e
                print(f"⚠️ {provider} {method_name} 失败: {str(e)}")
        
        raise last_error or ValueError("所有LLM提供商都失败了")
    
    def generate(self, prompt: str, **kwargs) -> str:
        return self._execute_with_fallback("generate", prompt, **kwargs)
    
    def generate_with_chunks(self, chunks: List[str], **kwargs) -> str:
        return self._execute_with_fallback("generate_with_chunks", chunks, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return self._execute_with_fallback("chat", messages, **kwargs)