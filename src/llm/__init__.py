"""
LLM 客户端 - 统一的大语言模型调用接口
"""

from typing import Dict, Any, List, Optional, AsyncIterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import os


class LLMProvider(Enum):
    """支持的 LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOONSHOT = "moonshot"  # Kimi
    DEEPSEEK = "deepseek"
    QWEN = "qwen"  # 阿里通义千问


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60

    def __post_init__(self):
        # 如果未提供 API key，尝试从环境变量获取
        if not self.api_key:
            env_map = {
                LLMProvider.OPENAI: "OPENAI_API_KEY",
                LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
                LLMProvider.MOONSHOT: "MOONSHOT_API_KEY",
                LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
                LLMProvider.QWEN: "DASHSCOPE_API_KEY",
            }
            self.api_key = os.getenv(env_map.get(self.provider, ""))


@dataclass
class Message:
    """消息格式"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None  # 工具名称
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


class LLMClient(ABC):
    """LLM 客户端抽象基类"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """对话接口"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None
    ) -> AsyncIterator[str]:
        """流式对话接口"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """文本嵌入"""
        pass


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容格式的客户端"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """对话"""
        formatted_messages = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            formatted_messages.append(msg)

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream
        }

        if tools:
            params["tools"] = tools

        response = await self.client.chat.completions.create(**params)

        if stream:
            return {"stream": response}

        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "tool_calls": choice.message.tool_calls if hasattr(choice.message, 'tool_calls') else None,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None
    ) -> AsyncIterator[str]:
        """流式对话"""
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "stream": True
        }

        if tools:
            params["tools"] = tools

        stream = await self.client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        # 使用专门的 embedding 模型
        embed_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = await self.client.embeddings.create(
            model=embed_model,
            input=text
        )
        return response.data[0].embedding


# 提供商默认配置
DEFAULT_CONFIGS: Dict[LLMProvider, Dict[str, str]] = {
    LLMProvider.OPENAI: {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1"
    },
    LLMProvider.MOONSHOT: {
        "model": "moonshot-v1-8k",
        "base_url": "https://api.moonshot.cn/v1"
    },
    LLMProvider.DEEPSEEK: {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1"
    },
    LLMProvider.QWEN: {
        "model": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
}


class LLMFactory:
    """LLM 客户端工厂"""

    @staticmethod
    def create(
        provider: str = "moonshot",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> LLMClient:
        """
        创建 LLM 客户端

        Args:
            provider: 提供商名称 (openai, moonshot, deepseek, qwen)
            model: 模型名称
            api_key: API 密钥
            base_url: 自定义 base URL
            **kwargs: 其他配置参数
        """
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise ValueError(f"不支持的提供商: {provider}")

        # 使用默认配置
        defaults = DEFAULT_CONFIGS.get(provider_enum, {})

        config = LLMConfig(
            provider=provider_enum,
            model=model or defaults.get("model", ""),
            api_key=api_key,
            base_url=base_url or defaults.get("base_url"),
            **kwargs
        )

        return OpenAICompatibleClient(config)

    @staticmethod
    def create_from_env() -> LLMClient:
        """从环境变量创建客户端"""
        provider = os.getenv("LLM_PROVIDER", "moonshot")
        model = os.getenv("LLM_MODEL")
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")

        return LLMFactory.create(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )


# 便捷函数
def create_llm(**kwargs) -> LLMClient:
    """快捷创建 LLM 客户端"""
    return LLMFactory.create(**kwargs)


def create_llm_from_env() -> LLMClient:
    """从环境变量快捷创建"""
    return LLMFactory.create_from_env()
