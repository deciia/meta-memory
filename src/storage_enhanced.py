"""
增强版存储引擎
集成5个参考技能的存储特性
"""

import logging
import json
import sqlite3
import zlib
import gzip
import hashlib
import shutil
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import time

logger = logging.getLogger(__name__)

class EnhancedMetaMemoryStorage:
    """增强版存储引擎"""
    
    def __init__(self, db_path: str, config: Dict):
        self.db_path = db_path
        self.config = config
        self.conn = None
        self.backup_dir = None
        
        # 初始化备份目录
        self._init_backup_dir()
        
        logger.info(f"Enhanced storage initialized: {db_path}")
    
    def _init_backup_dir(self):
        """初始化备份目录"""
        backup_path = self.config.get("backup_path", "~/.meta-memory/backups")
        self.backup_dir = Path(backup_path).expanduser()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup directory: {self.backup_dir}")
    
    def initialize(self):
        """初始化数据库"""
        self._connect()
        self._create_tables()
        self._create_indexes()
        self._create_fts_table()
        logger.info("Database initialized with enhanced schema")
    
    def _connect(self):
        """连接数据库"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            # 启用WAL模式 (参考Elite Longterm Memory)
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # 设置缓存大小
            self.conn.execute("PRAGMA cache_size = -2000")  # 2MB缓存
    
    def _create_tables(self):
        """创建表 (增强版)"""
        cursor = self.conn.cursor()
        
        # 记忆表 (增强)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                compressed_content BLOB,
                original_size INTEGER,
                compression_ratio REAL,
                compression_algorithm TEXT,
                tags TEXT,
                source TEXT,
                memory_layer TEXT,
                memory_type TEXT,
                priority INTEGER,
                importance_score REAL,
                context_keywords TEXT,
                state TEXT,
                created_at TEXT,
                last_accessed TEXT,
                last_wakeup TEXT,
                access_count INTEGER DEFAULT 0,
                wakeup_count INTEGER DEFAULT 0,
                expires_at TEXT,
                scheduled_wakeup TEXT,
                auto_forget_threshold REAL DEFAULT 0.3,
                owner_agent TEXT,
                shared_with TEXT,
                access_history TEXT,
                estimated_tokens INTEGER DEFAULT 0,
                last_token_check TEXT,
                embedding TEXT,
                embedding_model TEXT,
                decay_rate REAL DEFAULT 0.95,
                last_decay_update TEXT
            )
        """)
        
        # 代理表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                public_key TEXT,
                created_at TEXT,
                last_seen TEXT,
                permissions TEXT
            )
        """)
        
        # 共享权限表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sharing_permissions (
                memory_id TEXT,
                agent_id TEXT,
                permission TEXT,
                granted_at TEXT,
                expires_at TEXT,
                PRIMARY KEY (memory_id, agent_id),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        """)
        
        # 访问日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT,
                agent_id TEXT,
                action TEXT,
                timestamp TEXT,
                details TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        """)
        
        # 备份记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_path TEXT,
                created_at TEXT,
                size_bytes INTEGER,
                memory_count INTEGER,
                status TEXT
            )
        """)
        
        # 维护日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT,
                started_at TEXT,
                completed_at TEXT,
                duration_seconds REAL,
                result TEXT,
                details TEXT
            )
        """)
        
        self.conn.commit()
    
    def _create_indexes(self):
        """创建索引"""
        cursor = self.conn.cursor()
        
        # 创建常用查询索引
        indexes = [
            ("idx_memories_state", "memories(state)"),
            ("idx_memories_priority", "memories(priority)"),
            ("idx_memories_owner", "memories(owner_agent)"),
            ("idx_memories_layer", "memories(memory_layer)"),
            ("idx_memories_type", "memories(memory_type)"),
            ("idx_memories_importance", "memories(importance_score)"),
            ("idx_memories_created", "memories(created_at)"),
            ("idx_memories_expires", "memories(expires_at)"),
            ("idx_access_log_memory", "access_log(memory_id)"),
            ("idx_access_log_agent", "access_log(agent_id)"),
            ("idx_sharing_permissions", "sharing_permissions(memory_id, agent_id)")
        ]
        
        for index_name, index_sql in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_sql}")
            except Exception as e:
                logger.warning(f"Failed to create index {index_name}: {e}")
        
        self.conn.commit()
    
    def _create_fts_table(self):
        """创建全文搜索表"""
        if not self.config.get("enable_fts", True):
            return
        
        cursor = self.conn.cursor()
        
        try:
            # 创建FTS5虚拟表
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                USING fts5(id, content, tags, source, memory_layer, memory_type)
            """)
            
            # 创建触发器以同步数据
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories
                BEGIN
                    INSERT INTO memories_fts(rowid, id, content, tags, source, memory_layer, memory_type)
                    VALUES (new.rowid, new.id, new.content, new.tags, new.source, new.memory_layer, new.memory_type);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories
                BEGIN
                    DELETE FROM memories_fts WHERE rowid = old.rowid;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories
                BEGIN
                    DELETE FROM memories_fts WHERE rowid = old.rowid;
                    INSERT INTO memories_fts(rowid, id, content, tags, source, memory_layer, memory_type)
                    VALUES (new.rowid, new.id, new.content, new.tags, new.source, new.memory_layer, new.memory_type);
                END
            """)
            
            self.conn.commit()
            logger.info("FTS table and triggers created")
            
        except Exception as e:
            logger.error(f"Failed to create FTS table: {e}")
    
    # ========== 核心存储操作 ==========
    
    def store_memory(self, content: str, agent_id: str = "system", **kwargs) -> str:
        """存储记忆"""
        from .core import MemoryRecord, MemoryState, MemoryPriority, MemoryLayer, MemoryType, CompressionAlgorithm
        
        # 创建记忆记录
        memory = MemoryRecord(
            content=content,
            owner_agent=agent_id,
            **kwargs
        )
        
        # 设置默认值
        if 'memory_layer' not in kwargs:
            memory.memory_layer = MemoryLayer.SEMANTIC
        if 'memory_type' not in kwargs:
            memory.memory_type = MemoryType.TEXT
        if 'priority' not in kwargs:
            memory.priority = MemoryPriority.MEDIUM
        
        # 计算重要性分数
        memory.importance_score = self._calculate_importance(memory)
        
        # 保存到数据库
        self._save_memory_to_db(memory)
        
        # 记录访问
        self._log_access(memory.id, agent_id, "create", {
            "content_preview": content[:100],
            "layer": memory.memory_layer.value,
            "type": memory.memory_type.value
        })
        
        logger.info(f"Stored memory {memory.id} (layer: {memory.memory_layer.value}, "
                   f"type: {memory.memory_type.value}, importance: {memory.importance_score:.2f})")
        
        return memory.id
    
    def _calculate_importance(self, memory) -> float:
        """计算记忆重要性分数"""
        score = 0.0
        
        # 优先级分数
        priority_score = memory.priority.value / 5.0  # 归一化到0-1
        score += priority_score * 0.4
        
        # 内容长度分数
        content_length = len(memory.content) if memory.content else 0
        length_score = min(content_length / 1000, 1.0)  # 每1000字符1分，最多1分
        score += length_score * 0.2
        
        # 标签分数
        tag_count = len(memory.tags) if memory.tags else 0
        tag_score = min(tag_count * 0.1, 0.3)  # 每个标签0.1分，最多0.3分
        score += tag_score * 0.2
        
        # 层次分数
        layer_scores = {
            "episodic": 0.7,
            "semantic": 0.9,
            "procedural": 0.8
        }
        layer_score = layer_scores.get(memory.memory_layer.value, 0.5)
        score += layer_score * 0.2
        
        return min(score, 1.0)  # 限制在0-1之间
    
    def _save_memory_to_db(self, memory):
        """保存记忆到数据库"""
        cursor = self.conn.cursor()
        
        memory_dict = memory.to_dict()
        
        # 处理列表类型，转换为JSON字符串
        list_fields = ['tags', 'context_keywords', 'shared_with', 'access_history']
        for field in list_fields:
            if field in memory_dict and memory_dict[field] is not None:
                if isinstance(memory_dict[field], list) or isinstance(memory_dict[field], dict):
                    memory_dict[field] = json.dumps(memory_dict[field], ensure_ascii=False)
        
        # 准备SQL
        columns = []
        placeholders = []
        values = []
        
        for key, value in memory_dict.items():
            if value is not None:
                columns.append(key)
                placeholders.append("?")
                values.append(value)
        
        sql = f"""
            INSERT OR REPLACE INTO memories ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(sql, values)
        self.conn.commit()
    
    def retrieve_memory(self, memory_id: str, agent_id: str = "system", fast: bool = False) -> Optional[Any]:
        """检索记忆"""
        from .core import MemoryRecord
        
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # 检查权限
        if not self._check_permission(memory_id, agent_id, "read"):
            logger.warning(f"Agent {agent_id} has no read permission for memory {memory_id}")
            return None
        
        # 解析记忆
        memory = self._parse_memory_row(row)
        
        # 如果是休眠或压缩状态，需要唤醒
        if memory.state.value in ["dormant", "compressed"] and memory.compressed_content:
            if fast:
                # 快速模式：只返回元数据
                memory.content = f"[Compressed memory - {memory.id}]"
            else:
                # 正常模式：解压内容
                try:
                    memory.content = self._decompress_content(memory.compressed_content, 
                                                            memory.compression_algorithm)
                    memory.state = MemoryState.ACTIVE
                    memory.last_wakeup = datetime.now()
                    memory.wakeup_count += 1
                    
                    # 更新数据库
                    self._update_memory_state(memory_id, MemoryState.ACTIVE.value, 
                                            memory.last_wakeup, memory.wakeup_count)
                except Exception as e:
                    logger.error(f"Failed to decompress memory {memory_id}: {e}")
                    memory.content = f"[Decompression failed: {e}]"
        
        # 更新访问信息
        memory.last_accessed = datetime.now()
        memory.access_count += 1
        self._update_access_info(memory_id, memory.last_accessed, memory.access_count)
        
        # 记录访问
        self._log_access(memory_id, agent_id, "read", {})
        
        # 更新重要性分数
        self._update_importance_score(memory)
        
        return memory
    
    def _parse_memory_row(self, row) -> Any:
        """解析数据库行"""
        from .core import MemoryRecord
        
        data = dict(row)
        return MemoryRecord.from_dict(data)
    
    def _check_permission(self, memory_id: str, agent_id: str, permission: str) -> bool:
        """检查权限"""
        # 系统代理有所有权限
        if agent_id == "system":
            return True
        
        cursor = self.conn.cursor()
        
        # 检查是否是所有者
        cursor.execute("SELECT owner_agent FROM memories WHERE id = ?", (memory_id,))
        result = cursor.fetchone()
        
        if result and result[0] == agent_id:
            return True
        
        # 检查共享权限
        cursor.execute("""
            SELECT permission FROM sharing_permissions 
            WHERE memory_id = ? AND agent_id = ? AND (expires_at IS NULL OR expires_at > ?)
        """, (memory_id, agent_id, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        if result:
            granted_permission = result[0]
            
            # 检查权限等级
            permission_levels = {"read": 1, "write": 2, "admin": 3}
            required_level = permission_levels.get(permission, 0)
            granted_level = permission_levels.get(granted_permission, 0)
            
            return granted_level >= required_level
        
        return False
    
    def _decompress_content(self, compressed_content: bytes, algorithm: str) -> str:
        """解压内容"""
        try:
            if algorithm == "zlib":
                decompressed = zlib.decompress(compressed_content)
            elif algorithm == "gzip":
                decompressed = gzip.decompress(compressed_content)
            elif algorithm == "lz4":
                # 如果没有lz4，尝试其他方法
                try:
                    import lz4.frame
                    decompressed = lz4.frame.decompress(compressed_content)
                except ImportError:
                    # 如果没有lz4，尝试直接解码
                    try:
                        return compressed_content.decode('utf-8')
                    except:
                        return compressed_content.decode('latin-1')
            else:
                # 假设是未压缩的
                decompressed = compressed_content
            
            # 尝试多种编码
            try:
                return decompressed.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return decompressed.decode('gbk')
                except:
                    try:
                        return decompressed.decode('latin-1')
                    except:
                        # 最后尝试忽略错误
                        return decompressed.decode('utf-8', errors='replace')
                        
        except Exception as e:
            logger.error(f"Failed to decompress content: {e}")
            # 返回错误信息
            return f"[Decompression failed: {e}]"
    
    def _update_memory_state(self, memory_id: str, state: str, last_wakeup: datetime, wakeup_count: int):
        """更新记忆状态"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET state = ?, last_wakeup = ?, wakeup_count = ?
            WHERE id = ?
        """, (state, last_wakeup.isoformat(), wakeup_count, memory_id))
        self.conn.commit()
    
    def _update_access_info(self, memory_id: str, last_accessed: datetime, access_count: int):
        """更新访问信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET last_accessed = ?, access_count = ?
            WHERE id = ?
        """, (last_accessed.isoformat(), access_count, memory_id))
        self.conn.commit()
    
    def _update_importance_score(self, memory):
        """更新重要性分数"""
        # 基于访问频率和时间的简单更新
        frequency_score = min(memory.access_count * 0.05, 0.5)
        recency_score = 0.5  # 可以基于最后访问时间计算
        
        new_score = memory.importance_score * 0.7 + (frequency_score + recency_score) * 0.15
        memory.importance_score = max(0.1, min(new_score, 1.0))
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET importance_score = ?
            WHERE id = ?
        """, (memory.importance_score, memory.id))
        self.conn.commit()
    
    def _log_access(self, memory_id: str, agent_id: str, action: str, details: Dict):
        """记录访问日志"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO access_log (memory_id, agent_id, action, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (memory_id, agent_id, action, datetime.now().isoformat(), json.dumps(details)))
        self.conn.commit()
    
    # ========== 搜索功能 ==========
    
    def search_memories(self, query: str, agent_id: str = "system", **kwargs) -> List:
        """搜索记忆"""
        from .core import MemoryRecord
        
        limit = kwargs.get('limit', 10)
        memory_layer = kwargs.get('memory_layer')
        memory_type = kwargs.get('memory_type')
        min_importance = kwargs.get('min_importance', 0.0)
        
        cursor = self.conn.cursor()
        
        # 构建查询
        conditions = ["m.importance_score >= ?"]
        params = [min_importance]
        
        if memory_layer:
            conditions.append("m.memory_layer = ?")
            params.append(memory_layer.value if hasattr(memory_layer, 'value') else memory_layer)
        
        if memory_type:
            conditions.append("m.memory_type = ?")
            params.append(memory_type.value if hasattr(memory_type, 'value') else memory_type)
        
        # 权限检查
        conditions.append("(m.owner_agent = ? OR EXISTS (SELECT 1 FROM sharing_permissions sp WHERE sp.memory_id = m.id AND sp.agent_id = ?))")
        params.extend([agent_id, agent_id])
        
        where_clause = " AND ".join(conditions)
        
        if query and query.strip():
            # 简化：总是使用LIKE搜索，避免FTS问题
            sql = f"""
                SELECT m.* FROM memories m
                WHERE {where_clause} AND m.content LIKE ?
                ORDER BY m.importance_score DESC, m.last_accessed DESC
                LIMIT ?
            """
            params.append(f"%{query}%")
        else:
            # 不使用FTS
            sql = f"""
                SELECT m.* FROM memories m
                WHERE {where_clause}
                ORDER BY m.importance_score DESC, m.last_accessed DESC
                LIMIT ?
            """
        
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        memories = []
        for row in rows:
            memory = self._parse_memory_row(row)
            
            # 如果是休眠或压缩状态，只返回元数据
            if memory.state.value in ["dormant", "compressed"]:
                memory.content = f"[Compressed memory - {memory.id}]"
            
            memories.append(memory)
        
        return memories
    
    # ========== 遗忘和删除 ==========
    
    def forget_memory(self, memory_id: str, agent_id: str = "system") -> bool:
        """遗忘记忆（压缩存储）"""
        from .core import MemoryState, CompressionAlgorithm
        
        # 检查权限
        if not self._check_permission(memory_id, agent_id, "write"):
            return False
        
        cursor = self.conn.cursor()
        
        # 获取记忆
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        memory = self._parse_memory_row(row)
        
        # 如果已经是休眠或压缩状态，不需要再次压缩
        if memory.state.value in ["dormant", "compressed"]:
            return True
        
        # 压缩内容
        if memory.content:
            algorithm = CompressionAlgorithm(self.config.get("compression_algorithm", "zlib"))
            compression_level = self.config.get("compression_level", 3)
            
            compressed, ratio = self._compress_content(memory.content, algorithm, compression_level)
            
            # 更新数据库
            cursor.execute("""
                UPDATE memories 
                SET content = NULL,
                    compressed_content = ?,
                    original_size = ?,
                    compression_ratio = ?,
                    compression_algorithm = ?,
                    state = ?
                WHERE id = ?
            """, (
                compressed,
                len(memory.content.encode('utf-8')),
                ratio,
                algorithm.value,
                MemoryState.DORMANT.value,
                memory_id
            ))
            
            self.conn.commit()
            
            # 从FTS表中删除
            cursor.execute("DELETE FROM memories_fts WHERE rowid IN (SELECT rowid FROM memories WHERE id = ?)", (memory_id,))
            self.conn.commit()
            
            # 记录访问
            self._log_access(memory_id, agent_id, "forget", {
                "original_size": len(memory.content.encode('utf-8')),
                "compressed_size": len(compressed),
                "compression_ratio": ratio,
                "algorithm": algorithm.value
            })
            
            logger.info(f"Forgot memory {memory_id} (compressed to {ratio:.1f}x)")
            return True
        
        return False
    
    def _compress_content(self, content: str, algorithm, level: int) -> Tuple[bytes, float]:
        """压缩内容"""
        from .core import CompressionAlgorithm
        
        content_bytes = content.encode('utf-8')
        original_size = len(content_bytes)
        
        if algorithm == CompressionAlgorithm.ZLIB:
            compressed = zlib.compress(content_bytes, level)
        elif algorithm == CompressionAlgorithm.GZIP:
            compressed = gzip.compress(content_bytes, compresslevel=level)
        # LZ4 removed for compatibility
        else:
            compressed = content_bytes
        
        compressed_size = len(compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        return compressed, ratio
    
    def delete_memory(self, memory_id: str, agent_id: str = "system") -> bool:
        """删除记忆（永久）"""
        # 检查权限
        if not self._check_permission(memory_id, agent_id, "admin"):
            return False
        
        cursor = self.conn.cursor()
        
        # 记录删除前的信息（用于备份恢复）
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if row:
            memory_data = dict(row)
            
            # 记录删除
            self._log_access(memory_id, agent_id, "delete", {
                "memory_data": memory_data
            })
        
        # 删除记忆
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.conn.commit()
        
        logger.info(f"Deleted memory {memory_id}")
        return True
    
    # ========== 唤醒功能 ==========
    
    def wakeup_memory(self, memory_id: str, agent_id: str = "system") -> Optional[Any]:
        """唤醒记忆"""
        return self.retrieve_memory(memory_id, agent_id, fast=False)
    
    # ========== 统计和维护 ==========
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # 基本统计
        cursor.execute("SELECT COUNT(*) as total FROM memories")
        stats["total_memories"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as active FROM memories WHERE state = 'active'")
        stats["active_memories"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as dormant FROM memories WHERE state = 'dormant'")
        stats["dormant_memories"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as compressed FROM memories WHERE state = 'compressed'")
        stats["compressed_memories"] = cursor.fetchone()[0]
        
        # 层次统计
        cursor.execute("SELECT memory_layer, COUNT(*) as count FROM memories GROUP BY memory_layer")
        stats["layer_distribution"] = dict(cursor.fetchall())
        
        # 类型统计
        cursor.execute("SELECT memory_type, COUNT(*) as count FROM memories GROUP BY memory_type")
        stats["type_distribution"] = dict(cursor.fetchall())
        
        # 代理统计
        cursor.execute("SELECT COUNT(DISTINCT owner_agent) as agents FROM memories")
        stats["total_agents"] = cursor.fetchone()[0]
        
        # 压缩统计
        cursor.execute("SELECT AVG(compression_ratio) as avg_ratio FROM memories WHERE compression_ratio > 0")
        stats["avg_compression_ratio"] = cursor.fetchone()[0] or 1.0
        
        # 数据库大小
        db_file = Path(self.db_path)
        stats["db_size_bytes"] = db_file.stat().st_size if db_file.exists() else 0
        
        return stats
    
    def run_maintenance(self) -> Dict:
        """运行维护任务"""
        results = {
            "tasks": [],
            "details": {}
        }
        
        try:
            # 1. 清理过期记忆
            expired_count = self._cleanup_expired_memories()
            results["tasks"].append("cleanup_expired_memories")
            results["details"]["expired_memories"] = expired_count
            
            # 2. 优化数据库
            self._optimize_database()
            results["tasks"].append("optimize_database")
            
            # 3. 创建备份（如果配置了自动备份）
            if self.config.get("auto_backup", False):
                backup_result = self.create_backup()
                results["tasks"].append("create_backup")
                results["details"]["backup"] = backup_result
            
            # 4. 清理旧备份
            backup_cleanup = self._cleanup_old_backups()
            results["tasks"].append("cleanup_old_backups")
            results["details"]["backups_cleaned"] = backup_cleanup
            
            # 5. 记录维护日志
            self._log_maintenance("full_maintenance", results)
            
            logger.info(f"Maintenance completed: {results}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Maintenance failed: {e}")
        
        return results
    
    def _cleanup_expired_memories(self) -> int:
        """清理过期记忆"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id FROM memories 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (datetime.now().isoformat(),))
        
        expired_ids = [row[0] for row in cursor.fetchall()]
        
        for memory_id in expired_ids:
            # 标记为归档而不是删除
            cursor.execute("""
                UPDATE memories 
                SET state = 'archived'
                WHERE id = ?
            """, (memory_id,))
        
        self.conn.commit()
        return len(expired_ids)
    
    def _optimize_database(self):
        """优化数据库"""
        cursor = self.conn.cursor()
        
        # 重新构建索引
        cursor.execute("REINDEX")
        
        # 清理WAL日志
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        
        # 清理空闲空间
        cursor.execute("VACUUM")
        
        self.conn.commit()
    
    # ========== 备份和恢复 ==========
    
    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """创建备份"""
        if backup_path is None:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"memory_backup_{timestamp}.db"
        
        backup_path = Path(backup_path)
        
        try:
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            
            # 记录备份
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO backups (backup_path, created_at, size_bytes, memory_count, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(backup_path),
                datetime.now().isoformat(),
                backup_path.stat().st_size,
                self.get_stats()["total_memories"],
                "success"
            ))
            self.conn.commit()
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
            # 记录失败
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO backups (backup_path, created_at, status)
                VALUES (?, ?, ?)
            """, (str(backup_path) if backup_path else "unknown", 
                 datetime.now().isoformat(), f"failed: {e}"))
            self.conn.commit()
            
            raise
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """从备份恢复"""
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # 关闭当前连接
            if self.conn:
                self.conn.close()
                self.conn = None
            
            # 备份当前数据库
            current_db = Path(self.db_path)
            if current_db.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_current = current_db.parent / f"pre_restore_{timestamp}.db"
                shutil.copy2(current_db, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
            
            # 恢复备份
            shutil.copy2(backup_path, self.db_path)
            
            # 重新连接
            self._connect()
            
            logger.info(f"Database restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def _cleanup_old_backups(self) -> int:
        """清理旧备份"""
        max_backups = self.config.get("max_backups", 7)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT backup_path FROM backups 
            WHERE status = 'success'
            ORDER BY created_at DESC
        """)
        
        backups = [row[0] for row in cursor.fetchall()]
        
        cleaned_count = 0
        for backup_path in backups[max_backups:]:
            try:
                path = Path(backup_path)
                if path.exists():
                    path.unlink()
                    cleaned_count += 1
                    
                    # 更新备份记录
                    cursor.execute("""
                        UPDATE backups 
                        SET status = 'cleaned'
                        WHERE backup_path = ?
                    """, (backup_path,))
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup_path}: {e}")
        
        self.conn.commit()
        return cleaned_count
    
    def _log_maintenance(self, task_name: str, result: Dict):
        """记录维护日志"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_log (task_name, started_at, completed_at, result, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            task_name,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "success" if "error" not in result else "failed",
            json.dumps(result)
        ))
        self.conn.commit()
    
    # ========== 其他功能 ==========
    
    def update_memory(self, memory, agent_id: str = "system") -> bool:
        """更新记忆"""
        # 检查权限
        if not self._check_permission(memory.id, agent_id, "write"):
            return False
        
        self._save_memory_to_db(memory)
        
        # 记录访问
        self._log_access(memory.id, agent_id, "update", {
            "content_preview": memory.content[:100] if memory.content else ""
        })
        
        return True
    
    def export_memories(self, agent_id: str = "system", format: str = "json") -> str:
        """导出记忆"""
        memories = self.search_memories("", agent_id, limit=1000)
        
        if format == "json":
            data = {
                "export_time": datetime.now().isoformat(),
                "agent_id": agent_id,
                "count": len(memories),
                "memories": [mem.to_dict() for mem in memories]
            }
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            # 其他格式可以在这里扩展
            return f"Memories: {len(memories)}"
    
    def import_memories(self, data: str, agent_id: str = "system", format: str = "json") -> Dict:
        """导入记忆"""
        try:
            parsed = json.loads(data)
            
            imported_count = 0
            for mem_data in parsed.get("memories", []):
                try:
                    # 创建记忆
                    memory = MemoryRecord.from_dict(mem_data)
                    memory.owner_agent = agent_id  # 设置新的所有者
                    
                    # 保存到数据库
                    self._save_memory_to_db(memory)
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
    
    def create_memory_from_dict(self, data: Dict, agent_id: str = "system") -> Optional[Any]:
        """从字典创建记忆"""
        from .core import MemoryRecord
        
        try:
            memory = MemoryRecord.from_dict(data)
            memory.owner_agent = agent_id
            
            self._save_memory_to_db(memory)
            return memory
            
        except Exception as e:
            logger.error(f"Failed to create memory from dict: {e}")
            return None
    
    def cleanup(self) -> Dict:
        """清理系统"""
        results = {
            "tasks": [],
            "details": {}
        }
        
        try:
            # 清理临时文件等
            # 这里可以添加系统特定的清理逻辑
            
            results["tasks"].append("system_cleanup")
            results["details"]["status"] = "completed"
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

# ========== 测试函数 ==========

def test_enhanced_storage():
    """测试增强版存储"""
    print("=== Testing Enhanced Storage ===")
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    
    try:
        config = {
            "compression_algorithm": "zlib",
            "compression_level": 3,
            "auto_backup": False,
            "enable_fts": True
        }
        
        storage = EnhancedMetaMemoryStorage(db_path, config)
        storage.initialize()
        
        print("1. Storage initialized")
        
        # 测试存储记忆
        from .core import MemoryLayer, MemoryType, MemoryPriority
        
        memory_id = storage.store_memory(
            "测试增强版存储功能",
            agent_id="test_agent",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.TEXT,
            tags=["test", "storage"],
            priority=MemoryPriority.HIGH
        )
        print(f"2. Memory stored: {memory_id}")
        
        # 测试检索记忆
        memory = storage.retrieve_memory(memory_id, "test_agent")
        if memory:
            print(f"3. Memory retrieved: {memory.content[:50]}...")
        else:
            print("3. Memory retrieval failed")
        
        # 测试搜索
        results = storage.search_memories("测试", "test_agent")
        print(f"4. Search results: {len(results)} memories found")
        
        # 测试统计
        stats = storage.get_stats()
        print(f"5. Storage stats: {stats}")
        
        # 测试维护
        maintenance = storage.run_maintenance()
        print(f"6. Maintenance completed: {maintenance}")
        
        print("\n=== Enhanced storage test completed ===")
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
    test_enhanced_storage()