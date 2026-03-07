"""
预测唤醒系统 (参考Cognitive Memory)
智能预测和优化唤醒
"""

import logging
import json
import re
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class PredictiveWakeupSystem:
    """预测唤醒系统"""
    
    def __init__(self, storage, config: Dict):
        self.storage = storage
        self.config = config
        
        # 缓存系统
        self.wakeup_cache = {}  # memory_id -> (memory, timestamp)
        self.prediction_cache = {}  # context_hash -> predicted_memories
        self.context_history = deque(maxlen=100)  # 最近上下文历史
        
        # 统计信息
        self.stats = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_prediction_time_ms": 0,
            "last_prediction": None
        }
        
        # 衰减参数
        self.decay_enabled = config.get("decay_enabled", True)
        self.decay_rate = config.get("decay_rate", 0.95)
        
        logger.info("Predictive wakeup system initialized")
    
    def predict_and_wakeup(self, current_context: str, agent_id: str = "system") -> List[str]:
        """
        预测并唤醒相关记忆
        
        Args:
            current_context: 当前上下文
            agent_id: 代理ID
        
        Returns:
            唤醒的记忆ID列表
        """
        start_time = datetime.now()
        
        try:
            # 分析上下文
            context_keywords = self._extract_keywords(current_context)
            context_hash = self._hash_context(current_context)
            
            # 检查缓存
            if context_hash in self.prediction_cache:
                self.stats["cache_hits"] += 1
                predicted_ids = self.prediction_cache[context_hash]
                logger.debug(f"Cache hit for context: {context_hash[:8]}")
            else:
                self.stats["cache_misses"] += 1
                
                # 预测相关记忆
                predicted_ids = self._predict_related_memories(context_keywords, agent_id)
                
                # 更新缓存
                self.prediction_cache[context_hash] = predicted_ids
            
            # 唤醒预测的记忆
            woken_ids = []
            for memory_id in predicted_ids[:5]:  # 最多唤醒5个
                try:
                    memory = self.storage.retrieve_memory(memory_id, agent_id)
                    if memory and memory.state.value in ["dormant", "compressed"]:
                        # 唤醒记忆
                        woken_memory = self.storage.wakeup_memory(memory_id, agent_id)
                        if woken_memory:
                            woken_ids.append(memory_id)
                            logger.debug(f"Predictively woke up memory: {memory_id[:8]}")
                except Exception as e:
                    logger.warning(f"Failed to wakeup memory {memory_id}: {e}")
            
            # 更新上下文历史
            self.context_history.append({
                "timestamp": datetime.now(),
                "context": current_context[:100],  # 只存储前100字符
                "keywords": context_keywords,
                "woken_memories": woken_ids
            })
            
            # 更新统计
            self.stats["total_predictions"] += 1
            self.stats["successful_predictions"] += len(woken_ids) > 0
            self.stats["last_prediction"] = datetime.now().isoformat()
            
            prediction_time = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["avg_prediction_time_ms"] = (
                self.stats["avg_prediction_time_ms"] * (self.stats["total_predictions"] - 1) + prediction_time
            ) / self.stats["total_predictions"]
            
            logger.info(f"Predictive wakeup: context={current_context[:50]}..., "
                       f"predicted={len(predicted_ids)}, woken={len(woken_ids)}")
            
            return woken_ids
            
        except Exception as e:
            logger.error(f"Predictive wakeup failed: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 简单关键词提取
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
                     "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "should",
                     "can", "could", "may", "might", "must", "this", "that", "these", "those"}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 去重并限制数量
        unique_keywords = list(set(keywords))[:20]
        
        return unique_keywords
    
    def _hash_context(self, context: str) -> str:
        """生成上下文哈希"""
        return hashlib.md5(context.encode()).hexdigest()[:16]
    
    def _predict_related_memories(self, keywords: List[str], agent_id: str) -> List[str]:
        """预测相关记忆"""
        if not keywords:
            return []
        
        # 搜索相关记忆
        related_memories = []
        
        for keyword in keywords[:5]:  # 使用前5个关键词
            try:
                results = self.storage.search_memories(keyword, agent_id, limit=10)
                for memory in results:
                    # 计算相关性分数
                    relevance_score = self._calculate_relevance(memory, keywords)
                    
                    # 应用衰减
                    if self.decay_enabled:
                        decay_factor = self._calculate_decay_factor(memory)
                        relevance_score *= decay_factor
                    
                    related_memories.append((memory.id, relevance_score))
            except Exception as e:
                logger.warning(f"Failed to search for keyword '{keyword}': {e}")
        
        # 去重和排序
        memory_scores = {}
        for memory_id, score in related_memories:
            if memory_id not in memory_scores or score > memory_scores[memory_id]:
                memory_scores[memory_id] = score
        
        # 按分数排序
        sorted_memories = sorted(memory_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [mem_id for mem_id, score in sorted_memories[:20]]  # 返回前20个
    
    def _calculate_relevance(self, memory, keywords: List[str]) -> float:
        """计算记忆与关键词的相关性"""
        if not memory or not keywords:
            return 0.0
        
        # 检查记忆内容中的关键词
        content = memory.content.lower() if memory.content else ""
        tags = [tag.lower() for tag in memory.tags] if memory.tags else []
        
        # 计算匹配分数
        score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 在内容中匹配
            if keyword_lower in content:
                # 计算出现频率
                count = content.count(keyword_lower)
                score += min(count * 0.1, 0.5)  # 每个出现加0.1，最多0.5
            
            # 在标签中匹配
            if keyword_lower in tags:
                score += 0.3  # 标签匹配权重更高
        
        # 考虑记忆重要性
        importance_factor = memory.importance_score if hasattr(memory, 'importance_score') else 0.5
        score *= (0.5 + importance_factor)  # 重要性权重
        
        # 考虑访问频率
        if hasattr(memory, 'access_count'):
            frequency_factor = min(memory.access_count * 0.05, 0.5)
            score *= (1.0 + frequency_factor)
        
        return min(score, 1.0)  # 限制在0-1之间
    
    def _calculate_decay_factor(self, memory) -> float:
        """计算衰减因子 (参考Cognitive Memory)"""
        if not hasattr(memory, 'last_accessed') or not memory.last_accessed:
            return 1.0
        
        try:
            days_passed = (datetime.now() - memory.last_accessed).days
            decay_factor = self.decay_rate ** days_passed
            return max(decay_factor, 0.1)  # 最小衰减到0.1
        except:
            return 1.0
    
    def optimized_wakeup(self, memory_id: str, agent_id: str, urgency: str = "normal") -> Optional[Any]:
        """
        优化唤醒
        
        Args:
            memory_id: 记忆ID
            agent_id: 代理ID
            urgency: 紧急程度 (emergency/normal/background)
        
        Returns:
            唤醒的记忆
        """
        # 检查缓存
        if memory_id in self.wakeup_cache:
            cached_memory, cache_time = self.wakeup_cache[memory_id]
            
            # 检查缓存是否过期 (5分钟)
            if (datetime.now() - cache_time).total_seconds() < 300:
                logger.debug(f"Cache hit for memory {memory_id[:8]}")
                return cached_memory
        
        try:
            # 根据紧急程度选择唤醒策略
            if urgency == "emergency":
                # 紧急唤醒：快速解压，可能损失一些精度
                memory = self._emergency_wakeup(memory_id, agent_id)
            elif urgency == "background":
                # 后台唤醒：慢速但完全解压
                memory = self._background_wakeup(memory_id, agent_id)
            else:
                # 正常唤醒：平衡速度和精度
                memory = self._normal_wakeup(memory_id, agent_id)
            
            # 更新缓存
            if memory:
                self.wakeup_cache[memory_id] = (memory, datetime.now())
                
                # 限制缓存大小
                if len(self.wakeup_cache) > 100:
                    # 移除最旧的缓存项
                    oldest_key = min(self.wakeup_cache.keys(), 
                                   key=lambda k: self.wakeup_cache[k][1])
                    del self.wakeup_cache[oldest_key]
            
            return memory
            
        except Exception as e:
            logger.error(f"Optimized wakeup failed for memory {memory_id}: {e}")
            return None
    
    def _emergency_wakeup(self, memory_id: str, agent_id: str) -> Optional[Any]:
        """紧急唤醒：快速但可能不完整"""
        try:
            # 尝试快速检索
            memory = self.storage.retrieve_memory(memory_id, agent_id, fast=True)
            if memory:
                logger.debug(f"Emergency wakeup for memory {memory_id[:8]}")
                return memory
        except:
            pass
        
        # 回退到正常唤醒
        return self._normal_wakeup(memory_id, agent_id)
    
    def _normal_wakeup(self, memory_id: str, agent_id: str) -> Optional[Any]:
        """正常唤醒：平衡模式"""
        try:
            memory = self.storage.retrieve_memory(memory_id, agent_id)
            if memory:
                logger.debug(f"Normal wakeup for memory {memory_id[:8]}")
                return memory
        except Exception as e:
            logger.warning(f"Normal wakeup failed: {e}")
        
        return None
    
    def _background_wakeup(self, memory_id: str, agent_id: str) -> Optional[Any]:
        """后台唤醒：完整但较慢"""
        try:
            # 这里可以实现更完整的解压逻辑
            memory = self.storage.retrieve_memory(memory_id, agent_id)
            if memory:
                # 可以在这里添加额外的处理，比如重新计算嵌入向量等
                logger.debug(f"Background wakeup for memory {memory_id[:8]}")
                return memory
        except Exception as e:
            logger.warning(f"Background wakeup failed: {e}")
        
        return None
    
    def learn_from_context(self, context: str, accessed_memories: List[str]):
        """
        从上下文学习，改进预测
        
        Args:
            context: 上下文
            accessed_memories: 实际访问的记忆ID列表
        """
        if not context or not accessed_memories:
            return
        
        # 这里可以实现机器学习逻辑，改进预测模型
        # 目前只是简单记录
        logger.debug(f"Learning from context: {context[:50]}..., "
                    f"accessed memories: {len(accessed_memories)}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 添加缓存信息
        stats["wakeup_cache_size"] = len(self.wakeup_cache)
        stats["prediction_cache_size"] = len(self.prediction_cache)
        stats["context_history_size"] = len(self.context_history)
        
        # 计算命中率
        total_cache_access = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_access > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_access
        else:
            stats["cache_hit_rate"] = 0.0
        
        # 预测成功率
        if stats["total_predictions"] > 0:
            stats["prediction_success_rate"] = stats["successful_predictions"] / stats["total_predictions"]
        else:
            stats["prediction_success_rate"] = 0.0
        
        return stats
    
    def run_maintenance(self) -> Dict:
        """运行维护任务"""
        maintenance_results = {
            "tasks": [],
            "cleaned_cache_entries": 0,
            "cleaned_old_predictions": 0
        }
        
        try:
            # 清理过期缓存
            now = datetime.now()
            expired_keys = []
            
            for memory_id, (memory, cache_time) in self.wakeup_cache.items():
                if (now - cache_time).total_seconds() > 3600:  # 1小时过期
                    expired_keys.append(memory_id)
            
            for key in expired_keys:
                del self.wakeup_cache[key]
            
            maintenance_results["cleaned_cache_entries"] = len(expired_keys)
            maintenance_results["tasks"].append("cleaned_expired_cache")
            
            # 清理旧预测缓存
            if len(self.prediction_cache) > 1000:
                # 保留最近500个
                all_keys = list(self.prediction_cache.keys())
                keys_to_remove = all_keys[:-500]
                
                for key in keys_to_remove:
                    del self.prediction_cache[key]
                
                maintenance_results["cleaned_old_predictions"] = len(keys_to_remove)
                maintenance_results["tasks"].append("cleaned_old_predictions")
            
            # 清理上下文历史
            if len(self.context_history) > self.context_history.maxlen:
                # deque会自动清理，但我们可以记录一下
                maintenance_results["tasks"].append("context_history_auto_cleaned")
            
            logger.info(f"Predictive wakeup maintenance completed: {maintenance_results}")
            
        except Exception as e:
            maintenance_results["error"] = str(e)
            logger.error(f"Predictive wakeup maintenance failed: {e}")
        
        return maintenance_results
    
    def reset(self):
        """重置系统"""
        self.wakeup_cache.clear()
        self.prediction_cache.clear()
        self.context_history.clear()
        
        self.stats = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_prediction_time_ms": 0,
            "last_prediction": None
        }
        
        logger.info("Predictive wakeup system reset")

# ========== 测试函数 ==========

def test_predictive_wakeup():
    """测试预测唤醒系统"""
    print("=== Testing Predictive Wakeup ===")
    
    # 模拟存储
    class MockStorage:
        def search_memories(self, query, agent_id, limit=10):
            return []
        
        def retrieve_memory(self, memory_id, agent_id, fast=False):
            return None
        
        def wakeup_memory(self, memory_id, agent_id):
            return None
    
    storage = MockStorage()
    config = {
        "decay_enabled": True,
        "decay_rate": 0.95
    }
    
    system = PredictiveWakeupSystem(storage, config)
    
    # 测试关键词提取
    context = "今天讨论了向量搜索和预测唤醒系统的实现"
    keywords = system._extract_keywords(context)
    print(f"1. Extracted keywords: {keywords}")
    
    # 测试上下文哈希
    context_hash = system._hash_context(context)
    print(f"2. Context hash: {context_hash}")
    
    # 测试预测
    predicted = system.predict_and_wakeup(context, "test_agent")
    print(f"3. Predicted and woke up: {len(predicted)} memories")
    
    # 测试统计
    stats = system.get_stats()
    print(f"4. System stats: {stats}")
    
    # 测试维护
    maintenance = system.run_maintenance()
    print(f"5. Maintenance results: {maintenance}")
    
    print("\n=== Predictive wakeup test completed ===")
    return True

if __name__ == "__main__":
    test_predictive_wakeup()