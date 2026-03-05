"""
向量存储管理器
支持本地 SQLite + FAISS 索引 或远程 ChromaDB
"""

import os
import json
import sqlite3
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    category: str = "general"  # fact, event, preference, task
    importance: int = 3  # 1-5
    created_at: str = None
    last_accessed: str = None
    access_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


class VectorStore:
    """
    向量存储管理器
    
    使用 SQLite + 本地向量索引
    可选：切换到远程 ChromaDB
    """
    
    def __init__(self, db_path: str = "./memory/vector_store.db"):
        self.db_path = db_path
        self.embeddings_cache: Dict[str, List[float]] = {}
        
        # 初始化数据库
        self._init_db()
        
        # 尝试加载本地向量索引
        self._load_faiss_index()
    
    def _init_db(self):
        """初始化 SQLite 数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    metadata TEXT,
                    category TEXT DEFAULT 'general',
                    importance INTEGER DEFAULT 3,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON memories(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON memories(created_at)")
            conn.commit()
    
    def _load_faiss_index(self):
        """加载 FAISS 索引（如果有）"""
        index_path = self.db_path.replace('.db', '.faiss')
        if os.path.exists(index_path):
            try:
                import faiss
                self.index = faiss.read_index(index_path)
                logger.info(f"✅ 已加载 FAISS 索引: {index_path}")
            except ImportError:
                logger.warning("⚠️  FAISS 未安装，将使用暴力搜索")
                self.index = None
            except Exception as e:
                logger.error(f"❌ 加载 FAISS 索引失败: {e}")
                self.index = None
        else:
            self.index = None
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        TODO: 替换为实际的嵌入模型（OpenAI、本地模型等）
        现在使用简单的词频向量作为占位
        """
        # 简单的词袋模型作为占位
        words = text.lower().split()
        vocab = list(set(words))
        embedding = [words.count(w) for w in vocab[:50]]  # 限制维度
        
        # 填充到固定维度
        embedding = embedding + [0] * (50 - len(embedding))
        
        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding[:50]  # 固定 50 维
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))
    
    def add_memory(self, content: str, category: str = "general", 
                   importance: int = 3, metadata: Dict = None) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            category: 类别 (fact, event, preference, task)
            importance: 重要程度 1-5
            metadata: 额外元数据
        
        Returns:
            记忆 ID
        """
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(content) % 10000}"
        
        # 生成向量
        embedding = self._get_embedding(content)
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memories 
                   (id, content, embedding, metadata, category, importance, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory_id,
                    content,
                    pickle.dumps(embedding),
                    json.dumps(metadata or {}),
                    category,
                    importance,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
        
        # 更新缓存
        self.embeddings_cache[memory_id] = embedding
        
        logger.info(f"💾 记忆已存储 [{category}]: {content[:50]}...")
        return memory_id
    
    def search_similar(self, query: str, top_k: int = 5, 
                       category: str = None, min_similarity: float = 0.5) -> List[Tuple[MemoryItem, float]]:
        """
        搜索相似记忆
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            category: 限制类别
            min_similarity: 最小相似度阈值
        
        Returns:
            [(记忆项, 相似度分数), ...]
        """
        query_embedding = self._get_embedding(query)
        
        # 加载所有记忆
        memories = []
        with sqlite3.connect(self.db_path) as conn:
            if category:
                cursor = conn.execute(
                    "SELECT * FROM memories WHERE category = ?",
                    (category,)
                )
            else:
                cursor = conn.execute("SELECT * FROM memories")
            
            for row in cursor:
                mem = MemoryItem(
                    id=row[0],
                    content=row[1],
                    embedding=pickle.loads(row[2]) if row[2] else None,
                    metadata=json.loads(row[3]) if row[3] else {},
                    category=row[4],
                    importance=row[5],
                    created_at=row[6],
                    last_accessed=row[7],
                    access_count=row[8]
                )
                memories.append(mem)
        
        # 计算相似度
        scored_memories = []
        for mem in memories:
            if mem.embedding:
                similarity = self._cosine_similarity(query_embedding, mem.embedding)
                if similarity >= min_similarity:
                    scored_memories.append((mem, similarity))
        
        # 排序并返回 Top K
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_memories[:top_k]
        
        # 更新访问记录
        for mem, _ in top_results:
            self._update_access(mem.id)
        
        return top_results
    
    def _update_access(self, memory_id: str):
        """更新访问记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE memories 
                   SET last_accessed = ?, access_count = access_count + 1
                   WHERE id = ?""",
                (datetime.now().isoformat(), memory_id)
            )
            conn.commit()
    
    def get_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """根据 ID 获取记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                return MemoryItem(
                    id=row[0],
                    content=row[1],
                    embedding=pickle.loads(row[2]) if row[2] else None,
                    metadata=json.loads(row[3]) if row[3] else {},
                    category=row[4],
                    importance=row[5],
                    created_at=row[6],
                    last_accessed=row[7],
                    access_count=row[8]
                )
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                self.embeddings_cache.pop(memory_id, None)
                logger.info(f"🗑️  记忆已删除: {memory_id}")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            
            by_category = {}
            for row in conn.execute("SELECT category, COUNT(*) FROM memories GROUP BY category"):
                by_category[row[0]] = row[1]
            
            return {
                "total_memories": total,
                "by_category": by_category,
                "db_path": self.db_path
            }


class ChromaDBStore(VectorStore):
    """
    ChromaDB 向量存储（远程/ Docker 版本）
    
    等 Docker ChromaDB 启动后，可以切换到这个类
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.client = None
        self.collection = None
        
        try:
            import chromadb
            self.client = chromadb.HttpClient(host=host, port=port)
            self.collection = self.client.get_or_create_collection("personal_assistant")
            logger.info(f"✅ 已连接到 ChromaDB: {host}:{port}")
        except ImportError:
            logger.error("❌ 请先安装 ChromaDB: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"❌ 连接 ChromaDB 失败: {e}")
            raise
    
    def add_memory(self, content: str, category: str = "general",
                   importance: int = 3, metadata: Dict = None) -> str:
        """使用 ChromaDB 添加记忆"""
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(content) % 10000}"
        
        meta = metadata or {}
        meta.update({
            "category": category,
            "importance": importance,
            "created_at": datetime.now().isoformat()
        })
        
        self.collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[meta]
        )
        
        logger.info(f"💾 记忆已存储到 ChromaDB [{category}]: {content[:50]}...")
        return memory_id
    
    def search_similar(self, query: str, top_k: int = 5,
                       category: str = None, min_similarity: float = 0.5) -> List[Tuple[MemoryItem, float]]:
        """使用 ChromaDB 搜索"""
        where_clause = {"category": category} if category else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )
        
        memories = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, mem_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - distance  # Chroma 返回的是距离
                
                if similarity >= min_similarity:
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    mem = MemoryItem(
                        id=mem_id,
                        content=doc,
                        category=meta.get("category", "general"),
                        importance=meta.get("importance", 3),
                        metadata=meta
                    )
                    memories.append((mem, similarity))
        
        return memories