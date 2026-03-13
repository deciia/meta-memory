# -*- coding: utf-8 -*-
"""
增强版核心系统
集成5个参考技能的优秀特性
"""

import logging
import json
import hashlib
import sqlite3
import zlib
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
import tempfile
import shutil
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meta_memory.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== 枚举定义 ==========

class MemoryState(Enum):
    """记忆状态"""
    ACTIVE = "active"        # 活跃状态
    DORMANT = "dormant"      # 休眠状态 (压缩存储)
    COMPRESSED = "compressed" # 深度压缩状态
    ARCHIVED = "archived"    # 归档状态 (长期存储)

class MemoryPriority(Enum):
    """记忆优先级"""
    TRIVIAL = 1      # 琐碎
    LOW = 2          # 低
    MEDIUM = 3       # 中
    HIGH = 4         # 高
    CRITICAL = 5     # 关键

class MemoryLayer(Enum):
    """记忆层次 (参考Memory Manager)"""
    EPISODIC = "episodic"    # 情景记忆: 具体事件和经历
    SEMANTIC = "semantic"    # 语义记忆: 事实和知识
    PROCEDURAL = "procedural" # 程序记忆: 技能和流程

class MemoryType(Enum):
    """记忆类型 (参考Elite Longterm Memory)"""
    TEXT = "text"            # 文本
    CODE = "code"            # 代码
    CONVERSATION = "conversation" # 对话
    FACT = "fact"            # 事实
    LESSON = "lesson"        # 教训
    PREFERENCE = "preference" # 偏好
    SKILL = "skill"          # 技能

class CompressionAlgorithm(Enum):
    """压缩算法"""
    ZLIB = "zlib"            # 标准压缩
    GZIP = "gzip"            # Gzip压缩
    NONE = "none"            # 不压缩

# ========== 数据类定义 ==========

