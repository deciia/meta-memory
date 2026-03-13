"""
混合搜索引擎 - 结合传统搜索和向量搜索
当向量模型不可用时，自动回退到传统搜索
"""

import os
import re
import json
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import time

class SearchMode(Enum):
    """搜索模式"""
    AUTO = "auto"           # 自动选择最佳模式
    VECTOR = "vector"      # 向量搜索
    KEYWORD = "keyword"    # 关键词搜索
    HYBRID = "hybrid"      # 混合搜索

class HybridSearchEngine:
    """混合搜索引擎"""
    
    def __init__(self, db_path: str, config: Optional[Dict] = None):
        """
        初始化混合搜索引擎
        
        Args:
            db_path: SQLite数据库路径
            config: 配置字典
        """
        self.db_path = db_path
        self.config = config or {}
        self.vector_available = False
        self.vector_model = None
        
        # 初始化向量搜索（如果可用）
        self._init_vector_search()
        
        # 初始化传统搜索
        self._init_keyword_search()
        
        # 创建搜索表
        self._create_search_tables()
    
    def _init_vector_search(self):
        """初始化向量搜索"""
        try:
            # 尝试导入sentence-transformers
            from sentence_transformers import SentenceTransformer
            import torch
            
            # 检查是否有可用的模型
            model_name = self.config.get("vector_model", "all-MiniLM-L6-v2")
            
            # 尝试加载模型（如果已下载）
            try:
                self.vector_model = SentenceTransformer(model_name)
                self.vector_available = True
                print(f"✅ 向量搜索已启用，使用模型: {model_name}")
            except Exception as e:
                print(f"⚠️ 向量模型未找到，将在首次使用时下载: {e}")
                # 标记为可用但需要下载
                self.vector_available = True
                self.vector_model = None
                
        except ImportError as e:
            print(f"❌ 向量搜索依赖未安装: {e}")
            print("💡 建议安装: pip install sentence-transformers")
            self.vector_available = False
            self.vector_model = None
    
    def _init_keyword_search(self):
        """初始化关键词搜索"""
        # 关键词搜索不需要特殊初始化
        print("✅ 关键词搜索已启用")
    
    def _create_search_tables(self):
        """创建搜索表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建向量嵌入表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            memory_id TEXT PRIMARY KEY,
            embedding BLOB,
            embedding_model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建搜索索引表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_index (
            memory_id TEXT,
            keyword TEXT,
            weight REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (memory_id, keyword),
            FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建关键词索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_search_keyword ON search_index(keyword)
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入列表，如果不可用则返回None
        """
        if not self.vector_available or self.vector_model is None:
            return None
        
        try:
            # 如果模型未加载，尝试加载
            if self.vector_model is None:
                model_name = self.config.get("vector_model", "all-MiniLM-L6-v2")
                from sentence_transformers import SentenceTransformer
                self.vector_model = SentenceTransformer(model_name)
            
            # 生成嵌入
            embedding = self.vector_model.encode(text)
            return embedding.tolist()
            
        except Exception as e:
            print(f"❌ 生成向量嵌入失败: {e}")
            return None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        # 简单的中英文关键词提取
        keywords = []
        
        # 移除标点符号
        text_clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 分割单词
        words = text_clean.split()
        
        # 过滤停用词（简单版本）
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
            'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        for word in words:
            word_lower = word.lower()
            if (len(word) > 1 and  # 单字符词通常不是关键词
                word_lower not in stop_words and
                not word_lower.isdigit()):
                keywords.append(word_lower)
        
        # 去重并限制数量
        keywords = list(dict.fromkeys(keywords))[:max_keywords]
        
        return keywords
    
    def index_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """
        为记忆建立索引
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 记忆元数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 生成向量嵌入
            embedding = self.generate_embedding(content)
            if embedding:
                # 存储向量嵌入
                embedding_blob = json.dumps(embedding).encode('utf-8')
                cursor.execute('''
                INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding, embedding_model)
                VALUES (?, ?, ?)
                ''', (memory_id, embedding_blob, self.config.get("vector_model", "unknown")))
            
            # 2. 提取关键词并建立索引
            keywords = self.extract_keywords(content)
            
            # 计算关键词权重（基于频率和位置）
            content_lower = content.lower()
            for keyword in keywords:
                # 简单权重计算：出现次数 * 位置权重
                count = content_lower.count(keyword)
                # 检查是否在标题或开头（权重更高）
                position_weight = 1.0
                if content_lower.startswith(keyword) or f"# {keyword}" in content_lower:
                    position_weight = 2.0
                
                weight = count * position_weight
                
                cursor.execute('''
                INSERT OR REPLACE INTO search_index (memory_id, keyword, weight)
                VALUES (?, ?, ?)
                ''', (memory_id, keyword, weight))
            
            conn.commit()
            print(f"✅ 已为记忆 {memory_id} 建立索引: {len(keywords)} 个关键词")
            
        except Exception as e:
            print(f"❌ 索引记忆失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def search(self, query: str, mode: SearchMode = SearchMode.AUTO, 
               limit: int = 10, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            mode: 搜索模式
            limit: 返回结果数量限制
            agent_id: 代理ID（用于过滤）
            
        Returns:
            搜索结果列表
        """
        # 自动选择搜索模式
        if mode == SearchMode.AUTO:
            mode = self._select_search_mode(query)
        
        # 执行搜索
        if mode == SearchMode.VECTOR:
            results = self._vector_search(query, limit, agent_id)
        elif mode == SearchMode.KEYWORD:
            results = self._keyword_search(query, limit, agent_id)
        elif mode == SearchMode.HYBRID:
            results = self._hybrid_search(query, limit, agent_id)
        else:
            results = []
        
        return results
    
    def _select_search_mode(self, query: str) -> SearchMode:
        """
        自动选择搜索模式
        
        Args:
            query: 搜索查询
            
        Returns:
            推荐的搜索模式
        """
        # 检查查询特征
        query_lower = query.lower()
        
        # 如果是短查询或包含特定关键词，使用向量搜索
        if (len(query.split()) <= 3 or 
            any(word in query_lower for word in ['相似', '相关', '语义', '意思', 'meaning', 'similar'])):
            if self.vector_available:
                return SearchMode.VECTOR
        
        # 如果是具体查询或包含多个关键词，使用关键词搜索
        if (len(query.split()) > 3 or
            any(word in query_lower for word in ['具体', '特定', '精确', 'exact', 'specific'])):
            return SearchMode.KEYWORD
        
        # 默认使用混合搜索（如果向量可用）
        if self.vector_available:
            return SearchMode.HYBRID
        else:
            return SearchMode.KEYWORD
    
    def _vector_search(self, query: str, limit: int, agent_id: Optional[str]) -> List[Dict[str, Any]]:
        """向量搜索"""
        if not self.vector_available:
            print("⚠️ 向量搜索不可用，回退到关键词搜索")
            return self._keyword_search(query, limit, agent_id)
        
        try:
            # 生成查询向量
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return self._keyword_search(query, limit, agent_id)
            
            # 在数据库中搜索相似的向量
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取所有向量嵌入
            cursor.execute('''
            SELECT m.*, e.embedding
            FROM memories m
            LEFT JOIN memory_embeddings e ON m.id = e.memory_id
            WHERE e.embedding IS NOT NULL
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # 计算相似度
            results = []
            for row in rows:
                try:
                    embedding = json.loads(row['embedding'].decode('utf-8'))
                    # 简单的余弦相似度计算
                    similarity = self._cosine_similarity(query_embedding, embedding)
                    
                    # 应用代理过滤
                    if agent_id and row['agent_id'] != agent_id:
                        # 检查是否共享
                        if not self._is_memory_shared(row['id'], agent_id):
                            continue
                    
                    results.append({
                        'id': row['id'],
                        'content': row['content'],
                        'agent_id': row['agent_id'],
                        'memory_layer': row['memory_layer'],
                        'memory_type': row['memory_type'],
                        'created_at': row['created_at'],
                        'similarity': similarity,
                        'search_mode': 'vector'
                    })
                except Exception as e:
                    continue
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            print(f"❌ 向量搜索失败: {e}")
            return self._keyword_search(query, limit, agent_id)
    
    def _keyword_search(self, query: str, limit: int, agent_id: Optional[str]) -> List[Dict[str, Any]]:
        """关键词搜索"""
        try:
            # 提取查询关键词
            keywords = self.extract_keywords(query, max_keywords=5)
            
            if not keywords:
                return []
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建SQL查询
            sql = '''
            SELECT m.*, SUM(s.weight) as relevance
            FROM memories m
            JOIN search_index s ON m.id = s.memory_id
            WHERE s.keyword IN ({})
            '''.format(','.join(['?'] * len(keywords)))
            
            params = keywords
            
            # 添加代理过滤
            if agent_id:
                sql += '''
                AND (m.agent_id = ? OR EXISTS (
                    SELECT 1 FROM sharing_permissions sp 
                    WHERE sp.memory_id = m.id AND sp.agent_id = ?
                ))
                '''
                params.extend([agent_id, agent_id])
            
            sql += '''
            GROUP BY m.id
            ORDER BY relevance DESC
            LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'content': row['content'],
                    'agent_id': row['agent_id'],
                    'memory_layer': row['memory_layer'],
                    'memory_type': row['memory_type'],
                    'created_at': row['created_at'],
                    'relevance': row['relevance'],
                    'search_mode': 'keyword'
                })
            
            return results
            
        except Exception as e:
            print(f"❌ 关键词搜索失败: {e}")
            return []
    
    def _hybrid_search(self, query: str, limit: int, agent_id: Optional[str]) -> List[Dict[str, Any]]:
        """混合搜索"""
        # 并行执行两种搜索
        vector_results = self._vector_search(query, limit * 2, agent_id)
        keyword_results = self._keyword_search(query, limit * 2, agent_id)
        
        # 合并结果
        all_results = {}
        
        # 添加向量结果
        for result in vector_results:
            memory_id = result['id']
            if memory_id not in all_results:
                all_results[memory_id] = result
                all_results[memory_id]['combined_score'] = result.get('similarity', 0)
        
        # 添加关键词结果并更新分数
        for result in keyword_results:
            memory_id = result['id']
            if memory_id in all_results:
                # 合并分数：向量相似度 * 关键词相关性
                vector_score = all_results[memory_id].get('similarity', 0)
                keyword_score = result.get('relevance', 0) / 100.0  # 归一化
                all_results[memory_id]['combined_score'] = vector_score * (1 + keyword_score)
            else:
                all_results[memory_id] = result
                all_results[memory_id]['combined_score'] = result.get('relevance', 0) / 100.0
        
        # 转换为列表并按综合分数排序
        results = list(all_results.values())
        results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # 更新搜索模式
        for result in results:
            result['search_mode'] = 'hybrid'
        
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _is_memory_shared(self, memory_id: str, agent_id: str) -> bool:
        """检查记忆是否共享给指定代理"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT 1 FROM sharing_permissions 
            WHERE memory_id = ? AND agent_id = ?
            ''', (memory_id, agent_id))
            
            result = cursor.fetchone() is not None
            conn.close()
            
            return result
            
        except Exception:
            return False
    
    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'vector_available': self.vector_available,
            'indexed_memories': 0,
            'total_keywords': 0,
            'vector_embeddings': 0
        }
        
        try:
            # 获取索引的记忆数量
            cursor.execute('SELECT COUNT(DISTINCT memory_id) FROM search_index')
            stats['indexed_memories'] = cursor.fetchone()[0]
            
            # 获取关键词总数
            cursor.execute('SELECT COUNT(*) FROM search_index')
            stats['total_keywords'] = cursor.fetchone()[0]
            
            # 获取向量嵌入数量
            cursor.execute('SELECT COUNT(*) FROM memory_embeddings')
            stats['vector_embeddings'] = cursor.fetchone()[0]
            
        except Exception as e:
            print(f"❌ 获取搜索统计失败: {e}")
        
        conn.close()
        return stats
    
    def cleanup_old_indexes(self, days_old: int = 30):
        """清理旧的索引"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧的搜索索引
            cursor.execute('''
            DELETE FROM search_index 
            WHERE memory_id IN (
                SELECT id FROM memories 
                WHERE created_at < datetime('now', ?)
            )
            ''', (f'-{days_old} days',))
            
            deleted_count = cursor.rowcount
            
            # 删除旧的向量嵌入
            cursor.execute('''
            DELETE FROM memory_embeddings 
            WHERE memory_id IN (
                SELECT id FROM memories 
                WHERE created_at < datetime('now', ?)
            )
            ''', (f'-{days_old} days',))
            
            deleted_embeddings = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"✅ 清理完成: 删除 {deleted_count} 个旧索引, {deleted_embeddings} 个旧嵌入")
            
        except Exception as e:
            print(f"❌ 清理索引失败: {e}")