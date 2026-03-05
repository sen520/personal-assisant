"""
LangGraph 工作流定义 - 使用数据库版本
"""

import asyncio
import nest_asyncio
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state.state import AssistantState
from ..nodes.nodes_db import (
    user_input_node,
    intent_analysis_node,
    store_memory_node,
    retrieve_memory_node,
    task_manager_node,
    search_node,
    generate_response_node,
    end_node,
)

# 启用 nest_asyncio 支持嵌套 event loop
nest_asyncio.apply()


def create_workflow() -> StateGraph:
    """
    创建工作流图（数据库版本）
    """
    workflow = StateGraph(AssistantState)
    
    # 添加节点
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("intent_analysis", _make_sync(intent_analysis_node))
    workflow.add_node("store_memory", _make_sync(store_memory_node))
    workflow.add_node("retrieve_memory", _make_sync(retrieve_memory_node))
    workflow.add_node("task_manager", _make_sync(task_manager_node))
    workflow.add_node("search", _make_sync(search_node))
    workflow.add_node("generate_response", _make_sync(generate_response_node))
    workflow.add_node("end", end_node)
    
    # 设置入口
    workflow.set_entry_point("user_input")
    
    # 添加边
    workflow.add_edge("user_input", "intent_analysis")
    
    # 条件边
    workflow.add_conditional_edges(
        "intent_analysis",
        lambda state: state.get("next_node", "generate_response"),
        {
            "store_memory": "store_memory",
            "retrieve_memory": "retrieve_memory",
            "task_manager": "task_manager",
            "search": "search",
            "generate_response": "generate_response",
        }
    )
    
    # 结束边
    for node in ["store_memory", "retrieve_memory", "task_manager", "search", "generate_response"]:
        workflow.add_edge(node, "end")
    
    workflow.add_edge("end", END)
    
    return workflow


def _make_sync(async_func):
    """将异步函数包装为同步函数（用于 LangGraph）"""
    def wrapper(state):
        return asyncio.run(async_func(state))
    return wrapper


def build_app(checkpointer=None):
    """
    构建可运行的应用
    
    Args:
        checkpointer: 可选的检查点保存器
    
    Returns:
        可运行的应用
    """
    workflow = create_workflow()
    
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    app = workflow.compile(checkpointer=checkpointer)
    return app
