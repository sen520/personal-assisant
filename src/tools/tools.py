"""
工具定义 - 个人助理可调用的工具集
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
import uuid

import aiohttp
import pytz


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    message: str = ""

    def to_string(self) -> str:
        """转换为字符串供 LLM 使用"""
        if self.success:
            return json.dumps({
                "success": True,
                "data": self.data,
                "message": self.message
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": str(self.data),
                "message": self.message
            }, ensure_ascii=False)


class BaseTool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """转换为 OpenAI 工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class TimeTool(BaseTool):
    """获取当前时间工具"""

    name = "get_current_time"
    description = "获取当前日期和时间信息"
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区，如 'Asia/Shanghai'，默认使用本地时区"
            },
            "format": {
                "type": "string",
                "description": "时间格式，如 '%Y-%m-%d %H:%M:%S'，默认为 ISO 格式"
            }
        }
    }

    async def execute(self, timezone: Optional[str] = None, fmt: Optional[str] = None) -> ToolResult:
        """获取当前时间"""
        try:
            if timezone:
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
            else:
                now = datetime.now()

            if fmt:
                time_str = now.strftime(fmt)
            else:
                time_str = now.isoformat()

            return ToolResult(
                success=True,
                data={
                    "datetime": time_str,
                    "timestamp": now.timestamp(),
                    "year": now.year,
                    "month": now.month,
                    "day": now.day,
                    "weekday": now.strftime("%A"),
                    "hour": now.hour,
                    "minute": now.minute
                },
                message=f"当前时间: {time_str}"
            )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message="获取时间失败")


class CalculatorTool(BaseTool):
    """计算器工具"""

    name = "calculator"
    description = "执行数学计算，支持基本运算和常见数学函数"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2 + 3 * 4' 或 'sqrt(16) + pow(2, 3)'"
            }
        },
        "required": ["expression"]
    }

    async def execute(self, expression: str) -> ToolResult:
        """执行计算"""
        try:
            import math

            # 安全计算环境
            safe_dict = {
                "sqrt": math.sqrt,
                "pow": math.pow,
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum,
                "pi": math.pi,
                "e": math.e,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "ceil": math.ceil,
                "floor": math.floor,
            }

            # 限制危险操作
            allowed_chars = set('0123456789+-*/().,^% =abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
            if not all(c in allowed_chars for c in expression):
                return ToolResult(
                    success=False,
                    data="Invalid characters in expression",
                    message="表达式包含非法字符"
                )

            # 替换幂运算
            expression = expression.replace("^", "**")

            result = eval(expression, {"__builtins__": {}}, safe_dict)

            return ToolResult(
                success=True,
                data={"result": result},
                message=f"计算结果: {result}"
            )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message=f"计算错误: {str(e)}")


class MemoryStoreTool(BaseTool):
    """存储记忆工具"""

    name = "store_memory"
    description = "将重要信息存储到长期记忆中，方便日后回忆"
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要存储的内容"
            },
            "category": {
                "type": "string",
                "description": "记忆类别，如 'personal', 'work', 'preference', 'fact'",
                "enum": ["personal", "work", "preference", "fact", "other"]
            },
            "importance": {
                "type": "integer",
                "description": "重要程度 1-5",
                "minimum": 1,
                "maximum": 5
            }
        },
        "required": ["content"]
    }

    def __init__(self, memory_system=None):
        self.memory_system = memory_system

    async def execute(self, content: str, category: str = "other", importance: int = 3) -> ToolResult:
        """存储记忆"""
        try:
            if self.memory_system:
                # 如果提供了记忆系统，使用它来存储
                memory_id = await self.memory_system.store(
                    content=content,
                    category=category,
                    importance=importance
                )
                return ToolResult(
                    success=True,
                    data={"memory_id": memory_id},
                    message="记忆已存储"
                )
            # 模拟存储
            return ToolResult(
                success=True,
                data={"content": content, "category": category},
                message="记忆已存储（模拟模式）"
            )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message="存储失败")


