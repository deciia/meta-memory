"""
三层次记忆系统 (参考Memory Manager)
实现情景、语义、程序记忆
"""

import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import os

logger = logging.getLogger(__name__)

class ThreeLayerMemorySystem:
    """三层次记忆系统"""
    
    def __init__(self, storage, config: Dict):
        self.storage = storage
        self.config = config
        
        # 层次配置
        self.episodic_retention_days = config.get("episodic_retention_days", 30)
        self.semantic_retention_days = config.get("semantic_retention_days", 365)
        self.procedural_retention_days = config.get("procedural_retention_days", 180)
        
        # 统计信息
        self.stats = {
            "total_memories": 0,
            "episodic_count": 0,
            "semantic_count": 0,
            "procedural_count": 0,
            "last_categorization": None
        }
        
        logger.info("Three-layer memory system initialized")
    
    def categorize_memory(self, memory_id: str, memory_layer: Enum, agent_id: str = "system") -> bool:
        """
        分类记忆
        
        Args:
            memory_id: 记忆ID
            memory_layer: 记忆层次
            agent_id: 代理ID
        
        Returns:
            是否成功
        """
        try:
            # 获取记忆
            memory = self.storage.retrieve_memory(memory_id, agent_id)
            if not memory:
                return False
            
            # 设置过期时间
            if memory_layer.value == "episodic":
                expires_days = self.episodic_retention_days
            elif memory_layer.value == "semantic":
                expires_days = self.semantic_retention_days
            elif memory_layer.value == "procedural":
                expires_days = self.procedural_retention_days
            else:
                expires_days = 365  # 默认
            
            # 更新记忆
            memory.memory_layer = memory_layer
            if expires_days > 0:
                memory.expires_at = datetime.now() + timedelta(days=expires_days)
            
            # 保存回存储
            self.storage.update_memory(memory, agent_id)
            
            # 更新统计
            self._update_stats(memory_layer)
            
            logger.debug(f"Categorized memory {memory_id[:8]} as {memory_layer.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to categorize memory {memory_id}: {e}")
            return False
    
    def _update_stats(self, memory_layer: Enum):
        """更新统计"""
        layer_name = memory_layer.value
        
        if layer_name == "episodic":
            self.stats["episodic_count"] += 1
        elif layer_name == "semantic":
            self.stats["semantic_count"] += 1
        elif layer_name == "procedural":
            self.stats["procedural_count"] += 1
        
        self.stats["total_memories"] += 1
        self.stats["last_categorization"] = datetime.now().isoformat()
    
    def get_memories_by_layer(self, memory_layer: Enum, agent_id: str = "system", 
                            limit: int = 100) -> List:
        """
        获取指定层次的记忆
        
        Args:
            memory_layer: 记忆层次
            agent_id: 代理ID
            limit: 数量限制
        
        Returns:
            记忆列表
        """
        try:
            # 这里需要存储支持按层次查询
            # 简化实现：搜索所有记忆然后过滤
            all_memories = self.storage.search_memories("", agent_id, limit=limit*2)
            
            layer_memories = []
            for memory in all_memories:
                if hasattr(memory, 'memory_layer') and memory.memory_layer == memory_layer:
                    layer_memories.append(memory)
                
                if len(layer_memories) >= limit:
                    break
            
            logger.debug(f"Found {len(layer_memories)} {memory_layer.value} memories")
            return layer_memories
            
        except Exception as e:
            logger.error(f"Failed to get memories by layer {memory_layer.value}: {e}")
            return []
    
    def get_episodic_memories(self, agent_id: str = "system", limit: int = 50) -> List:
        """获取情景记忆"""
        from .core import MemoryLayer
        return self.get_memories_by_layer(MemoryLayer.EPISODIC, agent_id, limit)
    
    def get_semantic_memories(self, agent_id: str = "system", limit: int = 100) -> List:
        """获取语义记忆"""
        from .core import MemoryLayer
        return self.get_memories_by_layer(MemoryLayer.SEMANTIC, agent_id, limit)
    
    def get_procedural_memories(self, agent_id: str = "system", limit: int = 50) -> List:
        """获取程序记忆"""
        from .core import MemoryLayer
        return self.get_memories_by_layer(MemoryLayer.PROCEDURAL, agent_id, limit)
    
    def remove_memory(self, memory_id: str) -> bool:
        """
        从层次系统中移除记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            是否成功
        """
        # 这里可以添加层次特定的清理逻辑
        # 目前只是更新统计
        logger.debug(f"Removed memory {memory_id[:8]} from layer system")
        return True
    
    def run_maintenance(self) -> Dict:
        """运行维护任务"""
        maintenance_results = {
            "tasks": [],
            "expired_memories": 0,
            "layer_cleanup": {}
        }
        
        try:
            # 检查过期记忆
            now = datetime.now()
            
            # 这里可以实现层次特定的维护逻辑
            # 例如：归档旧的情景记忆，优化语义记忆等
            
            maintenance_results["tasks"].append("layer_maintenance_completed")
            logger.info("Three-layer memory maintenance completed")
            
        except Exception as e:
            maintenance_results["error"] = str(e)
            logger.error(f"Three-layer memory maintenance failed: {e}")
        
        return maintenance_results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 计算比例
        if stats["total_memories"] > 0:
            stats["episodic_percentage"] = stats["episodic_count"] / stats["total_memories"] * 100
            stats["semantic_percentage"] = stats["semantic_count"] / stats["total_memories"] * 100
            stats["procedural_percentage"] = stats["procedural_count"] / stats["total_memories"] * 100
        else:
            stats["episodic_percentage"] = 0
            stats["semantic_percentage"] = 0
            stats["procedural_percentage"] = 0
        
        # 添加配置信息
        stats["config"] = {
            "episodic_retention_days": self.episodic_retention_days,
            "semantic_retention_days": self.semantic_retention_days,
            "procedural_retention_days": self.procedural_retention_days
        }
        
        return stats
    
    def export_layer_data(self, memory_layer: Enum, format: str = "json") -> str:
        """
        导出层次数据
        
        Args:
            memory_layer: 记忆层次
            format: 导出格式
        
        Returns:
            导出的数据
        """
        try:
            memories = self.get_memories_by_layer(memory_layer, limit=1000)
            
            if format == "json":
                data = {
                    "layer": memory_layer.value,
                    "export_time": datetime.now().isoformat(),
                    "count": len(memories),
                    "memories": [mem.to_dict() for mem in memories]
                }
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                # 其他格式可以在这里扩展
                return f"Layer: {memory_layer.value}, Memories: {len(memories)}"
                
        except Exception as e:
            logger.error(f"Failed to export layer data: {e}")
            return ""
    
    def import_layer_data(self, data: str, memory_layer: Enum, agent_id: str = "system") -> Dict:
        """
        导入层次数据
        
        Args:
            data: 导入的数据
            memory_layer: 记忆层次
            agent_id: 代理ID
        
        Returns:
            导入结果
        """
        try:
            parsed = json.loads(data)
            
            if parsed.get("layer") != memory_layer.value:
                return {"success": False, "error": "Layer mismatch"}
            
            imported_count = 0
            for mem_data in parsed.get("memories", []):
                try:
                    # 创建记忆
                    memory = self.storage.create_memory_from_dict(mem_data, agent_id)
                    if memory:
                        # 分类记忆
                        self.categorize_memory(memory.id, memory_layer, agent_id)
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import memory: {e}")
            
            return {
                "success": True,
                "imported_count": imported_count,
                "total_count": len(parsed.get("memories", []))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# ========== 测试函数 ==========

def test_three_layer_memory():
    """测试三层次记忆系统"""
    print("=== Testing Three-Layer Memory ===")
    
    # 模拟存储
    class MockMemory:
        def __init__(self, id, content):
            self.id = id
            self.content = content
            self.memory_layer = None
            self.expires_at = None
    
    class MockStorage:
        def __init__(self):
            self.memories = {}
        
        def retrieve_memory(self, memory_id, agent_id):
            return self.memories.get(memory_id)
        
        def update_memory(self, memory, agent_id):
            self.memories[memory.id] = memory
            return True
        
        def search_memories(self, query, agent_id, limit=10):
            return list(self.memories.values())[:limit]
        
        def create_memory_from_dict(self, data, agent_id):
            memory = MockMemory(data.get("id", "test"), data.get("content", ""))
            return memory
    
    storage = MockStorage()
    config = {
        "episodic_retention_days": 30,
        "semantic_retention_days": 365,
        "procedural_retention_days": 180
    }
    
    system = ThreeLayerMemorySystem(storage, config)
    
    # 测试记忆分类
    from .core import MemoryLayer
    
    # 创建测试记忆
    test_memory = MockMemory("test_memory_1", "测试记忆内容")
    storage.memories[test_memory.id] = test_memory
    
    # 分类记忆
    success = system.categorize_memory(test_memory.id, MemoryLayer.EPISODIC, "test_agent")
    print(f"1. Memory categorized: {success}")
    
    if success:
        print(f"   Memory layer: {test_memory.memory_layer}")
        print(f"   Expires at: {test_memory.expires_at}")
    
    # 测试获取层次记忆
    episodic_memories = system.get_episodic_memories("test_agent", 10)
    print(f"2. Episodic memories: {len(episodic_memories)}")
    
    # 测试统计
    stats = system.get_stats()
    print(f"3. System stats: {stats}")
    
    # 测试维护
    maintenance = system.run_maintenance()
    print(f"4. Maintenance results: {maintenance}")
    
    print("\n=== Three-layer memory test completed ===")
    return True

if __name__ == "__main__":
    test_three_layer_memory()