"""
知识库 RAG 系统
支持文档上传、解析、向量化和检索
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config.settings import settings
from ..utils.logging import get_logger
from ..utils.vector_store import vector_store
from ..utils.document_parser import DocumentParser, get_file_icon, format_file_size

logger = get_logger(__name__)


class KnowledgeBase:
    """
    知识库系统
    
    功能：
    - 文档上传和存储
    - 文档解析（PDF/Word/TXT）
    - 文档分块和向量化
    - RAG 语义检索
    """
    
    def __init__(self, user_id: str, session):
        """
        初始化知识库
        
        Args:
            user_id: 用户 ID
            session: 数据库会话
        """
        self.user_id = user_id
        self.session = session
    
    def upload_document(
        self,
        file_path: str,
        filename: str,
        file_size: int,
        title: str = None
    ) -> Dict[str, Any]:
        """
        上传并处理文档
        
        Args:
            file_path: 文件临时路径
            filename: 原始文件名
            file_size: 文件大小
            title: 文档标题（可选）
        
        Returns:
            文档信息
        """
        from ..db.models import Document, DocumentChunk
        from ..db.repository import DocumentRepository
        
        # 检查文件类型
        if not DocumentParser.is_supported(filename):
            raise ValueError(f"不支持的文件类型: {filename}")
        
        repo = DocumentRepository(self.session)
        
        # 1. 创建文档记录
        doc_id = str(uuid.uuid4())
        doc = repo.create(
            id=doc_id,
            user_id=self.user_id,
            title=title or filename,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=self._get_file_type(filename)
        )
        
        try:
            # 2. 解析文档
            logger.info(f"解析文档: {filename}")
            parsed = DocumentParser.parse(file_path, filename)
            
            # 3. 更新文档内容
            repo.update_content(doc_id, parsed["content"], len(parsed["chunks"]))
            
            # 4. 存储分块
            chunk_ids = []
            for i, chunk_content in enumerate(parsed["chunks"]):
                chunk_id = str(uuid.uuid4())
                repo.create_chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    content=chunk_content,
                    chunk_index=i,
                    meta_data={"chunk_index": i, **parsed.get("metadata", {})}
                )
                chunk_ids.append(chunk_id)
            
            # 5. 向量化
            logger.info(f"向量化文档: {filename} ({len(chunk_ids)} 块)")
            self._vectorize_document(doc_id, parsed["chunks"], chunk_ids)
            
            # 6. 更新状态
            repo.update_status(doc_id, "indexed")
            
            logger.info(f"✅ 文档上传完成: {filename}")
            
            return {
                "id": doc_id,
                "title": parsed["title"],
                "filename": filename,
                "chunks_count": len(chunk_ids),
                "status": "indexed"
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            repo.update_status(doc_id, "error", str(e))
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        RAG 检索
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            document_ids: 指定文档 ID 列表（可选）
        
        Returns:
            检索结果列表
        """
        from ..db.repository import DocumentRepository
        
        repo = DocumentRepository(self.session)
        
        # 1. 获取用户的文档列表
        if document_ids:
            docs = repo.get_by_ids(document_ids, self.user_id)
        else:
            docs = repo.list_by_user(self.user_id, status="indexed")
        
        if not docs:
            return []
        
        # 2. 构建查询过滤条件
        collection_names = []
        for doc in docs:
            if doc.vector_collection:
                collection_names.append(doc.vector_collection)
        
        if not collection_names:
            return []
        
        # 3. 向量检索
        results = []
        
        # 对每个文档集合进行检索
        for collection_name in collection_names:
            try:
                vector_results = self._search_in_collection(
                    collection_name, query, top_k
                )
                results.extend(vector_results)
            except Exception as e:
                logger.warning(f"集合检索失败 {collection_name}: {e}")
        
        # 4. 按相似度排序并去重
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:top_k]
        
        # 5. 补充文档信息
        for result in results:
            chunk = repo.get_chunk_by_vector_id(result["vector_id"])
            if chunk:
                doc = repo.get(chunk.document_id)
                result["document"] = {
                    "id": doc.id if doc else None,
                    "title": doc.title if doc else "未知文档",
                    "filename": doc.filename if doc else "",
                    "file_type": doc.file_type if doc else ""
                }
                result["chunk_index"] = chunk.chunk_index
        
        return results
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档 ID
        
        Returns:
            是否成功
        """
        from ..db.repository import DocumentRepository
        
        repo = DocumentRepository(self.session)
        doc = repo.get_by_id(document_id, self.user_id)
        
        if not doc:
            return False
        
        try:
            # 1. 删除向量
            if doc.vector_collection:
                self._delete_vectors(doc.vector_collection)
            
            # 2. 删除数据库记录
            repo.delete(document_id, self.user_id)
            
            logger.info(f"✅ 文档已删除: {doc.filename}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取文档列表"""
        from ..db.repository import DocumentRepository
        
        repo = DocumentRepository(self.session)
        docs = repo.list_by_user(self.user_id, limit=limit)
        
        return [
            {
                "id": d.id,
                "title": d.title,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": format_file_size(d.file_size),
                "chunks_count": d.chunks_count,
                "status": d.status,
                "is_vectorized": bool(d.is_vectorized),
                "created_at": d.created_at.isoformat()
            }
            for d in docs
        ]
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档详情"""
        from ..db.repository import DocumentRepository
        
        repo = DocumentRepository(self.session)
        doc = repo.get_by_id(document_id, self.user_id)
        
        if not doc:
            return None
        
        return {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": format_file_size(doc.file_size),
            "content": doc.content[:2000] + "..." if doc.content and len(doc.content) > 2000 else doc.content,
            "chunks_count": doc.chunks_count,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        }
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        from pathlib import Path
        ext = Path(filename).suffix.lower()
        type_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.txt': 'txt',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.json': 'json',
            '.csv': 'csv'
        }
        return type_map.get(ext, 'unknown')
    
    def _vectorize_document(
        self,
        document_id: str,
        chunks: List[str],
        chunk_ids: List[str]
    ):
        """
        将文档分块向量化
        
        Args:
            document_id: 文档 ID
            chunks: 文本块列表
            chunk_ids: 块 ID 列表
        """
        from ..db.repository import DocumentRepository
        
        # 使用用户隔离的集合名称
        collection_name = f"kb_{self.user_id}_{document_id[:8]}"
        
        # 向量化每一块
        for i, (chunk_content, chunk_id) in enumerate(zip(chunks, chunk_ids)):
            try:
                vector_store.add_document_chunk(
                    collection_name=collection_name,
                    chunk_id=chunk_id,
                    content=chunk_content,
                    metadata={
                        "document_id": document_id,
                        "chunk_index": i
                    }
                )
            except Exception as e:
                logger.warning(f"块向量化失败 {chunk_id}: {e}")
        
        # 更新文档向量状态
        repo = DocumentRepository(self.session)
        repo.update_vector_status(document_id, True, collection_name)
    
    def _search_in_collection(
        self,
        collection_name: str,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """在指定集合中检索"""
        try:
            results = vector_store.search_document(
                collection_name=collection_name,
                query=query,
                n_results=top_k
            )
            return results
        except Exception as e:
            logger.warning(f"向量检索失败: {e}")
            return []
    
    def _delete_vectors(self, collection_name: str):
        """删除向量集合"""
        try:
            vector_store.delete_collection(collection_name)
        except Exception as e:
            logger.warning(f"删除向量集合失败: {e}")
