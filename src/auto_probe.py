# -*- coding: utf-8 -*-
"""
自动推测模块 - 集成到 Meta-Memory
基于 Ollama 向量 + 三层记忆 + 兴趣建模的自动记忆推断

这个模块让 meta-memory 能够在用户不明确触发的情况下，
自动分析上下文并推测用户可能需要的记忆。
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field


# ========== 配置 ==========

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_VECTOR_MODEL = "locusai/all-minilm-l6-v2"


# ========== Ollama 客户端 ==========

class OllamaClient:
    """轻量级 Ollama 客户端"""
    
    def __init__(self, host: str = DEFAULT_OLLAMA_HOST, model: str = DEFAULT_VECTOR_MODEL):
        self.host = host
        self.model = model
        self.embeddings_url = f"{host}/api/embeddings"
        
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本向量嵌入"""
        try:
            response = requests.post(
                self.embeddings_url,
                json={"model": self.model, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("embedding")
            return None
        except Exception:
            return None
            
    def compute_similarity(self, text1: str, text2: str) -> float:
        """计算余弦相似度"""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        if not emb1 or not emb2:
            return 0.0
            
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
        
    def search_similar(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
        """语义搜索"""
        query_emb = self.get_embedding(query)
        if not query_emb:
            return []
            
        results = []
        for i, doc in enumerate(documents):
            doc_emb = self.get_embedding(doc)
            if not doc_emb:
                continue
                
            # 余弦相似度
            dot = sum(a * b for a, b in zip(query_emb, doc_emb))
            norm1 = sum(a * a for a in query_emb) ** 0.5
            norm2 = sum(b * b for b in doc_emb) ** 0.5
            sim = dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0
            
            results.append({
                "index": i,
                "content": doc,
                "score": sim
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def health_check(self) -> bool:
        """检查服务健康"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# ========== 推测结果 ==========

@dataclass
class ProbeResult:
    """推测结果"""
    memories: List[Dict] = field(default_factory=list)
    injected_topics: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


# ========== 自动推测引擎 ==========

class AutoProbeEngine:
    """
    自动推测引擎
    
    核心功能：
    1. 无需触发词，每次消息自动分析
    2. 三层记忆检索（短期/中期/长期）
    3. 用户兴趣建模
    4. Ollama 向量语义增强
    """
    
    def __init__(self, memory_system, ollama_host: str = DEFAULT_OLLAMA_HOST, 
                 vector_model: str = DEFAULT_VECTOR_MODEL):
        """
        初始化
        
        Args:
            memory_system: MetaMemoryEnhanced 实例
            ollama_host: Ollama 服务地址
            vector_model: 向量模型名称
        """
        self.memory = memory_system
        self.ollama = OllamaClient(ollama_host, vector_model)
        
        # 配置
        self.config = {
            'short_term_window': 5,
            'medium_term_days': 7,
            'long_term_top_k': 5,
            'min_interest_score': 0.3,
            'auto_inject': True,
            'weights': {
                'short_term': 0.4,
                'medium_term': 0.3,
                'long_term': 0.3
            }
        }
        
        # 用户画像缓存
        self._user_profiles: Dict[str, Dict] = {}
        
    def probe_and_inject(self, current_message: str, user_id: str = "default") -> ProbeResult:
        """
        主入口：分析当前消息，推测用户可能需要的记忆
        
        无需触发词，每次消息都可触发
        
        Args:
            current_message: 用户当前消息
            user_id: 用户ID
            
        Returns:
            ProbeResult: 包含推测记忆、话题、置信度等
        """
        # 1. 提取话题
        current_topics = self._extract_topics(current_message)
        
        # 2. 三层记忆检索
        short_memories = self._probe_short_term(current_message, current_topics)
        medium_memories = self._probe_medium_term(current_topics)
        long_memories = self._probe_long_term(current_message, current_topics)
        
        # 3. 用户兴趣建模
        user_interests = self._get_user_interests(user_id)
        interest_boost = self._calculate_interest_boost(current_topics, user_interests)
        
        # 4. 综合评分
        combined = self._combine_results(
            short_memories, medium_memories, long_memories, interest_boost
        )
        
        # 5. 生成注入内容
        injected_context, confidence = self._generate_injection(combined)
        
        # 6. 更新画像
        self._update_user_profile(user_id, current_topics)
        
        # 7. 记录到短期记忆（通过 memory 系统）
        self._record_to_short_term(user_id, current_message, current_topics)
        
        return ProbeResult(
            memories=combined,
            injected_topics=current_topics,
            confidence=confidence,
            reasoning=self._generate_reasoning(combined, current_topics)
        )
    
    def deep_recall(self, query: str, depth: int = 3) -> List[Dict]:
        """
        深度回忆：用户明确要求回忆时使用
        
        比 probe_and_inject 更深入地检索
        
        Args:
            query: 查询内容
            depth: 检索深度 (1-3)
            
        Returns:
            按相关性排序的记忆列表
        """
        results = []
        query_topics = self._extract_topics(query)
        
        # 短期
        if depth >= 1:
            short = self._probe_short_term(query, query_topics)
            results.extend([{**r, 'layer': 'short'} for r in short])
        
        # 中期
        if depth >= 2:
            medium = self._probe_medium_term(query_topics)
            results.extend([{**r, 'layer': 'medium'} for r in medium])
        
        # 长期 + 向量
        if depth >= 3:
            long_vector = self._probe_long_term_with_vector(query)
            results.extend([{**r, 'layer': 'long'} for r in long_vector])
        
        # 排序
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:10]
    
    # ========== 内部方法 ==========
    
    def _extract_topics(self, text: str) -> List[str]:
        """从文本中提取话题"""
        topics = []
        text_lower = text.lower()
        
        # 预定义话题模式
        patterns = {
            '技能': ['skill', '技能', '安装', '开发', '配置'],
            '安全': ['安全', 'security', '防御', '部署', '防火墙'],
            '记忆': ['记忆', 'memory', '元记忆', '回忆', '记得'],
            '智能体': ['agent', '智能体', '小', '阿', '机器人'],
            '项目': ['项目', 'project', '任务', '工作'],
            '配置': ['配置', 'config', '设置', '安装'],
            '飞书': ['飞书', 'feishu', '群聊', '绑定'],
            '学习': ['学习', '学', '了解', '知道', '研究'],
            '搜索': ['搜索', 'search', '查找', '找']
        }
        
        for topic, keywords in patterns.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _probe_short_term(self, message: str, topics: List[str]) -> List[Dict]:
        """检索短期记忆"""
        # 尝试从 memory 系统获取最近的记忆
        try:
            # 获取最近的对话记忆
            recent = self.memory.recall("最近对话", limit=5)
            if isinstance(recent, list):
                results = []
                for mem in recent[:5]:
                    score = 0.0
                    # 话题匹配
                    for topic in topics:
                        if hasattr(mem, 'tags') and topic in (mem.tags or []):
                            score += 0.4
                        if topic in mem.content.lower():
                            score += 0.3
                    
                    if score > 0.1:
                        results.append({
                            'content': mem.content[:200],
                            'score': score,
                            'source': 'short_term'
                        })
                return results
        except:
            pass
        return []
    
    def _probe_medium_term(self, topics: List[str]) -> List[Dict]:
        """检索中期记忆"""
        try:
            # 获取近期摘要
            from datetime import datetime, timedelta
            since = datetime.now() - timedelta(days=self.config['medium_term_days'])
            
            results = []
            # 尝试用关键词搜索
            for topic in topics:
                mems = self.memory.recall(topic, limit=3)
                if isinstance(mems, list):
                    for mem in mems:
                        results.append({
                            'content': mem.content[:200],
                            'score': 0.5,
                            'source': 'medium_term'
                        })
            return results[:5]
        except:
            return []
    
    def _probe_long_term(self, message: str, topics: List[str]) -> List[Dict]:
        """检索长期记忆"""
        results = []
        
        try:
            # 获取高优先级记忆
            all_mems = self.memory.recall("重要", limit=10)
            if isinstance(all_mems, list):
                for mem in all_mems:
                    score = 0.0
                    # 重要性加权
                    if hasattr(mem, 'importance_score'):
                        score += mem.importance_score * 0.5
                    # 访问次数
                    if hasattr(mem, 'access_count'):
                        score += min(mem.access_count * 0.05, 0.3)
                    
                    if score > 0.1:
                        results.append({
                            'content': mem.content[:200],
                            'score': score,
                            'source': 'long_term'
                        })
        except:
            pass
        
        return results[:5]
    
    def _probe_long_term_with_vector(self, query: str) -> List[Dict]:
        """使用 Ollama 向量检索长期记忆"""
        try:
            # 获取所有记忆的内容
            all_mems = self.memory.recall("", limit=20)
            if not all_mems or not self.ollama.health_check():
                return []
            
            contents = [m.content[:500] for m in all_mems[:20]]
            
            # Ollama 语义搜索
            similar = self.ollama.search_similar(query, contents, top_k=5)
            
            results = []
            for s in similar:
                mem = all_mems[s['index']]
                results.append({
                    'content': mem.content[:200],
                    'score': s['score'],
                    'vector_similarity': s['score'],
                    'source': 'long_term_vector'
                })
            
            return results
        except:
            return []
    
    def _get_user_interests(self, user_id: str) -> List[str]:
        """获取用户兴趣"""
        profile = self._user_profiles.get(user_id, {})
        interests = profile.get('interests', [])
        
        # 按权重排序
        if isinstance(interests, dict):
            interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
            interests = [i[0] for i in interests[:10]]
        
        return interests
    
    def _calculate_interest_boost(self, current_topics: List[str], user_interests: List[str]) -> float:
        """计算兴趣增益"""
        if not user_interests:
            return 0.0
        
        matches = sum(1 for t in current_topics if t in user_interests)
        return matches / max(len(current_topics), 1)
    
    def _combine_results(self, short: List[Dict], medium: List[Dict], 
                        long: List[Dict], interest_boost: float) -> List[Dict]:
        """合并三层记忆结果"""
        all_results = []
        weights = self.config['weights']
        
        for r in short:
            r['weighted_score'] = r['score'] * weights['short_term']
            all_results.append(r)
        
        for r in medium:
            r['weighted_score'] = r['score'] * weights['medium_term']
            all_results.append(r)
        
        for r in long:
            r['weighted_score'] = r['score'] * weights['long_term']
            all_results.append(r)
        
        # 兴趣增益
        for r in all_results:
            r['weighted_score'] *= (1 + interest_boost * 0.5)
        
        # 去重
        seen = {}
        for r in all_results:
            key = r['content'][:50]
            if key not in seen or seen[key]['weighted_score'] < r['weighted_score']:
                seen[key] = r
        
        results = list(seen.values())
        results.sort(key=lambda x: x['weighted_score'], reverse=True)
        return results[:5]
    
    def _generate_injection(self, memories: List[Dict]) -> Tuple[str, float]:
        """生成注入内容"""
        if not memories:
            return "", 0.0
        
        parts = ["[相关记忆]"]
        for mem in memories[:3]:
            emoji = {'short_term': '💬', 'medium_term': '📋', 'long_term': '🧠'}.get(mem.get('source', ''), '📝')
            parts.append(f"{emoji} {mem['content'][:100]}...")
        
        context = "\n".join(parts)
        avg_score = sum(m['weighted_score'] for m in memories) / len(memories)
        return context, min(avg_score, 1.0)
    
    def _generate_reasoning(self, memories: List[Dict], topics: List[str]) -> str:
        """生成推理说明"""
        if not memories:
            return "未找到相关记忆"
        
        sources = {}
        for m in memories:
            src = m.get('source', 'unknown')
            sources[src] = sources.get(src, 0) + 1
        
        reasoning = f"基于话题 {topics} 检索，推测用户可能需要："
        reasoning += f"短期{sources.get('short_term', 0)}条，"
        reasoning += f"中期{sources.get('medium_term', 0)}条，"
        reasoning += f"长期{sources.get('long_term', 0)}条"
        
        return reasoning
    
    def _update_user_profile(self, user_id: str, topics: List[str]):
        """更新用户画像"""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = {'interests': {}, 'topics': []}
        
        profile = self._user_profiles[user_id]
        interests = profile.get('interests', {})
        
        for topic in topics:
            interests[topic] = interests.get(topic, 0) + 1
        
        profile['interests'] = interests
        profile['topics'] = list(set(profile.get('topics', []) + topics))[-20:]
    
    def _record_to_short_term(self, user_id: str, content: str, topics: List[str]):
        """记录到短期记忆"""
        try:
            # 通过 memory 系统添加一个记忆
            self.memory.remember(
                content=content,
                tags=topics,
                memory_type="conversation",
                priority="medium"
            )
        except:
            pass
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'ollama_health': self.ollama.health_check(),
            'vector_model': self.ollama.model,
            'user_profiles': len(self._user_profiles)
        }


# ========== 便捷函数 ==========

def create_auto_probe(memory_system, **kwargs) -> AutoProbeEngine:
    """创建自动推测引擎"""
    return AutoProbeEngine(memory_system, **kwargs)
