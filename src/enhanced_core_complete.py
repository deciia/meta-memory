# -*- coding: utf-8 -*-
"""
增强版核心系�?v3.0
集成第二批技能优化功能：
1. 混合搜索（向�?关键词，自动回退�?2. 反思和问题生成（参考continuity�?3. 知识图谱增强（参考cortex-memory�?4. 健康评分和自我修复（参考neuroboost-elixir�?5. Q值情景记忆（参考guava-memory�?6. 上下文压缩恢复（参考context-anchor�?"""

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
import re
import time
from collections import defaultdict

# 导入混合搜索
try:
    from .hybrid_search import HybridSearchEngine, SearchMode
    HYBRID_SEARCH_AVAILABLE = True
except ImportError:
    HYBRID_SEARCH_AVAILABLE = False
    print("⚠️ 混合搜索模块不可用，将使用基础搜索")

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
    """记忆状�?""
    ACTIVE = "active"        # 活跃状�?    DORMANT = "dormant"      # 休眠状�?(压缩存储)
    COMPRESSED = "compressed" # 深度压缩状�?    ARCHIVED = "archived"    # 归档状�?(长期存储)

class MemoryPriority(Enum):
    """记忆优先�?""
    TRIVIAL = 1      # 琐碎
    LOW = 2          # �?    MEDIUM = 3       # �?    HIGH = 4         # �?    CRITICAL = 5     # 关键

class MemoryLayer(Enum):
    """记忆层次（参考Memory Manager�?""
    EPISODIC = "episodic"    # 情景记忆：具体事件和经验
    SEMANTIC = "semantic"    # 语义记忆：事实和知识
    PROCEDURAL = "procedural" # 程序记忆：技能和流程

class MemoryType(Enum):
    """记忆类型（参考continuity�?""
    FACT = "fact"            # 事实：陈述性知�?    PREFERENCE = "preference" # 偏好：喜欢、不喜欢、风�?    RELATIONSHIP = "relationship" # 关系：连接动�?    PRINCIPLE = "principle"  # 原则：学到的指导方针
    COMMITMENT = "commitment" # 承诺：承诺、义�?    MOMENT = "moment"        # 时刻：重要事�?    SKILL = "skill"          # 技能：学到的能�?    QUESTION = "question"    # 问题：需要探索的事情
    DECISION = "decision"    # 决策：做出的决定
    LESSON = "lesson"        # 教训：学到的经验
    GOAL = "goal"            # 目标：追求的目标

class ConfidenceLevel(Enum):
    """置信度级别（参考continuity�?""
    EXPLICIT = (0.95, 1.0)   # 用户直接陈述
    IMPLIED = (0.70, 0.94)   # 强烈推断
    INFERRED = (0.40, 0.69)  # 模式识别
    SPECULATIVE = (0.0, 0.39) # 试探性，需要确�?
class HealthStatus(Enum):
    """健康状态（参考neuroboost-elixir�?""
    EXCELLENT = "excellent"  # 优秀�?90%
    GOOD = "good"           # 良好�?5-90%
    FAIR = "fair"           # 一般：60-75%
    POOR = "poor"           # 差：40-60%
    CRITICAL = "critical"   # 严重�?40%

# ========== 数据类定�?==========

