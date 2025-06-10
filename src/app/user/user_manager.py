"""
用户管理模块
功能：存储和管理用户基本信息，提供个性化服务
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

from src.infrastructure.vector_store.base import BaseVectorStore
from src.infrastructure.vector_store.qdrant import QdrantVectorStore
from src.infrastructure.vector_store.embedding_router import get_embedding

@dataclass
class UserProfile:
    """用户档案数据结构"""
    user_id: str
    platform: str  # telegram, web, etc.
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_preference: str = "zh"  # zh, en
    country_of_interest: Optional[str] = "Canada"  # 主要关注的国家
    immigration_category: Optional[str] = None  # 移民类别偏好
    consultation_count: int = 0
    first_interaction: Optional[str] = None
    last_interaction: Optional[str] = None
    notes: List[str] = None  # 用户备注信息
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.first_interaction is None:
            self.first_interaction = datetime.now(timezone.utc).isoformat()

class UserManager:
    """用户信息管理器"""
    
    USER_COLLECTION = "user_profiles"
    
    def __init__(self, vector_store: BaseVectorStore):
        self.vector_store = vector_store
        
    def create_user_profile(self, user_id: str, platform: str = "telegram", 
                          **kwargs) -> UserProfile:
        """创建新用户档案"""
        profile = UserProfile(
            user_id=user_id,
            platform=platform,
            **kwargs
        )
        
        # 存储到向量数据库
        self._save_profile(profile)
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户档案"""
        try:
            # 从向量数据库检索
            results = self.vector_store.search(
                collection_name=self.USER_COLLECTION,
                query_vector=get_embedding(f"user_profile_{user_id}"),
                limit=1,
                score_threshold=0.9
            )
            
            if results and len(results) > 0:
                payload = results[0].payload
                return UserProfile(**payload)
                
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            
        return None
    
    def update_user_profile(self, user_id: str, **updates) -> Optional[UserProfile]:
        """更新用户档案"""
        profile = self.get_user_profile(user_id)
        
        if not profile:
            # 如果用户不存在，创建新档案
            profile = self.create_user_profile(user_id, **updates)
        else:
            # 更新现有档案
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.last_interaction = datetime.now(timezone.utc).isoformat()
            profile.consultation_count += 1
            
            self._save_profile(profile)
        
        return profile
    
    def add_user_note(self, user_id: str, note: str) -> bool:
        """为用户添加备注"""
        profile = self.get_user_profile(user_id)
        
        if profile:
            profile.notes.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": note
            })
            self._save_profile(profile)
            return True
        
        return False
    
    def get_user_summary(self, user_id: str) -> str:
        """获取用户摘要信息"""
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return "新用户"
        
        summary_parts = []
        
        # 基本信息
        if profile.first_name:
            summary_parts.append(f"姓名: {profile.first_name}")
        
        # 偏好信息
        if profile.country_of_interest:
            summary_parts.append(f"关注国家: {profile.country_of_interest}")
        
        if profile.immigration_category:
            summary_parts.append(f"移民类别: {profile.immigration_category}")
        
        # 互动统计
        summary_parts.append(f"咨询次数: {profile.consultation_count}")
        
        # 语言偏好
        lang_display = "中文" if profile.language_preference == "zh" else "English"
        summary_parts.append(f"语言偏好: {lang_display}")
        
        return " | ".join(summary_parts)
    
    def _save_profile(self, profile: UserProfile):
        """保存用户档案到向量数据库"""
        try:
            point = {
                "id": str(uuid.uuid4()),
                "vector": get_embedding(f"user_profile_{profile.user_id}"),
                "payload": asdict(profile)
            }
            
            # 先删除现有记录（如果存在）
            self._delete_existing_profile(profile.user_id)
            
            # 插入新记录
            self.vector_store.upsert(
                collection_name=self.USER_COLLECTION,
                points=[point]
            )
            
        except Exception as e:
            print(f"Error saving user profile: {e}")
    
    def _delete_existing_profile(self, user_id: str):
        """删除现有的用户档案（用于更新）"""
        try:
            # 简单实现：由于Qdrant的限制，这里先跳过删除
            # 在实际应用中，可以使用point ID管理来实现精确删除
            pass
        except Exception as e:
            print(f"Error deleting existing profile: {e}")

# 全局用户管理器实例
_user_manager = None

def get_user_manager(vector_store: BaseVectorStore) -> UserManager:
    """获取用户管理器实例"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager(vector_store)
    return _user_manager 