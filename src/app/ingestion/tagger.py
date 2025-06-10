# src/app/ingestion/tagger.py

"""
标签管理器：负责知识点的标签管理
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List
from src.infrastructure.config.env_manager import get_config

# 初始化配置
config = get_config()
TAG_DIR: str = config.knowledge.tag_rule_dir


def load_tag_rules() -> dict:
    """加载标签规则"""
    rules_path = Path(TAG_DIR) / "rules.yaml"
    if not rules_path.exists():
        return {}
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_keyword_tags(domain: str) -> dict:
    path = os.path.join(TAG_DIR, f"{domain}.yaml")
    if not os.path.exists(path):
        print(f"⚠️ 标签配置文件未找到: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def auto_tag(text: str, domain: str) -> List[str]:
    keyword_tags = load_keyword_tags(domain)
    tags = set()
    for label, keywords in keyword_tags.items():
        for kw in keywords:
            if re.search(re.escape(kw), text, re.IGNORECASE):
                tags.add(label)
                break
    return list(tags)


if __name__ == "__main__":
    sample = "我现在有工签并且准备申请 express entry，想知道分数线是多少"
    print(auto_tag(sample, domain="immigration"))