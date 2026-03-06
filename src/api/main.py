"""
FastAPI 应用 - RESTful API 接口层
"""

from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

from ..config.settings import settings
from ..db.models import db_manager
from ..db.repository import AuthService
from ..db.memory_system import MemorySystemFactory


# ============================================================================
# JWT 配置
# ============================================================================

# 从环境变量获取密钥，如果没有则使用默认（生产环境必须设置）
JWT_SECRET_KEY = getattr(settings, 'jwt_secret_key', 'your-secret-key-here-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7


# ============================================================================
# 认证相关
# ============================================================================

security = HTTPBearer()


def create_access_token(user_id: str) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        user_id: 用户 ID
    
    Returns:
        JWT Token
    """
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return f"Bearer {token}"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    验证 JWT 令牌并返回用户 ID
    
    Args:
        credentials: HTTP 认证凭证
    
    Returns:
        用户 ID
    
    Raises:
        HTTPException: 令牌无效或过期
    """
    token = credentials.credentials
    
    # 移除 Bearer 前缀
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Pydantic 模型
# ============================================================================

class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class MessageCreate(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    role: str
    content: str
    created_at: str


class SessionCreate(BaseModel):
    """创建会话请求"""
    title: str = "新会话"


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    title: str
    created_at: str
    updated_at: str


class MemoryCreate(BaseModel):
    """创建记忆请求"""
    content: str = Field(..., min_length=1)
    category: str = "general"
    importance: int = Field(3, ge=1, le=5)


class MemoryResponse(BaseModel):
    """记忆响应"""
    id: str
    content: str
    category: str
    importance: int
    created_at: str


class TaskCreate(BaseModel):
    """创建任务请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    priority: int = Field(3, ge=1, le=5)


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    title: str
    description: str
    status: str
    priority: int
    created_at: str


class ChatResponse(BaseModel):
    """聊天响应"""
    user_message: MessageResponse
    assistant_message: MessageResponse
    session_id: str


# ============================================================================
# FastAPI 应用
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    db_manager.init_engine()
    yield
    # 关闭时清理


app = FastAPI(
    title="Personal Assistant API",
    description="智能个人助理 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 静态文件服务
# ============================================================================

@app.get("/")
def root():
    """根路径 - 返回前端页面"""
    return FileResponse("static/index.html")


# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# 认证接口
# ============================================================================

@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserCreate):
    """用户注册"""
    from sqlalchemy.orm import Session as SQLSession
    from ..db.models import User
    
    session = db_manager.get_session()
    try:
        # 检查用户是否存在
        existing = session.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # 创建用户
        user = AuthService.create_user(
            session,
            username=user_data.username,
            password=user_data.password,
            email=user_data.email
        )
        
        token = create_access_token(user.id)
        
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username
        )
    finally:
        session.close()


@app.post("/api/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin):
    """用户登录"""
    session = db_manager.get_session()
    try:
        user = AuthService.authenticate(
            session,
            username=user_data.username,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        token = create_access_token(user.id)
        
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username
        )
    finally:
        session.close()


# ============================================================================
# 会话接口
# ============================================================================

@app.post("/api/sessions", response_model=SessionResponse)
def create_session(session_data: SessionCreate, user_id: str = Depends(verify_token)):
    """创建新会话"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        session_id = memory.create_session(session_data.title)
        # 获取会话信息
        sessions = memory.list_sessions(limit=1)
        if sessions:
            s = sessions[0]
            return SessionResponse(
                id=session_id,
                title=session_data.title,
                created_at=s["created_at"],
                updated_at=s["updated_at"]
            )
        raise HTTPException(status_code=500, detail="Failed to create session")
    finally:
        memory.close()


@app.get("/api/sessions")
def list_sessions(user_id: str = Depends(verify_token), limit: int = 20):
    """获取会话列表"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        sessions = memory.list_sessions(limit=limit)
        return {"sessions": sessions, "total": len(sessions)}
    finally:
        memory.close()


# ============================================================================
# 聊天接口
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
def chat(message_data: MessageCreate, user_id: str = Depends(verify_token)):
    """
    发送消息并获取回复
    """
    from ..graph.workflow_db import build_app
    from ..state.state import AssistantState, Message
    import uuid
    
    memory = MemorySystemFactory.for_user(user_id)
    
    try:
        # 获取或创建会话
        session_id = message_data.session_id
        if not session_id:
            session_id = memory.create_session()
        
        # 保存用户消息
        user_msg_id = memory.add_message(session_id, "user", message_data.content)
        
        # 运行工作流
        app = build_app()
        state = AssistantState(
            session_id=session_id,
            user_id=user_id,
            messages=[Message(role="user", content=message_data.content)],
            should_continue=True
        )
        
        result = app.invoke(state, config={"configurable": {"thread_id": session_id}})
        
        # 获取助手回复
        assistant_msgs = [m for m in result.get("messages", []) if m.role == "assistant"]
        if assistant_msgs:
            assistant_content = assistant_msgs[-1].content
            # 保存助手消息
            assistant_msg_id = memory.add_message(session_id, "assistant", assistant_content)
        else:
            assistant_content = "抱歉，我无法处理这个请求。"
            assistant_msg_id = memory.add_message(session_id, "assistant", assistant_content)
        
        return ChatResponse(
            user_message=MessageResponse(
                id=user_msg_id,
                role="user",
                content=message_data.content,
                created_at=datetime.now().isoformat()
            ),
            assistant_message=MessageResponse(
                id=assistant_msg_id,
                role="assistant",
                content=assistant_content,
                created_at=datetime.now().isoformat()
            ),
            session_id=session_id
        )
        
    finally:
        memory.close()


@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str, user_id: str = Depends(verify_token), limit: int = 50):
    """获取会话消息"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        messages = memory.get_session_messages(session_id, limit=limit)
        return {
            "messages": [
                MessageResponse(
                    id=str(i),
                    role=m.role,
                    content=m.content,
                    created_at=m.timestamp.isoformat()
                )
                for i, m in enumerate(messages)
            ]
        }
    finally:
        memory.close()


# ============================================================================
# 记忆接口
# ============================================================================

@app.post("/api/memories", response_model=MemoryResponse)
def create_memory(memory_data: MemoryCreate, user_id: str = Depends(verify_token)):
    """创建记忆"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        memory_id = memory.remember(
            content=memory_data.content,
            category=memory_data.category,
            importance=memory_data.importance
        )
        
        return MemoryResponse(
            id=memory_id,
            content=memory_data.content,
            category=memory_data.category,
            importance=memory_data.importance,
            created_at=datetime.now().isoformat()
        )
    finally:
        memory.close()


@app.get("/api/memories")
def list_memories(
    user_id: str = Depends(verify_token),
    category: Optional[str] = None,
    limit: int = 100
):
    """获取记忆列表"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        memories = memory.recall(category=category, limit=limit)
        return {
            "memories": [
                MemoryResponse(
                    id=m.id,
                    content=m.content,
                    category=m.category,
                    importance=m.importance,
                    created_at=m.created_at.isoformat()
                )
                for m in memories
            ],
            "total": len(memories)
        }
    finally:
        memory.close()


@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: str, user_id: str = Depends(verify_token)):
    """删除记忆"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        success = memory.memory_repo.delete(memory_id, user_id)
        if success:
            return {"success": True, "message": "Memory deleted"}
        raise HTTPException(status_code=404, detail="Memory not found")
    finally:
        memory.close()


# ============================================================================
# 任务接口
# ============================================================================

@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task_data: TaskCreate, user_id: str = Depends(verify_token)):
    """创建任务"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        task_id = memory.create_task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority
        )
        
        return TaskResponse(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            status="pending",
            priority=task_data.priority,
            created_at=datetime.now().isoformat()
        )
    finally:
        memory.close()


