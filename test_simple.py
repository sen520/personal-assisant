#!/usr/bin/env python3
"""简化测试 - 测试工具和基础功能"""

import asyncio
from dotenv import load_dotenv

from src.llm import create_llm_from_env, Message
from src.tools.tools import execute_tool, list_tools

load_dotenv()


async def main():
    """主测试函数"""
    print("=" * 50)
    print("🤖 个人助理功能测试")
    print("=" * 50)

    # 测试 1: 工具集
    print("\n🧪 测试 1: 工具集")
    print("-" * 40)

    tools = list_tools()
    print(f"可用工具: {', '.join(tools)}")

    # 时间工具
    result = await execute_tool("get_current_time", timezone="Asia/Shanghai")
    print(f"\n⏰ 当前时间 (上海):")
    print(f"   {result.message}")

    # 计算器
    result = await execute_tool("calculator", expression="sqrt(16) + pow(2, 3)")
    print(f"\n🧮 计算 sqrt(16) + 2^3:")
    result_value = result.data.get("result")
    print(f"   = {result_value}")

    # 任务管理
    result = await execute_tool("manage_task", action="create", title="买咖啡", priority="high")
    print(f"\n📋 创建任务:")
    print(f"   {result.message}")

    result = await execute_tool("manage_task", action="list")
    print(f"\n📋 任务列表:")
    for task in result.data:
        title = task["title"]
        priority = task["priority"]
        print(f"   • {title} ({priority})")

    # 记忆存储（模拟模式）
    result = await execute_tool("store_memory", content="用户喜欢喝咖啡", category="preference")
    print(f"\n💾 存储记忆:")
    print(f"   {result.message}")

    # 测试 2: LLM 配置检查
    print(f"\n🧪 测试 2: LLM 配置")
    print("-" * 40)

    llm = create_llm_from_env()
    print("✅ LLM 配置加载成功")
    provider = llm.config.provider.value
    model = llm.config.model
    api_status = "已配置" if llm.config.api_key else "未配置"
    print(f"   提供商: {provider}")
    print(f"   模型: {model}")
    print(f"   API Key: {api_status}")

    # 尝试调用（可能失败如果 key 无效）
    try:
        messages = [
            Message(role="system", content="用一句话回答。"),
            Message(role="user", content="你好")
        ]
        response = await llm.chat(messages)
        content = response.get("content", "无内容")
        print(f"\n💬 LLM 响应:")
        print(f"   {content}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ LLM 调用失败: {e}")
        print("   请检查 API Key 是否有效")

    print("\n" + "=" * 50)
    print("✅ 工具集测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
