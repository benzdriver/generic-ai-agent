"""
Anthropic LLM实现：使用Anthropic的Claude模型
"""

import anthropic
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatAnthropic
from .base import BaseLLM
from config.env_manager import init_config

class AnthropicLLM(BaseLLM):
    """Anthropic LLM实现类"""
    
    def __init__(self):
        config = init_config()
        self.client = anthropic.Anthropic(
            api_key=config['anthropic']['api_key']
        )
        # 从环境变量获取模型名称，默认使用 claude-3-opus-20240229
        self.model_name = config['anthropic'].get('model', 'claude-3-opus-20240229')
        self.chat_model = ChatAnthropic(
            model_name=self.model_name,
            temperature=0.7,
            anthropic_api_key=config['anthropic']['api_key']
        )
        
        # 文本分割器，用于处理大型输入
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len
        )
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """生成回答"""
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def generate_with_chunks(self, chunks: List[str], **kwargs) -> str:
        """处理大型输入，分块生成回答"""
        # 创建总结链
        summary_prompt = PromptTemplate(
            input_variables=["text"],
            template="请总结以下内容的要点：\n\n{text}"
        )
        summary_chain = LLMChain(
            llm=self.chat_model,
            prompt=summary_prompt
        )
        
        # 对每个块生成总结
        summaries = []
        for chunk in chunks:
            summary = summary_chain.run(text=chunk)
            summaries.append(summary)
        
        # 合并所有总结
        merge_prompt = PromptTemplate(
            input_variables=["summaries"],
            template="请将以下几个要点合并成一个连贯的总结：\n\n{summaries}"
        )
        merge_chain = LLMChain(
            llm=self.chat_model,
            prompt=merge_prompt
        )
        
        final_summary = merge_chain.run(summaries="\n\n".join(summaries))
        return final_summary
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """对话模式"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=temperature,
            messages=messages
        )
        return response.content[0].text 