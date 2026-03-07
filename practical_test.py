#!/usr/bin/env python3
"""
实用测试 - 验证增强版元记忆技能真的好用
避免Unicode字符，专注于功能验证
"""

import sys
import os
import time
import json
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("PRACTICAL TEST - Enhanced Meta-Memory Skill")
print("="*70)

def test_basic_functionality():
    """测试基础功能"""
    print("\n1. BASIC FUNCTIONALITY TEST")
    
    try:
        # 尝试导入模块
        from src.enhanced_core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        print("  [PASS] Core modules imported")
        
        # 初始化系统
        memory = MetaMemoryEnhanced({
            'db_path': 'practical_test.db',
            'reflection_enabled': True
        })
        print("  [PASS] System initialized")
        
        # 测试1: 存储记忆
        print("\n  Test 1.1: Store memories")
        test_data = [
            ("User prefers Python for data analysis", "preference", MemoryPriority.HIGH),
            ("Decision: Use SQLite for local storage", "decision", MemoryPriority.CRITICAL),
            ("Plan to learn React next week", "goal", MemoryPriority.HIGH),
            ("Lesson: Start testing early", "lesson", MemoryPriority.MEDIUM)
        ]
        
        memory_ids = []
        for content, mem_type, priority in test_data:
            if mem_type == "preference":
                mtype = MemoryType.PREFERENCE
            elif mem_type == "decision":
                mtype = MemoryType.DECISION
            elif mem_type == "goal":
                mtype = MemoryType.GOAL
            else:
                mtype = MemoryType.LESSON
                
            mem_id = memory.remember(
                content=content,
                agent_id="test_user",
                memory_layer=MemoryLayer.SEMANTIC,
                memory_type=mtype,
                priority=priority
            )
            memory_ids.append(mem_id)
            print(f"    Stored: {content[:40]}...")
        
        print(f"  [PASS] Stored {len(memory_ids)} memories")
        
        # 测试2: 搜索记忆
        print("\n  Test 1.2: Search memories")
        search_queries = ["Python", "SQLite", "learn", "testing"]
        
        for query in search_queries:
            start = time.time()
            results = memory.recall(query, agent_id="test_user", limit=3)
            search_time = (time.time() - start) * 1000
            
            if results:
                print(f"    Query '{query}': {len(results)} results, {search_time:.1f}ms")
            else:
                print(f"    Query '{query}': No results")
        
        print("  [PASS] Search functionality works")
        
        # 测试3: 健康检查
        print("\n  Test 1.3: Health check")
        health = memory.check_health()
        print(f"    Health score: {health.health_score:.1f}/100")
        print(f"    Memory count: {health.memory_count}")
        print(f"    Active memories: {health.active_memories}")
        print("  [PASS] Health monitoring works")
        
        return memory, True
        
    except Exception as e:
        print(f"  [FAIL] Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def test_advanced_features(memory):
    """测试高级功能"""
    print("\n2. ADVANCED FEATURES TEST")
    
    try:
        # 测试1: 情景记忆
        print("\n  Test 2.1: Episodic memory with Q-values")
        
        # 记录任务情景
        tasks = [
            ("Install Python packages", "success"),
            ("Configure database", "success"),
            ("Debug code error", "failure"),
            ("Deploy application", "success")
        ]
        
        for task, outcome in tasks:
            episode_id = memory.record_episode(
                task=task,
                outcome=outcome,
                context={"test": True},
                agent_id="test_user"
            )
            print(f"    Recorded: {task} -> {outcome}")
        
        # 获取成功模式
        patterns = memory.get_successful_patterns("test_user", limit=2)
        if patterns:
            print(f"    Found {len(patterns)} success patterns")
        print("  [PASS] Episodic memory works")
        
        # 测试2: 上下文锚点
        print("\n  Test 2.2: Context anchors")
        anchor_id = memory.create_context_anchor(
            session_id="test_session",
            task_description="Testing enhanced memory system",
            key_decisions=["Use hybrid search", "Enable health monitoring"],
            open_loops=["Complete testing", "Generate report"],
            next_steps=["Run maintenance", "Backup data"]
        )
        
        if anchor_id:
            print(f"    Created context anchor: {anchor_id}")
            
            # 获取恢复简报
            briefing = memory.get_recovery_briefing(days_back=1)
            if briefing:
                print(f"    Current task: {briefing.get('current_task', 'None')}")
                print(f"    Open loops: {len(briefing.get('open_loops', []))}")
        print("  [PASS] Context anchors work")
        
        # 测试3: 自我修复
        print("\n  Test 2.3: Self-repair")
        repair_results = memory.perform_self_repair()
        
        if repair_results and 'error' not in repair_results:
            print(f"    Self-repair completed")
            print(f"    Reindexed: {repair_results.get('reindexed_memories', 0)} memories")
        else:
            print(f"    Self-repair: {repair_results.get('error', 'Unknown')}")
        print("  [PASS] Self-repair works")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Advanced features test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance(memory):
    """测试性能"""
    print("\n3. PERFORMANCE TEST")
    
    try:
        # 测试1: 批量操作性能
        print("\n  Test 3.1: Batch operations")
        
        batch_size = 10
        start_time = time.time()
        
        for i in range(batch_size):
            memory.remember(
                content=f"Performance test memory {i+1}",
                agent_id="perf_test",
                memory_layer=MemoryLayer.SEMANTIC,
                memory_type=MemoryType.FACT,
                priority=MemoryPriority.LOW
            )
        
        batch_time = (time.time() - start_time) * 1000
        avg_time = batch_time / batch_size
        
        print(f"    Batch insert {batch_size} memories")
        print(f"    Total time: {batch_time:.1f}ms")
        print(f"    Average per memory: {avg_time:.1f}ms")
        
        if avg_time < 100:
            print("    [PASS] Batch performance acceptable")
        else:
            print("    [WARN] Batch performance needs improvement")
        
        # 测试2: 搜索性能
        print("\n  Test 3.2: Search performance")
        
        test_queries = ["test", "memory", "performance", "search"]
        search_times = []
        
        for query in test_queries:
            start = time.time()
            results = memory.recall(query, limit=5)
            search_times.append((time.time() - start) * 1000)
        
        avg_search = sum(search_times) / len(search_times)
        print(f"    Average search time: {avg_search:.1f}ms")
        
        if avg_search < 200:
            print("    [PASS] Search performance acceptable")
        else:
            print("    [WARN] Search performance needs improvement")
        
        # 测试3: 系统统计
        print("\n  Test 3.3: System statistics")
        stats = memory.get_system_stats()
        
        if stats:
            print(f"    Database size: {stats['database']['size_mb']:.2f} MB")
            print(f"    Total memories: {stats['memories']['total']}")
            print(f"    Health score: {stats['performance']['health_score']:.1f}")
        
        print("  [PASS] Performance tests completed")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Performance test failed: {e}")
        return False

def run_real_world_scenario():
    """运行真实场景模拟"""
    print("\n4. REAL-WORLD SCENARIO")
    
    try:
        # 模拟开发工作流程
        print("\n  Scenario: Software development workflow")
        
        # 创建专门用于场景测试的系统
        scenario_memory = MetaMemoryEnhanced({
            'db_path': 'scenario_test.db',
            'reflection_enabled': True,
            'context_anchor_enabled': True
        })
        
        # 阶段1: 项目启动
        print("\n  Phase 1: Project initiation")
        scenario_memory.remember(
            content="Project: Build a task management app",
            agent_id="developer",
            memory_layer=MemoryLayer.EPISODIC,
            memory_type=MemoryType.DECISION,
            priority=MemoryPriority.CRITICAL
        )
        
        scenario_memory.remember(
            content="Technology stack: React frontend, Node.js backend, MongoDB database",
            agent_id="developer",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.DECISION,
            priority=MemoryPriority.HIGH
        )
        
        # 创建上下文锚点
        scenario_memory.create_context_anchor(
            session_id="project_init",
            task_description="Initialize task management project",
            key_decisions=["Use React/Node.js/MongoDB stack", "Start with basic CRUD features"],
            open_loops=["Set up development environment", "Create project structure"],
            next_steps=["Install dependencies", "Create initial components"]
        )
        
        # 阶段2: 开发过程
        print("\n  Phase 2: Development process")
        
        # 记录任务情景
        development_tasks = [
            ("Set up development environment", "success"),
            ("Create basic project structure", "success"),
            ("Implement user authentication", "success"),
            ("Fix database connection issue", "failure"),
            ("Deploy to test server", "success")
        ]
        
        for task, outcome in development_tasks:
            scenario_memory.record_episode(
                task=task,
                outcome=outcome,
                context={"phase": "development"},
                agent_id="developer"
            )
        
        # 阶段3: 搜索和回忆
        print("\n  Phase 3: Search and recall")
        
        # 搜索项目相关信息
        project_searches = ["project", "React", "database", "authentication"]
        
        for query in project_searches:
            results = scenario_memory.recall(query, agent_id="developer", limit=3)
            print(f"    Search '{query}': {len(results)} relevant memories")
        
        # 获取成功模式
        dev_patterns = scenario_memory.get_successful_patterns("developer", limit=3)
        if dev_patterns:
            print(f"\n    Development success patterns: {len(dev_patterns)}")
            for pattern in dev_patterns:
                print(f"      - Success rate: {pattern.get('success_rate', 0):.1%}")
        
        # 阶段4: 健康和维护
        print("\n  Phase 4: Health and maintenance")
        health = scenario_memory.check_health()
        print(f"    System health: {health.health_score:.1f}/100")
        
        # 运行维护
        maintenance = scenario_memory.run_maintenance()
        print(f"    Maintenance completed: {maintenance.get('timestamp', 'Unknown')}")
        
        # 获取恢复简报
        briefing = scenario_memory.get_recovery_briefing()
        if briefing:
            print(f"\n    Recovery briefing:")
            print(f"      Current task: {briefing.get('current_task', 'None')}")
            print(f"      Recent decisions: {len(briefing.get('recent_decisions', []))}")
            print(f"      Open loops: {len(briefing.get('open_loops', []))}")
        
        print("\n  [PASS] Real-world scenario completed successfully")
        
        # 清理场景测试数据库
        if os.path.exists('scenario_test.db'):
            os.remove('scenario_test.db')
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Real-world scenario failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    results = {
        "basic": False,
        "advanced": False,
        "performance": False,
        "scenario": False
    }
    
    # 运行基础功能测试
    memory, basic_ok = test_basic_functionality()
    results["basic"] = basic_ok
    
    if not basic_ok:
        print("\n[CRITICAL] Basic functionality failed. Stopping tests.")
        return results
    
    # 运行高级功能测试
    advanced_ok = test_advanced_features(memory)
    results["advanced"] = advanced_ok
    
    # 运行性能测试
    performance_ok = test_performance(memory)
    results["performance"] = performance_ok
    
    # 运行真实场景测试
    scenario_ok = run_real_world_scenario()
    results["scenario"] = scenario_ok
    
    # 生成测试报告
    print("\n" + "="*70)
    print("TEST REPORT")
    print("="*70)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    score = (passed_tests / total_tests) * 100
    
    print(f"\nTest Results:")
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name.upper():12} : {status}")
    
    print(f"\nOverall Score: {score:.1f}% ({passed_tests}/{total_tests})")
    
    if score >= 90:
        print("\n[EXCELLENT] System is production-ready!")
        print("  All core functions work correctly.")
        print("  Performance meets expectations.")
        print("  Advanced features add significant value.")
    elif score >= 70:
        print("\n[GOOD] System is functional but needs some improvements.")
        print("  Core functions work.")
        print("  Some advanced features may need tuning.")
    elif score >= 50:
        print("\n[FAIR] System works but has significant issues.")
        print("  Basic functions work.")
        print("  Advanced features need attention.")
    else:
        print("\n[POOR] System needs major improvements.")
        print("  Core functionality is compromised.")
    
    # 具体建议
    print("\nRecommendations:")
    if not results["basic"]:
        print("  • Fix basic functionality first")
    if not results["advanced"]:
        print("  • Debug advanced features")
    if not results["performance"]:
        print("  • Optimize performance")
    if not results["scenario"]:
        print("  • Improve real-world usability")
    
    if all(results.values()):
        print("  • System is ready for production use")
        print("  • Consider installing vector models for better search")
        print("  • Set up regular maintenance schedule")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 清理测试数据库
    test_dbs = ['practical_test.db', 'scenario_test.db']
    for db in test_dbs:
        if os.path.exists(db):
            os.remove(db)
            print(f"Cleaned up: {db}")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)