@app.get("/api/tasks")
def list_tasks(
    user_id: str = Depends(verify_token),
    status: Optional[str] = None,
    limit: int = 100
):
    """获取任务列表"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        tasks = memory.list_tasks(status=status, limit=limit)
        return {
            "tasks": [
                TaskResponse(
                    id=t["id"],
                    title=t["title"],
                    description=t.get("description", ""),
                    status=t["status"],
                    priority=t["priority"],
                    created_at=t["created_at"]
                )
                for t in tasks
            ],
            "total": len(tasks)
        }
    finally:
        memory.close()


@app.patch("/api/tasks/{task_id}")
def update_task_status(task_id: str, status: str, user_id: str = Depends(verify_token)):
    """更新任务状态"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        success = memory.complete_task(task_id) if status == "completed" else False
        if success:
            return {"success": True, "message": "Task updated"}
        raise HTTPException(status_code=404, detail="Task not found")
    finally:
        memory.close()


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(verify_token)):
    """删除任务"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        success = memory.delete_task(task_id)
        if success:
            return {"success": True, "message": "Task deleted"}
        raise HTTPException(status_code=404, detail="Task not found")
    finally:
        memory.close()


# ============================================================================
# 统计接口
# ============================================================================

@app.get("/api/stats")
def get_stats(user_id: str = Depends(verify_token)):
    """获取用户统计"""
    memory = MemorySystemFactory.for_user(user_id)
    try:
        stats = memory.get_stats()
        return stats
    finally:
        memory.close()


# ============================================================================
# 健康检查
# ============================================================================

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ============================================================================
# 启动入口
# ============================================================================

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """启动服务器"""
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
