#!/usr/bin/env python3
"""
API 测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("\n🧪 测试 1: 健康检查")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务正常: {response.json()}")
            return True
        else:
            print(f"❌ 状态码错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print("   请确保服务已启动: python -m src.api.main")
        return False


def test_register():
    """测试用户注册"""
    print("\n🧪 测试 2: 用户注册")
    print("-" * 40)
    
    import uuid
    username = f"api_test_{uuid.uuid4().hex[:6]}"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "password123"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 注册成功")
            print(f"   用户: {data['username']}")
            print(f"   Token: {data['access_token'][:20]}...")
            return data["access_token"]
        else:
            print(f"❌ 注册失败: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_chat(token: str):
    """测试聊天接口"""
    print("\n🧪 测试 3: 聊天接口")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"content": "你好，请介绍一下自己"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 聊天成功")
            print(f"   用户: {data['user_message']['content'][:30]}...")
            print(f"   助理: {data['assistant_message']['content'][:50]}...")
            print(f"   会话ID: {data['session_id'][:8]}...")
            return data["session_id"]
        else:
            print(f"❌ 聊天失败: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_create_task(token: str):
    """测试创建任务"""
    print("\n🧪 测试 4: 创建任务")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            json={"title": "测试任务", "description": "这是一个测试任务", "priority": 4},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务创建成功")
            print(f"   标题: {data['title']}")
            print(f"   ID: {data['id'][:8]}...")
            return data["id"]
        else:
            print(f"❌ 创建失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_list_tasks(token: str):
    """测试获取任务列表"""
    print("\n🧪 测试 5: 任务列表")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取成功: {data['total']} 个任务")
            for task in data['tasks'][:3]:
                print(f"   • {task['title']} ({task['status']})")
            return True
        else:
            print(f"❌ 获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_stats(token: str):
    """测试统计接口"""
    print("\n🧪 测试 6: 用户统计")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计获取成功")
            print(f"   会话: {data['sessions']}")
            print(f"   记忆: {data['memories']}")
            print(f"   任务: {data['tasks']['total']}")
            return True
        else:
            print(f"❌ 获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🌐 API 测试")
    print("=" * 60)
    
    # 测试 1: 健康检查
    if not test_health():
        print("\n❌ 服务未启动，终止测试")
        print("请运行: python -m src.api.main")
        return
    
    # 测试 2: 注册
    token = test_register()
    if not token:
        print("\n❌ 注册失败，终止测试")
        return
    
    results = [("注册", True)]
    
    # 测试 3: 聊天
    session_id = test_chat(token)
    results.append(("聊天", session_id is not None))
    
    # 测试 4: 创建任务
    task_id = test_create_task(token)
    results.append(("创建任务", task_id is not None))
    
    # 测试 5: 任务列表
    list_ok = test_list_tasks(token)
    results.append(("任务列表", list_ok))
    
    # 测试 6: 统计
    stats_ok = test_stats(token)
    results.append(("统计", stats_ok))
    
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
        print("\n🎉 所有 API 测试通过！")
    else:
        print("\n⚠️ 部分测试失败")


if __name__ == "__main__":
    main()
