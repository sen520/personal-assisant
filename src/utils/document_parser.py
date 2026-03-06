"""
文档处理 - 解析上传的文件
支持 PDF、Word、TXT、Markdown
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """文档解析器"""
    
    SUPPORTED_EXTENSIONS = {
        '.txt', '.md', '.markdown',
        '.pdf',
        '.docx', '.doc',
        '.json', '.csv'
    }
    
    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """检查文件是否支持"""
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
    
    @classmethod
    def parse(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            filename: 原始文件名
        
        Returns:
            {
                "title": "文档标题",
                "content": "文档内容",
                "chunks": ["分段内容"],
                "metadata": {"pages": 10, ...}
            }
        """
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf':
            return cls._parse_pdf(file_path, filename)
        elif ext in ['.docx', '.doc']:
            return cls._parse_docx(file_path, filename)
        elif ext in ['.txt', '.md', '.markdown']:
            return cls._parse_text(file_path, filename)
        elif ext == '.json':
            return cls._parse_json(file_path, filename)
        elif ext == '.csv':
            return cls._parse_csv(file_path, filename)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
    
    @classmethod
    def _parse_pdf(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """解析 PDF"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            pages_text = []
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    pages_text.append(f"[第{i+1}页]\n{text}")
            
            full_content = "\n\n".join(pages_text)
            
            # 提取标题（通常是第一页的第一行）
            title = filename.replace('.pdf', '')
            if pages_text:
                first_lines = pages_text[0].split('\n')[:3]
                for line in first_lines:
                    line = line.strip()
                    if line and len(line) > 3 and not line.startswith('['):
                        title = line[:100]
                        break
            
            # 分块
            chunks = cls._chunk_text(full_content)
            
            return {
                "title": title,
                "content": full_content,
                "chunks": chunks,
                "metadata": {
                    "pages": len(reader.pages),
                    "file_type": "pdf",
                    "filename": filename
                }
            }
            
        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            raise
    
    @classmethod
    def _parse_docx(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """解析 Word"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            full_content = "\n\n".join(paragraphs)
            
            # 提取标题
            title = filename.replace('.docx', '').replace('.doc', '')
            if paragraphs:
                for para in paragraphs[:5]:
                    if para.strip() and len(para.strip()) > 3:
                        title = para.strip()[:100]
                        break
            
            chunks = cls._chunk_text(full_content)
            
            return {
                "title": title,
                "content": full_content,
                "chunks": chunks,
                "metadata": {
                    "paragraphs": len(paragraphs),
                    "file_type": "docx",
                    "filename": filename
                }
            }
            
        except Exception as e:
            logger.error(f"Word 解析失败: {e}")
            raise
    
    @classmethod
    def _parse_text(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试提取标题（Markdown 格式）
            title = filename
            lines = content.split('\n')
            for line in lines[:10]:
                line = line.strip()
                # Markdown 标题
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                # 第一个非空行
                elif line and len(line) > 3:
                    title = line[:100]
                    break
            
            chunks = cls._chunk_text(content)
            
            return {
                "title": title,
                "content": content,
                "chunks": chunks,
                "metadata": {
                    "lines": len(lines),
                    "file_type": "text",
                    "filename": filename
                }
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            
            chunks = cls._chunk_text(content)
            return {
                "title": filename,
                "content": content,
                "chunks": chunks,
                "metadata": {
                    "file_type": "text",
                    "filename": filename,
                    "encoding": "gbk"
                }
            }
        except Exception as e:
            logger.error(f"文本解析失败: {e}")
            raise
    
    @classmethod
    def _parse_json(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """解析 JSON"""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 将 JSON 转为可读的文本
        content = json.dumps(data, ensure_ascii=False, indent=2)
        chunks = cls._chunk_text(content)
        
        return {
            "title": filename,
            "content": content,
            "chunks": chunks,
            "metadata": {
                "file_type": "json",
                "filename": filename
            }
        }
    
    @classmethod
    def _parse_csv(cls, file_path: str, filename: str) -> Dict[str, Any]:
        """解析 CSV"""
        import csv
        
        rows = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(", ".join(row))
        
        content = "\n".join(rows)
        chunks = cls._chunk_text(content)
        
        return {
            "title": filename,
            "content": content,
            "chunks": chunks,
            "metadata": {
                "rows": len(rows),
                "file_type": "csv",
                "filename": filename
            }
        }
    
    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将文本分块
        
        Args:
            text: 文本内容
            chunk_size: 每块大小（字符数）
            overlap: 重叠大小
        
        Returns:
            文本块列表
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 尽量在段落或句子边界处切割
            if end < len(text):
                # 尝试找段落边界
                paragraph_end = text.rfind('\n\n', start, end)
                if paragraph_end != -1 and paragraph_end > start + chunk_size * 0.5:
                    end = paragraph_end + 2
                else:
                    # 尝试找句子边界
                    sentence_end = max(
                        text.rfind('. ', start, end),
                        text.rfind('。', start, end),
                        text.rfind('？', start, end),
                        text.rfind('！', start, end)
                    )
                    if sentence_end != -1 and sentence_end > start + chunk_size * 0.5:
                        end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks


def get_file_icon(filename: str) -> str:
    """获取文件类型图标"""
    ext = Path(filename).suffix.lower()
    
    icons = {
        '.pdf': '📄',
        '.docx': '📝',
        '.doc': '📝',
        '.txt': '📃',
        '.md': '📑',
        '.markdown': '📑',
        '.json': '📋',
        '.csv': '📊',
    }
    
    return icons.get(ext, '📎')


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
