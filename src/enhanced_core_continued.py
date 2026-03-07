    def _test_search_performance(self) -> float:
        """测试搜索性能"""
        test_queries = ["测试", "记忆", "搜索", "test", "memory"]
        total_time = 0
        
        for query in test_queries:
            start_time = time.time()
            try:
                self.recall(query, limit=5)
                total_time += (time.time() - start_time) * 1000  # 转换为毫秒
            except:
                total_time += 100  # 如果失败，假设100ms
        
        avg_time = total_time / len(test_queries)
        return avg_time
    
    def _calculate_compression_ratio(self) -> float:
        """计算压缩率"""
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
            logger.error(f"❌ 计算压缩率失败: {e}")
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
            logger.error(f"❌ 保存健康记录失败: {e}")
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
            recommendations.append("活跃记忆比例较低，建议唤醒一些休眠记忆")
        
        if metrics.avg_confidence < 60:
            recommendations.append("平均置信度较低，建议记录更多明确信息")
        
        if metrics.success_rate < 0.5:
            recommendations.append("成功率较低，建议分析失败模式")
        
        if metrics.search_performance_ms > 500:
            recommendations.append("搜索性能较慢，建议优化搜索索引")
        
        if metrics.compression_ratio > 0.8:
            recommendations.append("压缩率较高，可能有数据损失风险")
        
        if not recommendations:
            recommendations.append("系统健康状态良好，继续保持")
        
        return recommendations
    
    def perform_self_repair(self) -> Dict[str, Any]:
        """执行自我修复"""
        logger.info("🔧 开始自我修复...")
        
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
            
            # 3. 优化数据库
            repairs['optimized_database'] = self._optimize_database()
            
            # 4. 创建备份
            repairs['backup_created'] = self._create_backup()
            
            logger.info(f"✅ 自我修复完成: {repairs}")
            return repairs
            
        except Exception as e:
            logger.error(f"❌ 自我修复失败: {e}")
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
            
            logger.info(f"✅ 重新索引了 {reindexed} 个记忆")
            return reindexed
            
        except Exception as e:
            logger.error(f"❌ 重新索引失败: {e}")
            return 0
        finally:
            conn.close()
    
    def _clean_orphaned_records(self) -> int:
        """清理孤儿记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 清理没有对应记忆的搜索索引
            cursor.execute('''
            DELETE FROM search_index 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_indexes = cursor.rowcount
            
            # 清理没有对应记忆的向量嵌入
            cursor.execute('''
            DELETE FROM memory_embeddings 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_embeddings = cursor.rowcount
            
            # 清理没有对应记忆的共享权限
            cursor.execute('''
            DELETE FROM sharing_permissions 
            WHERE memory_id NOT IN (SELECT id FROM memories)
            ''')
            orphaned_permissions = cursor.rowcount
            
            conn.commit()
            
            total_cleaned = orphaned_indexes + orphaned_embeddings + orphaned_permissions
            logger.info(f"✅ 清理了 {total_cleaned} 个孤儿记录")
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"❌ 清理孤儿记录失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def _optimize_database(self) -> bool:
        """优化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 执行VACUUM命令优化数据库
            cursor.execute('VACUUM')
            
            # 重新分析统计信息
            cursor.execute('ANALYZE')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 数据库优化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库优化失败: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """创建备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}.db"
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            
            # 压缩备份
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩的备份
            backup_path.unlink()
            
            logger.info(f"✅ 备份创建成功: {backup_path}.gz")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建备份失败: {e}")
            return False
    
    # ========== Q值情景记忆（参考guava-memory） ==========
    
    def record_episode(self, task: str, outcome: str, context: Dict[str, Any], 
                      agent_id: str) -> str:
        """
        记录任务情景（参考guava-memory）
        
        Args:
            task: 任务描述
            outcome: 结果 (success, failure, partial)
            context: 上下文信息
            agent_id: 代理ID
            
        Returns:
            情景ID
        """
        # 创建情景记忆
        episode_content = f"任务: {task}\n结果: {outcome}\n上下文: {json.dumps(context, ensure_ascii=False)}"
        
        memory_id = self.remember(
            content=episode_content,
            agent_id=agent_id,
            memory_layer=MemoryLayer.EPISODIC,
            memory_type=MemoryType.LESSON,
            priority=MemoryPriority.HIGH,
            confidence=0.9
        )
        
        # 更新Q值
        self._update_q_value(memory_id, outcome)
        
        logger.info(f"📝 记录情景: {task} -> {outcome}")
        return memory_id
    
    def _update_q_value(self, memory_id: str, outcome: str):
        """更新Q值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取当前值
            cursor.execute('SELECT q_value, success_count, failure_count FROM memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            
            if row:
                q_value, success_count, failure_count = row
                
                # 根据结果更新
                if outcome == 'success':
                    new_success = success_count + 1
                    new_failure = failure_count
                    # Q值增加
                    q_value = min(1.0, q_value + 0.1)
                elif outcome == 'failure':
                    new_success = success_count
                    new_failure = failure_count + 1
                    # Q值减少
                    q_value = max(0.0, q_value - 0.1)
                else:  # partial
                    new_success = success_count
                    new_failure = failure_count
                    # Q值微调
                    q_value = q_value
                
                # 更新数据库
                cursor.execute('''
                UPDATE memories 
                SET q_value = ?, success_count = ?, failure_count = ?, updated_at = ?
                WHERE id = ?
                ''', (
                    q_value, new_success, new_failure,
                    datetime.now().isoformat(), memory_id
                ))
                
                conn.commit()
                logger.info(f"✅ 更新Q值: {memory_id} -> {q_value:.2f}")
                
        except Exception as e:
            logger.error(f"❌ 更新Q值失败: {e}")
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
            logger.error(f"❌ 获取成功模式失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_anti_patterns(self, agent_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取反模式（需要避免的模式）"""
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
            logger.error(f"❌ 获取反模式失败: {e}")
            return []
        finally:
            conn.close()
    
    # ========== 上下文锚点（参考context-anchor） ==========
    
    def create_context_anchor(self, session_id: str, task_description: str,
                             key_decisions: List[str], open_loops: List[str],
                             next_steps: List[str]) -> str:
        """
        创建上下文锚点（参考context-anchor）
        
        Args:
            session_id: 会话ID
            task_description: 任务描述
            key_decisions: 关键决策列表
            open_loops: 未完成事项列表
            next_steps: 下一步行动列表
            
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
            logger.info(f"📍 创建上下文锚点: {anchor_id}")
            
            return anchor_id
            
        except Exception as e:
            logger.error(f"❌ 创建上下文锚点失败: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_context_anchor(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取上下文锚点
        
        Args:
            session_id: 会话ID（如果为None则获取最新的）
            
        Returns:
            上下文锚点信息
        """
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
            logger.error(f"❌ 获取上下文锚点失败: {e}")
            return None
        finally:
            conn.close()
    
    def update_context_anchor(self, anchor_id: str, updates: Dict[str, Any]) -> bool:
        """更新上下文锚点"""
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
                logger.info(f"✅ 更新上下文锚点: {anchor_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"❌ 更新上下文锚点失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_recovery_briefing(self, days_back: int = 2) -> Dict[str, Any]:
        """
        获取恢复简报（参考context-anchor）
        
        Args:
            days_back: 回溯天数
            
        Returns:
            恢复简报
        """
        briefing = {
            'current_task': None,
            'active_context': [],
            'recent_decisions': [],
            'open_loops': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 获取最新的上下文锚点
        anchor = self.get_context_anchor()
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
            logger.error(f"❌ 获取恢复简报失败: {e}")
        finally:
            conn.close()
        
        return briefing
    
    # ========== 系统统计和维护 ==========
    
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
            # 数据库大小
            if Path(self.db_path).exists():
                stats['database']['size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            # 记忆统计
            cursor.execute('SELECT COUNT(*) FROM memories')
            stats['memories']['total'] = cursor.fetchone()[0]
            
            # 按层次统计
            cursor.execute('SELECT memory_layer, COUNT(*) FROM memories GROUP BY memory_layer')
            for layer, count in cursor.fetchall():
                stats['memories']['by_layer'][layer] = count
            
            # 按类型统计
            cursor.execute('SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type')
            for mem_type, count in cursor.fetchall():
                stats['memories']['by_type'][mem_type] = count
            
            # 按状态统计
            cursor.execute('SELECT state, COUNT(*) FROM memories GROUP BY state')
            for state, count in cursor.fetchall():
                stats['memories']['by_state'][state] = count
            
            # 按代理统计
            cursor.execute('SELECT agent_id, COUNT(*) FROM memories GROUP BY agent_id')
            for agent_id, count in cursor.fetchall():
                stats['memories']['by_agent'][agent_id] = count
            
            # 时间戳
            cursor.execute('SELECT MIN(created_at), MAX(accessed_at) FROM memories')
            min_created, max_accessed = cursor.fetchone()
            stats['timestamps']['created'] = min_created
            stats['timestamps']['last_access'] = max_accessed
            
            # 最后维护时间
            cursor.execute('SELECT MAX(timestamp) FROM health_records')
            last_maintenance = cursor.fetchone()[0]
            stats['timestamps']['last_maintenance'] = last_maintenance
            
            # 性能指标
            stats['performance']['health_score'] = self.health_metrics.health_score
            stats['performance']['avg_search_time_ms'] = self.health_metrics.search_performance_ms
            
        except Exception as e:
            logger.error(f"❌ 获取系统统计失败: {e}")
        finally:
            conn.close()
        
        return stats
    
    def run_maintenance(self) -> Dict[str, Any]:
        """运行系统维护"""
        logger.info("🛠️ 开始系统维护...")
        
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
            # 1. 健康检查
            maintenance_results['health_check'] = self.check_health().to_dict()
            
            # 2. 自我修复
            maintenance_results['self_repair'] = self.perform_self_repair()
            
            # 3. 清理旧记忆
            maintenance_results['cleanup']['old_memories_archived'] = self._archive_old_memories(days=30)
            
            # 4. 清理旧索引
            if self.search_engine:
                self.search_engine.cleanup_old_indexes(days=30)
                # 注意：cleanup_old_indexes方法会自己记录日志
            
            # 5. 创建备份
            maintenance_results['backup_created'] = self._create_backup()
            
            logger.info("✅ 系统维护完成")
            
        except Exception as e:
            logger.error(f"❌ 系统维护失败: {e}")
            maintenance_results['error'] = str(e)
        
        return maintenance_results
    
    def _archive_old_memories(self, days: int = 30) -> int:
        """归档旧记忆"""
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
                logger.info(f"✅ 归档了 {archived_count} 个旧记忆")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"❌ 归档旧记忆失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    # ========== 工具方法 ==========
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """备份数据库"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"manual_backup_{timestamp}.db.gz"
        
        try:
            # 复制并压缩数据库
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"✅ 数据库备份成功: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ 数据库备份失败: {e}")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        try:
            # 解压备份文件
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 重新初始化
            self._init_database()
            
            logger.info(f"✅ 数据库恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库恢复失败: {e}")
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
            
            logger.info(f"✅ 导出 {len(memories)} 个记忆到: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导出记忆失败: {e}")
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
                    logger.error(f"❌ 导入单个记忆失败: {e}")
                    continue
            
            logger.info(f"✅ 导入 {imported_count} 个记忆")
            return imported_count
            
        except Exception as e:
            logger.error(f"❌ 导入记忆失败: {e}")
            return 0