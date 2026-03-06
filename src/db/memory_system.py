"""
基于 MySQL 的记忆系统 - 支持多用户数据隔离和向量语义检索
"""

import logging
from typing import List, Dict, Any, Optional

from .models import db_manager
from .repository import MemoryRepository, UserRepository, SessionRepository, TaskRepository
from ..models.base import MemoryItem, UserProfile, Message
from ..utils.vector_store import vector_store

logger = logging.getLogger(__name__)


class MySQLMemorySystem:
    """
    基于 MySQL 的记忆系统
    
    特性：
    - 多用户数据隔离
    - 持久化存储
    - 支持会话、记忆、任务管理
    """
    
    def __init__(self, user_id: str):
        """
        初始化记忆系统
        
        Args:
            user_id: 当前用户 ID
        """
        self.user_id = user_id
        self.session = db_manager.get_session()
        
        # 初始化各仓库
        self.memory_repo = MemoryRepository(self.session)
        self.user_repo = UserRepository(self.session)
        self.session_repo = SessionRepository(self.session)
        self.task_repo = TaskRepository(self.session)
        
        logger.info(f"✅ 记忆系统已初始化 [用户: {user_id}]")
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()
    
    # ========== 会话管理 ==========
    
    def create_session(self, title: str = "新会话") -> str:
        """创建新会话"""
        session = self.session_repo.create(self.user_id, title)
        return session.id
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Message]:
        """获取会话消息"""
        messages = self.session_repo.get_messages(session_id, self.user_id, limit)
        return [
            Message(
                role=m.role,
                content=m.content,
                timestamp=m.created_at,
                metadata=m.metadata or {}
            )
            for m in reversed(messages)  # 按时间正序
        ]
    
    def add_message(self, session_id: str, role: str, content: str, tokens: int = 0) -> str:
        """添加消息到会话"""
        message = self.session_repo.add_message(session_id, self.user_id, role, content, tokens)
        return message.id
    
    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """获取用户的会话列表"""
        sessions = self.session_repo.list_by_user(self.user_id, limit)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            }
            for s in sessions
        ]
    
    # ========== 长期记忆 ==========
    
    def remember(self, content: str, category: str = "general", 
                 importance: int = 3, metadata: Dict = None) -> str:
        """
        存储到长期记忆（MySQL + 向量存储）
        
        Args:
            content: 记忆内容
            category: 类别 (fact, event, preference, task)
            importance: 重要性 1-5
            metadata: 额外元数据
        
        Returns:
            记忆 ID
        """
        # 1. 存储到 MySQL
        memory = self.memory_repo.create(
            user_id=self.user_id,
            content=content,
            category=category,
            importance=importance,
            metadata=metadata or {}
        )
        
        # 2. 存储到向量库（异步语义检索）
        try:
            vector_store.add_memory(
                user_id=self.user_id,
                memory_id=memory.id,
                content=content,
                category=category,
                importance=importance,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"向量存储失败（不影响主流程）: {e}")
        
        logger.info(f"💾 记忆已存储 [{memory.id}]: {content[:50]}...")
        return memory.id
    
    def recall(self, query: str = None, category: str = None, 
               limit: int = 10, semantic: bool = False) -> List[MemoryItem]:
        """
        检索长期记忆
        
        Args:
            query: 查询关键词或语义查询
            category: 类别过滤
            limit: 返回数量
            semantic: 是否使用语义检索（需要 query 参数）
        
        Returns:
            记忆列表
        """
        # 使用语义检索
        if semantic and query:
            return self._semantic_search(query, category, limit)
        
        # 使用数据库检索（关键词匹配）
        memories = self.memory_repo.list_by_user(self.user_id, category, limit)
        
        # 简单的关键词过滤
        if query:
            query_lower = query.lower()
            memories = [m for m in memories if query_lower in m.content.lower()]
        
        return [
            MemoryItem(
                id=m.id,
                content=m.content,
                category=m.category,
                importance=m.importance,
                created_at=m.created_at,
                last_accessed=m.last_accessed,
                access_count=m.access_count,
                metadata=m.metadata or {}
            )
            for m in memories
        ]
    
    def _semantic_search(
        self, 
        query: str, 
        category: Optional[str] = None, 
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        语义搜索记忆
        
        Args:
            query: 语义查询
            category: 类别过滤
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        try:
            results = vector_store.search(
                user_id=self.user_id,
                query=query,
                n_results=limit,
                category=category,
                min_score=0.3  # 最低相似度阈值
            )
            
            # 更新访问统计
            memory_items = []
            for result in results:
                memory_id = result["memory_id"]
                # 从数据库获取完整信息
                db_memory = self.memory_repo.get(memory_id)
                if db_memory:
                    # 更新访问统计
                    self.memory_repo.update_access(memory_id)
                    memory_items.append(
                        MemoryItem(
                            id=db_memory.id,
                            content=db_memory.content,
                            category=db_memory.category,
                            importance=db_memory.importance,
                            created_at=db_memory.created_at,
                            last_accessed=db_memory.last_accessed,
                            access_count=db_memory.access_count,
                            metadata={
                                **(db_memory.metadata or {}),
                                "similarity": result["similarity"]  # 添加相似度分数
                            }
                        )
                    )
            
            logger.info(f"🔍 语义搜索 '{query[:30]}...' 找到 {len(memory_items)} 条结果")
            return memory_items
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            # 降级到普通搜索
            return self.recall(query, category, limit, semantic=False)
    
    def get_relevant_memories_for_input(self, user_input: str) -> str:
        """根据用户输入获取相关记忆，格式化为上下文"""
        memories = self.recall(user_input, limit=5)
        
        if not memories:
            return ""
        
        parts = ["\n### 相关记忆"]
        for mem in memories[:3]:  # 最多 3 条
            parts.append(f"- [{mem.category}] {mem.content}")
            # 更新访问统计
            self.memory_repo.update_access(mem.id, self.user_id)
        
        return "\n".join(parts)
    
    # ========== 任务管理 ==========
    
    def create_task(self, title: str, description: str = "", 
                    priority: int = 3, due_date: Optional[str] = None) -> str:
        """创建任务"""
        from datetime import datetime
        
        due = None
        if due_date:
            try:
                due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        task = self.task_repo.create(
            user_id=self.user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due
        )
        logger.info(f"📋 任务已创建 [{task.id}]: {title}")
        return task.id
    
    def list_tasks(self, status: str = None, limit: int = 100) -> List[Dict]:
        """获取任务列表"""
        tasks = self.task_repo.list_by_user(self.user_id, status, limit)
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat(),
                "due_date": t.due_date.isoformat() if t.due_date else None
            }
            for t in tasks
        ]
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        return self.task_repo.update_status(task_id, self.user_id, "completed")
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return self.task_repo.delete(task_id, self.user_id)
    
    # ========== 用户画像 ==========
    
    def get_user_profile(self) -> UserProfile:
        """获取用户画像"""
        profile = self.user_repo.get_profile(self.user_id)
        if profile:
            return self.user_repo.to_model(profile)
        
        # 返回默认画像
        return UserProfile(user_id=self.user_id)
    
    def update_user_profile(self, **kwargs) -> bool:
        """更新用户画像"""
        return self.user_repo.update_profile(self.user_id, **kwargs)
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        sessions = self.list_sessions(limit=1000)
        memories = self.memory_repo.list_by_user(self.user_id, limit=1000)
        tasks = self.task_repo.list_by_user(self.user_id, limit=1000)
        
        pending_tasks = [t for t in tasks if t.status == "pending"]
        completed_tasks = [t for t in tasks if t.status == "completed"]
        
        return {
            "sessions": len(sessions),
            "memories": len(memories),
            "tasks": {
                "total": len(tasks),
                "pending": len(pending_tasks),
                "completed": len(completed_tasks)
            },
            "user_id": self.user_id
        }


class MemorySystemFactory:
    """记忆系统工厂 - 创建带用户隔离的记忆系统"""
    
    @staticmethod
    def for_user(user_id: str) -> MySQLMemorySystem:
        """为指定用户创建记忆系统"""
        return MySQLMemorySystem(user_id)
    
    @staticmethod
    def init_database():
        """初始化数据库"""
        return db_manager.init_engine()