@dataclass
class MemoryMetadata:
    """记忆元数�?""
    id: str
    agent_id: str
    memory_layer: MemoryLayer
    memory_type: MemoryType
    priority: MemoryPriority
    state: MemoryState
    confidence: float  # 置信度分�?0.0-1.0
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime
    access_count: int = 0
    q_value: float = 0.0  # Q值评分（参考guava-memory�?    success_count: int = 0  # 成功次数
    failure_count: int = 0  # 失败次数
    tags: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)  # 实体列表
    relationships: List[str] = field(default_factory=list)  # 关系列表
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字�?""
        data = asdict(self)
        # 转换枚举值为字符�?        data['memory_layer'] = self.memory_layer.value
        data['memory_type'] = self.memory_type.value
        data['priority'] = self.priority.value
        data['state'] = self.state.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['accessed_at'] = self.accessed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryMetadata':
        """从字典创�?""
        # 转换字符串回枚举�?        data['memory_layer'] = MemoryLayer(data['memory_layer'])
        data['memory_type'] = MemoryType(data['memory_type'])
        data['priority'] = MemoryPriority(data['priority'])
        data['state'] = MemoryState(data['state'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['accessed_at'] = datetime.fromisoformat(data['accessed_at'])
        return cls(**data)

@dataclass
class ReflectionResult:
    """反思结果（参考continuity�?""
    session_id: str
    duration_minutes: int
    memories_extracted: List[Dict[str, Any]]
    questions_generated: List[str]
    identity_updates: Dict[str, Any]
    confidence_distribution: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字�?""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class HealthMetrics:
    """健康指标（参考neuroboost-elixir�?""
    memory_count: int = 0
    active_memories: int = 0
    compressed_memories: int = 0
    archived_memories: int = 0
    total_access_count: int = 0
    avg_confidence: float = 0.0
    avg_q_value: float = 0.0
    success_rate: float = 0.0
    search_performance_ms: float = 0.0
    compression_ratio: float = 0.0
    last_maintenance: Optional[datetime] = None
    health_score: float = 0.0  # 综合健康评分 0-100
    
    def calculate_health_score(self) -> float:
        """计算健康评分"""
        weights = {
            'active_ratio': 0.25,  # 活跃记忆比例
            'avg_confidence': 0.20,  # 平均置信�?            'success_rate': 0.20,  # 成功�?            'search_performance': 0.20,  # 搜索性能
            'compression_ratio': 0.15  # 压缩�?        }
        
        # 活跃记忆比例�?-1�?        active_ratio = self.active_memories / max(self.memory_count, 1)
        
        # 搜索性能评分�?-1，越快越好）
        perf_score = max(0, 1 - (self.search_performance_ms / 1000))
        
        # 压缩率评分（0-1，越高越好）
        compression_score = min(1.0, self.compression_ratio / 0.8)
        
        # 计算总分
        score = (
            active_ratio * weights['active_ratio'] +
            (self.avg_confidence / 100) * weights['avg_confidence'] +
            self.success_rate * weights['success_rate'] +
            perf_score * weights['search_performance'] +
            compression_score * weights['compression_ratio']
        ) * 100
        
        self.health_score = min(100, max(0, score))
        return self.health_score
    
    def get_health_status(self) -> HealthStatus:
        """获取健康状�?""
        if self.health_score >= 90:
            return HealthStatus.EXCELLENT
        elif self.health_score >= 75:
            return HealthStatus.GOOD
        elif self.health_score >= 60:
            return HealthStatus.FAIR
        elif self.health_score >= 40:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL

# ========== 核心系统 ==========

class MetaMemoryEnhanced:
    """增强版元记忆系统"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化增强版元记忆系�?        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.db_path = self.config.get('db_path', 'meta_memory.db')
        self.backup_dir = Path(self.config.get('backup_dir', 'backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 初始化混合搜索引�?        self.search_engine = None
        if HYBRID_SEARCH_AVAILABLE:
            try:
                self.search_engine = HybridSearchEngine(self.db_path, self.config)
                logger.info("�?混合搜索引擎初始化成�?)
            except Exception as e:
                logger.error(f"�?混合搜索引擎初始化失�? {e}")
                self.search_engine = None
        
        # 初始化反思系�?        self.reflection_enabled = self.config.get('reflection_enabled', True)
        self.reflection_threshold = self.config.get('reflection_threshold', 1800)  # 30分钟
        self.pending_questions = []
        
        # 初始化健康监�?        self.health_metrics = HealthMetrics()
        self.last_health_check = datetime.now()
        
        # 初始化上下文锚点
        self.context_anchor_enabled = self.config.get('context_anchor_enabled', True)
        
        logger.info(f"🚀 增强版元记忆系统初始化完�?(v3.0)")
        logger.info(f"  数据�? {self.db_path}")
        logger.info(f"  混合搜索: {'可用' if self.search_engine else '不可�?}")
        logger.info(f"  反思系�? {'启用' if self.reflection_enabled else '禁用'}")
        logger.info(f"  健康监控: 启用")
        logger.info(f"  上下文锚�? {'启用' if self.context_anchor_enabled else '禁用'}")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建主记忆表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            compressed_content BLOB,
            agent_id TEXT NOT NULL,
            memory_layer TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            priority INTEGER NOT NULL,
            state TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            q_value REAL DEFAULT 0.0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            tags TEXT,  -- JSON数组
            entities TEXT,  -- JSON数组
            relationships TEXT,  -- JSON数组
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            compression_algorithm TEXT,
            compression_level INTEGER
        )
        ''')
        
        # 创建共享权限�?        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sharing_permissions (
            memory_id TEXT,
            agent_id TEXT,
            permission TEXT,  -- read, write, admin
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (memory_id, agent_id),
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建反思记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reflections (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            duration_minutes INTEGER,
            memories_extracted TEXT,  -- JSON数组
            questions_generated TEXT,  -- JSON数组
            identity_updates TEXT,  -- JSON对象
            confidence_distribution TEXT,  -- JSON对象
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建健康记录�?        cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id TEXT PRIMARY KEY,
            metrics TEXT,  -- JSON对象
            health_score REAL,
            health_status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建上下文锚点表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS context_anchors (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            task_description TEXT,
            key_decisions TEXT,  -- JSON数组
            open_loops TEXT,  -- JSON数组
            next_steps TEXT,  -- JSON数组
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_layer ON memories(memory_layer)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_state ON memories(state)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reflections_timestamp ON reflections(timestamp)')
        
        conn.commit()
        conn.close()
        
        logger.info("�?数据库初始化完成")
    
    # ========== 核心记忆功能 ==========
    
    def remember(self, content: str, agent_id: str, 
                 memory_layer: MemoryLayer = MemoryLayer.SEMANTIC,
                 memory_type: MemoryType = MemoryType.FACT,
                 priority: MemoryPriority = MemoryPriority.MEDIUM,
                 confidence: float = 1.0,
                 tags: Optional[List[str]] = None,
                 entities: Optional[List[str]] = None,
                 relationships: Optional[List[str]] = None) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            agent_id: 代理ID
            memory_layer: 记忆层次
            memory_type: 记忆类型
            priority: 优先�?            confidence: 置信�?(0.0-1.0)
            tags: 标签列表
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            记忆ID
        """
        # 生成记忆ID
        memory_id = hashlib.md5(f"{content}{agent_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # 准备元数�?        now = datetime.now()
        metadata = MemoryMetadata(
            id=memory_id,
            agent_id=agent_id,
            memory_layer=memory_layer,
            memory_type=memory_type,
            priority=priority,
            state=MemoryState.ACTIVE,
            confidence=confidence,
            created_at=now,
            updated_at=now,
            accessed_at=now,
            tags=tags or [],
            entities=entities or [],
            relationships=relationships or []
        )
        
        # 存储到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO memories (
                id, content, agent_id, memory_layer, memory_type,
                priority, state, confidence, tags, entities, relationships,
                created_at, updated_at, accessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id, content, agent_id, memory_layer.value, memory_type.value,
                priority.value, MemoryState.ACTIVE.value, confidence,
                json.dumps(tags or [], ensure_ascii=False),
                json.dumps(entities or [], ensure_ascii=False),
                json.dumps(relationships or [], ensure_ascii=False),
                now.isoformat(), now.isoformat(), now.isoformat()
            ))
            
            conn.commit()
            logger.info(f"�?记忆存储成功: {memory_id} ({memory_type.value})")
            
            # 建立搜索索引
            if self.search_engine:
                metadata_dict = {
                    'agent_id': agent_id,
                    'memory_layer': memory_layer.value,
                    'memory_type': memory_type.value,
                    'priority': priority.value
                }
                self.search_engine.index_memory(memory_id, content, metadata_dict)
            
        except Exception as e:
            logger.error(f"�?记忆存储失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
        
        return memory_id
    
    def recall(self, query: str, agent_id: Optional[str] = None,
               limit: int = 10, search_mode: str = 'auto') -> List[Dict[str, Any]]:
        """
        回忆记忆（使用混合搜索）
        
        Args:
            query: 搜索查询
            agent_id: 代理ID（用于过滤）
            limit: 返回结果数量限制
            search_mode: 搜索模式 (auto, vector, keyword, hybrid)
            
        Returns:
            搜索结果列表
        """
        start_time = time.time()
        
        # 使用混合搜索引擎（如果可用）
        if self.search_engine:
            try:
                mode = SearchMode(search_mode)
                results = self.search_engine.search(query, mode, limit, agent_id)
                
                # 更新访问统计
                for result in results:
                    self._update_access_stats(result['id'])
                
                search_time = (time.time() - start_time) * 1000
                logger.info(f"🔍 混合搜索完成: {len(results)} 结果, {search_time:.1f}ms")
                
                return results
                
            except Exception as e:
                logger.error(f"�?混合搜索失败，回退到基础搜索: {e}")
        
        # 回退到基础关键词搜�?        return self._basic_keyword_search(query, agent_id, limit)
    
    def _basic_keyword_search(self, query: str, agent_id: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """基础关键词搜索（回退方案�?""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # 提取关键�?            keywords = self._extract_keywords_simple(query)
            
            if not keywords:
                # 如果没有关键词，返回最近记�?                sql = '''
                SELECT * FROM memories 
                WHERE state != 'archived'
                '''
                params = []
                
                if agent_id:
                    sql += ' AND agent_id = ?'
                    params.append(agent_id)
                
                sql += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
            else:
                # 构建关键词搜�?                sql = '''
                SELECT * FROM memories 
                WHERE state != 'archived'
                AND ('''
                
                conditions = []
                params = []
                
                for keyword in keywords:
                    conditions.append('content LIKE ?')
                    params.append(f'%{keyword}%')
                
                sql += ' OR '.join(conditions) + ')'
                
                if agent_id:
                    sql += ' AND agent_id = ?'
                    params.append(agent_id)
                
                sql += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'agent_id': row['agent_id'],
                    'memory_layer': row['memory_layer'],
                    'memory_type': row['memory_type'],
                    'created_at': row['created_at'],
                    'search_mode': 'keyword_fallback'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"�?基础搜索失败: {e}")
            return []
        finally:
            conn.close()
    
    def _extract_keywords_simple(self, text: str, max_keywords: int = 5) -> List[str]:
        """简单关键词提取"""
        # 移除标点符号
        text_clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 分割单词
        words = text_clean.split()
        
        # 过滤停用�?        stop_words = {
            '�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?, '一', '一�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?, '�?,
            'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        keywords = []
        for word in words:
            word_lower = word.lower()
            if (len(word) > 1 and
                word_lower not in stop_words and
                not word_lower.isdigit()):
                keywords.append(word_lower)
        
        # 去重并限制数�?        keywords = list(dict.fromkeys(keywords))[:max_keywords]
        
        return keywords
    
    def _update_access_stats(self, memory_id: str):
        """更新访问统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE memories 
            SET accessed_at = ?, access_count = access_count + 1
            WHERE id = ?
            ''', (datetime.now().isoformat(), memory_id))
            
            conn.commit()
        except Exception as e:
            logger.error(f"�?更新访问统计失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ========== 反思功能（参考continuity�?==========
    
    def reflect_on_session(self, session_id: str, messages: List[Dict[str, str]], 
                          duration_minutes: int) -> ReflectionResult:
        """
        对会话进行反思（参考continuity�?        
        Args:
            session_id: 会话ID
            messages: 消息列表
            duration_minutes: 会话时长（分钟）
            
        Returns:
            反思结�?        """
        if not self.reflection_enabled:
            logger.info("反思功能已禁用")
            return None
        
        logger.info(f"🔄 开始反思会�? {session_id}")
        
        # 提取记忆
        memories_extracted = self._extract_memories_from_messages(messages)
        
        # 生成问题
        questions_generated = self._generate_questions_from_memories(memories_extracted)
        
        # 更新身份认知
        identity_updates = self._update_identity_from_reflection(memories_extracted)
        
        # 计算置信度分�?        confidence_distribution = self._calculate_confidence_distribution(memories_extracted)
        
        # 创建反思结�?        reflection_result = ReflectionResult(
            session_id=session_id,
            duration_minutes=duration_minutes,
            memories_extracted=memories_extracted,
            questions_generated=questions_generated,
            identity_updates=identity_updates,
            confidence_distribution=confidence_distribution
        )
        
        # 保存反思记�?        self._save_reflection(reflection_result)
        
        # 更新待处理问�?        self.pending_questions.extend(questions_generated)
        
        logger.info(f"�?反思完�? 提取{len(memories_extracted)}个记�? 生成{len(questions_generated)}个问�?)
        
        return reflection_result
    
    def _extract_memories_from_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """从消息中提取记忆"""
        memories = []
        
        # 简单实现：从最后几条消息中提取关键信息
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for msg in recent_messages:
            content = msg.get('content', '')
            role = msg.get('role', '')
            
            # 提取潜在记忆
            if role == 'user':
                # 用户消息可能包含重要信息
                memory_types = self._identify_memory_type(content)
                
                for mem_type in memory_types:
                    memory = {
                        'type': mem_type.value,
                        'content': content[:200],  # 截断
                        'confidence': self._calculate_confidence(content, mem_type),
                        'source': 'explicit' if '记得' in content or '记住' in content else 'inferred'
                    }
                    memories.append(memory)
        
        return memories
    
    def _identify_memory_type(self, content: str) -> List[MemoryType]:
        """识别记忆类型"""
        types = []
        
        content_lower = content.lower()
        
        # 基于关键词识别类�?        type_patterns = {
            MemoryType.FACT: ['�?, '�?, '包括', '包含', '事实'],
            MemoryType.PREFERENCE: ['喜欢', '不喜�?, '偏好', '习惯', '风格'],
            MemoryType.DECISION: ['决定', '选择', '使用', '采用', '方案'],
            MemoryType.GOAL: ['目标', '想要', '希望', '计划', '打算'],
            MemoryType.QUESTION: ['为什�?, '怎么', '如何', '什�?, '?', '�?],
            MemoryType.LESSON: ['教训', '经验', '学到', '明白', '理解']
        }
        
        for mem_type, patterns in type_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                types.append(mem_type)
        
        return types if types else [MemoryType.FACT]
    
    def _calculate_confidence(self, content: str, memory_type: MemoryType) -> float:
        """计算置信�?""
        # 简单实现：基于关键词和长度
        confidence = 0.5  # 基础置信�?        
        # 明确性关键词增加置信�?        explicit_keywords = ['记得', '记住', '肯定', '确定', '确实']
        if any(keyword in content for keyword in explicit_keywords):
            confidence += 0.3
        
        # 长度适中增加置信�?        if 20 <= len(content) <= 200:
            confidence += 0.1
        
        # 限制�?.0-1.0之间
        return max(0.0, min(1.0, confidence))
    
    def _generate_questions_from_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """从记忆中生成问题"""
        questions = []
        
        for memory in memories:
            mem_type = memory['type']
            content = memory['content']
            
            # 根据记忆类型生成问题
            if mem_type == MemoryType.DECISION.value:
                question = f"关于'{content[:50]}...'的决定进展如何？"
                questions.append(question)
            
            elif mem_type == MemoryType.GOAL.value:
                question = f"'{content[:50]}...'这个目标的进展如何？"
                questions.append(question)
            
            elif mem_type == MemoryType.QUESTION.value:
                # 如果是问题类型，直接使用
                if '?' in content or '�? in content:
                    questions.append(content)
        
        # 限制问题数量
        return questions[:5]
    
    def _update_identity_from_reflection(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从反思中更新身份认知"""
        updates = {
            'growth': '',
            'narrative': '',
            'updated_at': datetime.now().isoformat()
        }
        
        # 分析记忆类型分布
        type_counts = defaultdict(int)
        for memory in memories:
            type_counts[memory['type']] += 1
        
        # 生成成长描述
        if type_counts.get(MemoryType.SKILL.value, 0) > 0:
            updates['growth'] = "正在学习新技�?
        elif type_counts.get(MemoryType.DECISION.value, 0) > 0:
            updates['growth'] = "做出重要决策"
        elif type_counts.get(MemoryType.LESSON.value, 0) > 0:
            updates['growth'] = "从经验中学习"
        
        # 生成叙事更新
        total_memories = len(memories)
        if total_memories > 5:
            updates['narrative'] = f"深度会话，提取了{total_memories}个重要记�?
        elif total_memories > 0:
            updates['narrative'] = f"常规会话，记录了{total_memories}个记�?
        else:
            updates['narrative'] = "日常维护会话"
        
        return updates
    
    def _calculate_confidence_distribution(self, memories: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算置信度分�?""
        distribution = {
            'explicit': 0,    # 0.95-1.0
            'implied': 0,     # 0.70-0.94
            'inferred': 0,    # 0.40-0.69
            'speculative': 0  # 0.0-0.39
        }
        
        for memory in memories:
            confidence = memory.get('confidence', 0.5)
            
            if confidence >= 0.95:
                distribution['explicit'] += 1
            elif confidence >= 0.70:
                distribution['implied'] += 1
            elif confidence >= 0.40:
                distribution['inferred'] += 1
            else:
                distribution['speculative'] += 1
        
        return distribution
    
    def _save_reflection(self, reflection: ReflectionResult):
        """保存反思记�?""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            reflection_id = hashlib.md5(f"{reflection.session_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
            
            cursor.execute('''
            INSERT INTO reflections (
                id, session_id, duration_minutes, memories_extracted,
                questions_generated, identity_updates, confidence_distribution, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reflection_id,
                reflection.session_id,
                reflection.duration_minutes,
                json.dumps(reflection.memories_extracted, ensure_ascii=False),
                json.dumps(reflection.questions_generated, ensure_ascii=False),
                json.dumps(reflection.identity_updates, ensure_ascii=False),
                json.dumps(reflection.confidence_distribution, ensure_ascii=False),
                reflection.timestamp.isoformat()
            ))
            
            conn.commit()
            logger.info(f"�?反思记录保存成�? {reflection_id}")
            
        except Exception as e:
            logger.error(f"�?保存反思记录失�? {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_pending_questions(self, limit: int = 3) -> List[str]:
        """获取待处理问�?""
        return self.pending_questions[:limit]
    
    def clear_pending_questions(self):
        """清空待处理问�?""
        self.pending_questions = []
        logger.info("�?已清空待处理问题")
    
    # ========== 健康监控（参考neuroboost-elixir�?==========
    
    def check_health(self) -> HealthMetrics:
        """检查系统健�?""
        logger.info("🩺 开始健康检�?..")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取基本统计
            cursor.execute('SELECT COUNT(*) FROM memories')
            total_memories = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE state = ?', (MemoryState.ACTIVE.value,))
            active_memories = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE state IN (?, ?)', 
                          (MemoryState.COMPRESSED.value, MemoryState.DORMANT.value))
            compressed_memories = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE state = ?', (MemoryState.ARCHIVED.value,))
            archived_memories = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(access_count) FROM memories')
            total_access = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT AVG(confidence) FROM memories')
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute('SELECT AVG(q_value) FROM memories WHERE q_value > 0')
            avg_q_value = cursor.fetchone()[0] or 0.0
            
            cursor.execute('''
            SELECT 
                SUM(success_count) as total_success,
                SUM(failure_count) as total_failure
            FROM memories
            ''')
            result = cursor.fetchone()
            total_success = result[0] or 0
            total_failure = result[1] or 0
            
            success_rate = total_success / max(total_success + total_failure, 1)
            
            # 测试搜索性能
            search_performance = self._test_search_performance()
            
            # 计算压缩�?            compression_ratio = self._calculate_compression_ratio()
            
            # 获取最后维护时�?            cursor.execute('SELECT MAX(timestamp) FROM health_records')
            last_maintenance_str = cursor.fetchone()[0]
            last_maintenance = datetime.fromisoformat(last_maintenance_str) if last_maintenance_str else None
            
            # 更新健康指标
            self.health_metrics = HealthMetrics(
                memory_count=total_memories,
                active_memories=active_memories,
                compressed_memories=compressed_memories,
                archived_memories=archived_memories,
                total_access_count=total_access,
                avg_confidence=avg_confidence * 100,  # 转换为百分比
                avg_q_value=avg_q_value,
                success_rate=success_rate,
                search_performance_ms=search_performance,
                compression_ratio=compression_ratio,
                last_maintenance=last_maintenance
            )
            
            # 计算健康评分
            self.health_metrics.calculate_health_score()
            
            # 保存健康记录
            self._save_health_record()
            
            self.last_health_check = datetime.now()
            
            status = self.health_metrics.get_health_status()
            logger.info(f"�?健康检查完�? {status.value} ({self.health_metrics.health_score:.1f}/100)")
            
            return self.health_metrics
            
        except Exception as e:
            logger.error(f"�?健康检查失�? {e}")
            return HealthMetrics()
        finally:
            conn.close()
    
    def _test_search_performance(self) -> float:
        """测试搜索性能"""
        test_queries = ["测试", "记忆", "搜索", "test", "memory"]
        total_time = 0
        
        for query in test_queries:
            start_time = time.time()
            try:
                self.recall(query, limit=5)
                total_time += (time.time() - start_time) * 1000  # 转换为毫�?            except:
                total_time += 100  # 如果失败，假�?00ms
        
        avg_time = total_time / len(test_queries)
        return avg_time
    def _test_search_performance(self) -> float:
        """测试搜索性能"""
        test_queries = ["测试", "记忆", "搜索", "test", "memory"]
        total_time = 0
        
        for query in test_queries:
            start_time = time.time()
            try:
                self.recall(query, limit=5)
                total_time += (time.time() - start_time) * 1000  # 转换为毫�?            except:
                total_time += 100  # 如果失败，假�?00ms
        
        avg_time = total_time / len(test_queries)
        return avg_time
    
    def _calculate_compression_ratio(self) -> float:
        """计算压缩�?""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT 
                SUM(LENGTH(content)) as original_size,
                SUM(LENGTH(compressed_content)) as compressed_size
            FROM memories 
            WHERE compressed_content IS NOT NULL
            ''')
            
            result = cursor.fetchone()
            original = result[0] or 1
            compressed = result[1] or 0
            
            if original > 0:
                ratio = compressed / original
                return ratio
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"�?计算压缩率失�? {e}")
            return 0.0
        finally:
            conn.close()
    
    def _save_health_record(self):
        """保存健康记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            record_id = hashlib.md5(f"health_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
            
            cursor.execute('''
            INSERT INTO health_records (id, metrics, health_score, health_status)
            VALUES (?, ?, ?, ?)
            ''', (
                record_id,
                json.dumps(asdict(self.health_metrics), ensure_ascii=False),
                self.health_metrics.health_score,
                self.health_metrics.get_health_status().value
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"�?保存健康记录失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        metrics = self.health_metrics
        status = metrics.get_health_status()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': metrics.health_score,
            'health_status': status.value,
            'metrics': {
                'memory_count': metrics.memory_count,
                'active_memories': metrics.active_memories,
                'active_ratio': metrics.active_memories / max(metrics.memory_count, 1),
                'compressed_memories': metrics.compressed_memories,
                'archived_memories': metrics.archived_memories,
                'total_access': metrics.total_access_count,
                'avg_confidence': metrics.avg_confidence,
                'avg_q_value': metrics.avg_q_value,
                'success_rate': metrics.success_rate,
                'search_performance_ms': metrics.search_performance_ms,
                'compression_ratio': metrics.compression_ratio
            },
            'recommendations': self._generate_health_recommendations()
        }
        
        return report
    
    def _generate_health_recommendations(self) -> List[str]:
        """生成健康建议"""
        recommendations = []
        metrics = self.health_metrics
        
        # 基于健康指标生成建议
        if metrics.active_memories / max(metrics.memory_count, 1) < 0.3:
            recommendations.append("活跃记忆比例较低，建议唤醒一些休眠记�?)
        
        if metrics.avg_confidence < 60:
            recommendations.append("平均置信度较低，建议记录更多明确信息")
        
        if metrics.success_rate < 0.5:
            recommendations.append("成功率较低，建议分析失败模式")
        
        if metrics.search_performance_ms > 500:
            recommendations.append("搜索性能较慢，建议优化搜索索�?)
        
        if metrics.compression_ratio > 0.8:
            recommendations.append("压缩率较高，可能有数据损失风�?)
        
        if not recommendations:
            recommendations.append("系统健康状态良好，继续保持")
        
        return recommendations
    
    def perform_self_repair(self) -> Dict[str, Any]:
        """执行自我修复"""
        logger.info("🔧 开始自我修�?..")
        
        repairs = {
            'reindexed_memories': 0,
            'cleaned_orphaned': 0,
            'optimized_database': False,
            'backup_created': False
        }
        
        try:
            # 1. 重新索引记忆（如果搜索引擎可用）
            if self.search_engine:
                repairs['reindexed_memories'] = self._reindex_memories()
            
            # 2. 清理孤儿记录
            repairs['cleaned_orphaned'] = self._clean_orphaned_records()
            
            # 3. 优化数据�?            repairs['optimized_database'] = self._optimize_database()
            
            # 4. 创建备份
            repairs['backup_created'] = self._create_backup()
            
            logger.info(f"�?自我修复完成: {repairs}")
            return repairs
            
        except Exception as e:
            logger.error(f"�?自我修复失败: {e}")
            return {'error': str(e)}
    
    def _reindex_memories(self) -> int:
        """重新索引记忆"""
        if not self.search_engine:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, content, agent_id, memory_layer, memory_type, priority FROM memories')
            rows = cursor.fetchall()
            
            reindexed = 0
            for row in rows:
                memory_id, content, agent_id, memory_layer, memory_type, priority = row
                
                metadata = {
                    'agent_id': agent_id,
                    'memory_layer': memory_layer,
                    'memory_type': memory_type,
                    'priority': priority
                }
                
                self.search_engine.index_memory(memory_id, content, metadata)
                reindexed += 1
            
            logger.info(f"�?重新索引�?{reindexed} 个记�?)
            return reindexed
            
        except Exception as e:
            logger.error(f"�?重新索引失败: {e}")
            return 0
        finally:
            conn.close()
    
    def _clean_orphaned_records(self) -> int:
        """清理孤儿记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 清理没有对应记忆的搜索索�?            cursor.execute('''
            DELETE FROM search_index 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_indexes = cursor.rowcount
            
            # 清理没有对应记忆的向量嵌�?            cursor.execute('''
            DELETE FROM memory_embeddings 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_embeddings = cursor.rowcount
            
            # 清理没有对应记忆的共享权�?            cursor.execute('''
            DELETE FROM sharing_permissions 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_permissions = cursor.rowcount
            
            conn.commit()
            
            total_cleaned = orphaned_indexes + orphaned_embeddings + orphaned_permissions
            logger.info(f"�?清理�?{total_cleaned} 个孤儿记�?)
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"�?清理孤儿记录失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def _optimize_database(self) -> bool:
        """优化数据�?""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 执行VACUUM命令优化数据�?            cursor.execute('VACUUM')
            
            # 重新分析统计信息
            cursor.execute('ANALYZE')
            
            conn.commit()
            conn.close()
            
            logger.info("�?数据库优化完�?)
            return True
            
        except Exception as e:
            logger.error(f"�?数据库优化失�? {e}")
            return False
    
    def _create_backup(self) -> bool:
        """创建备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}.db"
            
            # 复制数据库文�?            shutil.copy2(self.db_path, backup_path)
            
            # 压缩备份
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩的备份
            backup_path.unlink()
            
            logger.info(f"�?备份创建成功: {backup_path}.gz")
            return True
            
        except Exception as e:
            logger.error(f"�?创建备份失败: {e}")
            return False
    
    # ========== Q值情景记忆（参考guava-memory�?==========
    
    def record_episode(self, task: str, outcome: str, context: Dict[str, Any], 
                      agent_id: str) -> str:
        """
        记录任务情景（参考guava-memory�?        
        Args:
            task: 任务描述
            outcome: 结果 (success, failure, partial)
            context: 上下文信�?            agent_id: 代理ID
            
        Returns:
            情景ID
        """
        # 创建情景记忆
        episode_content = f"任务: {task}\n结果: {outcome}\n上下�? {json.dumps(context, ensure_ascii=False)}"
        
        memory_id = self.remember(
            content=episode_content,
            agent_id=agent_id,
            memory_layer=MemoryLayer.EPISODIC,
            memory_type=MemoryType.LESSON,
            priority=MemoryPriority.HIGH,
            confidence=0.9
        )
        
        # 更新Q�?        self._update_q_value(memory_id, outcome)
        
        logger.info(f"📝 记录情景: {task} -> {outcome}")
        return memory_id
    
    def _update_q_value(self, memory_id: str, outcome: str):
        """更新Q�?""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取当前�?            cursor.execute('SELECT q_value, success_count, failure_count FROM memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            
            if row:
                q_value, success_count, failure_count = row
                
                # 根据结果更新
                if outcome == 'success':
                    new_success = success_count + 1
                    new_failure = failure_count
                    # Q值增�?                    q_value = min(1.0, q_value + 0.1)
                elif outcome == 'failure':
                    new_success = success_count
                    new_failure = failure_count + 1
                    # Q值减�?                    q_value = max(0.0, q_value - 0.1)
                else:  # partial
                    new_success = success_count
                    new_failure = failure_count
                    # Q值微�?                    q_value = q_value
                
                # 更新数据�?                cursor.execute('''
                UPDATE memories 
                SET q_value = ?, success_count = ?, failure_count = ?, updated_at = ?
                WHERE id = ?
                ''', (
                    q_value, new_success, new_failure,
                    datetime.now().isoformat(), memory_id
                ))
                
                conn.commit()
                logger.info(f"�?更新Q�? {memory_id} -> {q_value:.2f}")
                
        except Exception as e:
            logger.error(f"�?更新Q值失�? {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_successful_patterns(self, agent_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取成功模式"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT * FROM memories 
            WHERE agent_id = ? 
            AND memory_layer = 'episodic'
            AND q_value > 0.7
            AND success_count > failure_count
            ORDER BY q_value DESC, success_count DESC
            LIMIT ?
            ''', (agent_id, limit))
            
            rows = cursor.fetchall()
            patterns = []
            
            for row in rows:
                patterns.append({
                    'id': row['id'],
                    'content': row['content'],
                    'q_value': row['q_value'],
                    'success_count': row['success_count'],
                    'failure_count': row['failure_count'],
                    'success_rate': row['success_count'] / max(row['success_count'] + row['failure_count'], 1)
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"�?获取成功模式失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_anti_patterns(self, agent_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取反模式（需要避免的模式�?""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT * FROM memories 
            WHERE agent_id = ? 
            AND memory_layer = 'episodic'
            AND failure_count > success_count
            ORDER BY failure_count DESC, q_value ASC
            LIMIT ?
            ''', (agent_id, limit))
            
            rows = cursor.fetchall()
            anti_patterns = []
            
            for row in rows:
                anti_patterns.append({
                    'id': row['id'],
                    'content': row['content'],
                    'q_value': row['q_value'],
                    'success_count': row['success_count'],
                    'failure_count': row['failure_count'],
                    'failure_rate': row['failure_count'] / max(row['success_count'] + row['failure_count'], 1)
                })
            
            return anti_patterns
            
        except Exception as e:
            logger.error(f"�?获取反模式失�? {e}")
            return []
        finally:
            conn.close()
    
    # ========== 上下文锚点（参考context-anchor�?==========
    
    def create_context_anchor(self, session_id: str, task_description: str,
                             key_decisions: List[str], open_loops: List[str],
                             next_steps: List[str]) -> str:
        """
        创建上下文锚点（参考context-anchor�?        
        Args:
            session_id: 会话ID
            task_description: 任务描述
            key_decisions: 关键决策列表
            open_loops: 未完成事项列�?            next_steps: 下一步行动列�?            
        Returns:
            锚点ID
        """
        if not self.context_anchor_enabled:
            logger.info("上下文锚点功能已禁用")
            return None
        
        anchor_id = hashlib.md5(f"anchor_{session_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO context_anchors (
                id, session_id, task_description, key_decisions,
                open_loops, next_steps, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                anchor_id,
                session_id,
                task_description,
                json.dumps(key_decisions, ensure_ascii=False),
                json.dumps(open_loops, ensure_ascii=False),
                json.dumps(next_steps, ensure_ascii=False),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"📍 创建上下文锚�? {anchor_id}")
            
            return anchor_id
            
        except Exception as e:
            logger.error(f"�?创建上下文锚点失�? {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_context_anchor(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取上下文锚�?        
        Args:
            session_id: 会话ID（如果为None则获取最新的�?            
        Returns:
            上下文锚点信�?        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if session_id:
                cursor.execute('''
                SELECT * FROM context_anchors 
                WHERE session_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                ''', (session_id,))
            else:
                cursor.execute('''
                SELECT * FROM context_anchors 
                ORDER BY updated_at DESC
                LIMIT 1
                ''')
            
            row = cursor.fetchone()
            
            if row:
                anchor = {
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'task_description': row['task_description'],
                    'key_decisions': json.loads(row['key_decisions']),
                    'open_loops': json.loads(row['open_loops']),
                    'next_steps': json.loads(row['next_steps']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                return anchor
            else:
                return None
                
        except Exception as e:
            logger.error(f"�?获取上下文锚点失�? {e}")
            return None
        finally:
            conn.close()
    
    def update_context_anchor(self, anchor_id: str, updates: Dict[str, Any]) -> bool:
        """更新上下文锚�?""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 构建更新语句
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['key_decisions', 'open_loops', 'next_steps']:
                    set_clauses.append(f"{key} = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key in ['task_description']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            params.append(anchor_id)
            
            sql = f'''
            UPDATE context_anchors 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            '''
            
            cursor.execute(sql, params)
            conn.commit()
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"�?更新上下文锚�? {anchor_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"�?更新上下文锚点失�? {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_recovery_briefing(self, days_back: int = 2) -> Dict[str, Any]:
        """
        获取恢复简报（参考context-anchor�?        
        Args:
            days_back: 回溯天数
            
        Returns:
            恢复简�?        """
        briefing = {
            'current_task': None,
            'active_context': [],
            'recent_decisions': [],
            'open_loops': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 获取最新的上下文锚�?        anchor = self.get_context_anchor()
        if anchor:
            briefing['current_task'] = anchor['task_description']
            briefing['open_loops'] = anchor['open_loops']
        
        # 获取最近的关键决策
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # 获取最近的决定
            cursor.execute('''
            SELECT content, created_at 
            FROM memories 
            WHERE memory_type = 'decision'
            AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            LIMIT 10
            ''', (f'-{days_back} days',))
            
            for row in cursor.fetchall():
                briefing['recent_decisions'].append({
                    'content': row['content'][:100],
                    'created_at': row['created_at']
                })
            
            # 获取活跃记忆
            cursor.execute('''
            SELECT content, memory_type, created_at 
            FROM memories 
            WHERE state = 'active'
            ORDER BY accessed_at DESC
            LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                briefing['active_context'].append({
                    'content': row['content'][:80],
                    'type': row['memory_type'],
                    'created_at': row['created_at']
                })
            
        except Exception as e:
            logger.error(f"�?获取恢复简报失�? {e}")
        finally:
            conn.close()
        
        return briefing
    
    # ========== 系统统计和维�?==========
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'database': {
                'path': self.db_path,
                'size_mb': 0
            },
            'memories': {
                'total': 0,
                'by_layer': {},
                'by_type': {},
                'by_state': {},
                'by_agent': {}
            },
            'performance': {
                'avg_search_time_ms': 0,
                'health_score': 0
            },
            'timestamps': {
                'created': None,
                'last_access': None,
                'last_maintenance': None
            }
        }
        
        try:
            # 数据库大�?            if Path(self.db_path).exists():
                stats['database']['size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            # 记忆统计
            cursor.execute('SELECT COUNT(*) FROM memories')
            stats['memories']['total'] = cursor.fetchone()[0]
            
            # 按层次统�?            cursor.execute('SELECT memory_layer, COUNT(*) FROM memories GROUP BY memory_layer')
            for layer, count in cursor.fetchall():
                stats['memories']['by_layer'][layer] = count
            
            # 按类型统�?            cursor.execute('SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type')
            for mem_type, count in cursor.fetchall():
                stats['memories']['by_type'][mem_type] = count
            
            # 按状态统�?            cursor.execute('SELECT state, COUNT(*) FROM memories GROUP BY state')
            for state, count in cursor.fetchall():
                stats['memories']['by_state'][state] = count
            
            # 按代理统�?            cursor.execute('SELECT agent_id, COUNT(*) FROM memories GROUP BY agent_id')
            for agent_id, count in cursor.fetchall():
                stats['memories']['by_agent'][agent_id] = count
            
            # 时间�?            cursor.execute('SELECT MIN(created_at), MAX(accessed_at) FROM memories')
            min_created, max_accessed = cursor.fetchone()
            stats['timestamps']['created'] = min_created
            stats['timestamps']['last_access'] = max_accessed
            
            # 最后维护时�?            cursor.execute('SELECT MAX(timestamp) FROM health_records')
            last_maintenance = cursor.fetchone()[0]
            stats['timestamps']['last_maintenance'] = last_maintenance
            
            # 性能指标
            stats['performance']['health_score'] = self.health_metrics.health_score
            stats['performance']['avg_search_time_ms'] = self.health_metrics.search_performance_ms
            
        except Exception as e:
            logger.error(f"�?获取系统统计失败: {e}")
        finally:
            conn.close()
        
        return stats
    
    def run_maintenance(self) -> Dict[str, Any]:
        """运行系统维护"""
        logger.info("🛠�?开始系统维�?..")
        
        maintenance_results = {
            'health_check': None,
            'self_repair': None,
            'cleanup': {
                'old_memories_archived': 0,
                'old_indexes_cleaned': 0
            },
            'backup_created': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. 健康检�?            maintenance_results['health_check'] = self.check_health().to_dict()
            
            # 2. 自我修复
            maintenance_results['self_repair'] = self.perform_self_repair()
            
            # 3. 清理旧记�?            maintenance_results['cleanup']['old_memories_archived'] = self._archive_old_memories(days=30)
            
            # 4. 清理旧索�?            if self.search_engine:
                self.search_engine.cleanup_old_indexes(days=30)
                # 注意：cleanup_old_indexes方法会自己记录日�?            
            # 5. 创建备份
            maintenance_results['backup_created'] = self._create_backup()
            
            logger.info("�?系统维护完成")
            
        except Exception as e:
            logger.error(f"�?系统维护失败: {e}")
            maintenance_results['error'] = str(e)
        
        return maintenance_results
    
    def _archive_old_memories(self, days: int = 30) -> int:
        """归档旧记�?""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE memories 
            SET state = 'archived', updated_at = ?
            WHERE state != 'archived'
            AND accessed_at < datetime('now', ?)
            AND priority < ?
            ''', (
                datetime.now().isoformat(),
                f'-{days} days',
                MemoryPriority.HIGH.value
            ))
            
            archived_count = cursor.rowcount
            conn.commit()
            
            if archived_count > 0:
                logger.info(f"�?归档�?{archived_count} 个旧记忆")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"�?归档旧记忆失�? {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    # ========== 工具方法 ==========
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据�?""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"manual_backup_{timestamp}.db.gz"
        
        try:
            # 复制并压缩数据库
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"�?数据库备份成�? {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"�?数据库备份失�? {e}")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据�?""
        try:
            # 解压备份文件
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 重新初始�?            self._init_database()
            
            logger.info(f"�?数据库恢复成�? {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"�?数据库恢复失�? {e}")
            return False
    
    def export_memories(self, export_path: str, format: str = 'json') -> bool:
        """导出记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM memories ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory = dict(row)
                # 转换JSON字段
                for field in ['tags', 'entities', 'relationships']:
                    if memory[field]:
                        memory[field] = json.loads(memory[field])
                memories.append(memory)
            
            if format == 'json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(memories, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                # 简单CSV导出
                import csv
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    if memories:
                        writer = csv.DictWriter(f, fieldnames=memories[0].keys())
                        writer.writeheader()
                        writer.writerows(memories)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"�?导出 {len(memories)} 个记忆到: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"�?导出记忆失败: {e}")
            return False
        finally:
            conn.close()
    
    def import_memories(self, import_path: str, format: str = 'json') -> int:
        """导入记忆"""
        try:
            if format == 'json':
                with open(import_path, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
            elif format == 'csv':
                import csv
                with open(import_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    memories = list(reader)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            imported_count = 0
            for memory in memories:
                try:
                    # 转换JSON字段
                    for field in ['tags', 'entities', 'relationships']:
                        if field in memory and isinstance(memory[field], str):
                            memory[field] = json.loads(memory[field])
                    
                    # 插入记忆
                    self.remember(
                        content=memory.get('content', ''),
                        agent_id=memory.get('agent_id', 'imported'),
                        memory_layer=MemoryLayer(memory.get('memory_layer', 'semantic')),
                        memory_type=MemoryType(memory.get('memory_type', 'fact')),
                        priority=MemoryPriority(memory.get('priority', 3)),
                        confidence=memory.get('confidence', 1.0),
                        tags=memory.get('tags', []),
                        entities=memory.get('entities', []),
                        relationships=memory.get('relationships', [])
                    )
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"�?导入单个记忆失败: {e}")
                    continue
            
            logger.info(f"�?导入 {imported_count} 个记�?)
            return imported_count
            
        except Exception as e:
            logger.error(f"�?导入记忆失败: {e}")
            return 0
