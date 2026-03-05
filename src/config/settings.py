"""
配置管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    
    kimi_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # 项目配置
    project_name: str = "personal-assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # 记忆配置
    memory_storage_path: str = "./memory"
    max_memory_items: int = 1000
    
    # 向量数据库
    chroma_persist_dir: str = "./chroma_db"
    
    class Config:
        env_file = ".env"


# 全局配置实例
settings = Settings()