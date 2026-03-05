"""
长期记忆管理 - 基于向量存储的持久化记忆
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.base import MemoryItem, UserProfile
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    长期记忆管理器
    
    使用向量数据库存储，支持语义检索
    """
    
    def __init__(self, db_path: str = "./memory/vector_store.db"):
        self.store = VectorStore(db_path)
        logger.info("✅ 长期记忆系统已初始化")
    
    def remember(
        self,
        content: str,
        category: str = "general",
        importance: int = 3,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            category: 类别 (fact, event, preference, task)
            importance: 重要程度 1-5
            metadata: 额外元数据
        
        Returns:
            记忆 ID
        """
        memory_id = self.store.add_memory(
            content=content,
            category=category,
            importance=importance,
            metadata=metadata or {}
        )
        
        logger.info(f"💾 长期记忆已存储 [{category}]: {content[:50]}...")
        return memory_id
    
    def recall(
        self,
        query: str,
        top_k: int = 5,
        category: str = None,
        min_relevance: float = 0.5
    ) -> List[MemoryItem]:
        """
        检索记忆
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            category: 限制类别
            min_relevance: 最小相关度
        
        Returns:
            相关记忆列表
        """
        results = self.store.search_similar(
            query=query,
            top_k=top_k,
            category=category,
            min_similarity=min_relevance
        )
        
        memories = []
        for mem, score in results:
            mem.mark_accessed()
            memories.append(mem)
        
        logger.info(f"🔍 检索到 {len(memories)} 条相关记忆")
        return memories
    
    def forget(self, memory_id: str) -> bool:
        """删除记忆"""
        return self.store.delete_memory(memory_id)
    
    def get_facts_about(self, topic: str) -> List[str]:
        """获取关于某个主题的所有事实"""
        memories = self.recall(
            query=topic,
            category="fact",
            top_k=10
        )
        return [m.content for m in memories]
    
    def get_preferences(self) -> Dict[str, Any]:
        """获取用户偏好"""
        memories = self.store.search_similar(
            query="用户偏好 喜欢 习惯",
            category="preference",
            top_k=20,
            min_similarity=0.3
        )
        
        preferences = {}
        for mem, _ in memories:
            # 简单提取偏好（实际可以用 NLP）
            preferences[mem.id] = mem.content
        
        return preferences
    
    def consolidate_memories(self) -> int:
        """
        记忆整合
        
        合并相似记忆，删除低频访问的低重要性记忆
        
        Returns:
            清理的记忆数量
        """
        # TODO: 实现记忆整合逻辑
        # 1. 找出相似的记忆对
        # 2. 合并它们
        # 3. 删除长期未访问的低重要性记忆
        
        logger.info("🔄 记忆整合完成")
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.store.get_stats()


class UserProfileManager:
    """
    用户画像管理器
    """
    
    def __init__(self, profile_path: str = "./memory/user_profile.json"):
        self.profile_path = profile_path
        self.profile: Optional[UserProfile] = None
        self._load_profile()
    
    def _load_profile(self):
        """从文件加载用户画像"""
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.profile = UserProfile(**data)
            logger.info("✅ 用户画像已加载")
        except FileNotFoundError:
            self.profile = UserProfile(user_id="default_user")
            self._save_profile()
            logger.info("📝 创建默认用户画像")
        except Exception as e:
            logger.error(f"❌ 加载用户画像失败: {e}")
            self.profile = UserProfile(user_id="default_user")
    
    def _save_profile(self):
        """保存用户画像到文件"""
        try:
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.profile.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存用户画像失败: {e}")
    
    def update_profile(self, **kwargs):
        """更新用户画像"""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        
        self.profile.updated_at = datetime.now()
        self._save_profile()
        logger.info(f"✏️  用户画像已更新: {kwargs}")
    
    def get_profile(self) -> UserProfile:
        """获取用户画像"""
        return self.profile
    
    def get_system_prompt_addition(self) -> str:
        """获取用于增强系统提示的用户信息"""
        parts = []
        
        if self.profile.name:
            parts.append(f"用户称呼: {self.profile.name}")
        
        if self.profile.tech_background:
            parts.append(f"技术背景: {', '.join(self.profile.tech_background)}")
        
        if self.profile.communication_style:
            style_map = {
                "concise": "简洁",
                "detailed": "详细",
                "formal": "正式",
                "casual": "随意"
            }
            parts.append(f"沟通风格: {style_map.get(self.profile.communication_style, self.profile.communication_style)}")
        
        return "\n".join(parts) if parts else ""
