"""
元记忆增强层 - 主模块
作为外部增强层，增强 OpenClaw 内置记忆系统
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from builtin_reader import get_all_built_in_memories, get_memory_stats, read_memory_md, read_daily_logs
from ollama_embedder import MetaMemoryIndex, OllamaEmbedder


class MetaMemoryEnhancer:
    """
    元记忆增强器
    - 读取内置记忆（只读）
    - 向量化存储（外部）
    - 提供增强能力
    """
    
    def __init__(self, index_path: str = None):
        self.index_path = index_path
        self.index = MetaMemoryIndex(index_path)
        self._initialized = False
    
    def initialize(self, force_rebuild: bool = False):
        """初始化 - 同步内置记忆到索引"""
        print("[MetaMemory] 初始化增强层...")
        
        # 读取内置记忆
        memories = get_all_built_in_memories()
        print(f"[MetaMemory] 读取到 {len(memories)} 条内置记忆")
        
        # 添加到索引
        if force_rebuild:
            print("[MetaMemory] 重建索引...")
            self.index.rebuild_index(memories)
        else:
            print("[MetaMemory] 增量添加...")
            self.index.add_memories(memories)
        
        self._initialized = True
        print(f"[MetaMemory] 初始化完成，索引包含 {len(self.index.metadata)} 条")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索 - 增强版
        不仅搜索关键词，还理解语义
        """
        if not self._initialized:
            self.initialize()
        
        return self.index.search(query, top_k)
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """
        建议优化 - 基于分析
        例如：可以提炼的知识点、可以压缩的内容
        """
        suggestions = []
        
        # 分析 daily logs，找出可以提炼到 MEMORY.md 的内容
        daily = read_daily_logs()
        
        for d in daily:
            # 简单启发式：包含"经验"、"原则"、"偏好"的内容
            if any(kw in d["content"] for kw in ["经验", "原则", "偏好", "用户要求"]):
                suggestions.append({
                    "type": "promote",
                    "source": d["source"],
                    "title": d["title"],
                    "reason": "可能值得提炼到 MEMORY.md",
                    "content_preview": d["content"][:200]
                })
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取增强层统计"""
        builtin_stats = get_memory_stats()
        index_stats = {
            "indexed": len(self.index.metadata),
            "vector_dim": self.index.embedder.dimension,
            "model": self.index.embedder.model
        }
        
        return {
            "builtin": builtin_stats,
            "enhancer": index_stats
        }
    
    def sync(self):
        """同步 - 增量更新索引"""
        # 读取新的内置记忆
        memories = get_all_built_in_memories()
        
        # 添加新记忆
        self.index.add_memories(memories)
        
        return {
            "total_indexed": len(self.index.metadata),
            "builtin_total": get_memory_stats()["total"]
        }


# 全局实例
_enhancer: Optional[MetaMemoryEnhancer] = None


def get_enhancer() -> MetaMemoryEnhancer:
    """获取全局增强器实例"""
    global _enhancer
    if _enhancer is None:
        _enhancer = MetaMemoryEnhancer()
    return _enhancer


def search_memories(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """便捷函数：搜索记忆"""
    enhancer = get_enhancer()
    return enhancer.search(query, top_k)


def suggest_memory_updates() -> List[Dict[str, Any]]:
    """便捷函数：获取优化建议"""
    enhancer = get_enhancer()
    return enhancer.suggest_optimizations()


if __name__ == "__main__":
    # 测试
    print("=== 元记忆增强层测试 ===\n")
    
    enhancer = get_enhancer()
    enhancer.initialize()
    
    print("\n=== 统计信息 ===")
    stats = enhancer.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n=== 语义搜索测试 ===")
    results = search_memories("用户偏好")
    for r in results:
        print(f"\n[{r['score']:.3f}] {r['title'][:50]}")
        print(f"  来源: {r['source']} | 类型: {r['type']}")
    
    print("\n=== 优化建议 ===")
    suggestions = suggest_memory_updates()
    for s in suggestions:
        print(f"\n[{s['type']}] {s['title'][:40]}")
        print(f"  原因: {s['reason']}")
