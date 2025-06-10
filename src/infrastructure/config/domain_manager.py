# src/infrastructure/config/domain_manager.py

"""
模块名称：domain_manager.py
领域配置管理器：负责管理不同垂直领域的配置信息
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from .env_manager import get_config

class DomainManager:
    """领域配置管理器类"""
    
    _instance = None
    _domains: Dict[str, Dict[str, Any]] = {}
    _domain_paths: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DomainManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_domains()
    
    def _load_domains(self):
        """加载所有领域配置"""
        config = get_config()
        
        # 获取领域配置目录
        domain_dir = config.domains.config_dir
        domain_path = Path(domain_dir)
        
        if not domain_path.exists():
            print(f"⚠️ 领域配置目录不存在: {domain_path}")
            return
        
        # 加载所有领域配置文件
        for domain_file in domain_path.glob('*.yaml'):
            domain_name = domain_file.stem
            try:
                with open(domain_file, 'r', encoding='utf-8') as f:
                    domain_config = yaml.safe_load(f)
                    self._domains[domain_name] = domain_config
                    self._domain_paths[domain_name] = str(domain_file)
                    print(f"✅ 已加载领域配置: {domain_name}")
            except Exception as e:
                print(f"⚠️ 加载领域配置失败 {domain_name}: {str(e)}")
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """获取领域配置
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, Any]: 领域配置信息
        """
        return self._domains.get(domain, {})
    
    def get_domain_llm_config(self, domain: str) -> Dict[str, Any]:
        """获取领域LLM配置
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, Any]: 领域LLM配置信息
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get('llm', {})
    
    def get_domain_prompt_template(self, domain: str) -> Optional[str]:
        """获取领域提示词模板
        
        Args:
            domain: 领域名称
            
        Returns:
            Optional[str]: 领域提示词模板
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get('prompt_template')
    
    def get_domain_collection(self, domain: str) -> Optional[str]:
        """获取领域向量集合名称
        
        Args:
            domain: 领域名称
            
        Returns:
            Optional[str]: 领域向量集合名称
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get('vector_collection')
    
    def get_domain_tags(self, domain: str) -> List[str]:
        """获取领域标签列表
        
        Args:
            domain: 领域名称
            
        Returns:
            List[str]: 领域标签列表
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get('tags', [])
    
    def get_domain_evaluation_metrics(self, domain: str) -> Dict[str, Any]:
        """获取领域评估指标
        
        Args:
            domain: 领域名称
            
        Returns:
            Dict[str, Any]: 领域评估指标
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get('evaluation_metrics', {})
    
    def register_domain(self, domain: str, config: Dict[str, Any], save: bool = True) -> None:
        """注册新的领域配置
        
        Args:
            domain: 领域名称
            config: 领域配置信息
            save: 是否保存到文件
        """
        self._domains[domain] = config
        
        if save:
            system_config = get_config()
            domain_dir = system_config.domains.config_dir
            
            # 确保目录存在
            os.makedirs(domain_dir, exist_ok=True)
            
            # 保存配置文件
            domain_file = os.path.join(domain_dir, f"{domain}.yaml")
            with open(domain_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            self._domain_paths[domain] = domain_file
            print(f"✅ 已注册并保存领域配置: {domain}")
        else:
            print(f"✅ 已注册领域配置(内存): {domain}")
    
    def list_domains(self) -> List[str]:
        """列出所有已注册的领域
        
        Returns:
            List[str]: 领域名称列表
        """
        return list(self._domains.keys())

# 单例实例
domain_manager = DomainManager()

def get_domain_manager() -> DomainManager:
    """
    Get the domain manager singleton instance.
    
    Returns:
        DomainManager: The domain manager instance
    """
    return domain_manager

# 示例领域配置结构
DOMAIN_CONFIG_EXAMPLE = {
    "name": "legal",  # 领域名称
    "description": "法律咨询领域",  # 领域描述
    "llm": {  # LLM相关配置
        "preferred_provider": "openai",  # 首选LLM提供商
        "model_params": {  # 模型参数
            "temperature": 0.2,
            "top_p": 0.9
        }
    },
    "prompt_template": """  # 提示词模板
你是一名专业的法律顾问助手，请根据以下相关法律资料回答用户的问题。

【相关法律资料】
{context}

【用户提问】
{query}

请用准确、专业的法律术语回答，引用相关法条。如果信息不足以提供法律建议，请明确说明并建议咨询专业律师。
""",
    "vector_collection": "legal_docs",  # 向量集合名称
    "tags": ["合同", "诉讼", "法规", "知识产权"],  # 领域标签
    "evaluation_metrics": {  # 评估指标
        "accuracy": 0.9,  # 准确率权重
        "citation": 0.8,  # 引用率权重
        "completeness": 0.7  # 完整性权重
    }
}