class MemoryRetrieveTool(BaseTool):
    """检索记忆工具"""

    name = "retrieve_memory"
    description = "从长期记忆中检索相关信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索关键词或问题"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }

    def __init__(self, memory_system=None):
        self.memory_system = memory_system

    async def execute(self, query: str, limit: int = 5) -> ToolResult:
        """检索记忆"""
        try:
            if self.memory_system:
                memories = await self.memory_system.retrieve(query, limit=limit)
                return ToolResult(
                    success=True,
                    data=memories,
                    message=f"找到 {len(memories)} 条相关记忆"
                )
            return ToolResult(
                success=True,
                data=[],
                message="检索完成（模拟模式，无记忆系统）"
            )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message="检索失败")


class WeatherTool(BaseTool):
    """天气查询工具（需要配置 API）"""

    name = "get_weather"
    description = "查询指定城市的天气信息"
    parameters = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，如 '北京'、'上海'、'Nanjing'"
            },
            "days": {
                "type": "integer",
                "description": "预报天数 1-7",
                "default": 1,
                "minimum": 1,
                "maximum": 7
            }
        },
        "required": ["city"]
    }

    async def execute(self, city: str, days: int = 1) -> ToolResult:
        """获取天气"""
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            # 返回模拟数据
            return ToolResult(
                success=True,
                data={
                    "city": city,
                    "note": "模拟数据（未配置天气 API）",
                    "current": {
                        "temperature": "22°C",
                        "condition": "晴朗",
                        "humidity": "65%",
                        "wind": "东南风 3级"
                    }
                },
                message=f"{city} 当前天气：晴朗，22°C（模拟数据）"
            )

        # 这里可以接入真实的天气 API
        # 如和风天气、OpenWeatherMap 等
        return ToolResult(
            success=False,
            data="Weather API not implemented",
            message="天气 API 尚未实现"
        )


