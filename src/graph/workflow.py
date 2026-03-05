"""
LangGraph 工作流定义 - 个人助理的核心流程
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state.state import AssistantState
from ..nodes.nodes import (
    user_input_node,
    intent_analysis_node,
    store_memory_node,
    retrieve_memory_node,
    task_manager_node,
    search_node,
    generate_response_node,
    end_node,
)


def create_workflow() -> StateGraph:
    """
    创建工作流图
    """
    # 初始化状态图
    workflow = StateGraph(AssistantState)
    
    # 添加节点
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("intent_analysis", intent_analysis_node)
    workflow.add_node("store_memory", store_memory_node)
    workflow.add_node("retrieve_memory", retrieve_memory_node)
    workflow.add_node("task_manager", task_manager_node)
    workflow.add_node("search", search_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("end", end_node)
    
    # 设置入口
    workflow.set_entry_point("user_input")
    
    # 添加边
    workflow.add_edge("user_input", "intent_analysis")
    
    # 条件边：根据意图分析结果路由到不同节点
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
    
    # 所有功能节点都指向结束
    workflow.add_edge("store_memory", "end")
    workflow.add_edge("retrieve_memory", "end")
    workflow.add_edge("task_manager", "end")
    workflow.add_edge("search", "end")
    workflow.add_edge("generate_response", "end")
    
    # 结束节点
    workflow.add_edge("end", END)
    
    return workflow


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