@dataclass
class MemoryRecord:
    """记忆记录 (增强版)"""
    id: str = field(default_factory=lambda: hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16])
    content: str = ""
    compressed_content: bytes = b""
    original_size: int = 0
    compression_ratio: float = 1.0
    compression_algorithm: CompressionAlgorithm = CompressionAlgorithm.ZLIB
    
    # 分类信息
    tags: List[str] = field(default_factory=list)
    memory_layer: MemoryLayer = MemoryLayer.SEMANTIC
    memory_type: MemoryType = MemoryType.TEXT
    source: str = "system"
    
    # 重要性评估
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance_score: float = 0.5
    context_keywords: List[str] = field(default_factory=list)
    
    # 状态管理
    state: MemoryState = MemoryState.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    last_wakeup: Optional[datetime] = None
    access_count: int = 0
    wakeup_count: int = 0
    
    # 生命周期
    expires_at: Optional[datetime] = None
    scheduled_wakeup: Optional[datetime] = None
    auto_forget_threshold: float = 0.3
    
    # 所有权和共享
    owner_agent: str = "system"
    shared_with: Dict[str, str] = field(default_factory=dict)  # agent_id -> permission
    
    # 使用历史
    access_history: List[Dict] = field(default_factory=list)
    
    # Token优化
    estimated_tokens: int = 0
    last_token_check: Optional[datetime] = None
    
    # 向量嵌入 (用于语义搜索)
    embedding: Optional[List[float]] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # 衰减参数 (参考Cognitive Memory)
    decay_rate: float = 0.95  # 每日衰减率
    last_decay_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        data['state'] = self.state.value
        data['priority'] = self.priority.value
        data['memory_layer'] = self.memory_layer.value
        data['memory_type'] = self.memory_type.value
        data['compression_algorithm'] = self.compression_algorithm.value
        
        # 处理日期时间
        for key in ['created_at', 'last_accessed', 'last_wakeup', 'expires_at', 
                   'scheduled_wakeup', 'last_token_check', 'last_decay_update']:
            if getattr(self, key):
                data[key] = getattr(self, key).isoformat()
            else:
                data[key] = None
        
        # 处理嵌入向量
        if self.embedding:
            data['embedding'] = json.dumps(self.embedding)
        else:
            data['embedding'] = None
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryRecord':
        """从字典创建"""
        # 处理枚举类型
        if 'state' in data and data['state']:
            data['state'] = MemoryState(data['state'])
        if 'priority' in data and data['priority']:
            data['priority'] = MemoryPriority(data['priority'])
        if 'memory_layer' in data and data['memory_layer']:
            data['memory_layer'] = MemoryLayer(data['memory_layer'])
        if 'memory_type' in data and data['memory_type']:
            data['memory_type'] = MemoryType(data['memory_type'])
        if 'compression_algorithm' in data and data['compression_algorithm']:
            data['compression_algorithm'] = CompressionAlgorithm(data['compression_algorithm'])
        
        # 处理日期时间
        date_fields = ['created_at', 'last_accessed', 'last_wakeup', 'expires_at',
                      'scheduled_wakeup', 'last_token_check', 'last_decay_update']
        for field in date_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field])
            else:
                data[field] = None
        
        # 处理嵌入向量
        if 'embedding' in data and data['embedding']:
            data['embedding'] = json.loads(data['embedding'])
        else:
            data['embedding'] = None
        
        return cls(**data)
    
    def estimate_tokens(self) -> int:
        """估计token数量 (简单实现)"""
        if self.estimated_tokens > 0:
            return self.estimated_tokens
        
        # 简单估算: 4个字符约等于1个token
        self.estimated_tokens = max(1, len(self.content) // 4)
        self.last_token_check = datetime.now()
        return self.estimated_tokens
    
    def update_decay(self) -> float:
        """更新衰减分数 (参考Cognitive Memory)"""
        now = datetime.now()
        days_passed = (now - self.last_decay_update).days
        
        if days_passed > 0:
            # 应用衰减
            decay_factor = self.decay_rate ** days_passed
            self.importance_score *= decay_factor
            self.last_decay_update = now
            
            logger.debug(f"Updated decay for memory {self.id}: "
                        f"days={days_passed}, decay_factor={decay_factor:.3f}, "
                        f"new_score={self.importance_score:.3f}")
        
        return self.importance_score

# ========== 增强版核心系统 ==========

class MetaMemoryEnhanced:
    """增强版元记忆系统"""
    
    def __init__(self, storage_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        初始化增强版系统
        
        Args:
            storage_path: 数据库存储路径
            config: 配置字典
        """
        self.config = self._load_config(config)
        self.db_path = self._get_db_path(storage_path)
        
        # 初始化组件
        self.storage = self._init_storage()
        self.vector_search = self._init_vector_search()
        self.predictive_wakeup = self._init_predictive_wakeup()
        self.three_layer_memory = self._init_three_layer_memory()
        self.monitoring = self._init_monitoring()
        self.coordinator = self._init_coordinator()
        self.optimizer = self._init_optimizer()
        
        # 初始化数据库
        self._init_database()
        
        logger.info(f"MetaMemoryEnhanced initialized at {self.db_path}")
        logger.info(f"Config: {json.dumps(self.config, indent=2, default=str)}")
    
    def _load_config(self, config: Optional[Dict]) -> Dict:
        """加载配置"""
        default_config = {
            "storage": {
                "compression_algorithm": "zlib",
                "compression_level": 3,
                "auto_backup": True,
                "backup_interval_hours": 24,
                "max_backups": 7,
                "backup_path": "~/.meta-memory/backups"
            },
            "retrieval": {
                "enable_fts": True,
                "enable_vector_search": True,
                "vector_model": "all-MiniLM-L6-v2",
                "hybrid_search_weight": 0.7,  # 向量搜索权重
                "cache_size": 100,
                "cache_ttl_seconds": 3600
            },
            "optimization": {
                "target_token_reduction": 0.5,
                "auto_forget_enabled": True,
                "forget_threshold": 0.3,
                "min_importance_active": 0.5,
                "wakeup_prediction": True,
                "decay_enabled": True,
                "decay_rate": 0.95
            },
            "multi_agent": {
                "enabled": True,
                "default_permission": "read",
                "conflict_resolution": "timestamp",
                "sync_interval_seconds": 300
            },
            "monitoring": {
                "enable_logging": True,
                "log_retention_days": 30,
                "performance_monitoring": True,
                "health_check_interval_hours": 1,
                "vector_audit_enabled": True,
                "maintenance_automation": True
            },
            "memory_layers": {
                "enabled": True,
                "episodic_retention_days": 30,
                "semantic_retention_days": 365,
                "procedural_retention_days": 180
            }
        }
        
        if config:
            # 深度合并配置
            import copy
            merged = copy.deepcopy(default_config)
            self._deep_update(merged, config)
            return merged
        return default_config
    
    def _deep_update(self, target: Dict, source: Dict):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _get_db_path(self, storage_path: Optional[str]) -> str:
        """获取数据库路径"""
        if storage_path:
            return storage_path
        
        # 默认路径 - 统一存储到 .meta-memory
        storage_dir = Path.home() / ".meta-memory"
        storage_dir.mkdir(exist_ok=True)
        return str(storage_dir / "memory.db")
    
    def _init_storage(self):
        """初始化存储引擎"""
        from .storage_enhanced import EnhancedMetaMemoryStorage
        return EnhancedMetaMemoryStorage(
            db_path=self.db_path,
            config=self.config["storage"]
        )
    
    def _init_vector_search(self):
        """初始化向量搜索引擎"""
        from .vector_search import VectorSearchEngine
        return VectorSearchEngine(
            config=self.config["retrieval"]
        )
    
    def _init_predictive_wakeup(self):
        """初始化预测唤醒系统"""
        from .predictive_wakeup import PredictiveWakeupSystem
        return PredictiveWakeupSystem(
            storage=self.storage,
            config=self.config["optimization"]
        )
    
    def _init_three_layer_memory(self):
        """初始化三层次记忆系统"""
        from .three_layer_memory import ThreeLayerMemorySystem
        return ThreeLayerMemorySystem(
            storage=self.storage,
            config=self.config["memory_layers"]
        )
    
    def _init_monitoring(self):
        """初始化监控系统"""
        # 简化监控系统
        class SimpleMonitoringSystem:
            def __init__(self, storage, config):
                self.storage = storage
                self.config = config
            
            def get_stats(self):
                return {"status": "simple_monitoring"}
            
            def run_maintenance(self):
                return {"tasks": ["simple_maintenance"]}
            
            def audit_vector_memories(self):
                return {"status": "not_implemented"}
        
        return SimpleMonitoringSystem(
            storage=self.storage,
            config=self.config["monitoring"]
        )
    
    def _init_coordinator(self):
        """初始化协调器"""
        # 简化协调器
        class SimpleCoordinationEngine:
            def __init__(self, storage, config):
                self.storage = storage
                self.config = config
                self.agents = {}
            
            def share_memory(self, memory_id, target_agent_id, permission, agent_id):
                # 实际实现：在数据库中设置共享权限
                try:
                    cursor = self.storage.conn.cursor()
                    
                    # 检查记忆是否存在且属于发起代理
                    cursor.execute(
                        "SELECT owner_agent FROM memories WHERE id = ?",
                        (memory_id,)
                    )
                    memory = cursor.fetchone()
                    
                    if not memory:
                        return False
                    
                    owner_agent = memory[0]
                    if owner_agent != agent_id:
                        # 只有记忆所有者可以共享
                        return False
                    
                    # 设置共享权限
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO sharing_permissions 
                        (memory_id, agent_id, permission, granted_at)
                        VALUES (?, ?, ?, datetime('now'))
                        """,
                        (memory_id, target_agent_id, permission)
                    )
                    
                    self.storage.conn.commit()
                    return True
                    
                except Exception as e:
                    print(f"[ERROR] 设置共享权限失败: {e}")
                    return False
            
            def register_agent(self, agent_id, agent_name, public_key):
                self.agents[agent_id] = {
                    "name": agent_name,
                    "public_key": public_key,
                    "created_at": datetime.now().isoformat()
                }
                return True
            
            def sync_agent(self, agent_id):
                return {"status": "synced", "agent_id": agent_id}
            
            def get_stats(self):
                return {
                    "total_agents": len(self.agents),
                    "agents": list(self.agents.keys())
                }
        
        return SimpleCoordinationEngine(
            storage=self.storage,
            config=self.config["multi_agent"]
        )
    
    def _init_optimizer(self):
        """初始化优化器"""
        # 简化优化器
        class SimpleOptimizationEngine:
            def __init__(self, storage, config):
                self.storage = storage
                self.config = config
            
            def optimize_context(self, memories, max_tokens=4000):
                # 简单优化：按重要性排序，选择最重要的记忆
                if not memories:
                    return []
                
                # 按重要性排序
                sorted_memories = sorted(memories, 
                                       key=lambda m: getattr(m, 'importance_score', 0.5), 
                                       reverse=True)
                
                # 计算token总数
                total_tokens = 0
                optimized = []
                
                for memory in sorted_memories:
                    # 估计token数
                    if hasattr(memory, 'estimate_tokens'):
                        token_count = memory.estimate_tokens()
                    else:
                        # 简单估算
                        content = getattr(memory, 'content', '')
                        token_count = max(1, len(content) // 4)
                    
                    if total_tokens + token_count <= max_tokens:
                        optimized.append(memory)
                        total_tokens += token_count
                    else:
                        break
                
                return optimized
        
        return SimpleOptimizationEngine(
            storage=self.storage,
            config=self.config["optimization"]
        )
    
    def _init_database(self):
        """初始化数据库"""
        self.storage.initialize()
        logger.info("Database initialized")
    
    # ========== 核心API ==========
    
    def remember(self, content: str, agent_id: str = "system", **kwargs) -> str:
        """
        存储记忆 (增强版)
        
        Args:
            content: 记忆内容
            agent_id: 代理ID
            **kwargs: 额外参数
                - tags: 标签列表
                - memory_layer: 记忆层次
                - memory_type: 记忆类型
                - priority: 优先级
                - embedding: 预计算嵌入向量
        
        Returns:
            记忆ID
        """
        # 提取记忆层次和类型
        memory_layer = kwargs.pop('memory_layer', MemoryLayer.SEMANTIC)
        memory_type = kwargs.pop('memory_type', MemoryType.TEXT)
        
        # 存储记忆
        memory_id = self.storage.store_memory(
            content=content,
            agent_id=agent_id,
            memory_layer=memory_layer,
            memory_type=memory_type,
            **kwargs
        )
        
        # 如果启用了向量搜索，生成嵌入向量
        if self.config["retrieval"]["enable_vector_search"]:
            self.vector_search.index_memory(memory_id, content, agent_id)
        
        # 记录到三层次记忆系统
        if self.config["memory_layers"]["enabled"]:
            self.three_layer_memory.categorize_memory(memory_id, memory_layer, agent_id)
        
        logger.info(f"Remembered memory {memory_id} (layer: {memory_layer.value}, type: {memory_type.value})")
        return memory_id
    
    def recall(self, query: str, agent_id: str = "system", **kwargs) -> List[MemoryRecord]:
        """
        回忆记忆 (增强版 - 混合搜索)
        
        Args:
            query: 查询词
            agent_id: 代理ID
            **kwargs: 额外参数
                - memory_layer: 限制记忆层次
                - memory_type: 限制记忆类型
                - use_vector_search: 是否使用向量搜索
                - limit: 返回数量限制
        
        Returns:
            记忆记录列表
        """
        use_vector_search = kwargs.pop('use_vector_search', 
                                     self.config["retrieval"]["enable_vector_search"])
        
        if use_vector_search and self.vector_search.is_available():
            # 使用混合搜索
            vector_results = self.vector_search.semantic_search(query, agent_id, **kwargs)
            fts_results = self.storage.search_memories(query, agent_id, **kwargs)
            
            # 合并和去重结果
            results = self._merge_search_results(vector_results, fts_results, query)
        else:
            # 使用传统搜索
            results = self.storage.search_memories(query, agent_id, **kwargs)
        
        # 应用预测性唤醒
        if self.config["optimization"]["wakeup_prediction"] and results:
            self.predictive_wakeup.predict_and_wakeup(query, agent_id)
        
        logger.info(f"Recalled {len(results)} memories for query: {query}")
        return results
    
    def _merge_search_results(self, vector_results: List[MemoryRecord], 
                            fts_results: List[MemoryRecord], query: str) -> List[MemoryRecord]:
        """合并向量搜索和全文搜索结果"""
        # 简单的合并策略：基于分数排序
        all_results = {}
        
        # 收集向量搜索结果
        for i, mem in enumerate(vector_results):
            score = 1.0 - (i * 0.1)  # 简单分数
            if mem.id not in all_results:
                all_results[mem.id] = {"memory": mem, "score": score * self.config["retrieval"]["hybrid_search_weight"]}
        
        # 收集全文搜索结果
        for i, mem in enumerate(fts_results):
            score = 1.0 - (i * 0.1)  # 简单分数
            if mem.id in all_results:
                all_results[mem.id]["score"] += score * (1 - self.config["retrieval"]["hybrid_search_weight"])
            else:
                all_results[mem.id] = {"memory": mem, "score": score * (1 - self.config["retrieval"]["hybrid_search_weight"])}
        
        # 按分数排序
        sorted_results = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)
        return [item["memory"] for item in sorted_results]
    
    def forget(self, memory_id: str, agent_id: str = "system", permanent: bool = False) -> bool:
        """
        遗忘记忆
        
        Args:
            memory_id: 记忆ID
            agent_id: 代理ID
            permanent: 是否永久删除
        
        Returns:
            是否成功
        """
        if permanent:
            success = self.storage.delete_memory(memory_id, agent_id)
            if success:
                # 从向量索引中删除
                if self.config["retrieval"]["enable_vector_search"]:
                    self.vector_search.remove_from_index(memory_id)
                
                # 从三层次记忆中删除
                if self.config["memory_layers"]["enabled"]:
                    self.three_layer_memory.remove_memory(memory_id)
                
                logger.info(f"Permanently deleted memory {memory_id}")
        else:
            success = self.storage.forget_memory(memory_id, agent_id)
            if success:
                logger.info(f"Forgot memory {memory_id} (compressed storage)")
        
        return success
    
    def wakeup(self, memory_id: str, agent_id: str = "system", urgency: str = "normal") -> Optional[MemoryRecord]:
        """
        唤醒记忆 (增强版 - 支持紧急程度)
        
        Args:
            memory_id: 记忆ID
            agent_id: 代理ID
            urgency: 紧急程度 (emergency/normal/background)
        
        Returns:
            记忆记录
        """
        memory = self.storage.retrieve_memory(memory_id, agent_id)
        
        if memory and memory.state in [MemoryState.DORMANT, MemoryState.COMPRESSED]:
            # 应用预测性唤醒优化
            if self.config["optimization"]["wakeup_prediction"]:
                memory = self.predictive_wakeup.optimized_wakeup(memory_id, agent_id, urgency)
            else:
                memory = self.storage.wakeup_memory(memory_id, agent_id)
            
            if memory:
                logger.info(f"Woke up memory {memory_id} (urgency: {urgency})")
        
        return memory
    
    def share(self, memory_id: str, target_agent_id: str, 
             permission: str = "read", agent_id: str = "system") -> bool:
        """
        共享记忆
        
        Args:
            memory_id: 记忆ID
            target_agent_id: 目标代理ID
            permission: 权限 (read/write/admin)
            agent_id: 发起代理ID
        
        Returns:
            是否成功
        """
        success = self.coordinator.share_memory(memory_id, target_agent_id, permission, agent_id)
        if success:
            logger.info(f"Shared memory {memory_id} with agent {target_agent_id} (permission: {permission})")
        
        return success
    
    def get_permissions(self, memory_id: str) -> Dict:
        """
        获取记忆的权限信息
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            权限信息字典
        """
        try:
            cursor = self.storage.conn.cursor()
            
            # 获取记忆所有者
            cursor.execute(
                "SELECT owner_agent FROM memories WHERE id = ?",
                (memory_id,)
            )
            memory = cursor.fetchone()
            
            if not memory:
                return {"error": "Memory not found"}
            
            owner_agent = memory[0]
            
            # 获取共享权限
            cursor.execute(
                "SELECT agent_id, permission FROM sharing_permissions WHERE memory_id = ?",
                (memory_id,)
            )
            shared_permissions = cursor.fetchall()
            
            permissions = {
                "memory_id": memory_id,
                "owner": owner_agent,
                "shared_with": {agent: perm for agent, perm in shared_permissions}
            }
            
            return permissions
            
        except Exception as e:
            return {"error": str(e)}
    def optimize_context(self, memories: List[MemoryRecord], 
                        max_tokens: int = 4000) -> List[MemoryRecord]:
        """
        优化上下文 (增强版)
        
        Args:
            memories: 记忆列表
            max_tokens: 最大token数
        
        Returns:
            优化后的记忆列表
        """
        return self.optimizer.optimize_context(memories, max_tokens)
    
    def get_memory(self, memory_id: str, agent_id: str = "system") -> Optional[Any]:
        """
        直接获取记忆
        
        Args:
            memory_id: 记忆ID
            agent_id: 代理ID
        
        Returns:
            记忆记录或None
        """
        from .core import MemoryRecord
        
        # 使用storage的retrieve_memory方法
        memory = self.storage.retrieve_memory(memory_id, agent_id)
        
        if memory:
            logger.info(f"Retrieved memory {memory_id} for agent {agent_id}")
        
        return memory
    
    def get_stats(self) -> Dict:
        """
        获取系统统计信息 (增强版)
        
        Returns:
            统计信息字典
        """
        base_stats = self.storage.get_stats()
        
        # 添加增强统计
        enhanced_stats = {
            "base": base_stats,
            "vector_search": self.vector_search.get_stats() if self.config["retrieval"]["enable_vector_search"] else {},
            "predictive_wakeup": self.predictive_wakeup.get_stats() if self.config["optimization"]["wakeup_prediction"] else {},
            "three_layer_memory": self.three_layer_memory.get_stats() if self.config["memory_layers"]["enabled"] else {},
            "monitoring": self.monitoring.get_stats(),
            "multi_agent": self.coordinator.get_stats() if self.config["multi_agent"]["enabled"] else {}
        }
        
        return enhanced_stats
    
    def run_maintenance(self) -> Dict:
        """
        运行维护任务 (增强版)
        
        Returns:
            维护结果
        """
        maintenance_results = {}
        
        # 运行存储维护
        storage_maintenance = self.storage.run_maintenance()
        maintenance_results["storage"] = storage_maintenance
        
        # 运行监控维护
        if self.config["monitoring"]["maintenance_automation"]:
            monitoring_maintenance = self.monitoring.run_maintenance()
            maintenance_results["monitoring"] = monitoring_maintenance
        
        # 运行向量审计
        if self.config["monitoring"]["vector_audit_enabled"] and self.config["retrieval"]["enable_vector_search"]:
            vector_audit = self.monitoring.audit_vector_memories()
            maintenance_results["vector_audit"] = vector_audit
        
        # 运行三层次记忆维护
        if self.config["memory_layers"]["enabled"]:
            layer_maintenance = self.three_layer_memory.run_maintenance()
            maintenance_results["memory_layers"] = layer_maintenance
        
        # 运行预测性唤醒维护
        if self.config["optimization"]["wakeup_prediction"]:
            predictive_maintenance = self.predictive_wakeup.run_maintenance()
            maintenance_results["predictive_wakeup"] = predictive_maintenance
        
        logger.info(f"Ran enhanced maintenance: {len(maintenance_results)} tasks completed")
        return maintenance_results
    
    def register_agent(self, agent_id: str, agent_name: str = "", public_key: str = "") -> bool:
        """
        注册代理
        
        Args:
            agent_id: 代理ID
            agent_name: 代理名称
            public_key: 公钥 (用于加密)
        
        Returns:
            是否成功
        """
        return self.coordinator.register_agent(agent_id, agent_name, public_key)
    
    def sync_agent(self, agent_id: str) -> Dict:
        """
        同步代理记忆
        
        Args:
            agent_id: 代理ID
        
        Returns:
            同步结果
        """
        return self.coordinator.sync_agent(agent_id)
    
    def export_memories(self, agent_id: str = "system", format: str = "json") -> str:
        """
        导出记忆
        
        Args:
            agent_id: 代理ID
            format: 导出格式 (json/csv)
        
        Returns:
            导出的数据
        """
        return self.storage.export_memories(agent_id, format)
    
    def import_memories(self, data: str, agent_id: str = "system", format: str = "json") -> Dict:
        """
        导入记忆
        
        Args:
            data: 导入的数据
            agent_id: 代理ID
            format: 导入格式
        
        Returns:
            导入结果
        """
        return self.storage.import_memories(data, agent_id, format)
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """
        创建备份
        
        Args:
            backup_path: 备份路径
        
        Returns:
            备份文件路径
        """
        return self.storage.create_backup(backup_path)
    
    def restore(self, backup_path: str) -> bool:
        """
        从备份恢复
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            是否成功
        """
        return self.storage.restore_from_backup(backup_path)
    
    def cleanup(self) -> Dict:
        """
        清理系统
        
        Returns:
            清理结果
        """
        return self.storage.cleanup()

# ========== 工具函数 ==========

def create_default_config() -> Dict:
    """创建默认配置"""
    system = MetaMemoryEnhanced()
    return system.config

def test_enhanced_system():
    """测试增强版系统"""
    print("=== Testing MetaMemoryEnhanced ===")
    
    # 使用临时数据库
    import tempfile
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    
    try:
        # 创建配置
        config = {
            "retrieval": {
                "enable_vector_search": False,  # 测试时禁用向量搜索
                "enable_fts": True
            },
            "optimization": {
                "wakeup_prediction": True
            },
            "memory_layers": {
                "enabled": True
            },
            "monitoring": {
                "maintenance_automation": True
            }
        }
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path, config=config)
        print("1. System initialized")
        
        # 注册代理
        memory.register_agent("test_agent1", "Test Agent 1")
        memory.register_agent("test_agent2", "Test Agent 2")
        print("2. Agents registered")
        
        # 存储不同层次的记忆
        memory_ids = []
        
        # 情景记忆
        episodic_id = memory.remember(
            "今天和用户讨论了元记忆技能的设计",
            agent_id="test_agent1",
            memory_layer=MemoryLayer.EPISODIC,
            memory_type=MemoryType.CONVERSATION,
            tags=["meeting", "design", "memory"],
            priority=MemoryPriority.HIGH
        )
        memory_ids.append(episodic_id)
        print(f"3. Stored episodic memory: {episodic_id[:8]}")
        
        # 语义记忆
        semantic_id = memory.remember(
            "元记忆技能应该支持向量搜索和智能唤醒",
            agent_id="test_agent1",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            tags=["fact", "requirement", "design"],
            priority=MemoryPriority.CRITICAL
        )
        memory_ids.append(semantic_id)
        print(f"4. Stored semantic memory: {semantic_id[:8]}")
        
        # 程序记忆
        procedural_id = memory.remember(
            "使用 sentence-transformers 进行向量搜索的步骤",
            agent_id="test_agent1",
            memory_layer=MemoryLayer.PROCEDURAL,
            memory_type=MemoryType.SKILL,
            tags=["skill", "tutorial", "vector"],
            priority=MemoryPriority.HIGH
        )
        memory_ids.append(procedural_id)
        print(f"5. Stored procedural memory: {procedural_id[:8]}")
        
        # 搜索记忆
        results = memory.recall("向量搜索", agent_id="test_agent1")
        print(f"6. Search results: {len(results)} memories found")
        
        # 共享记忆
        memory.share(semantic_id, "test_agent2", "read", "test_agent1")
        print("7. Memory shared with agent2")
        
        # 遗忘记忆
        memory.forget(episodic_id, "test_agent1", permanent=False)
        print(f"8. Memory {episodic_id[:8]} forgotten (compressed)")
        
        # 唤醒记忆
        woken = memory.wakeup(episodic_id, "test_agent1", urgency="normal")
        if woken:
            print(f"9. Memory {episodic_id[:8]} woken up: {woken.content[:50]}...")
        
        # 获取统计
        stats = memory.get_stats()
        print(f"10. System stats: {stats.get('base', {}).get('storage', {}).get('total_memories', 0)} memories")
        
        # 运行维护
        maintenance = memory.run_maintenance()
        print(f"11. Maintenance completed: {len(maintenance)} tasks")
        
        print("\n=== All tests passed ===")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    test_enhanced_system()