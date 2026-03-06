#!/usr/bin/env python3
"""
集成测试脚本 - 无需启动服务
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有模块可以正常导入"""
    print("\n🧪 测试 1: 模块导入")
    print("-" * 40)
    
    try:
        from src.config.settings import settings
        print("✅ 配置模块")
        
        from src.db.models import db_manager, User, Task, Memory, Document
        print("✅ 数据库模型")
        
        from src.db.repository import AuthService, UserRepository, TaskRepository
        print("✅ 数据访问层")
        
        from src.db.memory_system import MemorySystemFactory
        print("✅ 记忆系统")
        
        from src.utils.cache import cache_manager
        print("✅ 缓存模块")
        
        from src.utils.vector_store import vector_store
        print("✅ 向量存储")
        
        from src.utils.scheduler import reminder_scheduler
        print("✅ 定时任务")
        
        from src.utils.knowledge_base import KnowledgeBase
        print("✅ 知识库")
        
        from src.utils.model_manager import model_manager
        print("✅ 模型管理")
        
        from src.utils.data_exporter import DataExporter
        print("✅ 数据导出")
        
        from src.utils.admin_service import AdminService
        print("✅ 管理后台")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings():
    """测试配置加载"""
    print("\n🧪 测试 2: 配置加载")
    print("-" * 40)
    
    try:
        from src.config.settings import settings
        
        print(f"项目名: {settings.project_name}")
        print(f"调试模式: {settings.debug}")
        print(f"数据库: {'SQLite' if settings.use_sqlite else 'MySQL'}")
        print(f"LLM 模型: {settings.llm_model}")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_database():
    """测试数据库连接"""
    print("\n🧪 测试 3: 数据库连接")
    print("-" * 40)
    
    try:
        from src.db.models import db_manager
        from src.db.connection import check_database_health
        
        # 初始化数据库
        db_manager.init_engine()
        
        # 检查健康状态
        health = check_database_health()
        print(f"数据库状态: {health['status']}")
        print(f"数据库类型: {health.get('database', 'unknown')}")
        
        return health['status'] == 'healthy'
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False


def test_auth():
    """测试认证服务"""
    print("\n🧪 测试 4: 认证服务")
    print("-" * 40)
    
    try:
        from src.db.models import db_manager
        from src.db.repository import AuthService
        
        session = db_manager.get_session()
        try:
            # 测试密码哈希
            hashed, salt = AuthService._hash_password("test_password")
            print(f"密码哈希: {hashed[:20]}...")
            
            # 验证密码
            is_valid = AuthService.verify_password("test_password", hashed, salt)
            print(f"密码验证: {'通过' if is_valid else '失败'}")
            
            return is_valid
        finally:
            session.close()
    except Exception as e:
        print(f"❌ 认证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """测试模型定义"""
    print("\n🧪 测试 5: 数据模型")
    print("-" * 40)
    
    try:
        from src.db.models import User, Task, Memory, Reminder, Document, DocumentChunk
        
        print(f"✅ User 模型")
        print(f"✅ Task 模型")
        print(f"✅ Memory 模型")
        print(f"✅ Reminder 模型")
        print(f"✅ Document 模型")
        print(f"✅ DocumentChunk 模型")
        
        return True
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False


def test_utils():
    """测试工具函数"""
    print("\n🧪 测试 6: 工具函数")
    print("-" * 40)
    
    try:
        from src.utils.document_parser import DocumentParser, get_file_icon, format_file_size
        
        # 测试文件图标
        icons = [get_file_icon("test.pdf"), get_file_icon("test.docx"), get_file_icon("test.txt")]
        print(f"文件图标: {' '.join(icons)}")
        
        # 测试文件大小格式化
        sizes = [format_file_size(1024), format_file_size(1024*1024), format_file_size(1024*1024*1024)]
        print(f"文件大小: {', '.join(sizes)}")
        
        # 测试支持的文件类型
        supported = DocumentParser.SUPPORTED_EXTENSIONS
        print(f"支持格式: {len(supported)} 种")
        
        return True
    except Exception as e:
        print(f"❌ 工具测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 集成测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("配置加载", test_settings),
        ("数据库连接", test_database),
        ("认证服务", test_auth),
        ("数据模型", test_models),
        ("工具函数", test_utils),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} 异常: {e}")
            results.append((name, False))
    
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
        print("\n🎉 所有集成测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
