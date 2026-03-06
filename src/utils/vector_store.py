"""
向量存储 - ChromaDB 封装
支持语义检索
"""

import uuid
import hashlib
from typing import List, Dict, Any, Optional

from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    向量存储管理器
    基于 ChromaDB 实现语义检索
    """
    
    _instance = None
    _client = None
    _collections = {}
    _embedding_func = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_chroma(self):
        """初始化 ChromaDB"""
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            # 持久化存储
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir
            )
            
            # 使用 SiliconFlow 的嵌入模型
            self._embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-large-zh-v1.5"
            )
            
            logger.info(f"✅ ChromaDB 向量存储已初始化: {settings.chroma_persist_dir}")
            
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB 初始化失败: {e}")
            self._client = None
    
    def _get_collection(self, user_id: str):
        """获取用户的向量集合"""
        if self._client is None:
            self.init_chroma()
        
        if self._client is None:
            return None
        
        # 用户隔离：每个用户一个 collection
        collection_name = f"memories_{user_id[:16]}"
        
        if collection_name not in self._collections:
            try:
                collection = self._client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_func,
                    metadata={"user_id": user_id}
                )
                self._collections[collection_name] = collection
            except Exception as e:
                logger.error(f"创建向量集合失败: {e}")
                return None
        
        return self._collections.get(collection_name)
    
    def add_memory(
        self,
        user_id: str,
        memory_id: str,
        content: str,
        category: str = "general",
        importance: int = 3,
        metadata: Dict = None
    ) -> bool:
        """
        添加记忆到向量存储
        
        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID
            content: 记忆内容
            category: 类别
            importance: 重要性
            metadata: 额外元数据
        
        Returns:
            是否成功
        """
        collection = self._get_collection(user_id)
        if collection is None:
            return False
        
        try:
            # 生成文档 ID
            doc_id = f"mem_{memory_id}"
            
            # 构建元数据
            doc_metadata = {
                "memory_id": memory_id,
                "category": category,
                "importance": importance,
                **(metadata or {})
            }
            
            # 添加到向量库
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            logger.debug(f"记忆已向量化: {memory_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"添加向量记忆失败: {e}")
            return False
    
    def search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        语义搜索记忆
        
        Args:
            user_id: 用户 ID
            query: 搜索查询
            n_results: 返回结果数量
            category: 类别过滤
            min_score: 最低相似度分数 (0-1)
        
        Returns:
            搜索结果列表
        """
        collection = self._get_collection(user_id)
        if collection is None:
            return []
        
        try:
            # 构建过滤条件
            where_filter = None
            if category:
                where_filter = {"category": category}
            
            # 执行搜索
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            memories = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # 距离转换为相似度分数 (余弦距离 -> 相似度)
                    distance = results["distances"][0][i]
                    similarity = 1 - (distance / 2)  # 归一化到 0-1
                    
                    if similarity >= min_score:
                        memories.append({
                            "memory_id": results["metadatas"][0][i].get("memory_id"),
                            "content": results["documents"][0][i],
                            "category": results["metadatas"][0][i].get("category", "general"),
                            "importance": results["metadatas"][0][i].get("importance", 3),
                            "similarity": round(similarity, 4),
                            "metadata": {k: v for k, v in results["metadatas"][0][i].items() 
                                        if k not in ["memory_id", "category", "importance"]}
                        })
            
            # 按相似度排序
            memories.sort(key=lambda x: x["similarity"], reverse=True)
            
            logger.debug(f"语义搜索: '{query[:30]}...' 找到 {len(memories)} 条结果")
            return memories
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        删除向量记忆
        
        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID
        
        Returns:
            是否成功
        """
        collection = self._get_collection(user_id)
        if collection is None:
            return False
        
        try:
            doc_id = f"mem_{memory_id}"
            collection.delete(ids=[doc_id])
            logger.debug(f"向量记忆已删除: {memory_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"删除向量记忆失败: {e}")
            return False
    
    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        content: str = None,
        category: str = None,
        importance: int = None,
        metadata: Dict = None
    ) -> bool:
        """
        更新向量记忆
        
        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID
            content: 新内容
            category: 新类别
            importance: 新重要性
            metadata: 新元数据
        
        Returns:
            是否成功
        """
        collection = self._get_collection(user_id)
        if collection is None:
            return False
        
        try:
            doc_id = f"mem_{memory_id}"
            
            # 先获取现有数据
            existing = collection.get(ids=[doc_id])
            if not existing["ids"]:
                return False
            
            # 构建更新数据
            update_data = {}
            if content:
                update_data["documents"] = [content]
            
            # 更新元数据
            new_metadata = existing["metadatas"][0].copy()
            if category:
                new_metadata["category"] = category
            if importance is not None:
                new_metadata["importance"] = importance
            if metadata:
                new_metadata.update(metadata)
            
            update_data["metadatas"] = [new_metadata]
            
            collection.update(ids=[doc_id], **update_data)
            logger.debug(f"向量记忆已更新: {memory_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"更新向量记忆失败: {e}")
            return False
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """获取向量存储统计"""
        collection = self._get_collection(user_id)
        if collection is None:
            return {"count": 0, "error": "Collection not found"}
        
        try:
            count = collection.count()
            return {"count": count}
        except Exception as e:
            return {"count": 0, "error": str(e)}
    
    def clear_user_memories(self, user_id: str) -> bool:
        """清除用户的所有向量记忆"""
        collection = self._get_collection(user_id)
        if collection is None:
            return False
        
        try:
            # 获取所有 ID 并删除
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
            logger.info(f"用户 {user_id[:8]}... 的向量记忆已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除向量记忆失败: {e}")
            return False

    def add_document_chunk(
        self,
        collection_name: str,
        chunk_id: str,
        content: str,
        metadata: dict = None
    ) -> bool:
        """
        添加文档分块到向量库
        
        Args:
            collection_name: 集合名称
            chunk_id: 块 ID
            content: 块内容
            metadata: 元数据
        
        Returns:
            是否成功
        """
        if self._client is None:
            self.init_chroma()
        
        if self._client is None:
            return False
        
        try:
            # 获取或创建集合
            collection = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._embedding_func
            )
            
            # 添加文档
            collection.add(
                ids=[chunk_id],
                documents=[content],
                metadatas=[metadata or {}]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"添加文档分块失败: {e}")
            return False
    
    def search_document(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        在文档集合中搜索
        
        Args:
            collection_name: 集合名称
            query: 查询
            n_results: 结果数量
            min_score: 最低相似度
        
        Returns:
            搜索结果列表
        """
        if self._client is None:
            self.init_chroma()
        
        if self._client is None:
            return []
        
        try:
            collection = self._client.get_collection(
                name=collection_name,
                embedding_function=self._embedding_func
            )
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1 - (distance / 2)
                    
                    if similarity >= min_score:
                        search_results.append({
                            "vector_id": chunk_id,
                            "content": results["documents"][0][i],
                            "similarity": round(similarity, 4),
                            "metadata": results["metadatas"][0][i]
                        })
            
            return search_results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        删除整个集合
        
        Args:
            collection_name: 集合名称
        
        Returns:
            是否成功
        """
        if self._client is None:
            return False
        
        try:
            self._client.delete_collection(name=collection_name)
            logger.info(f"向量集合已删除: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除向量集合失败: {e}")
            return False


# 全局向量存储实例
vector_store = VectorStore()


def init_vector_store():
    """初始化向量存储"""
    vector_store.init_chroma()
