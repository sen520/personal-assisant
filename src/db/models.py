"""
数据库模型 - SQLAlchemy ORM 定义
支持多用户数据隔离
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Integer, 
    Float, ForeignKey, JSON, Index, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func

from ..config.settings import settings

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")
    memories = relationship("Memory", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 偏好设置
    name = Column(String(50), default="")
    preferred_language = Column(String(10), default="zh")
    communication_style = Column(String(20), default="concise")  # concise, detailed, formal, casual
    
    # 背景信息
    tech_background = Column(JSON, default=list)
    common_tasks = Column(JSON, default=list)
    active_hours = Column(JSON, default=list)
    
    # 其他偏好
    preferences = Column(JSON, default=dict)  # 灵活存储其他偏好
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    user = relationship("User", back_populates="profile")


class Session(Base):
    """会话表 - 存储对话会话"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 会话信息
    title = Column(String(200), default="新会话")
    status = Column(String(20), default="active")  # active, archived, deleted
    
    # 会话摘要（用于长期记忆）
    summary = Column(Text, default="")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", order_by="Message.created_at")
    
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_status', 'status'),
    )


class Message(Base):
    """消息表 - 存储对话消息"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # 元数据
    tokens = Column(Integer, default=0)
    meta_data = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    session = relationship("Session", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_session_id', 'session_id'),
        Index('idx_message_user_id', 'user_id'),
        Index('idx_message_created_at', 'created_at'),
    )


class Memory(Base):
    """长期记忆表"""
    __tablename__ = "memories"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 记忆内容
    content = Column(Text, nullable=False)
    category = Column(String(20), default="general")  # fact, event, preference, task
    importance = Column(Integer, default=3)  # 1-5
    
    # 向量嵌入（用于语义检索）
    embedding_id = Column(String(100), default="")  # ChromaDB 中的 ID
    
    # 访问统计
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    
    # 元数据
    source_session_id = Column(String(36), nullable=True)
    meta_data = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    user = relationship("User", back_populates="memories")
    
    __table_args__ = (
        Index('idx_memory_user_id', 'user_id'),
        Index('idx_memory_category', 'category'),
        Index('idx_memory_importance', 'importance'),
    )


class TaskStatus(PyEnum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 任务内容
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    
    # 任务状态
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=3)  # 1-5
    
    # 时间安排
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 标签和元数据
    tags = Column(JSON, default=list)
    meta_data = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    user = relationship("User", back_populates="tasks")
    
    __table_args__ = (
        Index('idx_task_user_id', 'user_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        Index('idx_task_due_date', 'due_date'),
    )


class Reminder(Base):
    """提醒表"""
    __tablename__ = "reminders"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 提醒时间
    remind_at = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 重复设置
    is_recurring = Column(Integer, default=0)  # 0=一次性, 1=重复
    recurrence_rule = Column(JSON, default=dict)  # 重复规则: {"type": "daily|weekly|monthly", "interval": 1}
    
    # 状态
    status = Column(String(20), default="pending")  # pending, sent, dismissed, snoozed
    
    # 通知渠道
    notify_channels = Column(JSON, default=list)  # ["in_app", "email", "feishu"]
    
    # 关联任务
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    sent_at = Column(DateTime, nullable=True)
    
    # 关联
    user = relationship("User", back_populates="reminders")
    task = relationship("Task")
    
    __table_args__ = (
        Index('idx_reminder_user_id', 'user_id'),
        Index('idx_reminder_status', 'status'),
        Index('idx_reminder_remind_at', 'remind_at'),
        Index('idx_reminder_user_status_time', 'user_id', 'status', 'remind_at'),
    )


# 添加关系到 User 类
User.reminders = relationship("Reminder", back_populates="user")


class Document(Base):
    """上传文档表 - 知识库"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 文档信息
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # 存储路径
    file_size = Column(Integer, default=0)  # 文件大小（字节）
    file_type = Column(String(50), nullable=False)  # pdf/docx/txt等
    
    # 文档内容
    content = Column(Text, nullable=True)  # 完整文本内容
    chunks_count = Column(Integer, default=0)  # 分块数量
    
    # 状态
    status = Column(String(20), default="processing")  # processing, indexed, error
    error_message = Column(Text, nullable=True)
    
    # 向量化状态
    is_vectorized = Column(Integer, default=0)  # 0=否, 1=是
    vector_collection = Column(String(100), nullable=True)  # 向量集合名称
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_doc_user_id', 'user_id'),
        Index('idx_doc_status', 'status'),
        Index('idx_doc_created', 'created_at'),
    )


class DocumentChunk(Base):
    """文档分块表 - 用于 RAG 检索"""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    
    # 分块内容
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)  # 块序号
    
    # 向量 ID（ChromaDB 中的 ID）
    vector_id = Column(String(100), nullable=True)
    
    # 元数据 (使用 meta_data 避免与 SQLAlchemy 保留字冲突)
    meta_data = Column(JSON, default=dict)  # 页码、段落等信息
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunk_doc_id', 'document_id'),
        Index('idx_chunk_vector_id', 'vector_id'),
    )


# 添加关系到 User 类
User.documents = relationship("Document", back_populates="user")


# ============================================================================
# 数据库连接管理
# ============================================================================

class DatabaseManager:
    """数据库连接管理器"""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_engine(self, database_url: Optional[str] = None):
        """初始化数据库引擎"""
        if database_url is None:
            # 根据配置选择数据库类型
            if getattr(settings, 'use_sqlite', True):
                # SQLite 模式（开发/测试）
                import os
                sqlite_path = getattr(settings, 'sqlite_path', './data/app.db')
                os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
                database_url = f"sqlite:///{sqlite_path}"
            else:
                # MySQL 模式（生产）
                db_user = getattr(settings, 'db_user', 'root')
                db_password = getattr(settings, 'db_password', 'password')
                db_host = getattr(settings, 'db_host', 'localhost')
                db_port = getattr(settings, 'db_port', '3306')
                db_name = getattr(settings, 'db_name', 'personal_assistant')
                database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self._engine = create_engine(
            database_url,
            pool_size=5 if 'mysql' in database_url else 1,
            max_overflow=10 if 'mysql' in database_url else 0,
            pool_recycle=3600,
            echo=settings.debug
        )
        
        self._session_factory = sessionmaker(bind=self._engine)
        
        # 创建表
        Base.metadata.create_all(self._engine)
        
        return self._engine
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if self._session_factory is None:
            self.init_engine()
        return self._session_factory()
    
    def get_engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self.init_engine()
        return self._engine


# 全局数据库管理器实例
db_manager = DatabaseManager()


# ============================================================================
# 便捷函数
# ============================================================================

def get_db():
    """获取数据库会话（生成器模式，用于 FastAPI）"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def init_database(database_url: Optional[str] = None):
    """初始化数据库"""
    return db_manager.init_engine(database_url)
