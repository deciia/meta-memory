#!/usr/bin/env python3
"""
简化版增强系统测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 创建一个简化版的增强核心
test_code = '''
import json
import hashlib
import sqlite3
from datetime import datetime
from enum import Enum
import time

class MemoryLayer(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryType(Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    DECISION = "decision"

class MemoryPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class MetaMemoryEnhanced:
    def __init__(self, config=None):
        self.config = config or {}
        self.db_path = self.config.get('db_path', 'test_memory.db')
        self._init_database()
        print(f"[INIT] 增强版元记忆系统初始化完成")
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            memory_layer TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            priority INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
    
    def remember(self, content, agent_id, 
                 memory_layer=MemoryLayer.SEMANTIC,
                 memory_type=MemoryType.FACT,
                 priority=MemoryPriority.MEDIUM):
        memory_id = hashlib.md5(f"{content}{agent_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO memories (id, content, agent_id, memory_layer, memory_type, priority)
        VALUES (?, ?, ?, ?, ?, ?)''', (
            memory_id, content, agent_id, 
            memory_layer.value, memory_type.value, priority.value
        ))
        conn.commit()
        conn.close()
        
        print(f"[REMEMBER] 存储记忆: {memory_id}")
        return memory_id
    
    def recall(self, query, agent_id=None, limit=10):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if agent_id:
            cursor.execute('''SELECT * FROM memories 
            WHERE agent_id = ? AND content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?''', (agent_id, f'%{query}%', limit))
        else:
            cursor.execute('''SELECT * FROM memories 
            WHERE content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?''', (f'%{query}%', limit))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'content': row['content'],
                'agent_id': row['agent_id'],
                'memory_layer': row['memory_layer'],
                'memory_type': row['memory_type']
            })
        
        conn.close()
        print(f"[RECALL] 搜索查询: '{query}', 找到 {len(results)} 个结果")
        return results
    
    def check_health(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM memories')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM memories WHERE priority = ?', (MemoryPriority.HIGH.value,))
        high_priority = cursor.fetchone()[0]
        
        conn.close()
        
        health_score = min(100, (total * 10 + high_priority * 20))
        
        print(f"[HEALTH] 健康检查: {total} 个记忆, {high_priority} 个高优先级, 评分: {health_score}")
        
        return type('HealthMetrics', (), {
            'memory_count': total,
            'health_score': health_score
        })()
'''

# 执行测试
print("="*60)
print("增强版元记忆系统简化测试")
print("="*60)

# 动态执行代码
exec(test_code)

# 测试功能
try:
    # 初始化
    memory = MetaMemoryEnhanced({'db_path': 'test_simple.db'})
    
    # 存储测试记忆
    print("\n1. 存储测试记忆...")
    memory.remember("用户喜欢Python编程", "test_agent", MemoryLayer.SEMANTIC, MemoryType.PREFERENCE, MemoryPriority.HIGH)
    memory.remember("决定使用SQLite数据库", "test_agent", MemoryLayer.EPISODIC, MemoryType.DECISION, MemoryPriority.HIGH)
    memory.remember("机器学习需要大量数据", "test_agent", MemoryLayer.SEMANTIC, MemoryType.FACT, MemoryPriority.MEDIUM)
    
    # 搜索测试
    print("\n2. 搜索测试...")
    results = memory.recall("Python", "test_agent")
    print(f"  找到 {len(results)} 个相关记忆")
    
    results = memory.recall("数据库", "test_agent")
    print(f"  找到 {len(results)} 个相关记忆")
    
    # 健康检查
    print("\n3. 健康检查...")
    health = memory.check_health()
    print(f"  系统健康评分: {health.health_score}/100")
    
    print("\n" + "="*60)
    print("✅ 简化测试完成!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()