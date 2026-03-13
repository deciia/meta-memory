"""
Meta-Memory Enhancer - 完整版
集成：自动推测引擎 + 三层记忆检索 + 防止卡住
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 添加技能路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "src"))

from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
from src.builtin_reader import get_all_built_in_memories, get_memory_stats
from src.ollama_embedder import MetaMemoryIndex, OllamaEmbedder


# ========== 三层记忆系统 ==========

class ThreeLayerRetrieval:
    """三层记忆检索系统"""
    
    def __init__(self):
        self.ollama = OllamaEmbedder()
        
    def retrieve(self, query: str, context: Dict = None) -> Dict:
        """
        三层检索
        
        Args:
            query: 查询内容
            context: 额外上下文（可选）
            
        Returns:
            {
                "short_term": [...],   # 短期 - 最近5条
                "mid_term": [...],     # 中期 - 最近7天
                "long_term": [...]     # 长期 - 向量相关
            }
        """
        # 获取所有内置记忆
        all_memories = get_all_built_in_memories()
        
        # 按时间排序
        sorted_memories = sorted(
            all_memories, 
            key=lambda x: x.get("source", ""),
            reverse=True
        )
        
        # 短期: 最近5条
        short_term = sorted_memories[:5]
        
        # 中期: 最近7天的（简化处理：取5-20条）
        mid_term = sorted_memories[5:20]
        
        # 长期: 向量相似
        index = MetaMemoryIndex(r"C:\Users\Administrator\.meta-memory\index")
        long_term = index.search(query, top_k=10)
        
        return {
            "short_term": short_term,
            "mid_term": mid_term,
            "long_term": long_term
        }


# ========== 自动推测引擎 ==========

class AutoInferenceEngine:
    """自动推测引擎 - 无需触发词自动分析"""
    
    TRIGGERS = [
        "元记忆", "深度回忆", "仔细回想", "记得我", "搜索记忆",
        "之前说过", "上次", "以前", "帮我想想"
    ]
    
    def __init__(self):
        self.ollama = OllamaEmbedder()
        self.user_interests = {}  # 用户兴趣模型
        
    def should_activate(self, message: str) -> bool:
        """判断是否需要激活元记忆"""
        msg = message.lower()
        return any(trigger in msg for trigger in self.TRIGGERS)
    
    def infer(self, query: str, context: Dict = None) -> Dict:
        """
        智能推测
        
        Args:
            query: 用户查询
            context: 上下文
            
        Returns:
            推测结果
        """
        # 使用三层检索
        retrieval = ThreeLayerRetrieval()
        layers = retrieval.retrieve(query, context)
        
        # 收集所有记忆用于相似度计算
        all_content = []
        for layer_name, memories in layers.items():
            for m in memories:
                all_content.append({
                    "layer": layer_name,
                    "content": m.get("content", ""),
                    "title": m.get("title", "")
                })
        
        # 计算与查询的相似度
        if not all_content:
            return {"results": [], "summary": "No memories found"}
        
        # 取前10条最相关的
        results = []
        for item in all_content[:10]:
            content = item["content"][:500]  # 截断
            score = self._quick_similarity(query, content)
            results.append({
                **item,
                "score": score
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "results": results[:5],  # 返回top5
            "layers_found": {
                "short_term": len(layers["short_term"]),
                "mid_term": len(layers["mid_term"]),
                "long_term": len(layers["long_term"])
            }
        }
    
    def _quick_similarity(self, query: str, content: str) -> float:
        """快速相似度计算（不使用API）"""
        # 简单的词重叠计算
        query_words = set(query.lower())
        content_words = set(content.lower())
        intersection = query_words & content_words
        union = query_words | content_words
        return len(intersection) / len(union) if union else 0


# ========== 主系统 ==========

class MetaMemorySystem:
    """统一元记忆系统"""
    
    def __init__(self):
        self.original = MetaMemoryEnhanced()
        self.enhanced_index = MetaMemoryIndex(r"C:\Users\Administrator\.meta-memory\index")
        self.auto_inference = AutoInferenceEngine()
        self.three_layer = ThreeLayerRetrieval()
        self._initialized = False
        
    def initialize(self, force_rebuild: bool = False):
        print("[MetaMemory] Initializing...")
        
        # 读取内置记忆
        builtin_memories = get_all_built_in_memories()
        print(f"[MetaMemory] Built-in: {len(builtin_memories)}")
        
        # 添加到索引
        if force_rebuild:
            self.enhanced_index.rebuild_index(builtin_memories)
        else:
            self.enhanced_index.add_memories(builtin_memories)
        
        self._initialized = True
        print(f"[MetaMemory] Ready - indexed: {len(self.enhanced_index.metadata)}")
    
    # === 原有接口 ===
    
    def remember(self, content: str, agent_id: str = "assistant", **kwargs):
        return self.original.remember(content, agent_id, **kwargs)
    
    def recall(self, query: str, agent_id: str = "assistant", top_k: int = 10):
        original_results = self.original.recall(query, agent_id)
        enhanced_results = self.enhanced_index.search(query, top_k)
        return {"original": original_results, "enhanced": enhanced_results}
    
    def forget(self, memory_id: str, agent_id: str = "assistant"):
        return self.original.forget(memory_id, agent_id)
    
    def wakeup(self, memory_id: str, agent_id: str = "assistant", urgency: str = "normal"):
        return self.original.wakeup(memory_id, agent_id, urgency)
    
    def get_stats(self):
        return {
            "original": self.original.get_stats(),
            "enhanced": {
                "indexed": len(self.enhanced_index.metadata),
                "path": str(self.enhanced_index.storage_path)
            }
        }
    
    # === 增强接口 ===
    
    def search_builtin(self, query: str, top_k: int = 5):
        return self.enhanced_index.search(query, top_k)
    
    def deep_recall(self, query: str, context: Dict = None, timeout: int = 30) -> Dict:
        """
        深度回忆 - 带超时保护
        
        Args:
            query: 查询
            context: 上下文
            timeout: 超时秒数
            
        Returns:
            检索结果（限制输出防止卡住）
        """
        start_time = time.time()
        
        # 使用三层检索
        layers = self.three_layer.retrieve(query, context)
        
        # 限制每层数量
        for layer in ["short_term", "mid_term", "long_term"]:
            layers[layer] = layers[layer][:5]  # 每层最多5条
        
        # 格式化输出
        results = []
        for layer_name, memories in layers.items():
            for m in memories:
                results.append({
                    "layer": layer_name,
                    "title": m.get("title", "")[:100],
                    "content": m.get("content", "")[:300],  # 限制内容长度
                    "source": m.get("source", "")
                })
        
        elapsed = time.time() - start_time
        
        return {
            "query": query,
            "results": results[:10],  # 最多10条
            "layers": {k: len(v) for k, v in layers.items()},
            "elapsed_seconds": round(elapsed, 2),
            "total_found": len(results)
        }
    
    def auto_infer(self, query: str, context: Dict = None) -> Dict:
        """
        自动推测 - 无需触发词
        """
        if not self.auto_inference.should_activate(query):
            return {"activated": False, "reason": "No trigger words"}
        
        # 带超时
        start_time = time.time()
        result = self.auto_inference.infer(query, context)
        elapsed = time.time() - start_time
        
        return {
            "activated": True,
            "elapsed_seconds": round(elapsed, 2),
            **result
        }
    
    def sync(self):
        builtin_memories = get_all_built_in_memories()
        self.enhanced_index.add_memories(builtin_memories)
        return {
            "total_indexed": len(self.enhanced_index.metadata),
            "builtin_total": len(builtin_memories)
        }


# 全局实例
_system: Optional[MetaMemorySystem] = None


def get_system() -> MetaMemorySystem:
    global _system
    if _system is None:
        _system = MetaMemorySystem()
    return _system


# 便捷函数
def remember(content: str, agent_id: str = "assistant", **kwargs):
    return get_system().remember(content, agent_id, **kwargs)

def recall(query: str, agent_id: str = "assistant"):
    return get_system().recall(query, agent_id)

def search(query: str, top_k: int = 5):
    return get_system().search_builtin(query, top_k)

def deep_recall(query: str, timeout: int = 30):
    """深度回忆 - 带超时保护"""
    return get_system().deep_recall(query, timeout=timeout)

def auto_infer(query: str):
    """自动推测"""
    return get_system().auto_infer(query)

def get_stats():
    return get_system().get_stats()


if __name__ == "__main__":
    print("=== MetaMemory System (Enhanced) ===\n")
    
    system = get_system()
    system.initialize()
    
    print("\n--- Stats ---")
    stats = system.get_stats()
    print(f"Indexed: {stats['enhanced']['indexed']}")
    
    print("\n--- Deep Recall Test ---")
    result = deep_recall("用户偏好")
    print(f"Found: {result['total_found']}, Time: {result['elapsed_seconds']}s")
    print(f"Layers: {result['layers']}")
    
    print("\n--- Auto Infer Test ---")
    result = auto_infer("从元记忆获取我之前的工作")
    print(f"Activated: {result.get('activated')}")
