"""
Meta-Memory Skill Enhanced (增强版)
基于5个参考技能优化的元记忆技能

核心改进:
1. 向量搜索集成 (Elite Longterm Memory)
2. 智能预测唤醒 (Cognitive Memory)
3. 三层次记忆架构 (Memory Manager)
4. 完善监控维护 (Memory Hygiene)

保持6个核心需求不变:
1. 元技能性质
2. 完全本地存储
3. 遗忘和唤醒功能
4. 记忆百分百不丢失
5. 压缩保存和快捷调取
6. 多代理共享记忆
"""

from .core import (
    MetaMemoryEnhanced,
    MemoryRecord,
    MemoryState,
    MemoryPriority,
    MemoryLayer,
    MemoryType
)

from .vector_search import VectorSearchEngine
from .predictive_wakeup import PredictiveWakeupSystem
from .three_layer_memory import ThreeLayerMemorySystem
# from .enhanced_monitoring import EnhancedMonitoringSystem  # TODO: Implement

__version__ = "2.0.0"
__author__ = "小艾 (基于5个参考技能优化)"
__description__ = "增强版元记忆技能 - 集成向量搜索、智能预测唤醒、三层次架构和完善监控"

__all__ = [
    "MetaMemoryEnhanced",
    "MemoryRecord",
    "MemoryState",
    "MemoryPriority",
    "MemoryLayer",
    "MemoryType",
    "VectorSearchEngine",
    "PredictiveWakeupSystem",
    "ThreeLayerMemorySystem",
    # "EnhancedMonitoringSystem"  # TODO: Implement
]