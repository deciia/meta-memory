"""
元记忆增强层 - 继承版
继承原有元记忆核心功能，同时增强 OpenClaw 内置记忆系统
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加 src 路径
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# 导入原有元记忆模块
ORIGINAL_MODELS_AVAILABLE = False

try:
    # 直接导入，避免相对导入问题
    import importlib.util
    
    # 尝试加载 core
    spec = importlib.util.spec_from_file_location("core", src_path / "core.py")
    if spec and spec.loader:
        core_module = importlib.util.module_from_spec(spec)
        sys.modules['core'] = core_module
        spec.loader.exec_module(core_module)
        from core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        # 加载其他模块
        for mod_name in ["vector_search", "predictive_wakeup", "three_layer_memory", "auto_probe"]:
            try:
                spec = importlib.util.spec_from_file_location(mod_name, src_path / f"{mod_name}.py")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Warning: Could not load {mod_name}: {e}")
        
        from vector_search import VectorSearchEngine
        from predictive_wakeup import PredictiveWakeupSystem
        from three_layer_memory import ThreeLayerMemorySystem
        from auto_probe import create_auto_probe
        
        ORIGINAL_MODELS_AVAILABLE = True
        print("[Enhancer] Original modules loaded successfully")
        
except Exception as e:
    print(f"Warning: Original meta-memory modules not fully available: {e}")

# 新增模块
from builtin_reader import get_all_built_in_memories, get_memory_stats, read_memory_md, read_daily_logs
from ollama_embedder import MetaMemoryIndex


class MetaMemoryEnhancer:
    """
    元记忆增强器（继承版）
    
    继承原有功能：
    - MetaMemoryEnhanced 核心系统
    - VectorSearchEngine 向量搜索
    - PredictiveWakeupSystem 预测唤醒
    - ThreeLayerMemorySystem 三层记忆
    - AutoProbeEngine 自动探测
    
    增强功能：
    - 读取内置记忆（只读）
    - 语义搜索增强
    - 优化建议
    """
    
    def __init__(self, index_path: str = None):
        self.index_path = index_path or r"C:\Users\Administrator\.meta_memory"
        
        # 向量索引（新增）
        self.index = MetaMemoryIndex(self.index_path)
        
        # 原有元记忆系统（继承）
        self.original_memory = None
        self.vector_engine = None
        self.wakeup_system = None
        self.three_layer = None
        self.auto_probe = None
        
        # 初始化继承模块
        self._init_original_modules()
        
        self._initialized = False
    
    def _init_original_modules(self):
        """初始化原有元记忆模块"""
        if not ORIGINAL_MODELS_AVAILABLE:
            return
            
        try:
            # 原有核心系统
            self.original_memory = MetaMemoryEnhanced()
            print("[Enhancer] Original MetaMemoryEnhanced loaded")
            
            # 向量搜索
            self.vector_engine = VectorSearchEngine({
                "enable_vector_search": True,
                "vector_model": "all-MiniLM-L6-v2"
            })
            print("[Enhancer] Original VectorSearchEngine loaded")
            
            # 预测唤醒
            self.wakeup_system = PredictiveWakeupSystem({})
            print("[Enhancer] Original PredictiveWakeupSystem loaded")
            
            # 三层记忆
            self.three_layer = ThreeLayerMemorySystem({})
            print("[Enhancer] Original ThreeLayerMemorySystem loaded")
            
            # 自动探测
            self.auto_probe = create_auto_probe({})
            print("[Enhancer] Original AutoProbeEngine loaded")
            
        except Exception as e:
            print(f"[Enhancer] Error loading original modules: {e}")
    
    def initialize(self, force_rebuild: bool = False):
        """初始化 - 同步内置记忆到索引"""
        print("[MetaMemory-Enhancer] Initializing...")
        
        # 1. 读取内置记忆
        memories = get_all_built_in_memories()
        print(f"[MetaMemory-Enhancer] Read {len(memories)} built-in memories")
        
        # 2. 添加到索引
        if force_rebuild:
            print("[MetaMemory-Enhancer] Rebuilding index...")
            self.index.rebuild_index(memories)
        else:
            print("[MetaMemory-Enhancer] Incremental adding...")
            self.index.add_memories(memories)
        
        # 3. 同步到原有系统（如果可用）
        if self.original_memory:
            print("[MetaMemory-Enhancer] Syncing to original system...")
            for mem in memories:
                self.original_memory.remember(
                    content=mem["content"],
                    agent_id="builtin",
                    memory_layer=MemoryLayer.SEMANTIC,
                    memory_type=MemoryType.CONVERSATION,
                    priority=MemoryPriority.MEDIUM
                )
        
        self._initialized = True
        print(f"[MetaMemory-Enhancer] Ready, indexed {len(self.index.metadata)} memories")
    
    def remember(self, content: str, agent_id: str = "assistant", **kwargs):
        """存储记忆（兼容原有接口）"""
        if self.original_memory:
            return self.original_memory.remember(content, agent_id, **kwargs)
        return None
    
    def recall(self, query: str, agent_id: str = "assistant", **kwargs):
        """检索记忆（优先使用增强搜索）"""
        # 1. 先用增强索引搜索
        enhanced_results = self.index.search(query, top_k=10)
        
        # 2. 如果有原有系统，也搜索
        if self.original_memory:
            original_results = self.original_memory.recall(query, agent_id, **kwargs)
            # 合并结果
            return {
                "enhanced": enhanced_results,
                "original": original_results,
                "combined": self._merge_results(enhanced_results, original_results)
            }
        
        return {"enhanced": enhanced_results, "original": [], "combined": enhanced_results}
    
    def _merge_results(self, enhanced: List, original: List) -> List:
        """合并搜索结果"""
        merged = {}
        
        # 添加增强结果
        for r in enhanced:
            merged[r["id"]] = {"source": "enhanced", **r}
        
        # 添加原有结果
        for r in original:
            if r.get("id") not in merged:
                merged[r.get("id", "")] = {"source": "original", **r}
        
        return list(merged.values())[:10]
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索 - 增强版
        """
        if not self._initialized:
            self.initialize()
        
        return self.index.search(query, top_k)
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """优化建议"""
        suggestions = []
        
        # 分析 daily logs
        daily = read_daily_logs()
        for d in daily:
            if any(kw in d["content"] for kw in ["经验", "原则", "偏好", "用户要求", "安全", "配置"]):
                suggestions.append({
                    "type": "promote",
                    "source": d["source"],
                    "title": d["title"],
                    "reason": "May be worth promoting to MEMORY.md",
                    "content_preview": d["content"][:200]
                })
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        builtin_stats = get_memory_stats()
        index_stats = {
            "indexed": len(self.index.metadata),
            "vector_dim": self.index.embedder.dimension,
            "model": self.index.embedder.model
        }
        
        # 原有系统状态
        original_stats = {}
        if self.original_memory:
            try:
                stats = self.original_memory.get_stats()
                original_stats = {
                    "total_memories": stats.get("total_memories", 0),
                    "active": stats.get("active_memories", 0),
                    "dormant": stats.get("dormant_memories", 0)
                }
            except:
                pass
        
        return {
            "builtin": builtin_stats,
            "enhancer": index_stats,
            "original": original_stats,
            "features": {
                "vector_search": self.vector_engine is not None,
                "predictive_wakeup": self.wakeup_system is not None,
                "three_layer": self.three_layer is not None,
                "auto_probe": self.auto_probe is not None
            }
        }
    
    def sync(self):
        """同步"""
        memories = get_all_built_in_memories()
        self.index.add_memories(memories)
        
        return {
            "total_indexed": len(self.index.metadata),
            "builtin_total": get_memory_stats()["total"]
        }


