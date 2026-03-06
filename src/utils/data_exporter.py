"""
数据导出服务
支持导出会话、记忆、任务为 PDF/Markdown/JSON
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO

from ..utils.logging import get_logger
from ..db.models import db_manager
from ..db.memory_system import MemorySystemFactory

logger = get_logger(__name__)


class DataExporter:
    """数据导出器"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    # =========================================================================
    # 导出会话
    # =========================================================================
    
    def export_session(
        self,
        session_id: str,
        format: str = "markdown"
    ) -> bytes:
        """
        导出单个会话
        
        Args:
            session_id: 会话 ID
            format: 导出格式 (markdown, pdf, json)
        
        Returns:
            文件内容 (bytes)
        """
        memory = MemorySystemFactory.for_user(self.user_id)
        try:
            # 获取会话消息
            messages = memory.get_session_messages(session_id, limit=1000)
            
            if format == "markdown":
                return self._session_to_markdown(session_id, messages)
            elif format == "pdf":
                return self._session_to_pdf(session_id, messages)
            elif format == "json":
                return self._session_to_json(session_id, messages)
            else:
                raise ValueError(f"不支持的格式: {format}")
                
        finally:
            memory.close()
    
    def export_all_sessions(self, format: str = "json") -> bytes:
        """导出所有会话"""
        memory = MemorySystemFactory.for_user(self.user_id)
        try:
            sessions = memory.list_sessions(limit=1000)
            
            data = {
                "user_id": self.user_id,
                "export_time": datetime.now().isoformat(),
                "sessions": []
            }
            
            for session in sessions:
                session_id = session["id"]
                messages = memory.get_session_messages(session_id, limit=1000)
                data["sessions"].append({
                    "session": session,
                    "messages": [
                        {
                            "role": m.role,
                            "content": m.content,
                            "timestamp": m.timestamp.isoformat()
                        }
                        for m in messages
                    ]
                })
            
            return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            
        finally:
            memory.close()
    
    def _session_to_markdown(self, session_id: str, messages: List[Any]) -> bytes:
        """会话转 Markdown"""
        lines = [
            "# 💬 会话记录",
            "",
            f"- **会话 ID**: {session_id}",
            f"- **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **消息数**: {len(messages)}",
            "",
            "---",
            ""
        ]
        
        for msg in messages:
            role_icon = "👤" if msg.role == "user" else "🤖"
            role_name = "用户" if msg.role == "user" else "助手"
            time_str = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            lines.append(f"## {role_icon} {role_name} ({time_str})")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines).encode('utf-8')
    
    def _session_to_pdf(self, session_id: str, messages: List[Any]) -> bytes:
        """会话转 PDF"""
        try:
            from fpdf import FPDF
        except ImportError:
            raise ImportError("请安装 fpdf2: pip install fpdf2")
        
        pdf = FPDF()
        pdf.add_page()
        
        # 设置中文字体（需要系统中存在）
        try:
            pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
            pdf.set_font('DejaVu', '', 12)
        except:
            pdf.set_font('Arial', '', 12)
        
        # 标题
        pdf.set_font_size(16)
        pdf.cell(0, 10, 'Session Export', ln=True)
        pdf.set_font_size(10)
        pdf.cell(0, 5, f'Session ID: {session_id}', ln=True)
        pdf.cell(0, 5, f'Export Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True)
        pdf.cell(0, 5, f'Messages: {len(messages)}', ln=True)
        pdf.ln(10)
        
        # 消息内容
        for msg in messages:
            role_name = "User" if msg.role == "user" else "Assistant"
            time_str = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            pdf.set_font_size(11)
            pdf.cell(0, 8, f'{role_name} ({time_str}):', ln=True)
            pdf.set_font_size(10)
            
            # 处理长文本换行
            content = msg.content.replace('\n', ' ')
            pdf.multi_cell(0, 5, content)
            pdf.ln(5)
        
        return pdf.output(dest='S').encode('latin-1') if isinstance(pdf.output(dest='S'), str) else pdf.output(dest='S')
    
    def _session_to_json(self, session_id: str, messages: List[Any]) -> bytes:
        """会话转 JSON"""
        data = {
            "session_id": session_id,
            "user_id": self.user_id,
            "export_time": datetime.now().isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    # =========================================================================
    # 导出记忆
    # =========================================================================
    
    def export_memories(self, format: str = "markdown") -> bytes:
        """
        导出所有记忆
        
        Args:
            format: 导出格式 (markdown, json)
        """
        memory = MemorySystemFactory.for_user(self.user_id)
        try:
            memories = memory.recall(limit=1000)
            
            if format == "markdown":
                return self._memories_to_markdown(memories)
            elif format == "json":
                return self._memories_to_json(memories)
            else:
                raise ValueError(f"不支持的格式: {format}")
                
        finally:
            memory.close()
    
    def _memories_to_markdown(self, memories: List[Any]) -> bytes:
        """记忆转 Markdown"""
        lines = [
            "# 🧠 记忆导出",
            "",
            f"- **用户 ID**: {self.user_id}",
            f"- **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **记忆数**: {len(memories)}",
            "",
            "---",
            ""
        ]
        
        category_icons = {
            "fact": "📚",
            "preference": "❤️",
            "task": "✅",
            "general": "📝"
        }
        
        for mem in memories:
            icon = category_icons.get(mem.category, "📝")
            time_str = mem.created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            lines.append(f"## {icon} {mem.category.upper()}")
            lines.append("")
            lines.append(f"**重要性**: {'⭐' * mem.importance}")
            lines.append(f"**创建时间**: {time_str}")
            lines.append("")
            lines.append(mem.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines).encode('utf-8')
    
    def _memories_to_json(self, memories: List[Any]) -> bytes:
        """记忆转 JSON"""
        data = {
            "user_id": self.user_id,
            "export_time": datetime.now().isoformat(),
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "category": m.category,
                    "importance": m.importance,
                    "created_at": m.created_at.isoformat(),
                    "access_count": m.access_count
                }
                for m in memories
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    # =========================================================================
    # 导出任务
    # =========================================================================
    
    def export_tasks(self, format: str = "markdown") -> bytes:
        """
        导出所有任务
        
        Args:
            format: 导出格式 (markdown, json)
        """
        memory = MemorySystemFactory.for_user(self.user_id)
        try:
            tasks = memory.list_tasks(limit=1000)
            
            if format == "markdown":
                return self._tasks_to_markdown(tasks)
            elif format == "json":
                return self._tasks_to_json(tasks)
            else:
                raise ValueError(f"不支持的格式: {format}")
                
        finally:
            memory.close()
    
    def _tasks_to_markdown(self, tasks: List[Dict]) -> bytes:
        """任务转 Markdown"""
        lines = [
            "# 📋 任务导出",
            "",
            f"- **用户 ID**: {self.user_id}",
            f"- **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **任务数**: {len(tasks)}",
            "",
            "---",
            ""
        ]
        
        # 按状态分组
        by_status = {}
        for task in tasks:
            status = task.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)
        
        status_names = {
            "pending": "⏳ 待处理",
            "completed": "✅ 已完成",
            "in_progress": "🔄 进行中"
        }
        
        for status, status_tasks in by_status.items():
            lines.append(f"## {status_names.get(status, status)}")
            lines.append("")
            
            for task in status_tasks:
                priority_icons = {1: "🔴", 3: "🟡", 5: "🟢"}
                icon = priority_icons.get(task.get("priority"), "⚪")
                
                lines.append(f"- [{icon}] **{task.get('title', 'Untitled')}**")
                if task.get('description'):
                    lines.append(f"  - {task['description']}")
                lines.append(f"  - 创建: {task.get('created_at', 'N/A')}")
                lines.append("")
            
            lines.append("")
        
        return '\n'.join(lines).encode('utf-8')
    
    def _tasks_to_json(self, tasks: List[Dict]) -> bytes:
        """任务转 JSON"""
        data = {
            "user_id": self.user_id,
            "export_time": datetime.now().isoformat(),
            "tasks": tasks
        }
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    
    # =========================================================================
    # 导出全部数据
    # =========================================================================
    
    def export_all(self) -> bytes:
        """导出所有数据（JSON 格式）"""
        memory = MemorySystemFactory.for_user(self.user_id)
        try:
            sessions = memory.list_sessions(limit=1000)
            memories = memory.recall(limit=1000)
            tasks = memory.list_tasks(limit=1000)
            
            data = {
                "user_id": self.user_id,
                "export_time": datetime.now().isoformat(),
                "data": {
                    "sessions": sessions,
                    "memories": [
                        {
                            "id": m.id,
                            "content": m.content,
                            "category": m.category,
                            "importance": m.importance,
                            "created_at": m.created_at.isoformat()
                        }
                        for m in memories
                    ],
                    "tasks": tasks
                }
            }
            
            return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            
        finally:
            memory.close()


def get_export_filename(data_type: str, format: str) -> str:
    """获取导出文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    extensions = {
        "markdown": "md",
        "json": "json",
        "pdf": "pdf"
    }
    
    ext = extensions.get(format, format)
    return f"{data_type}_{timestamp}.{ext}"
