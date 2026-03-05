#!/usr/bin/env python3
"""简单测试脚本 - 测试个人助理核心功能"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试 1: LLM 客户端
async def test_llm():
    """测试 LLM 客户端"""
    print("🧪 测试 1: LLM 客户端")
    print("-" * 40)

    try:
        from src.llm import create_llm_from_env, Message

        llm = create_llm_from_env()
        print(f"✅ LLM 客户端创建成功")
        print(f"   模型: {llm.config.model}")
        print(f"   提供商: {llm.config.provider.value}")

        # 简单对话测试
        messages = [
            Message(role="system", content="你是一个友好的助手，用简短的话回答。"),
            Message(role="user", content="你好，请介绍一下自己")
        ]

        print("\n💬 发送测试消息...")
        response = await llm.chat(messages)

        print(f"✅ 收到回复:")
        print(f"   {response.get('content', '无内容')[:100]}...")

        if response.get('usage'):
            usage = response['usage']
            print(f"\n📊 Token 使用: {usage.get('total_tokens', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# 测试 2: 工具集
async def test_tools():
    """测试工具集"""
    print("\n🧪 测试 2: 工具集")
    print("-" * 40)

    try:
        from src.tools.tools import execute_tool, list_tools

        print(f"可用工具: {', '.join(list_tools())}")

        # 测试时间工具
        result = await execute_tool("get_current_time")
        print(f"\n⏰ 时间工具:")
        print(f"   {result.message}")

        # 测试计算器
        result = await execute_tool("calculator", expression="2 + 3 * 4")
        print(f"\n🧮 计算器:")
        print(f"   2 + 3 * 4 = {result.data.get('result') if result.success else '错误'}")

        # 测试任务管理
        result = await execute_tool("manage_task", action="create", title="测试任务", priority="high")
        print(f"\n📋 任务管理:")
        print(f"   {result.message}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# 测试 3: 完整工作流
async def test_workflow():
    """测试完整工作流"""
    print("\n🧪 测试 3: 完整工作流")
    print("-" * 40)

    try:
        from src.graph.workflow import build_app
        from src.state.state import AssistantState, Message

        app = build_app()
        print("✅ 工作流构建成功")

        # 创建测试状态
        state = AssistantState(
            session_id="test-session",
            user_id="test-user",
            messages=[
                Message(role="user", content="你好，现在几点了？")
            ],
            should_continue=True
        )

        print("\n🚀 运行工作流...")
        result = app.invoke(state, config={"configurable": {"thread_id": "test-thread"}})

        # 获取回复
        messages = result.get("messages", [])
        assistant_msgs = [m for m in messages if m.role == "assistant"]

        if assistant_msgs:
            print(f"✅ 助手回复:")
            print(f"   {assistant_msgs[-1].content[:150]}...")
        else:
            print("⚠️ 无助手回复")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 50)
    print("🤖 个人助理功能测试")
    print("=" * 50)

    results = []

    # 运行测试
    results.append(("LLM 客户端", await test_llm()))
    results.append(("工具集", await test_tools()))
    results.append(("完整工作流", await test_workflow()))

    # 汇总
    print("\n" + "=" * 50)
    print("📋 测试结果汇总")
    print("=" * 50)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 项通过")


if __name__ == "__main__":
    asyncio.run(main())
