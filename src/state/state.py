"""
状态管理 - 定义个人助理的工作状态
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息记录"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """任务项"""
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: int = 3  # 1-5, 1最高
    created_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class MemoryItem(BaseModel):
    """记忆项"""
    id: str
    content: str
    category: str  # "fact", "preference", "event", "task"
    importance: int = 3  # 1-5
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0


class AssistantState(TypedDict):
    """
    个人助理状态
    
    这是 LangGraph 的核心状态定义
    """
    # 会话信息
    session_id: str
    user_id: str
    
    # 消息历史
    messages: Annotated[List[Message], "append"]
    
    # 当前任务
    current_task: Optional[Task]
    task_queue: List[Task]
    completed_tasks: List[Task]
    
    # 检索到的记忆
    retrieved_memories: List[MemoryItem]
    
    # 工具调用
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    # 工作流控制
    next_node: Optional[str]
    iteration_count: int
    should_continue: bool
    error: Optional[str]
    
    # 元数据
    metadata: Dict[str, Any]