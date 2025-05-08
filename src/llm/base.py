"""
LLM基础接口：定义所有LLM模型需要实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union

class BaseLLM(ABC):
    """LLM基础接口类"""
    
    def should_use_chunks(self, text: Union[str, List[str]]) -> bool:
        """判断是否应该使用分块处理
        
        Args:
            text: 输入文本或文本列表
            
        Returns:
            bool: 是否应该使用分块处理
        """
        if isinstance(text, list):
            # 如果是列表，判断总长度
            total_length = sum(len(t) for t in text)
            return total_length > 2000 or len(text) > 3
        else:
            # 单个文本，判断长度
            return len(text) > 2000
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成回答"""
        pass
    
    @abstractmethod
    def generate_with_chunks(self, chunks: List[str], **kwargs) -> str:
        """处理大型输入，分块生成回答"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话模式"""
        pass 