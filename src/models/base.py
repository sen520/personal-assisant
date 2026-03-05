"""
数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class IntentType(Enum):
    """意图类型"""
    QUERY = "query"           # 查询
    EXECUTE = "execute"       # 执行
    REMEMBER = "remember"     # 记忆
    RECALL = "recall"         # 回忆
    CHAT = "chat"             # 闲聊
    TASK = "task"             # 任务
    UNKNOWN = "unknown"       # 未知


class UrgencyLevel(Enum):
    """紧急程度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class Message:
    """消息记录"""
    role: str                           # user / assistant / system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Task:
    """任务项"""
    id: str
    description: str
    status: str = "pending"             # pending, in_progress, completed, cancelled
    priority: int = 3                   # 1-5
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_completed(self):
        self.status = "completed"
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    category: str = "general"           # fact, event, preference, task
    importance: int = 3                 # 1-5
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_accessed(self):
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "metadata": self.metadata
        }


@dataclass
class Intent:
    """意图分析结果"""
    type: IntentType
    confidence: float                   # 置信度 0-1
    urgency: UrgencyLevel
    entities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    expected_output: str = ""
    raw_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPlan:
    """工作流计划"""
    steps: List[str]                    # 步骤列表
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    fallback_plan: Optional[str] = None
    estimated_time: int = 0             # 预估时间（秒）


@dataclass  
class ValidationResult:
    """验证结果"""
    is_valid: bool
    completeness_score: float           # 完整性 0-1
    correctness_score: float            # 正确性 0-1
    safety_score: float                 # 安全性 0-1
    quality_score: float                # 总体质量 0-1
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    name: str = ""
    preferred_language: str = "zh"
    communication_style: str = "concise"  # concise, detailed, formal, casual
    tech_background: List[str] = field(default_factory=list)
    common_tasks: List[str] = field(default_factory=list)
    active_hours: List[int] = field(default_factory=list)  # 活跃时段
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "preferred_language": self.preferred_language,
            "communication_style": self.communication_style,
            "tech_background": self.tech_background,
            "common_tasks": self.common_tasks,
            "active_hours": self.active_hours,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }