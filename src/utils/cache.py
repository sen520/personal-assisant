"""
Redis 缓存管理器
提供 API 响应缓存功能
"""

import json
import hashlib
import logging
from typing import Optional, Any, Callable
from functools import wraps
import pickle

from ..config.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    _instance = None
    _redis_client = None
    _enabled = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_redis(self):
        """初始化 Redis 连接"""
        try:
            import redis
            
            redis_host = getattr(settings, 'redis_host', 'localhost')
            redis_port = getattr(settings, 'redis_port', 6379)
            redis_db = getattr(settings, 'redis_db', 0)
            redis_password = getattr(settings, 'redis_password', None)
            
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False,  # 使用二进制序列化
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=20
            )
            
            # 测试连接
            self._redis_client.ping()
            self._enabled = True
            logger.info(f"✅ Redis 缓存已连接: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis 连接失败，使用内存缓存: {e}")
            self._redis_client = None
            self._enabled = False
    
    def get_redis(self):
        """获取 Redis 客户端"""
        if self._redis_client is None:
            self.init_redis()
        return self._redis_client
    
    def is_enabled(self) -> bool:
        """检查缓存是否可用"""
        return self._enabled and self._redis_client is not None
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args, **kwargs: 用于生成唯一键的参数
        
        Returns:
            缓存键
        """
        key_parts = [prefix]
        
        # 添加 args
        if args:
            key_parts.append(str(args))
        
        # 添加 kwargs（排序确保一致性）
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(str(sorted_kwargs))
        
        # 生成哈希
        raw_key = "|".join(key_parts)
        return f"pa:{prefix}:{hashlib.md5(raw_key.encode()).hexdigest()[:16]}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或 None
        """
        if not self.is_enabled():
            return None
        
        try:
            data = self._redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        expire: int = 300  # 默认5分钟
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
        
        Returns:
            是否设置成功
        """
        if not self.is_enabled():
            return False
        
        try:
            serialized = pickle.dumps(value)
            self._redis_client.setex(key, expire, serialized)
            return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            是否删除成功
        """
        if not self.is_enabled():
            return False
        
        try:
            self._redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        按模式删除缓存
        
        Args:
            pattern: 匹配模式，如 "pa:sessions:*"
        
        Returns:
            删除的键数量
        """
        if not self.is_enabled():
            return 0
        
        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                return self._redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"缓存批量删除失败: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """
        清除用户相关缓存
        
        Args:
            user_id: 用户 ID
        
        Returns:
            删除的键数量
        """
        patterns = [
            f"pa:sessions:*{user_id}*",
            f"pa:tasks:*{user_id}*",
            f"pa:memories:*{user_id}*",
            f"pa:stats:*{user_id}*"
        ]
        
        total = 0
        for pattern in patterns:
            total += self.delete_pattern(pattern)
        
        if total > 0:
            logger.info(f"已清除用户 {user_id[:8]}... 的 {total} 个缓存")
        
        return total


# 全局缓存实例
cache_manager = CacheManager()


# ============================================================================
# 缓存装饰器
# ============================================================================

def cached(
    prefix: str,
    expire: int = 300,
    key_func: Optional[Callable] = None
):
    """
    缓存装饰器
    
    使用示例:
        @cached("sessions", expire=60)
        def list_sessions(user_id: str):
            return db.query(...)
    
    Args:
        prefix: 缓存键前缀
        expire: 过期时间（秒）
        key_func: 自定义键生成函数
    
    Returns:
        装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_manager.set(cache_key, result, expire)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        
        # 添加清除缓存的方法
        wrapper.invalidate = lambda *args, **kwargs: cache_manager.delete(
            key_func(*args, **kwargs) if key_func else cache_manager.generate_key(prefix, *args, **kwargs)
        )
        
        return wrapper
    return decorator


def cache_response(prefix: str, expire: int = 300):
    """
    FastAPI 响应缓存装饰器
    
    使用示例:
        @app.get("/api/sessions")
        @cache_response("sessions", expire=60)
        def list_sessions(user_id: str = Depends(verify_token)):
            return {...}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取 user_id 从 kwargs
            user_id = kwargs.get('user_id', 'anonymous')
            
            # 生成缓存键
            cache_key = cache_manager.generate_key(
                f"{prefix}:{user_id}",
                func.__name__,
                *args,
                **{k: v for k, v in kwargs.items() if k != 'user_id'}
            )
            
            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"响应缓存命中: {cache_key}")
                return cached_value
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 存入缓存（仅当结果是 dict 或 list 时）
            if isinstance(result, (dict, list)):
                cache_manager.set(cache_key, result, expire)
                logger.debug(f"响应缓存设置: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# 便捷函数
# ============================================================================

def init_cache():
    """初始化缓存"""
    cache_manager.init_redis()


def get_cache_stats() -> dict:
    """获取缓存统计"""
    if not cache_manager.is_enabled():
        return {"enabled": False}
    
    try:
        info = cache_manager.get_redis().info()
        return {
            "enabled": True,
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": cache_manager.get_redis().dbsize()
        }
    except Exception as e:
        return {"enabled": True, "error": str(e)}
