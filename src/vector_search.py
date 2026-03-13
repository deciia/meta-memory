"""
向量搜索引擎 (参考Elite Longterm Memory)
集成语义搜索功能
"""

import logging
import json
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import hashlib
import os
import sys

logger = logging.getLogger(__name__)

class VectorSearchEngine:
    """向量搜索引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.vector_db = None
        self.is_available_flag = False
        
        # 尝试加载向量模型
        self._try_load_model()
        
        # 初始化向量数据库
        self._init_vector_db()
    
    def _try_load_model(self):
        """尝试加载向量模型"""
        try:
            # 检查是否安装了sentence-transformers
            import importlib.util
            spec = importlib.util.find_spec("sentence_transformers")
            
            if spec is None:
                logger.warning("sentence-transformers not installed. Vector search will be disabled.")
                logger.info("To enable vector search: pip install sentence-transformers")
                self.is_available_flag = False
                return
            
            # 延迟导入，避免未安装时出错
            global SentenceTransformer
            from sentence_transformers import SentenceTransformer
            
            model_name = self.config.get("vector_model", "all-MiniLM-L6-v2")
            
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"Loaded vector model: {model_name}")
                self.is_available_flag = True
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                logger.info("Trying alternative model...")
                
                # 尝试备用模型
                try:
                    self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                    logger.info("Loaded alternative model: paraphrase-MiniLM-L6-v2")
                    self.is_available_flag = True
                except Exception as e2:
                    logger.error(f"Failed to load alternative model: {e2}")
                    self.is_available_flag = False
        
        except ImportError as e:
            logger.warning(f"Import error: {e}")
            self.is_available_flag = False
        except Exception as e:
            logger.error(f"Unexpected error loading model: {e}")
            self.is_available_flag = False
    
    def _init_vector_db(self):
        """初始化向量数据库"""
        if not self.is_available():
            return
        
        try:
            # 检查是否安装了chromadb
            import importlib.util
            spec = importlib.util.find_spec("chromadb")
            
            if spec is None:
                logger.warning("chromadb not installed. Using in-memory storage.")
                self.vector_db = InMemoryVectorDB()
                return
            
            # 延迟导入
            global chromadb
            import chromadb
            
            # 创建本地向量数据库
            db_path = os.path.join(os.path.expanduser("~"), ".meta-memory", "vector_db")
            os.makedirs(db_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(path=db_path)
            
            # 创建或获取集合
            collection_name = "memories"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"Loaded existing vector collection: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Memory embeddings"}
                )
                logger.info(f"Created new vector collection: {collection_name}")
            
            logger.info("Vector database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            # 回退到内存存储
            self.vector_db = InMemoryVectorDB()
    
    def is_available(self) -> bool:
        """检查向量搜索是否可用"""
        return self.is_available_flag and self.model is not None
    
    def encode_text(self, text: str) -> Optional[List[float]]:
        """编码文本为向量"""
        if not self.is_available() or not text:
            return None
        
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return None
    
    def index_memory(self, memory_id: str, content: str, agent_id: str = "system"):
        """索引记忆到向量数据库"""
        if not self.is_available():
            return False
        
        try:
            # 生成嵌入向量
            embedding = self.encode_text(content)
            if embedding is None:
                return False
            
            # 准备元数据
            metadata = {
                "memory_id": memory_id,
                "agent_id": agent_id,
                "content_preview": content[:100],
                "indexed_at": datetime.now().isoformat()
            }
            
            # 存储到向量数据库
            if hasattr(self, 'collection'):
                # 使用ChromaDB
                self.collection.add(
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
            elif self.vector_db:
                # 使用内存数据库
                self.vector_db.add(memory_id, embedding, metadata)
            
            logger.debug(f"Indexed memory {memory_id} in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index memory {memory_id}: {e}")
            return False
    
    def semantic_search(self, query: str, agent_id: str = "system", **kwargs) -> List:
        """
        语义搜索
        
        Args:
            query: 查询文本
            agent_id: 代理ID
            **kwargs: 额外参数
                - limit: 返回数量
                - min_similarity: 最小相似度
                - filter_by_agent: 是否按代理过滤
        
        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []
        
        try:
            # 编码查询
            query_embedding = self.encode_text(query)
            if query_embedding is None:
                return []
            
            # 搜索参数
            limit = kwargs.get('limit', 10)
            min_similarity = kwargs.get('min_similarity', 0.5)
            filter_by_agent = kwargs.get('filter_by_agent', False)
            
            # 执行搜索
            if hasattr(self, 'collection'):
                # ChromaDB搜索
                where_filter = None
                if filter_by_agent:
                    where_filter = {"agent_id": agent_id}
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_filter,
                    include=["metadatas", "distances"]
                )
                
                # 解析结果
                memories = []
                if results['ids'] and len(results['ids']) > 0:
                    for i in range(len(results['ids'][0])):
                        memory_id = results['ids'][0][i]
                        metadata = results['metadatas'][0][i]
                        distance = results['distances'][0][i]
                        
                        # 计算相似度分数
                        similarity = 1.0 - distance  # ChromaDB使用余弦距离
                        
                        if similarity >= min_similarity:
                            memories.append({
                                "memory_id": memory_id,
                                "similarity": similarity,
                                "metadata": metadata
                            })
                
                return memories
                
            elif self.vector_db:
                # 内存数据库搜索
                return self.vector_db.search(query_embedding, limit, min_similarity)
            
            return []
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def remove_from_index(self, memory_id: str) -> bool:
        """从向量索引中删除记忆"""
        if not self.is_available():
            return False
        
        try:
            if hasattr(self, 'collection'):
                self.collection.delete(ids=[memory_id])
            elif self.vector_db:
                self.vector_db.remove(memory_id)
            
            logger.debug(f"Removed memory {memory_id} from vector index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove memory {memory_id} from index: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            "available": self.is_available(),
            "model_loaded": self.model is not None,
            "vector_db_type": "none"
        }
        
        if hasattr(self, 'collection'):
            try:
                stats["vector_db_type"] = "chromadb"
                stats["collection_count"] = self.collection.count()
            except:
                stats["collection_count"] = 0
        elif self.vector_db:
            stats["vector_db_type"] = "in_memory"
            stats["vector_count"] = len(self.vector_db.vectors)
        
        return stats
    
    def cleanup(self) -> Dict:
        """清理向量数据库"""
        if not self.is_available():
            return {"status": "not_available"}
        
        try:
            # 这里可以添加清理逻辑，比如删除旧索引等
            return {"status": "success", "message": "Vector database cleaned"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# ========== 内存向量数据库 (备用) ==========

class InMemoryVectorDB:
    """内存向量数据库 (备用)"""
    
    def __init__(self):
        self.vectors = {}  # memory_id -> embedding
        self.metadata = {}  # memory_id -> metadata
    
    def add(self, memory_id: str, embedding: List[float], metadata: Dict):
        """添加向量"""
        self.vectors[memory_id] = embedding
        self.metadata[memory_id] = metadata
    
    def remove(self, memory_id: str):
        """删除向量"""
        if memory_id in self.vectors:
            del self.vectors[memory_id]
        if memory_id in self.metadata:
            del self.metadata[memory_id]
    
    def search(self, query_embedding: List[float], limit: int = 10, min_similarity: float = 0.5) -> List:
        """搜索相似向量"""
        if not self.vectors:
            return []
        
        # 计算相似度
        similarities = []
        for mem_id, embedding in self.vectors.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= min_similarity:
                similarities.append((mem_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回结果
        results = []
        for mem_id, similarity in similarities[:limit]:
            results.append({
                "memory_id": mem_id,
                "similarity": similarity,
                "metadata": self.metadata.get(mem_id, {})
            })
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # 转换为numpy数组
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except:
            # 纯Python实现
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot / (norm1 * norm2)

# ========== 测试函数 ==========

def test_vector_search():
    """测试向量搜索"""
    print("=== Testing Vector Search ===")
    
    config = {
        "vector_model": "all-MiniLM-L6-v2",
        "enable_vector_search": True
    }
    
    engine = VectorSearchEngine(config)
    
    print(f"1. Vector search available: {engine.is_available()}")
    
    if engine.is_available():
        # 测试编码
        text = "这是一个测试文本"
        embedding = engine.encode_text(text)
        print(f"2. Text encoded: {embedding is not None}")
        
        if embedding:
            print(f"   Embedding dimension: {len(embedding)}")
        
        # 测试索引
        memory_id = "test_memory_123"
        success = engine.index_memory(memory_id, text, "test_agent")
        print(f"3. Memory indexed: {success}")
        
        # 测试搜索
        results = engine.semantic_search("测试", "test_agent")
        print(f"4. Search results: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}: {result['memory_id']} (similarity: {result['similarity']:.3f})")
        
        # 测试删除
        success = engine.remove_from_index(memory_id)
        print(f"5. Memory removed: {success}")
        
        # 获取统计
        stats = engine.get_stats()
        print(f"6. Stats: {stats}")
    
    print("\n=== Vector search test completed ===")
    return engine.is_available()

if __name__ == "__main__":
    test_vector_search()