class WebSearchTool(BaseTool):
    """网页搜索工具（需要配置 API）"""

    name = "web_search"
    description = "搜索互联网上的信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """执行搜索"""
        # 检查是否配置了搜索 API
        search_api = os.getenv("SEARCH_API", "")

        if search_api == "brave":
            return await self._search_brave(query, num_results)
        if search_api == "serper":
            return await self._search_serper(query, num_results)
        return ToolResult(
            success=False,
            data="No search API configured",
            message="搜索功能需要配置 SEARCH_API 环境变量（brave 或 serper）"
        )

    async def _search_brave(self, query: str, num: int) -> ToolResult:
        """使用 Brave Search"""
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            return ToolResult(success=False, data="Missing BRAVE_API_KEY", message="缺少 API 密钥")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}
                params = {"q": query, "count": num}

                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params
                ) as resp:
                    data = await resp.json()

                    results = [
                        {"title": r.get("title"), "url": r.get("url"), "description": r.get("description")}
                        for r in data.get("web", {}).get("results", [])
                    ]

                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"找到 {len(results)} 条搜索结果"
                    )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message="搜索失败")

    async def _search_serper(self, query: str, num: int) -> ToolResult:
        """使用 Serper"""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return ToolResult(success=False, data="Missing SERPER_API_KEY", message="缺少 API 密钥")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
                payload = {"q": query, "num": num}

                async with session.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload
                ) as resp:
                    data = await resp.json()

                    results = [
                        {"title": r.get("title"), "url": r.get("link"), "description": r.get("snippet")}
                        for r in data.get("organic", [])
                    ]

                    return ToolResult(
                        success=True,
                        data=results,
                        message=f"找到 {len(results)} 条搜索结果"
                    )
        except Exception as e:
            return ToolResult(success=False, data=str(e), message="搜索失败")


class TaskManagerTool(BaseTool):
    """任务管理工具"""

    name = "manage_task"
    description = "管理待办事项和任务列表，支持创建、查询、更新、删除任务"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "操作类型",
                "enum": ["create", "list", "update", "delete", "complete"]
            },
            "title": {
                "type": "string",
                "description": "任务标题（创建/更新时使用）"
            },
            "description": {
                "type": "string",
                "description": "任务描述"
            },
            "task_id": {
                "type": "string",
                "description": "任务 ID（更新/删除/完成时使用）"
            },
            "due_date": {
                "type": "string",
                "description": "截止日期，格式如 '2026-03-10'"
            },
            "priority": {
                "type": "string",
                "description": "优先级",
                "enum": ["low", "medium", "high"]
            }
        },
        "required": ["action"]
    }

    def __init__(self, task_store=None):
        self.task_store = task_store
        self.tasks = {}  # 内存存储，实际应用使用数据库

    async def execute(
        self,
        action: str,
        title: str = "",
        description: str = "",
        task_id: str = "",
        due_date: str = "",
        priority: str = "medium"
    ) -> ToolResult:
        """执行任务管理操作"""
        try:
            if action == "create":
                return await self._create_task(title, description, due_date, priority)
            if action == "list":
                return await self._list_tasks()
            if action == "update":
                return await self._update_task(task_id, title, description, priority)
            if action == "delete":
                return await self._delete_task(task_id)
            if action == "complete":
                return await self._complete_task(task_id)
            return ToolResult(success=False, data="Unknown action", message="未知操作")
        except Exception as e:
            return ToolResult(success=False, data=str(e), message=f"操作失败: {str(e)}")

    async def _create_task(self, title: str, description: str = "", due_date: str = "", priority: str = "medium") -> ToolResult:
        task_id = str(uuid.uuid4())[:8]

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        self.tasks[task_id] = task

        return ToolResult(
            success=True,
            data=task,
            message=f"任务已创建: {title} (ID: {task_id})"
        )

    async def _list_tasks(self) -> ToolResult:
        tasks = list(self.tasks.values())
        return ToolResult(
            success=True,
            data=tasks,
            message=f"共有 {len(tasks)} 个任务"
        )

    async def _update_task(self, task_id: str, title: str = "", description: str = "", priority: str = "") -> ToolResult:
        if task_id not in self.tasks:
            return ToolResult(success=False, data="Task not found", message="任务不存在")

        task = self.tasks[task_id]
        if title:
            task["title"] = title
        if description:
            task["description"] = description
        if priority:
            task["priority"] = priority

        return ToolResult(
            success=True,
            data=task,
            message=f"任务已更新 (ID: {task_id})"
        )

    async def _delete_task(self, task_id: str) -> ToolResult:
        if task_id not in self.tasks:
            return ToolResult(success=False, data="Task not found", message="任务不存在")

        del self.tasks[task_id]
        return ToolResult(
            success=True,
            data=None,
            message=f"任务已删除 (ID: {task_id})"
        )

    async def _complete_task(self, task_id: str) -> ToolResult:
        if task_id not in self.tasks:
            return ToolResult(success=False, data="Task not found", message="任务不存在")

        self.tasks[task_id]["status"] = "completed"
        return ToolResult(
            success=True,
            data=self.tasks[task_id],
            message=f"任务已完成 (ID: {task_id})"
        )


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        self.register(TimeTool())
        self.register(CalculatorTool())
        self.register(MemoryStoreTool())
        self.register(MemoryRetrieveTool())
        self.register(WeatherTool())
        self.register(WebSearchTool())
        self.register(TaskManagerTool())

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 OpenAI Schema"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """执行指定工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                data=f"Tool '{name}' not found",
                message=f"工具 '{name}' 不存在"
            )

        return await tool.execute(**kwargs)


# 全局工具注册中心
tool_registry = ToolRegistry()


# 便捷函数
def get_tool(name: str) -> Optional[BaseTool]:
    """获取工具"""
    return tool_registry.get(name)


def list_tools() -> List[str]:
    """列出工具"""
    return tool_registry.list_tools()


def get_tool_schemas() -> List[Dict[str, Any]]:
    """获取工具 schemas"""
    return tool_registry.get_schemas()


async def execute_tool(name: str, **kwargs) -> ToolResult:
    """执行工具"""
    return await tool_registry.execute(name, **kwargs)
