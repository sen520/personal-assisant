#!/usr/bin/env python3
"""交互式测试 - 测试完整对话流程"""

import asyncio
from dotenv import load_dotenv

load_dotenv()


async def chat_test():
    """测试对话功能"""
    print("=" * 60)
    print("🤖 个人助理 - 交互式测试")
    print("=" * 60)
    print("\n输入 'quit' 或 'exit' 退出\n")

    from src.llm import create_llm_from_env, Message
    from src.tools.tools import execute_tool

    llm = create_llm_from_env()

    # 系统提示
    system_prompt = """你是一个有用的个人助理。你可以：
1. 回答问题和聊天
2. 使用工具获取时间、计算、管理任务等
3. 记住重要信息

当前可用工具：
- get_current_time: 获取当前时间
- calculator: 计算器
- manage_task: 任务管理
- store_memory: 存储记忆

请友好、简洁地回答。"""

    messages = [Message(role="system", content=system_prompt)]

    while True:
        user_input = input("\n👤 你: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        # 添加用户消息
        messages.append(Message(role="user", content=user_input))

        try:
            # 调用 LLM
            import json
            from src.tools.tools import get_tool_schemas

            tools = get_tool_schemas()
            response = await llm.chat(messages, tools=tools)

            content = response.get("content", "")
            tool_calls = response.get("tool_calls")

            # 处理工具调用
            if tool_calls:
                print(f"🔧 调用工具: {len(tool_calls)} 个")

                # 添加助手消息（带工具调用）
                messages.append(Message(
                    role="assistant",
                    content=content or "",
                    tool_calls=[{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                ))

                # 执行工具并添加结果
                for tc in tool_calls:
                    func_name = tc.function.name
                    func_args = json.loads(tc.function.arguments)

                    result = await execute_tool(func_name, **func_args)

                    messages.append(Message(
                        role="tool",
                        tool_call_id=tc.id,
                        content=result.to_string()
                    ))

                # 再次调用获取最终回复
                final_response = await llm.chat(messages)
                content = final_response.get("content", "")

            print(f"\n🤖 助理: {content}")

            # 添加助手回复到历史
            messages.append(Message(role="assistant", content=content))

            # 限制历史长度
            if len(messages) > 20:
                messages = [messages[0]] + messages[-18:]

        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(chat_test())
