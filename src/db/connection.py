"""
数据库连接池和上下文管理器
解决连接泄漏问题
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from functools import wraps
import time

from sqlalchemy.exc import OperationalError, DatabaseError

from .models import db_manager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """数据库操作错误"""
    pass


def retry_on_db_error(max_retries: int = 3, delay: float = 0.1):
    """
    数据库操作重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DatabaseError) as e:
                    last_error = e
                    logger.warning(f"数据库操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        raise DatabaseError(f"数据库操作失败，已重试 {max_retries} 次: {e}")
            raise last_error
        return wrapper
    return decorator


@contextmanager
def get_db_session() -> Generator:
    """
    数据库会话上下文管理器
    
    使用示例：
        with get_db_session() as session:
            user = session.query(User).first()
    
    Yields:
        SQLAlchemy Session 对象
    """
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库事务回滚: {e}")
        raise
    finally:
        session.close()


@contextmanager
def get_memory_context(user_id: str):
    """
    记忆系统上下文管理器
    
    使用示例：
        with get_memory_context("user_id") as memory:
            memory.remember(content="...")
    
    Args:
        user_id: 用户 ID
    
    Yields:
        MySQLMemorySystem 对象
    """
    from .memory_system import MemorySystemFactory
    
    memory = MemorySystemFactory.for_user(user_id)
    try:
        yield memory
    finally:
        memory.close()


class ConnectionPoolMonitor:
    """数据库连接池监控"""
    
    @staticmethod
    def get_pool_status():
        """获取连接池状态"""
        engine = db_manager.get_engine()
        if hasattr(engine, 'pool'):
            pool = engine.pool
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
            }
        return {"error": "Connection pool not available"}
    
    @staticmethod
    def log_pool_status():
        """记录连接池状态到日志"""
        status = ConnectionPoolMonitor.get_pool_status()
        logger.info(f"连接池状态: {status}")


# ============================================================================
# 便捷函数
# ============================================================================

def init_database_with_retry(max_retries: int = 5) -> bool:
    """
    带重试的数据库初始化
    
    Args:
        max_retries: 最大重试次数
    
    Returns:
        是否初始化成功
    """
    for attempt in range(max_retries):
        try:
            db_manager.init_engine()
            logger.info("数据库初始化成功")
            return True
        except Exception as e:
            logger.warning(f"数据库初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s, 8s...
            else:
                logger.error("数据库初始化最终失败")
                raise
    return False


from sqlalchemy import text

def check_database_health():
    """
    检查数据库健康状态
    
    Returns:
        dict: 健康状态信息
    """
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "pool": ConnectionPoolMonitor.get_pool_status()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
