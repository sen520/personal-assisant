"""
节点定义 - 个人助理的核心功能节点（数据库版）
接入 MySQL 记忆系统，支持多用户
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime
from rich.console import Console

from ..state.state import AssistantState, Message
from ..llm import create_llm_from_env, Message as LLMMessage
from ..tools.tools import tool_registry, execute_tool
from ..db.memory_system import MemorySystemFactory

console = Console()
logger = logging.getLogger(__name__)


class NodeContext:
    """节点上下文，保存共享资源"""
    llm = None
    
    @classmethod
    def get_llm(cls):
        if cls.llm is None:
            cls.llm = create_llm_from_env()
        return cls.llm


def user_input_node(state: AssistantState) -> AssistantState:
    """用户输入节点 - 初始化用户上下文"""
    user_id = state.get("user_id", "anonymous")
    logger.info(f"[Node] 用户输入 [用户: {user_id}]")
    return state


async def intent_analysis_node(state: AssistantState) -> AssistantState:
    """
    意图分析节点 - 使用 LLM 进行意图识别
    """
    messages = state.get("messages", [])
    if not messages:
        state["next_node"] = "generate_response"
        return state
    
    last_message = messages[-1]
    if last_message.role != "user":
        state["next_node"] = "generate_response"
        return state
    
    # 简化意图识别（基于关键词）
    content = last_message.content.lower()
    
    if any(kw in content for kw in ["记住", "记住", "save", "存储"]):
        state["next_node"] = "store_memory"
        state["intent"] = "remember"
    elif any(kw in content for kw in ["回忆", "记得", "之前", "recall", "remember"]):
        state["next_node"] = "retrieve_memory"
        state["intent"] = "recall"
    elif any(kw in content for kw in ["任务", "todo", "待办", "task"]):
        state["next_node"] = "task_manager"
        state["intent"] = "task"
    elif any(kw in content for kw in ["搜索", "查找", "search", "find"]):
        state["next_node"] = "search"
        state["intent"] = "search"
    else:
        state["next_node"] = "generate_response"
        state["intent"] = "chat"
    
    console.print(f"[dim]🎯 意图识别: {state['intent']} -> {state['next_node']}[/dim]")
    return state


async def store_memory_node(state: AssistantState) -> AssistantState:
    """存储记忆节点 - 使用数据库"""
    messages = state.get("messages", [])
    user_id = state.get("user_id", "anonymous")
    
    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break
    
    if not last_user_msg:
        state["next_node"] = "end"
        return state
    
    console.print("[blue]💾 正在存储记忆...[/blue]")
    
    try:
        # 使用数据库记忆系统
        memory = MemorySystemFactory.for_user(user_id)
        
        # 提取要记忆的内容
        llm = NodeContext.get_llm()
        
        system_prompt = """从用户输入中提取需要记住的核心信息，以简洁的句子返回。"""
        
        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=last_user_msg)
        ]
        
        response = await llm.chat(llm_messages)
        content_to_store = response.get("content", last_user_msg)
        
        # 存储到数据库
        memory_id = memory.remember(
            content=content_to_store,
            category="personal",
            importance=4
        )
        memory.close()
        
        state["messages"].append(Message(
            role="assistant",
            content=f"好的，我已经记住了：{content_to_store} (ID: {memory_id[:8]})"
        ))
        
    except Exception as e:
        logger.error(f"存储记忆失败: {e}")
        console.print(f"[red]❌ 存储记忆失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，我没能记住这个信息。"
        ))
    
    state["next_node"] = "end"
    return state


async def retrieve_memory_node(state: AssistantState) -> AssistantState:
    """检索记忆节点 - 使用数据库"""
    messages = state.get("messages", [])
    user_id = state.get("user_id", "anonymous")
    
    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break
    
    if not last_user_msg:
        state["next_node"] = "end"
        return state
    
    console.print("[blue]🔍 正在检索记忆...[/blue]")
    
    try:
        # 使用数据库记忆系统
        memory = MemorySystemFactory.for_user(user_id)
        
        # 检索记忆
        memories = memory.recall(query=last_user_msg, limit=3)
        memory.close()
        
        if memories:
            memory_text = "\n".join([f"- [{m.category}] {m.content}" for m in memories])
            
            # 使用 LLM 生成回复
            llm = NodeContext.get_llm()
            
            prompt = f"""用户问题：{last_user_msg}

找到的相关记忆：
{memory_text}

