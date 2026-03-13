"""
元记忆增强层 - Ollama 向量化引擎
使用本地 Ollama API 进行语义嵌入
"""

import json
import numpy as np
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib


class OllamaEmbedder:
    """Ollama 向量化引擎"""
    
    def __init__(self, model: str = "locusai/all-minilm-l6-v2", ollama_host: str = "http://localhost:11434"):
        self.model = model
        self.ollama_host = ollama_host
        self.dimension = 384  # all-MiniLM-L6-v2 输出维度
        self._test_connection()
        
    def _test_connection(self):
        """测试 Ollama 连接"""
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if r.status_code == 200:
                print(f"[OllamaEmbedder] Connected to Ollama at {self.ollama_host}")
            else:
                print(f"[OllamaEmbedder] Ollama returned status {r.status_code}")
        except Exception as e:
            print(f"[OllamaEmbedder] Cannot connect to Ollama: {e}")
    
    def _get_embedding_via_api(self, text: str) -> Optional[List[float]]:
        """通过 Ollama API 获取 embedding"""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
            return None
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None
    
    def embed(self, text: str) -> Optional[np.ndarray]:
        """
        将文本转换为向量
        """
        # 方法1: 使用 Ollama API
        vector = self._get_embedding_via_api(text)
        if vector:
            return np.array(vector)
        
        # 方法2: 备用 - 使用简单的哈希
        return self._simple_hash_vector(text)
    
    def _simple_hash_vector(self, text: str) -> np.ndarray:
        """简单的哈希向量（备用方案）"""
        # 使用 MD5 哈希生成固定向量
        h = hashlib.md5(text.encode()).digest()
        # 扩展到 384 维
        vector = np.array([int(b) for b in h], dtype=np.float32)
        # 重复并归一化
        vector = np.tile(vector, 96)[:384]
        vector = vector / (np.linalg.norm(vector) + 1e-8)
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """批量向量化"""
        return [self.embed(text) for text in texts]


class MetaMemoryIndex:
    """
    元记忆索引 - 存储和管理向量
    """
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = r"C:\Users\Administrator\.meta-memory"
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedder = OllamaEmbedder()
        self.vectors = []  # 内存索引
        self.metadata = []  # 元数据
        
        self._load_index()
    
    def _get_index_file(self) -> Path:
        return self.storage_path / "vectors.npz"
    
    def _get_meta_file(self) -> Path:
        return self.storage_path / "metadata.json"
    
    def _load_index(self):
        """加载已有索引"""
        index_file = self._get_index_file()
        meta_file = self._get_meta_file()
        
        if index_file.exists() and meta_file.exists():
            try:
                data = np.load(index_file)
                self.vectors = [data[f'vec_{i}'] for i in range(data['count'])]
                with open(meta_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"Loaded {len(self.vectors)} vectors from index")
            except Exception as e:
                print(f"Failed to load index: {e}")
                self.vectors = []
                self.metadata = []
    
    def _save_index(self):
        """保存索引"""
        index_file = self._get_index_file()
        meta_file = self._get_meta_file()
        
        # 保存向量
        if self.vectors:
            arr = np.vstack(self.vectors)
            np.savez(index_file, count=len(self.vectors), **{f'vec_{i}': v for i, v in enumerate(self.vectors)})
        
        # 保存元数据
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(self.vectors)} vectors to index")
    
    def add_memories(self, memories: List[Dict[str, Any]]):
        """添加记忆到索引"""
        for mem in memories:
            if mem["id"] in [m["id"] for m in self.metadata]:
                continue  # 已存在
                
            vector = self.embedder.embed(mem["content"][:1000])  # 截断长文本
            
            self.vectors.append(vector)
            self.metadata.append({
                "id": mem["id"],
                "source": mem["source"],
                "title": mem["title"][:100],
                "content": mem["content"],
                "type": mem.get("type", "unknown")
            })
        
        if memories:
            self._save_index()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """语义搜索"""
        query_vector = self.embedder.embed(query[:500])
        
        if not self.vectors:
            return []
        
        # 计算余弦相似度
        similarities = []
        for i, vec in enumerate(self.vectors):
            sim = np.dot(query_vector, vec) / (np.linalg.norm(query_vector) * np.linalg.norm(vec) + 1e-8)
            similarities.append((i, sim))
        
        # 排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回 top_k
        results = []
        for i, sim in similarities[:top_k]:
            mem = self.metadata[i].copy()
            mem["score"] = float(sim)
            results.append(mem)
        
        return results
    
    def rebuild_index(self, memories: List[Dict[str, Any]]):
        """重建整个索引"""
        self.vectors = []
        self.metadata = []
        self.add_memories(memories)


if __name__ == "__main__":
    # 测试
    from builtin_reader import get_all_built_in_memories
    
    print("=== 初始化索引 ===")
    index = MetaMemoryIndex()
    
    print("\n=== 读取内置记忆 ===")
    memories = get_all_built_in_memories()
    print(f"找到 {len(memories)} 条记忆")
    
    print("\n=== 添加到索引 ===")
    index.add_memories(memories)
    
    print("\n=== 测试搜索 ===")
    results = index.search("用户偏好")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['title'][:40]}")
