#!/usr/bin/env python3
"""
个人助理 - 主入口

基于 LangGraph 的个人智能助理系统
"""

import uuid
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.graph.workflow import build_app
from src.state.state import AssistantState, Message
from src.config.settings import settings

console = Console()


def print_banner():
    """打印欢迎信息"""
    banner = Text()
    banner.append("🤖 ", style="bold blue")
    banner.append("Personal Assistant\n", style="bold cyan")
    banner.append("基于 LangGraph 的个人智能助理", style="dim")
    
    console.print(Panel(banner, border_style="blue"))
    console.print()


def create_initial_state(user_input: str, session_id: Optional[str] = None) -> AssistantState:
    """创建初始状态"""
    return AssistantState(
        session_id=session_id or str(uuid.uuid4()),
        user_id="default_user",
        messages=[Message(role="user", content=user_input)],
        current_task=None,
        task_queue=[],
        completed_tasks=[],
        retrieved_memories=[],
        tool_calls=[],
        tool_results=[],
        next_node=None,
        iteration_count=0,
        should_continue=True,
        error=None,
        metadata={}
    )


def chat_loop():
    """交互式对话循环"""
    print_banner()
    
    # 构建应用
    app = build_app()
    
    session_id = str(uuid.uuid4())
    
    console.print("[dim]输入 'quit' 或 'exit' 退出\n[/dim]")
    
    while True:
        # 获取用户输入
        user_input = console.input("[bold green]You:[/bold green] ").strip()
        
        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("\n[dim]再见！[/dim]")
            break
        
        if not user_input:
            continue
        
        # 创建初始状态
        state = create_initial_state(user_input, session_id)
        
        # 运行工作流
        try:
            result = app.invoke(state)
            
            # 获取助手回复
            messages = result.get("messages", [])
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            if assistant_messages:
                last_response = assistant_messages[-1].content
                console.print(f"[bold blue]Assistant:[/bold blue] {last_response}\n")
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}\n")


def main():
    """主函数"""
    try:
        chat_loop()
    except KeyboardInterrupt:
        console.print("\n\n[dim]已中断[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]发生错误:[/bold red] {e}")


if __name__ == "__main__":
    main()