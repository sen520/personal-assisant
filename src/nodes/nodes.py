"""
节点定义 - 个人助理的核心功能节点
"""

import json
from typing import Dict, Any
from datetime import datetime
from rich.console import Console

from ..state.state import AssistantState, Message
from ..llm import create_llm_from_env, Message as LLMMessage
from ..tools.tools import tool_registry, execute_tool

console = Console()


class NodeContext:
    """节点上下文，保存共享资源"""
    llm = None

    @classmethod
    def get_llm(cls):
        if cls.llm is None:
            cls.llm = create_llm_from_env()
        return cls.llm


def user_input_node(state: AssistantState) -> AssistantState:
    """
    用户输入节点

    接收用户输入并进行初步处理
    """
    # 这里在实际运行时会从外部获取输入
    # 现在只是状态传递
    return state


async def intent_analysis_node(state: AssistantState) -> AssistantState:
    """
    意图分析节点 - 使用 LLM 进行意图识别

    分析用户意图，决定下一步操作
    """
    messages = state.get("messages", [])
    if not messages:
        state["next_node"] = "generate_response"
        return state

    last_message = messages[-1]
    if last_message.role != "user":
        state["next_node"] = "generate_response"
        return state

    try:
        llm = NodeContext.get_llm()

        # 构建意图分析提示
        system_prompt = """你是一个意图分析助手。分析用户输入的意图，并返回以下类别之一：
- store_memory: 用户要求记住/保存某些信息
- retrieve_memory: 用户询问过去的记忆或信息
- task_manager: 用户提到任务、待办事项、计划
- search: 用户需要搜索网络信息
- general: 一般对话或问答

只返回类别名称，不要其他内容。"""

        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=last_message.content)
        ]

        response = await llm.chat(llm_messages)
        intent = response.get("content", "general").strip().lower()

        # 映射到节点名称
        intent_map = {
            "store_memory": "store_memory",
            "retrieve_memory": "retrieve_memory",
            "task_manager": "task_manager",
            "search": "search",
            "general": "generate_response"
        }

        state["next_node"] = intent_map.get(intent, "generate_response")
        state["intent"] = intent

        console.print(f"[dim]🎯 意图识别: {intent} -> {state['next_node']}[/dim]")

    except Exception as e:
        console.print(f"[yellow]⚠️ 意图分析失败: {e}，使用默认路由[/yellow]")
        state["next_node"] = "generate_response"

    return state


async def store_memory_node(state: AssistantState) -> AssistantState:
    """
    存储记忆节点

    将重要信息存储到长期记忆
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    if not last_user_msg:
        return state

    console.print("[blue]💾 正在存储记忆...[/blue]")

    try:
        # 提取要记忆的内容
        llm = NodeContext.get_llm()

        system_prompt = """从用户输入中提取需要记住的核心信息，以简洁的句子返回。
例如：
用户："请记住我的生日是3月15日"
返回："用户的生日是3月15日"

用户："我叫张三，是一名程序员"
返回："用户名叫张三，职业是程序员"""

        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=last_user_msg)
        ]

        response = await llm.chat(llm_messages)
        content_to_store = response.get("content", last_user_msg)

        # 执行存储工具
        await execute_tool("store_memory", content=content_to_store, category="personal")

        state["messages"].append(Message(
            role="assistant",
            content=f"好的，我已经记住了：{content_to_store}"
        ))

    except Exception as e:
        console.print(f"[red]❌ 存储记忆失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，我没能记住这个信息。"
        ))

    state["next_node"] = "end"
    return state