请根据这些记忆回答用户的问题。如果记忆不足以回答问题，请直接说明。"""
            
            llm_messages = [
                LLMMessage(role="user", content=prompt)
            ]
            
            response = await llm.chat(llm_messages)
            reply = response.get("content", "根据我的记忆...")
        else:
            reply = "抱歉，我没有找到相关的记忆。"
        
        state["messages"].append(Message(
            role="assistant",
            content=reply
        ))
        
    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，检索记忆时出错了。"
        ))
    
    state["next_node"] = "end"
    return state


async def task_manager_node(state: AssistantState) -> AssistantState:
    """任务管理节点 - 使用数据库"""
    messages = state.get("messages", [])
    user_id = state.get("user_id", "anonymous")
    
    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break
    
    if not last_user_msg:
        state["next_node"] = "end"
        return state
    
    console.print("[blue]📋 正在处理任务...[/blue]")
    
    try:
        memory = MemorySystemFactory.for_user(user_id)
        
        # 判断用户想要做什么操作
        content_lower = last_user_msg.lower()
        
        if any(kw in content_lower for kw in ["创建", "添加", "新建", "增加", "create", "add"]):
            # 创建任务
            llm = NodeContext.get_llm()
            
            system_prompt = """从用户输入中提取任务标题，只返回标题，不要其他内容。"""
            
            llm_messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=last_user_msg)
            ]
            
            response = await llm.chat(llm_messages)
            title = response.get("content", last_user_msg[:50])
            
            task_id = memory.create_task(title=title, priority=3)
            reply = f"已创建任务：{title} (ID: {task_id[:8]})"
            
        elif any(kw in content_lower for kw in ["列表", "查看", "所有", "list", "show"]):
            # 显示任务列表
            tasks = memory.list_tasks()
            if tasks:
                task_list = "\n".join([f"• {t['title']} ({t['status']})" for t in tasks])
                reply = f"你的任务列表：\n{task_list}"
            else:
                reply = "当前没有任务。"
        else:
            reply = "请告诉我你想对任务做什么操作（创建/查看）。"
        
        memory.close()
        
        state["messages"].append(Message(
            role="assistant",
            content=reply
        ))
        
    except Exception as e:
        logger.error(f"任务管理失败: {e}")
        state["messages"].append(Message(
            role="assistant",
            content="处理任务时出错了。"
        ))
    
    state["next_node"] = "end"
    return state


async def search_node(state: AssistantState) -> AssistantState:
    """搜索节点"""
    messages = state.get("messages", [])
    
    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break
    
    if not last_user_msg:
        state["next_node"] = "end"
        return state
    
    console.print("[blue]🔎 正在搜索...[/blue]")
    
    try:
        # 提取搜索关键词
        llm = NodeContext.get_llm()
        
        system_prompt = "从用户输入中提取核心搜索关键词，只返回关键词，不要其他内容。"
        
        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=last_user_msg)
        ]
        
        response = await llm.chat(llm_messages)
        query = response.get("content", last_user_msg)
        
        # 执行搜索
        result = await execute_tool("web_search", query=query, num_results=3)
        
        if result.success and result.data:
            results = result.data
            search_summary = "\n\n".join([
                f"{i+1}. {r.get('title', 'No title')}\n{r.get('description', 'No description')[:100]}..."
                for i, r in enumerate(results[:3])
            ])
            reply = f"搜索结果：\n\n{search_summary}"
        else:
            reply = f"搜索完成，但没有找到相关结果。\n（{result.message}）"
        
        state["messages"].append(Message(
            role="assistant",
            content=reply
        ))
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        state["messages"].append(Message(
            role="assistant",
            content="搜索功能暂时不可用。"
        ))
    
    state["next_node"] = "end"
    return state


async def generate_response_node(state: AssistantState) -> AssistantState:
    """
    生成回复节点 - 使用 LLM 生成自然语言回复
    接入数据库获取用户上下文和记忆
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id", "anonymous")
    session_id = state.get("session_id")
    
    if not messages:
        state["next_node"] = "end"
        return state
    
    console.print("[blue]💬 正在生成回复...[/blue]")
    
    try:
        llm = NodeContext.get_llm()
        
        # 构建系统提示
        system_prompt = """你是一个有帮助的个人助理。你可以：
- 回答问题和进行对话
- 记住重要信息（说"记住..."）
- 回忆之前的对话（说"记得..."）
- 管理任务（说"添加任务..."）
- 获取当前时间和天气
- 进行计算

请友好、简洁地回答。"""
        
        # 尝试获取用户记忆上下文
        try:
            memory = MemorySystemFactory.for_user(user_id)
            
            # 获取最后一条用户消息
            last_user_msg = None
            for m in reversed(messages):
                if m.role == "user":
                    last_user_msg = m.content
                    break
            
            # 获取相关记忆
            if last_user_msg:
                memory_context = memory.get_relevant_memories_for_input(last_user_msg)
                if memory_context:
                    system_prompt += f"\n\n{memory_context}"
            
            memory.close()
        except Exception as e:
            logger.warning(f"获取记忆上下文失败: {e}")
        
        # 构建消息历史
        llm_messages = [LLMMessage(role="system", content=system_prompt)]
        
        # 添加最近的消息（保留最近10条）
        for msg in messages[-10:]:
            llm_messages.append(LLMMessage(role=msg.role, content=msg.content))
        
        # 调用 LLM
        response = await llm.chat(llm_messages)
        content = response.get("content", "")
        
        state["messages"].append(Message(
            role="assistant",
            content=content or "我在听，请继续说。"
        ))
        
    except Exception as e:
        logger.error(f"生成回复失败: {e}")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，我暂时无法处理这个请求。"
        ))
    
    state["next_node"] = "end"
    return state


def end_node(state: AssistantState) -> AssistantState:
    """结束节点"""
    state["should_continue"] = False
    return state
