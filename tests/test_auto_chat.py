#!/usr/bin/env python3
"""自动对话测试 - 测试各种场景"""

import asyncio
from dotenv import load_dotenv

load_dotenv()


async def test_conversation():
    """测试各种对话场景"""
    print("=" * 60)
    print("🤖 个人助理 - 自动对话测试")
    print("=" * 60)

    from src.llm import create_llm_from_env, Message
    from src.tools.tools import execute_tool, get_tool_schemas
    import json

    llm = create_llm_from_env()
    tools = get_tool_schemas()

    test_cases = [
        {
            "name": "基础对话",
            "input": "你好，请介绍一下你自己",
            "expect_tool": False
        },
        {
            "name": "获取时间",
            "input": "现在几点了？",
            "expect_tool": True
        },
        {
            "name": "数学计算",
            "input": "帮我算一下 15 * 23 + 100 等于多少",
            "expect_tool": True
        },
        {
            "name": "创建任务",
            "input": "帮我添加一个任务：今晚学习 Python，优先级高",
            "expect_tool": True
        }
    ]

    system_prompt = """你是一个有用的个人助理，可以回答问题、使用工具获取信息、管理任务等。
可用工具：get_current_time, calculator, manage_task
请简洁友好地回答。"""

    messages = [Message(role="system", content=system_prompt)]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📌 测试 {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*60}")
        print(f"👤 用户: {test['input']}")

        messages.append(Message(role="user", content=test['input']))

        try:
            response = await llm.chat(messages, tools=tools)
            content = response.get("content", "")
            tool_calls = response.get("tool_calls")

            # 处理工具调用
            if tool_calls:
                print(f"🔧 检测到工具调用: {[tc.function.name for tc in tool_calls]}")

                messages.append(Message(
                    role="assistant",
                    content=content or "",
                    tool_calls=[{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                ))

                for tc in tool_calls:
                    result = await execute_tool(tc.function.name, **json.loads(tc.function.arguments))
                    messages.append(Message(
                        role="tool",
                        tool_call_id=tc.id,
                        content=result.to_string()
                    ))

                final = await llm.chat(messages)
                content = final.get("content", "")

            print(f"🤖 助理: {content[:200]}{'...' if len(content) > 200 else ''}")
            messages.append(Message(role="assistant", content=content))

            # 检查结果
            if test['expect_tool'] and not tool_calls:
                print("⚠️ 警告: 期望使用工具但未调用")
            elif not test['expect_tool'] and tool_calls:
                print("⚠️ 警告: 未期望使用工具但调用了")
            else:
                print("✅ 测试通过")

        except Exception as e:
            print(f"❌ 错误: {e}")

    print(f"\n{'='*60}")
    print("🎉 所有测试完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_conversation())
