"""
管理后台服务
系统监控和管理功能
"""

import os
import psutil
from typing import Dict, Any, List
from datetime import datetime

from ..config.settings import settings
from ..utils.logging import get_logger
from ..db.models import db_manager
from ..db.repository import UserRepository

logger = get_logger(__name__)


class AdminService:
    """管理后台服务"""
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # CPU 和内存
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": round(disk.used / disk.total * 100, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """获取数据库统计"""
        try:
            session = db_manager.get_session()
            try:
                from ..db.models import User, Session as ChatSession, Memory, Task, Document
                
                stats = {
                    "users": session.query(User).count(),
                    "sessions": session.query(ChatSession).count(),
                    "memories": session.query(Memory).count(),
                    "tasks": session.query(Task).count(),
                    "documents": session.query(Document).count(),
                    "timestamp": datetime.now().isoformat()
                }
                
                return stats
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def list_users(
        skip: int = 0,
        limit: int = 100,
        search: str = None
    ) -> List[Dict[str, Any]]:
        """获取用户列表"""
        try:
            session = db_manager.get_session()
            try:
                from ..db.models import User
                
                query = session.query(User)
                
                if search:
                    query = query.filter(
                        User.username.ilike(f"%{search}%") | 
                        User.email.ilike(f"%{search}%")
                    )
                
                users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
                
                return [
                    {
                        "id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "is_active": bool(u.is_active),
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                        "last_login": u.last_login.isoformat() if hasattr(u, 'last_login') and u.last_login else None
                    }
                    for u in users
                ]
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []
    
    @staticmethod
    def get_user_detail(user_id: str) -> Dict[str, Any]:
        """获取用户详情"""
        try:
            session = db_manager.get_session()
            try:
                from ..db.models import User, Session as ChatSession, Memory, Task, Document
                
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return None
                
                # 统计用户数据
                sessions_count = session.query(ChatSession).filter(ChatSession.user_id == user_id).count()
                memories_count = session.query(Memory).filter(Memory.user_id == user_id).count()
                tasks_count = session.query(Task).filter(Task.user_id == user_id).count()
                documents_count = session.query(Document).filter(Document.user_id == user_id).count()
                
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": bool(user.is_active),
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "stats": {
                        "sessions": sessions_count,
                        "memories": memories_count,
                        "tasks": tasks_count,
                        "documents": documents_count
                    }
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取用户详情失败: {e}")
            return None
    
    @staticmethod
    def toggle_user_status(user_id: str, is_active: bool) -> bool:
        """启用/禁用用户"""
        try:
            session = db_manager.get_session()
            try:
                from ..db.models import User
                
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                user.is_active = 1 if is_active else 0
                session.commit()
                
                logger.info(f"用户 {user_id} 状态已更新为: {'启用' if is_active else '禁用'}")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新用户状态失败: {e}")
            return False
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            from ..utils.cache import get_cache_stats
            return get_cache_stats()
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_vector_stats() -> Dict[str, Any]:
        """获取向量存储统计"""
        try:
            from ..utils.vector_store import vector_store
            # 这里可以扩展为获取所有集合的统计
            return {
                "status": "active",
                "note": "Vector store is running",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取向量统计失败: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_logs(limit: int = 100) -> List[str]:
        """获取最近日志（简化版）"""
        # 实际项目中应该读取日志文件
        return ["日志功能待实现"]
    
    @staticmethod
    def get_api_stats() -> Dict[str, Any]:
        """获取 API 调用统计"""
        # 实际项目中应该从中间件统计
        return {
            "total_requests": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "note": "API stats tracking not implemented"
        }


# 检查是否为管理员（简单实现，实际应该使用角色系统）
def is_admin(user_id: str) -> bool:
    """检查用户是否为管理员"""
    # 可以配置管理员 ID 列表
    admin_ids = os.getenv("ADMIN_USER_IDS", "").split(",")
    return user_id in admin_ids
