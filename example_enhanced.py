#!/usr/bin/env python3
"""
增强版元记忆系统使用示例
展示所有新功能的使用方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority, HealthStatus
from datetime import datetime, timedelta
import json

def main():
    print("="*60)
    print("🤖 增强版元记忆系统演示")
    print("="*60)
    
    # 1. 初始化系统
    print("\n1. 🚀 初始化系统...")
    config = {
        'db_path': 'enhanced_memory_demo.db',
        'reflection_enabled': True,
        'context_anchor_enabled': True,
        'vector_model': 'all-MiniLM-L6-v2'  # 轻量级模型
    }
    
    memory = MetaMemoryEnhanced(config)
    print("✅ 系统初始化完成")
    
    # 2. 存储不同类型记忆
    print("\n2. 💾 存储记忆...")
    
    # 事实记忆
    fact_id = memory.remember(
        content="用户喜欢使用Python进行数据分析",
        agent_id="assistant",
        memory_layer=MemoryLayer.SEMANTIC,
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.HIGH,
        confidence=0.95,
        tags=["python", "数据分析", "偏好"]
    )
    print(f"  事实记忆: {fact_id}")
    
    # 决策记忆
    decision_id = memory.remember(
        content="决定使用SQLite作为本地数据库",
        agent_id="assistant",
        memory_layer=MemoryLayer.EPISODIC,
        memory_type=MemoryType.DECISION,
        priority=MemoryPriority.CRITICAL,
        confidence=1.0,
        tags=["数据库", "技术选型", "决策"]
    )
    print(f"  决策记忆: {decision_id}")
    
    # 偏好记忆
    preference_id = memory.remember(
        content="用户偏好暗色主题界面",
        agent_id="assistant",
        memory_layer=MemoryLayer.SEMANTIC,
        memory_type=MemoryType.PREFERENCE,
        priority=MemoryPriority.MEDIUM,
        confidence=0.85,
        tags=["UI", "主题", "偏好"]
    )
    print(f"  偏好记忆: {preference_id}")
    
    # 3. 混合搜索演示
    print("\n3. 🔍 混合搜索演示...")
    
    queries = [
        ("Python数据分析", "具体查询"),
        ("数据库选择", "语义查询"),
        ("用户偏好", "关键词查询")
    ]
    
    for query, query_type in queries:
        print(f"\n  查询: '{query}' ({query_type})")
        results = memory.recall(query, agent_id="assistant", limit=3, search_mode='auto')
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"    {i}. [{result['search_mode']}] {result['content'][:50]}...")
        else:
            print("    无结果")
    
    # 4. 反思功能演示
    print("\n4. 🧠 反思功能演示...")
    
    # 模拟会话消息
    test_messages = [
        {"role": "user", "content": "我记得我们决定使用SQLite作为数据库"},
        {"role": "assistant", "content": "是的，这是昨天的决定"},
        {"role": "user", "content": "我喜欢Python进行数据分析"},
        {"role": "assistant", "content": "明白了，我会记住这个偏好"},
        {"role": "user", "content": "我们接下来要做什么？"}
    ]
    
    reflection = memory.reflect_on_session(
        session_id="test_session_001",
        messages=test_messages,
        duration_minutes=15
    )
    
    if reflection:
        print(f"  提取记忆: {len(reflection.memories_extracted)} 个")
        print(f"  生成问题: {len(reflection.questions_generated)} 个")
        
        if reflection.questions_generated:
            print("  待处理问题:")
            for q in reflection.questions_generated:
                print(f"    • {q}")
    
    # 5. 健康监控演示
    print("\n5. 🩺 健康监控演示...")
    
    health_metrics = memory.check_health()
    health_status = health_metrics.get_health_status()
    
    print(f"  健康评分: {health_metrics.health_score:.1f}/100")
    print(f"  健康状态: {health_status.value}")
    print(f"  记忆总数: {health_metrics.memory_count}")
    print(f"  活跃记忆: {health_metrics.active_memories}")
    print(f"  平均置信度: {health_metrics.avg_confidence:.1f}%")
    print(f"  搜索性能: {health_metrics.search_performance_ms:.1f}ms")
    
    # 获取健康报告
    health_report = memory.get_health_report()
    print(f"  建议: {health_report['recommendations'][0]}")
    
    # 6. Q值情景记忆演示
    print("\n6. 📊 Q值情景记忆演示...")
    
    # 记录任务情景
    episode1 = memory.record_episode(
        task="安装Python包",
        outcome="success",
        context={"package": "pandas", "version": "2.0.0"},
        agent_id="assistant"
    )
    print(f"  记录成功情景: {episode1}")
    
    episode2 = memory.record_episode(
        task="配置数据库连接",
        outcome="failure",
        context={"database": "MySQL", "error": "连接超时"},
        agent_id="assistant"
    )
    print(f"  记录失败情景: {episode2}")
    
    # 获取成功模式
    successful_patterns = memory.get_successful_patterns("assistant", limit=2)
    if successful_patterns:
        print(f"  成功模式 ({len(successful_patterns)} 个):")
        for pattern in successful_patterns:
            print(f"    • Q值: {pattern['q_value']:.2f}, 成功率: {pattern['success_rate']:.1%}")
    
    # 7. 上下文锚点演示
    print("\n7. 📍 上下文锚点演示...")
    
    anchor_id = memory.create_context_anchor(
        session_id="demo_session",
        task_description="演示增强版元记忆系统功能",
        key_decisions=[
            "使用SQLite作为演示数据库",
            "启用所有增强功能"
        ],
        open_loops=[
            "测试向量搜索性能",
            "验证健康监控准确性"
        ],
        next_steps=[
            "运行自我修复",
            "创建系统备份"
        ]
    )
    
    if anchor_id:
        print(f"  创建上下文锚点: {anchor_id}")
        
        # 获取恢复简报
        briefing = memory.get_recovery_briefing(days_back=1)
        print(f"  当前任务: {briefing['current_task']}")
        print(f"  未完成事项: {len(briefing['open_loops'])} 个")
    
    # 8. 自我修复演示
    print("\n8. 🔧 自我修复演示...")
    
    repair_results = memory.perform_self_repair()
    print(f"  重新索引: {repair_results.get('reindexed_memories', 0)} 个记忆")
    print(f"  清理孤儿: {repair_results.get('cleaned_orphaned', 0)} 个记录")
    print(f"  数据库优化: {'成功' if repair_results.get('optimized_database') else '失败'}")
    print(f"  备份创建: {'成功' if repair_results.get('backup_created') else '失败'}")
    
    # 9. 系统统计
    print("\n9. 📈 系统统计...")
    
    stats = memory.get_system_stats()
    print(f"  数据库大小: {stats['database']['size_mb']:.2f} MB")
    print(f"  记忆分布:")
    print(f"    情景记忆: {stats['memories']['by_layer'].get('episodic', 0)}")
    print(f"    语义记忆: {stats['memories']['by_layer'].get('semantic', 0)}")
    print(f"    程序记忆: {stats['memories']['by_layer'].get('procedural', 0)}")
    
    # 10. 系统维护
    print("\n10. 🛠️ 系统维护...")
    
    maintenance = memory.run_maintenance()
    print(f"  维护完成: {maintenance['timestamp']}")
    
    print("\n" + "="*60)
    print("🎉 演示完成!")
    print("="*60)
    
    # 显示待处理问题
    pending_questions = memory.get_pending_questions()
    if pending_questions:
        print("\n📋 待处理问题:")
        for i, question in enumerate(pending_questions, 1):
            print(f"  {i}. {question}")
    
    print("\n💡 下一步建议:")
    print("  1. 安装向量模型以获得更好的搜索效果")
    print("  2. 定期运行健康检查和维护")
    print("  3. 使用上下文锚点快速恢复工作状态")
    print("  4. 分析成功/失败模式以优化决策")

if __name__ == "__main__":
    main()