"""
日志配置 - 结构化日志
"""

import sys
import logging
from typing import Optional

import structlog

from ..config.settings import settings


def configure_logging():
    """配置结构化日志"""
    
    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )
    
    # 配置 structlog
    structlog.configure(
        processors=[
            # 添加时间戳
            structlog.processors.TimeStamper(fmt="iso"),
            # 添加日志级别
            structlog.stdlib.add_log_level,
            # 添加调用者信息
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # 格式化异常
            structlog.stdlib.ExtraAdder(),
            # 根据配置选择渲染器
            structlog.dev.ConsoleRenderer(colors=True)
            if settings.debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 减少第三方库的日志噪音
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    获取结构化日志记录器
    
    Args:
        name: 日志名称
    
    Returns:
        结构化日志记录器
    """
    return structlog.get_logger(name)


class RequestContext:
    """请求上下文管理"""
    
    @staticmethod
    def bind_request_id(request_id: str):
        """绑定请求 ID"""
        structlog.contextvars.bind_contextvars(request_id=request_id)
    
    @staticmethod
    def bind_user_id(user_id: str):
        """绑定用户 ID"""
        structlog.contextvars.bind_contextvars(user_id=user_id)
    
    @staticmethod
    def clear():
        """清除上下文"""
        structlog.contextvars.clear_contextvars()