# 全局实例
_enhancer: Optional[MetaMemoryEnhancer] = None


def get_enhancer() -> MetaMemoryEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = MetaMemoryEnhancer()
    return _enhancer


def search_memories(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    enhancer = get_enhancer()
    return enhancer.search(query, top_k)


def suggest_memory_updates() -> List[Dict[str, Any]]:
    enhancer = get_enhancer()
    return enhancer.suggest_optimizations()


def remember(content: str, agent_id: str = "assistant", **kwargs):
    """存储记忆"""
    enhancer = get_enhancer()
    return enhancer.remember(content, agent_id, **kwargs)


def recall(query: str, agent_id: str = "assistant", **kwargs):
    """检索记忆"""
    enhancer = get_enhancer()
    return enhancer.recall(query, agent_id, **kwargs)


if __name__ == "__main__":
    import json
    
    print("=== MetaMemory Enhancer (Inherited) ===\n")
    
    enhancer = get_enhancer()
    enhancer.initialize()
    
    print("\n=== Stats ===")
    stats = enhancer.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n=== Search Test ===")
    results = search_memories("user preference")
    for r in results[:3]:
        print(f"  [{r.get('score', 0):.3f}] {r.get('title', 'N/A')[:50]}")
    
    print("\n=== Suggestions ===")
    suggestions = suggest_memory_updates()
    print(f"  Found {len(suggestions)} suggestions")
