"""
用户认证和数据访问层
"""

import uuid
import hashlib
import secrets
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from .models import User, UserProfile, Session as ChatSession, Message, Memory, Task, db_manager
from ..models.base import UserProfile as UserProfileModel


class AuthService:
    """认证服务"""
    
    @staticmethod
    def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """密码哈希"""
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwd_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """验证密码"""
        pwd_hash, _ = AuthService._hash_password(password, salt)
        # 简化处理，实际存储格式需要调整
        return pwd_hash == hashed
    
    @staticmethod
    def create_user(session: Session, username: str, password: str, email: Optional[str] = None) -> User:
        """创建新用户"""
        user_id = str(uuid.uuid4())
        pwd_hash, salt = AuthService._hash_password(password)
        
        # 组合存储: hash:salt
        password_with_salt = f"{pwd_hash}:{salt}"
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_with_salt
        )
        session.add(user)
        
        # 创建默认用户画像
        profile = UserProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=username
        )
        session.add(profile)
        
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def authenticate(session: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = session.query(User).filter(User.username == username, User.is_active == 1).first()
        if not user:
            return None
        
        # 解析存储的密码
        stored = user.password_hash
        if ":" in stored:
            hashed, salt = stored.split(":")
            if AuthService.verify_password(password, hashed, salt):
                return user
        
        return None
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        return session.query(User).filter(User.id == user_id, User.is_active == 1).first()


class UserRepository:
    """用户数据访问"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        return self.session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def update_profile(self, user_id: str, **kwargs) -> bool:
        """更新用户画像"""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.session.commit()
        return True
    
    def to_model(self, profile: UserProfile) -> UserProfileModel:
        """转换为 dataclass 模型"""
        return UserProfileModel(
            user_id=profile.user_id,
            name=profile.name,
            preferred_language=profile.preferred_language,
            communication_style=profile.communication_style,
            tech_background=profile.tech_background or [],
            common_tasks=profile.common_tasks or [],
            active_hours=profile.active_hours or []
        )


class SessionRepository:
    """会话数据访问"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, title: str = "新会话") -> ChatSession:
        """创建新会话"""
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return chat_session
    
    def get_by_id(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """获取会话（带用户权限检查）"""
        return self.session.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
    
    def list_by_user(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        """获取用户的会话列表"""
        return self.session.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.status == "active"
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    def add_message(self, session_id: str, user_id: str, role: str, content: str, tokens: int = 0) -> Message:
        """添加消息"""
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            tokens=tokens
        )
        self.session.add(message)
        
        # 更新会话时间
        chat_session = self.get_by_id(session_id, user_id)
        if chat_session:
            chat_session.updated_at = datetime.now()
        
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def get_messages(self, session_id: str, user_id: str, limit: int = 50) -> List[Message]:
        """获取会话消息"""
        # 先检查权限
        chat_session = self.get_by_id(session_id, user_id)
        if not chat_session:
            return []
        
        return self.session.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(limit).all()


class MemoryRepository:
    """记忆数据访问"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, content: str, category: str = "general", 
               importance: int = 3, embedding_id: str = "", metadata: dict = None) -> Memory:
        """创建记忆"""
        memory = Memory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=content,
            category=category,
            importance=importance,
            embedding_id=embedding_id,
            metadata=metadata or {}
        )
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory
    
    def get_by_id(self, memory_id: str, user_id: str) -> Optional[Memory]:
        """获取记忆（带用户权限检查）"""
        return self.session.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
    
    def list_by_user(self, user_id: str, category: Optional[str] = None, 
                     limit: int = 100) -> List[Memory]:
        """获取用户的记忆列表"""
        query = self.session.query(Memory).filter(Memory.user_id == user_id)
        
        if category:
            query = query.filter(Memory.category == category)
        
        return query.order_by(Memory.created_at.desc()).limit(limit).all()
    
    def update_access(self, memory_id: str, user_id: str):
        """更新访问时间"""
        memory = self.get_by_id(memory_id, user_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.session.commit()
    
    def delete(self, memory_id: str, user_id: str) -> bool:
        """删除记忆"""
        memory = self.get_by_id(memory_id, user_id)
        if memory:
            self.session.delete(memory)
            self.session.commit()
            return True
        return False


class TaskRepository:
    """任务数据访问"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, title: str, description: str = "",
               priority: int = 3, due_date: Optional[datetime] = None,
               tags: List[str] = None) -> Task:
        """创建任务"""
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or []
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def get_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """获取任务"""
        return self.session.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
    
    def list_by_user(self, user_id: str, status: Optional[str] = None,
                     limit: int = 100) -> List[Task]:
        """获取任务列表"""
        query = self.session.query(Task).filter(Task.user_id == user_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.order_by(Task.created_at.desc()).limit(limit).all()
    
    def update_status(self, task_id: str, user_id: str, status: str) -> bool:
        """更新任务状态"""
        task = self.get_by_id(task_id, user_id)
        if not task:
            return False
        
        task.status = status
        if status == "completed":
            task.completed_at = datetime.now()
        
        self.session.commit()
        return True
    
    def delete(self, task_id: str, user_id: str) -> bool:
        """删除任务"""
        task = self.get_by_id(task_id, user_id)
        if task:
            self.session.delete(task)
            self.session.commit()
            return True
        return False
