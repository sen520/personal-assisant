#!/usr/bin/env python3
"""
个人助理 - 主入口

启动 API 服务: python main.py
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import start_server


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║   🤖 Personal Assistant API                               ║
    ║                                                            ║
    ║   访问: http://localhost:8000                             ║
    ║   文档: http://localhost:8000/docs                        ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    start_server(host="0.0.0.0", port=8000)
