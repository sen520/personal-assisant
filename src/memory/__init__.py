"""
记忆系统 - 整合短期记忆、长期记忆、用户画像和约束检查

使用示例:
    from src.memory import MemorySystem
    
    memory = MemorySystem()
    
    # 存储记忆
    memory.remember("用户喜欢 Python 编程", category="preference")
    
    # 检索记忆
    results = memory.recall("用户喜欢什么编程语言")
    
    # 获取用户画像
    profile = memory.get_user_profile()
"""

from .short_term import ShortTermMemory
from .long_term import LongTermMemory, UserProfileManager
from .constraints import ConstraintChecker, BehaviorGuidelines
from .vector_store import VectorStore, ChromaDBStore
from ..models.base import MemoryItem

__all__ = [
    'MemorySystem',
    'ShortTermMemory',
    'LongTermMemory',
    'UserProfileManager',
    'ConstraintChecker',
    'BehaviorGuidelines',
    'VectorStore',
    'ChromaDBStore',
    'MemoryItem',
]