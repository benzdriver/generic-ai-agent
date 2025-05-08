"""
OpenAI LLM实现：使用OpenAI的模型
"""

import openai
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from .base import BaseLLM
from config.env_manager import init_config

class OpenAILLM(BaseLLM):
    """OpenAI LLM实现类"""
    
    def __init__(self):
        config = init_config()
        openai.api_key = config['openai']['api_key']
        self.model_name = config['openai']['model']
        self.chat_model = ChatOpenAI(
            model_name=self.model_name,
            temperature=0.7,
            openai_api_key=openai.api_key
        )
        
        # 文本分割器，用于处理大型输入
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len
        )
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """生成回答"""
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def generate_with_chunks(self, chunks: List[str], **kwargs) -> str:
        """处理大型输入，分块生成回答
        
        使用 LangChain 处理大型输入：
        1. 将输入分成多个块
        2. 对每个块生成中间总结
        3. 最后合并所有总结
        """
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
        with get_openai_callback() as cb:
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
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content 