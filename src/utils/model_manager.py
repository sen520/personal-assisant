"""
模型管理服务
支持多 LLM 切换和配置
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelInfo:
    """模型信息"""
    id: str                          # 模型唯一标识
    name: str                        # 显示名称
    provider: str                    # 提供商
    description: str                 # 描述
    max_tokens: int                  # 最大 token 数
    supports_streaming: bool = True  # 是否支持流式
    supports_tools: bool = True      # 是否支持工具
    is_available: bool = True        # 是否可用


# 支持的模型列表
SUPPORTED_MODELS: List[ModelInfo] = [
    # OpenAI
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        description="OpenAI 旗舰模型，多模态能力强",
        max_tokens=128000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        description="OpenAI 轻量级模型，性价比高",
        max_tokens=128000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        description="OpenAI 快速模型",
        max_tokens=16385,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # Anthropic
    ModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        description="Anthropic 高性能模型",
        max_tokens=200000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="anthropic",
        description="Anthropic 最强模型",
        max_tokens=200000,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # Kimi (Moonshot)
    ModelInfo(
        id="moonshot-v1-8k",
        name="Kimi (8K)",
        provider="moonshot",
        description="Moonshot 轻量级模型",
        max_tokens=8192,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="moonshot-v1-32k",
        name="Kimi (32K)",
        provider="moonshot",
        description="Moonshot 长文本模型",
        max_tokens=32768,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="moonshot-v1-128k",
        name="Kimi (128K)",
        provider="moonshot",
        description="Moonshot 超长文本模型",
        max_tokens=128000,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # DeepSeek
    ModelInfo(
        id="deepseek-chat",
        name="DeepSeek Chat",
        provider="deepseek",
        description="DeepSeek 对话模型",
        max_tokens=64000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="deepseek-coder",
        name="DeepSeek Coder",
        provider="deepseek",
        description="DeepSeek 代码模型",
        max_tokens=64000,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # 阿里通义千问
    ModelInfo(
        id="qwen-plus",
        name="通义千问 Plus",
        provider="qwen",
        description="阿里通义千问增强版",
        max_tokens=32000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="qwen-turbo",
        name="通义千问 Turbo",
        provider="qwen",
        description="阿里通义千问快速版",
        max_tokens=32000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="qwen-max",
        name="通义千问 Max",
        provider="qwen",
        description="阿里通义千问最强版",
        max_tokens=32000,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # 硅基流动 (SiliconFlow) - 聚合平台
    ModelInfo(
        id="deepseek-ai/DeepSeek-V3",
        name="DeepSeek-V3 (SiliconFlow)",
        provider="siliconflow",
        description="DeepSeek-V3 通过 SiliconFlow",
        max_tokens=64000,
        supports_streaming=True,
        supports_tools=True
    ),
    ModelInfo(
        id="deepseek-ai/DeepSeek-R1",
        name="DeepSeek-R1 (SiliconFlow)",
        provider="siliconflow",
        description="DeepSeek-R1 推理模型",
        max_tokens=64000,
        supports_streaming=True,
        supports_tools=False
    ),
    ModelInfo(
        id="Qwen/Qwen2.5-72B-Instruct",
        name="Qwen2.5-72B (SiliconFlow)",
        provider="siliconflow",
        description="通义千问 72B 通过 SiliconFlow",
        max_tokens=32000,
        supports_streaming=True,
        supports_tools=True
    ),
]


class ModelManager:
    """
    模型管理器
    
    管理用户模型偏好和配置
    """
    
    _instance = None
    _user_models: Dict[str, str] = {}  # user_id -> model_id
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型列表"""
        models = []
        for m in SUPPORTED_MODELS:
            # 检查是否有 API key
            has_key = self._check_api_key(m.provider)
            model_dict = asdict(m)
            model_dict['has_api_key'] = has_key
            models.append(model_dict)
        return models
    
    def _check_api_key(self, provider: str) -> bool:
        """检查提供商的 API key 是否配置"""
        env_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'moonshot': 'MOONSHOT_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'qwen': 'DASHSCOPE_API_KEY',
            'siliconflow': 'LLM_API_KEY',  # 硅基流动使用通用 key
        }
        env_key = env_map.get(provider)
        if not env_key:
            return False
        return bool(os.getenv(env_key))
    
    def get_user_model(self, user_id: str) -> Optional[ModelInfo]:
        """获取用户当前选择的模型"""
        model_id = self._user_models.get(user_id)
        if not model_id:
            # 使用系统默认
            model_id = getattr(settings, 'llm_model', 'deepseek-ai/DeepSeek-V3')
        
        for m in SUPPORTED_MODELS:
            if m.id == model_id:
                return m
        return None
    
    def set_user_model(self, user_id: str, model_id: str) -> bool:
        """设置用户模型"""
        # 验证模型是否存在
        model = self.get_model_by_id(model_id)
        if not model:
            return False
        
        # 检查 API key 是否配置
        if not self._check_api_key(model.provider):
            logger.warning(f"用户 {user_id[:8]}... 选择模型 {model_id} 但未配置 API key")
        
        self._user_models[user_id] = model_id
        logger.info(f"用户 {user_id[:8]}... 切换模型为: {model.name}")
        return True
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """通过 ID 获取模型信息"""
        for m in SUPPORTED_MODELS:
            if m.id == model_id:
                return m
        return None
    
    def create_llm_client(self, user_id: str, **kwargs):
        """为用户创建 LLM 客户端"""
        from ..llm import LLMFactory
        
        model_info = self.get_user_model(user_id)
        if not model_info:
            # 使用默认
            return LLMFactory.create_from_env()
        
        # 获取配置
        config = self._get_provider_config(model_info.provider)
        
        return LLMFactory.create(
            provider=config.get('provider', 'siliconflow'),
            model=model_info.id,
            api_key=config.get('api_key'),
            base_url=config.get('base_url'),
            **kwargs
        )
    
    def _get_provider_config(self, provider: str) -> Dict[str, str]:
        """获取提供商配置"""
        configs = {
            'openai': {
                'provider': 'openai',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'base_url': 'https://api.openai.com/v1'
            },
            'anthropic': {
                'provider': 'anthropic',
                'api_key': os.getenv('ANTHROPIC_API_KEY'),
                'base_url': None  # Anthropic 使用 SDK 内置
            },
            'moonshot': {
                'provider': 'moonshot',
                'api_key': os.getenv('MOONSHOT_API_KEY'),
                'base_url': 'https://api.moonshot.cn/v1'
            },
            'deepseek': {
                'provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'base_url': 'https://api.deepseek.com/v1'
            },
            'qwen': {
                'provider': 'qwen',
                'api_key': os.getenv('DASHSCOPE_API_KEY'),
                'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
            },
            'siliconflow': {
                'provider': 'openai',  # 使用 OpenAI 兼容格式
                'api_key': os.getenv('LLM_API_KEY'),
                'base_url': os.getenv('LLM_BASE_URL', 'https://api.siliconflow.cn/v1')
            }
        }
        return configs.get(provider, configs['siliconflow'])
    
    def compare_models(self, query: str, model_ids: List[str]) -> List[Dict[str, Any]]:
        """
        对比多个模型的回复
        
        Args:
            query: 测试查询
            model_ids: 要对比的模型 ID 列表
        
        Returns:
            各模型回复对比
        """
        import asyncio
        
        results = []
        
        for model_id in model_ids:
            model = self.get_model_by_id(model_id)
            if not model:
                continue
            
            start_time = os.times().elapsed
            try:
                # 创建临时客户端
                config = self._get_provider_config(model.provider)
                from ..llm import LLMFactory, Message
                
                client = LLMFactory.create(
                    provider=config.get('provider', 'openai'),
                    model=model_id,
                    api_key=config.get('api_key'),
                    base_url=config.get('base_url')
                )
                
                # 发送请求
                messages = [Message(role="user", content=query)]
                response = asyncio.get_event_loop().run_until_complete(
                    client.chat(messages)
                )
                
                end_time = os.times().elapsed
                
                results.append({
                    "model": model.name,
                    "model_id": model_id,
                    "response": response.get('content', ''),
                    "latency_ms": round((end_time - start_time) * 1000, 2),
                    "tokens": response.get('usage', {}).get('total_tokens', 0),
                    "success": True
                })
                
            except Exception as e:
                end_time = os.times().elapsed
                results.append({
                    "model": model.name if model else model_id,
                    "model_id": model_id,
                    "error": str(e),
                    "latency_ms": round((end_time - start_time) * 1000, 2),
                    "success": False
                })
        
        return results


# 全局模型管理器实例
model_manager = ModelManager()


def get_available_models() -> List[Dict[str, Any]]:
    """获取可用模型列表"""
    return model_manager.get_available_models()


def get_user_model(user_id: str) -> Optional[ModelInfo]:
    """获取用户当前模型"""
    return model_manager.get_user_model(user_id)


def set_user_model(user_id: str, model_id: str) -> bool:
    """设置用户模型"""
    return model_manager.set_user_model(user_id, model_id)
