#!/usr/bin/env python3
"""
工作流测试 - 测试数据库版本的工作流
"""

import asyncio
import uuid
from dotenv import load_dotenv

load_dotenv()


async def test_workflow():
    """测试工作流"""
    print("=" * 60)
    print("🤖 工作流测试（数据库版本）")
    print("=" * 60)
    
    from src.graph.workflow_db import build_app
    from src.state.state import AssistantState, Message
    from src.db.memory_system import MemorySystemFactory
    from src.db.repository import AuthService
    from src.db.models import db_manager
    
    # 创建测试用户
    session = db_manager.get_session()
    try:
        user = AuthService.create_user(session, f"workflow_test_{uuid.uuid4().hex[:6]}", "password")
        user_id = user.id
        print(f"✅ 测试用户创建: {user.username}")
    except Exception as e:
        print(f"使用匿名用户: {e}")
        user_id = "anonymous"
    finally:
        session.close()
    
    # 构建应用
    app = build_app()
    
    # 测试用例
    test_cases = [
        {
            "name": "基础对话",
            "input": "你好，请介绍一下你自己",
        },
        {
            "name": "存储记忆",
            "input": "请记住我喜欢 Python 编程",
        },
        {
            "name": "检索记忆",
            "input": "我喜欢什么编程语言？",
        },
        {
            "name": "创建任务",
            "input": "添加一个任务：学习 FastAPI",
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📌 测试 {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*60}")
        print(f"👤 用户: {test['input']}")
        
        # 创建状态
        state = AssistantState(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            messages=[Message(role="user", content=test['input'])],
            should_continue=True
        )
        
        try:
            # 运行工作流
            result = app.invoke(state, config={"configurable": {"thread_id": f"test-{i}"}})
            
            # 获取回复
            messages = result.get("messages", [])
            assistant_msgs = [m for m in messages if m.role == "assistant"]
            
            if assistant_msgs:
                reply = assistant_msgs[-1].content
                print(f"🤖 助理: {reply[:150]}{'...' if len(reply) > 150 else ''}")
                print("✅ 测试通过")
            else:
                print("⚠️ 无助理回复")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 显示用户统计
    try:
        memory = MemorySystemFactory.for_user(user_id)
        stats = memory.get_stats()
        print(f"\n{'='*60}")
        print("📊 用户统计")
        print(f"{'='*60}")
        print(f"会话数: {stats['sessions']}")
        print(f"记忆数: {stats['memories']}")
        print(f"任务数: {stats['tasks']['total']}")
        memory.close()
    except Exception as e:
        print(f"获取统计失败: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 工作流测试完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_workflow())