async def retrieve_memory_node(state: AssistantState) -> AssistantState:
    """
    检索记忆节点

    从长期记忆中检索相关信息
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    if not last_user_msg:
        return state

    console.print("[blue]🔍 正在检索记忆...[/blue]")

    try:
        # 执行检索工具
        result = await execute_tool("retrieve_memory", query=last_user_msg, limit=3)

        if result.success and result.data:
            memories = result.data
            memory_text = "\n".join([f"- {m}" for m in memories])

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
        console.print(f"[red]❌ 检索记忆失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，检索记忆时出错了。"
        ))

    state["next_node"] = "end"
    return state


async def task_manager_node(state: AssistantState) -> AssistantState:
    """
    任务管理节点

    处理任务相关的增删改查
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    if not last_user_msg:
        return state

    console.print("[blue]📋 正在处理任务...[/blue]")

    try:
        llm = NodeContext.get_llm()

        # 判断用户想要做什么操作
        system_prompt = """分析用户的任务管理请求，返回以下格式之一：
- CREATE|任务标题|描述（可选）|优先级（low/medium/high）
- LIST
- COMPLETE|任务ID或关键词

只返回命令，不要其他内容。"""

        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=last_user_msg)
        ]

        response = await llm.chat(llm_messages)
        command = response.get("content", "LIST").strip()

        parts = command.split("|")
        action = parts[0].upper()

        if action == "CREATE" and len(parts) >= 2:
            title = parts[1]
            description = parts[2] if len(parts) > 2 else ""
            priority = parts[3] if len(parts) > 3 else "medium"
            result = await execute_tool("manage_task", action="create", title=title, description=description, priority=priority)
            reply = f"已创建任务：{title}" if result.success else f"创建失败：{result.message}"

        elif action == "LIST":
            result = await execute_tool("manage_task", action="list")
            if result.success and result.data:
                tasks = result.data
                task_list = "\n".join([f"• {t['title']} ({t['status']})" for t in tasks])
                reply = f"你的任务列表：\n{task_list}"
            else:
                reply = "当前没有任务。"

        elif action == "COMPLETE":
            # 简化处理，标记最后一个任务为完成
            result = await execute_tool("manage_task", action="list")
            if result.success and result.data:
                task_id = result.data[-1].get("id")
                result = await execute_tool("manage_task", action="complete", task_id=task_id)
                reply = "已标记任务为完成。" if result.success else f"操作失败：{result.message}"
            else:
                reply = "没有找到可完成的任务。"
        else:
            reply = "我不太明白你想对任务做什么操作。"

        state["messages"].append(Message(
            role="assistant",
            content=reply
        ))

    except Exception as e:
        console.print(f"[red]❌ 任务管理失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="处理任务时出错了。"
        ))

    state["next_node"] = "end"
    return state


async def search_node(state: AssistantState) -> AssistantState:
    """
    搜索节点

    执行信息检索
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last_user_msg = None
    for m in reversed(messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    if not last_user_msg:
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
                for i, r in enumerate(results)
            ])

            reply = f"搜索结果：\n\n{search_summary}"
        else:
            reply = f"搜索完成，但没有找到相关结果。\n（{result.message}）"

        state["messages"].append(Message(
            role="assistant",
            content=reply
        ))

    except Exception as e:
        console.print(f"[red]❌ 搜索失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="搜索功能暂时不可用。"
        ))

    state["next_node"] = "end"
    return state


async def generate_response_node(state: AssistantState) -> AssistantState:
    """
    生成回复节点

    使用 LLM 生成自然语言回复，支持工具调用
    """
    messages = state.get("messages", [])
    if not messages:
        state["next_node"] = "end"
        return state

    console.print("[blue]💬 正在生成回复...[/blue]")

    try:
        llm = NodeContext.get_llm()

        # 构建消息历史
        llm_messages = []
        system_prompt = """你是一个有帮助的个人助理。你可以：
- 回答问题和进行对话
- 记住重要信息（说"记住..."）
- 回忆之前的对话（说"记得..."）
- 管理任务（说"添加任务..."）
- 获取当前时间和天气
- 进行计算

请友好、简洁地回答。"""

        llm_messages.append(LLMMessage(role="system", content=system_prompt))

        # 添加最近的消息（保留最近10条）
        for msg in messages[-10:]:
            llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

        # 获取工具 schemas
        tools = tool_registry.get_schemas()

        # 调用 LLM（带工具支持）
        response = await llm.chat(llm_messages, tools=tools)

        content = response.get("content", "")
        tool_calls = response.get("tool_calls")

        # 处理工具调用
        if tool_calls:
            console.print(f"[dim]🔧 工具调用: {len(tool_calls)} 个[/dim]")

            tool_results = []
            for tc in tool_calls:
                function_name = tc.function.name
                function_args = json.loads(tc.function.arguments)

                result = await execute_tool(function_name, **function_args)
                tool_results.append({
                    "tool": function_name,
                    "result": result.to_string()
                })

            # 将工具结果加入对话
            tool_result_text = "\n".join([f"[{r['tool']}] {r['result']}" for r in tool_results])

            # 再次调用 LLM 生成最终回复
            llm_messages.append(LLMMessage(
                role="assistant",
                content=content or "",
                tool_calls=[{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in tool_calls]
            ))

            for tc, tr in zip(tool_calls, tool_results):
                llm_messages.append(LLMMessage(
                    role="tool",
                    tool_call_id=tc.id,
                    content=tr["result"]
                ))

            final_response = await llm.chat(llm_messages)
            content = final_response.get("content", "")

        state["messages"].append(Message(
            role="assistant",
            content=content or "我在听，请继续说。"
        ))

    except Exception as e:
        console.print(f"[red]❌ 生成回复失败: {e}[/red]")
        state["messages"].append(Message(
            role="assistant",
            content="抱歉，我暂时无法处理这个请求。"
        ))

    state["next_node"] = "end"
    return state


def end_node(state: AssistantState) -> AssistantState:
    """
    结束节点
    """
    state["should_continue"] = False
    return state
