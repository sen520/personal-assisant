"""
记忆系统 - 统一入口
整合短期记忆、长期记忆、用户画像和约束检查
"""

import logging
from typing import List, Dict, Any, Optional

from .short_term import ShortTermMemory
from .long_term import LongTermMemory, UserProfileManager
from .constraints import ConstraintChecker
from ..models.base import MemoryItem, UserProfile

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    记忆系统统一入口
    
    整合：
    - 短期记忆：当前会话上下文
    - 长期记忆：持久化知识存储
    - 用户画像：用户偏好和背景
    - 约束检查：安全和行为验证
    """
    
    def __init__(
        self,
        vector_db_path: str = "./memory/vector_store.db",
        profile_path: str = "./memory/user_profile.json"
    ):
        """初始化记忆系统"""
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(vector_db_path)
        self.user_profile = UserProfileManager(profile_path)
        self.checker = ConstraintChecker()
        
        logger.info("✅ 记忆系统已初始化")
    
    # ========== 短期记忆操作 ==========
    
    def add_to_conversation(self, role: str, content: str, metadata: Dict = None):
        """
        添加对话消息到短期记忆
        
        Args:
            role: user / assistant / system
            content: 消息内容
            metadata: 额外元数据
        """
        from ..models.base import Message
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.short_term.add_message(message)
        
        # 检查是否需要触发长期记忆存储
        if self.short_term.should_summarize():
            self._consolidate_short_term()
    
    def get_conversation_context(self) -> str:
        """获取当前对话上下文"""
        return self.short_term.get_context()
    
    def get_conversation_messages(self) -> List[Dict]:
        """获取对话消息（供 LLM 使用）"""
        return self.short_term.get_messages_for_llm()
    
    # ========== 长期记忆操作 ==========
    
    def remember(
        self,
        content: str,
        category: str = "general",
        importance: int = 3,
        metadata: Dict = None
    ) -> str:
        """
        存储到长期记忆
        
        Args:
            content: 记忆内容
            category: fact / event / preference / task
            importance: 1-5
            metadata: 额外信息
        
        Returns:
            记忆 ID
        """
        return self.long_term.remember(
            content=content,
            category=category,
            importance=importance,
            metadata=metadata
        )
    
    def recall(
        self,
        query: str,
        top_k: int = 5,
        category: str = None
    ) -> List[MemoryItem]:
        """
        从长期记忆检索
        
        Args:
            query: 查询内容
            top_k: 返回数量
            category: 限制类别
        
        Returns:
            相关记忆列表
        """
        return self.long_term.recall(query, top_k, category)
    
    def get_relevant_memories_for_input(self, user_input: str) -> str:
        """
        根据用户输入获取相关记忆
        
        自动检索相关记忆并格式化为上下文
        """
        memories = self.recall(user_input, top_k=3)
        
        if not memories:
            return ""
        
        parts = ["\n### 相关记忆"]
        for mem in memories:
            parts.append(f"- [{mem.category}] {mem.content}")
        
        return "\n".join(parts)
    
    # ========== 用户画像操作 ==========
    
    def get_user_profile(self) -> UserProfile:
        """获取用户画像"""
        return self.user_profile.get_profile()
    
    def update_user_profile(self, **kwargs):
        """更新用户画像"""
        self.user_profile.update_profile(**kwargs)
    
    def get_user_context_for_prompt(self) -> str:
        """获取用于系统提示的用户上下文"""
        return self.user_profile.get_system_prompt_addition()
    
    # ========== 安全检查 ==========
    
    def validate_output(self, output: str, output_type: str = "text") -> tuple[bool, str]:
        """
        验证输出是否安全
        
        Returns:
            (是否通过, 错误信息)
        """
        passed, checks = self.checker.validate(output, output_type)
        
        if not passed:
            error_msgs = []
            for check in checks:
                if not check.passed:
                    error_msgs.append(f"{check.message}")
                    if check.details:
                        error_msgs.extend([f"  - {d}" for d in check.details])
            
            return False, "\n".join(error_msgs)
        
        return True, ""
    
    # ========== 内部方法 ==========
    
    def _consolidate_short_term(self):
        """整合短期记忆到长期记忆"""
        logger.info("🔄 整合短期记忆到长期记忆...")
        
        # 生成摘要
        summary = self.short_term.generate_summary()
        
        # 存储为事件记忆
        self.long_term.remember(
            content=summary,
            category="event",
            importance=2
        )
        
        # 提取关键事实（简单实现）
        for moment in self.short_term.key_moments:
            self.long_term.remember(
                content=moment.content,
                category="fact",
                importance=4
            )
        
        # 清空短期记忆（保留最近几轮）
        self.short_term.clear()
        
        logger.info("✅ 记忆整合完成")
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        return {
            "short_term": self.short_term.get_stats(),
            "long_term": self.long_term.get_stats(),
            "user_profile": {
                "name": self.user_profile.profile.name,
                "tech_background": self.user_profile.profile.tech_background
            }
        }