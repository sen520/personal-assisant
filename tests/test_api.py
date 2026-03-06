#!/usr/bin/env python3
"""
API 测试脚本
"""

import pytest
import requests
import json

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def base_url():
    return BASE_URL


class TestHealth:
    """健康检查测试"""
    
    def test_health(self, base_url):
        """测试健康检查"""
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuth:
    """认证测试"""
    
    def test_register(self, base_url):
        """测试用户注册"""
        import uuid
        username = f"test_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{base_url}/api/auth/register",
            json={"username": username, "password": "password123"},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == username


class TestAPIWithAuth:
    """需要认证的 API 测试"""
    
    @pytest.fixture(scope="class")
    def token(self, base_url):
        """获取认证 token"""
        import uuid
        username = f"apitest_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{base_url}/api/auth/register",
            json={"username": username, "password": "password123"},
            timeout=10
        )
        
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_chat(self, base_url, token):
        """测试聊天接口"""
        response = requests.post(
            f"{base_url}/api/chat",
            json={"content": "你好"},
            headers={"Authorization": token},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "assistant_message" in data
        assert "session_id" in data
    
    def test_create_task(self, base_url, token):
        """测试创建任务"""
        response = requests.post(
            f"{base_url}/api/tasks",
            json={"title": "测试任务", "description": "测试", "priority": 3},
            headers={"Authorization": token},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试任务"
        assert "id" in data
    
    def test_list_tasks(self, base_url, token):
        """测试获取任务列表"""
        response = requests.get(
            f"{base_url}/api/tasks",
            headers={"Authorization": token},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
    
    def test_stats(self, base_url, token):
        """测试统计接口"""
        response = requests.get(
            f"{base_url}/api/stats",
            headers={"Authorization": token},
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "memories" in data
        assert "tasks" in data
