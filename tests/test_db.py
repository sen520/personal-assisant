#!/usr/bin/env python3
"""
数据库测试脚本 - 测试 MySQL 记忆系统
"""

import sys
from datetime import datetime

# 测试数据库连接
def test_connection():
    """测试数据库连接"""
    print("🧪 测试 1: 数据库连接")
    print("-" * 40)
    
    try:
        from src.db.memory_system import MemorySystemFactory
        
        # 初始化数据库
        MemorySystemFactory.init_database()
        print("✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   请确保 MySQL 已启动: docker-compose up -d mysql")
        return False


def test_user_operations():
    """测试用户操作"""
    print("\n🧪 测试 2: 用户操作")
    print("-" * 40)
    
    from src.db.models import db_manager
    from src.db.repository import AuthService
    
    session = db_manager.get_session()
    
    try:
        # 创建测试用户
        username = f"test_user_{datetime.now().strftime('%H%M%S')}"
        user = AuthService.create_user(session, username, "password123")
        print(f"✅ 用户创建成功: {user.username} (ID: {user.id})")
        
        # 认证测试
        auth_user = AuthService.authenticate(session, username, "password123")
        if auth_user:
            print(f"✅ 用户认证成功")
        else:
            print("❌ 用户认证失败")
        
        return user.id
    except Exception as e:
        print(f"❌ 用户操作失败: {e}")
        return None
    finally:
        session.close()


def test_memory_system(user_id: str):
    """测试记忆系统"""
    print(f"\n🧪 测试 3: 记忆系统 [用户: {user_id[:8]}...]")
    print("-" * 40)
    
    from src.db.memory_system import MemorySystemFactory
    
    try:
        memory = MemorySystemFactory.for_user(user_id)
        
        # 测试会话
        session_id = memory.create_session("测试会话")
        print(f"✅ 会话创建成功: {session_id[:8]}...")
        
        # 测试消息
        memory.add_message(session_id, "user", "你好，请记住我喜欢 Python")
        memory.add_message(session_id, "assistant", "好的，我记住了您喜欢 Python")
        print("✅ 消息添加成功")
        
        # 测试记忆存储
        memory_id = memory.remember(
            content="用户喜欢 Python 编程语言",
            category="preference",
            importance=4
        )
        print(f"✅ 记忆存储成功: {memory_id[:8]}...")
        
        # 测试记忆检索
        memories = memory.recall(query="Python", limit=5)
        print(f"✅ 记忆检索成功: 找到 {len(memories)} 条")
        for m in memories:
            print(f"   - [{m.category}] {m.content[:40]}...")
        
        # 测试任务
        task_id = memory.create_task(
            title="学习 FastAPI",
            description="学习使用 FastAPI 构建 API",
            priority=4
        )
        print(f"✅ 任务创建成功: {task_id[:8]}...")
        
        tasks = memory.list_tasks()
        print(f"✅ 任务列表: {len(tasks)} 个任务")
        
        # 获取统计
        stats = memory.get_stats()
        print(f"\n📊 用户统计:")
        print(f"   会话数: {stats['sessions']}")
        print(f"   记忆数: {stats['memories']}")
        print(f"   任务数: {stats['tasks']['total']}")
        
        memory.close()
        return True
        
    except Exception as e:
        print(f"❌ 记忆系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_user_isolation():
    """测试多用户数据隔离"""
    print("\n🧪 测试 4: 多用户数据隔离")
    print("-" * 40)
    
    from src.db.memory_system import MemorySystemFactory
    from src.db.models import db_manager
    from src.db.repository import AuthService
    
    session = db_manager.get_session()
    
    try:
        # 创建两个用户
        user1 = AuthService.create_user(session, f"user_a_{datetime.now().strftime('%S')}", "pass")
        user2 = AuthService.create_user(session, f"user_b_{datetime.now().strftime('%S')}", "pass")
        
        print(f"✅ 创建用户 A: {user1.username}")
        print(f"✅ 创建用户 B: {user2.username}")
        
        session.close()
        
        # 用户 A 存储记忆
        mem_a = MemorySystemFactory.for_user(user1.id)
        mem_a.remember("用户 A 的秘密", category="fact", importance=5)
        
        # 用户 B 存储记忆
        mem_b = MemorySystemFactory.for_user(user2.id)
        mem_b.remember("用户 B 的秘密", category="fact", importance=5)
        
        # 检查隔离
        memories_a = mem_a.recall(query="秘密")
        memories_b = mem_b.recall(query="秘密")
        
        print(f"\n用户 A 的记忆: {len(memories_a)} 条")
        for m in memories_a:
            print(f"   - {m.content}")
        
        print(f"用户 B 的记忆: {len(memories_b)} 条")
        for m in memories_b:
            print(f"   - {m.content}")
        
        # 验证隔离
        if len(memories_a) == 1 and "用户 A" in memories_a[0].content:
            print("\n✅ 数据隔离验证通过")
        else:
            print("\n❌ 数据隔离验证失败")
        
        mem_a.close()
        mem_b.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 隔离测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🗄️  MySQL 数据库测试")
    print("=" * 60)
    
    # 检查依赖
    try:
        import pymysql
    except ImportError:
        print("\n❌ 缺少 pymysql，正在安装...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pymysql"], check=True)
        print("✅ pymysql 安装完成")
    
    # 运行测试
    results = []
    
    # 测试 1: 连接
    if not test_connection():
        print("\n❌ 数据库连接失败，终止测试")
        return
    
    # 测试 2: 用户操作
    user_id = test_user_operations()
    results.append(("用户操作", user_id is not None))
    
    # 测试 3: 记忆系统
    if user_id:
        memory_ok = test_memory_system(user_id)
        results.append(("记忆系统", memory_ok))
    
    # 测试 4: 数据隔离
    isolation_ok = test_multi_user_isolation()
    results.append(("数据隔离", isolation_ok))
    
    # 汇总
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！数据库已就绪")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")


if __name__ == "__main__":
    main()
