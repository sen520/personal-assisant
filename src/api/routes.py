"""
API 路由 - 使用上下文管理器重构版本
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLSession

from ..db.connection import get_db_session, get_memory_context
from ..db.repository import AuthService
from ..db.models import User

router = APIRouter(prefix="/api")


# ============================================================================
# 认证接口
# ============================================================================

@router.post("/auth/register")
def register(user_data: UserCreate):
    """用户注册"""
    try:
        with get_db_session() as session:
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
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.id,
                "username": user.username
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/auth/login")
def login(user_data: UserLogin):
    """用户登录"""
    try:
        with get_db_session() as session:
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
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.id,
                "username": user.username
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ============================================================================
# 会话接口
# ============================================================================

@router.post("/sessions")
def create_session(session_data: SessionCreate, user_id: str = Depends(verify_token)):
    """创建新会话"""
    try:
        with get_memory_context(user_id) as memory:
            session_id = memory.create_session(session_data.title)
            sessions = memory.list_sessions(limit=1)
            
            if sessions:
                s = sessions[0]
                return {
                    "id": session_id,
                    "title": session_data.title,
                    "created_at": s["created_at"],
                    "updated_at": s["updated_at"]
                }
            raise HTTPException(status_code=500, detail="Failed to create session")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions")
def list_sessions(user_id: str = Depends(verify_token), limit: int = 20):
    """获取会话列表"""
    try:
        with get_memory_context(user_id) as memory:
            sessions = memory.list_sessions(limit=limit)
            return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


# ============================================================================
# 聊天接口
# ============================================================================

@router.post("/chat")
def chat(message_data: MessageCreate, user_id: str = Depends(verify_token)):
    """发送消息并获取回复"""
    from ..graph.workflow_db import build_app
    from ..state.state import AssistantState, Message
    import uuid
    
    try:
        with get_memory_context(user_id) as memory:
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
                assistant_msg_id = memory.add_message(session_id, "assistant", assistant_content)
            else:
                assistant_content = "抱歉，我无法处理这个请求。"
                assistant_msg_id = memory.add_message(session_id, "assistant", assistant_content)
            
            return {
                "user_message": {
                    "id": user_msg_id,
                    "role": "user",
                    "content": message_data.content,
                    "created_at": datetime.now().isoformat()
                },
                "assistant_message": {
                    "id": assistant_msg_id,
                    "role": "assistant",
                    "content": assistant_content,
                    "created_at": datetime.now().isoformat()
                },
                "session_id": session_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: str, user_id: str = Depends(verify_token), limit: int = 50):
    """获取会话消息"""
    try:
        with get_memory_context(user_id) as memory:
            messages = memory.get_session_messages(session_id, limit=limit)
            return {
                "messages": [
                    {
                        "id": str(i),
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.timestamp.isoformat()
                    }
                    for i, m in enumerate(messages)
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


# ============================================================================
# 记忆接口
# ============================================================================

@router.post("/memories")
def create_memory(memory_data: MemoryCreate, user_id: str = Depends(verify_token)):
    """创建记忆"""
    try:
        with get_memory_context(user_id) as memory:
            memory_id = memory.remember(
                content=memory_data.content,
                category=memory_data.category,
                importance=memory_data.importance
            )
            
            return {
                "id": memory_id,
                "content": memory_data.content,
                "category": memory_data.category,
                "importance": memory_data.importance,
                "created_at": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(e)}")


@router.get("/memories")
def list_memories(user_id: str = Depends(verify_token), category: Optional[str] = None, limit: int = 100):
    """获取记忆列表"""
    try:
        with get_memory_context(user_id) as memory:
            memories = memory.recall(category=category, limit=limit)
            return {
                "memories": [
                    {
                        "id": m.id,
                        "content": m.content,
                        "category": m.category,
                        "importance": m.importance,
                        "created_at": m.created_at.isoformat()
                    }
                    for m in memories
                ],
                "total": len(memories)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: str, user_id: str = Depends(verify_token)):
    """删除记忆"""
    try:
        with get_memory_context(user_id) as memory:
            success = memory.memory_repo.delete(memory_id, user_id)
            if success:
                return {"success": True, "message": "Memory deleted"}
            raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


# ============================================================================
# 任务接口
# ============================================================================

@router.post("/tasks")
def create_task(task_data: TaskCreate, user_id: str = Depends(verify_token)):
    """创建任务"""
    try:
        with get_memory_context(user_id) as memory:
            task_id = memory.create_task(
                title=task_data.title,
                description=task_data.description,
                priority=task_data.priority
            )
            
            return {
                "id": task_id,
                "title": task_data.title,
                "description": task_data.description,
                "status": "pending",
                "priority": task_data.priority,
                "created_at": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks")
def list_tasks(user_id: str = Depends(verify_token), status: Optional[str] = None, limit: int = 100):
    """获取任务列表"""
    try:
        with get_memory_context(user_id) as memory:
            tasks = memory.list_tasks(status=status, limit=limit)
            return {
                "tasks": [
                    {
                        "id": t["id"],
                        "title": t["title"],
                        "description": t.get("description", ""),
                        "status": t["status"],
                        "priority": t["priority"],
                        "created_at": t["created_at"]
                    }
                    for t in tasks
                ],
                "total": len(tasks)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.patch("/tasks/{task_id}")
def update_task_status(task_id: str, status: str, user_id: str = Depends(verify_token)):
    """更新任务状态"""
    try:
        with get_memory_context(user_id) as memory:
            success = memory.complete_task(task_id) if status == "completed" else False
            if success:
                return {"success": True, "message": "Task updated"}
            raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(verify_token)):
    """删除任务"""
    try:
        with get_memory_context(user_id) as memory:
            success = memory.delete_task(task_id)
            if success:
                return {"success": True, "message": "Task deleted"}
            raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


# ============================================================================
# 统计接口
# ============================================================================

@router.get("/stats")
def get_stats(user_id: str = Depends(verify_token)):
    """获取用户统计"""
    try:
        with get_memory_context(user_id) as memory:
            stats = memory.get_stats()
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
