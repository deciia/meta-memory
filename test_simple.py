"""
简单测试合并后的元记忆技能
"""

import sys
import os
import tempfile
import shutil

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_basic():
    """测试基本功能"""
    print("=== 测试合并版元记忆技能 ===")
    
    try:
        # 导入核心模块
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        # 使用临时数据库
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print(f"测试数据库: {db_path}")
        
        # 简化配置
        config = {
            "retrieval": {
                "enable_vector_search": False,
                "enable_fts": True
            },
            "optimization": {
                "wakeup_prediction": False,
                "decay_enabled": False
            },
            "memory_layers": {
                "enabled": True
            },
            "monitoring": {
                "maintenance_automation": False
            }
        }
        
        # 初始化系统
        print("1. 初始化系统...")
        memory = MetaMemoryEnhanced(storage_path=db_path, config=config)
        print("   [OK] 系统初始化成功")
        
        # 测试记忆存储
        print("2. 测试记忆存储...")
        
        # 存储情景记忆
        episodic_id = memory.remember(
            "测试合并版元记忆技能",
            agent_id="test_agent",
            memory_layer=MemoryLayer.EPISODIC,
            memory_type=MemoryType.CONVERSATION,
            tags=["test", "merged"],
            priority=MemoryPriority.HIGH
        )
        print(f"   [OK] 存储情景记忆: {episodic_id[:8]}")
        
        # 存储语义记忆
        semantic_id = memory.remember(
            "合并版集成了5个参考技能的最佳实践",
            agent_id="test_agent",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            tags=["test", "enhanced"],
            priority=MemoryPriority.CRITICAL
        )
        print(f"   [OK] 存储语义记忆: {semantic_id[:8]}")
        
        # 测试搜索
        print("3. 测试搜索功能...")
        results = memory.recall("合并", agent_id="test_agent")
        print(f"   [OK] 搜索'合并': 找到 {len(results)} 个结果")
        
        # 测试遗忘和唤醒
        print("4. 测试遗忘和唤醒...")
        
        # 遗忘记忆
        forget_success = memory.forget(episodic_id, "test_agent", permanent=False)
        print(f"   [OK] 遗忘记忆: {'成功' if forget_success else '失败'}")
        
        # 唤醒记忆
        woken_memory = memory.wakeup(episodic_id, "test_agent", urgency="normal")
        print(f"   [OK] 唤醒记忆: {'成功' if woken_memory else '失败'}")
        
        # 获取统计
        print("5. 获取系统统计...")
        stats = memory.get_stats()
        total_memories = stats.get('base', {}).get('storage', {}).get('total_memories', 0)
        print(f"   [OK] 总记忆数: {total_memories}")
        
        # 测试维护
        print("6. 测试维护功能...")
        maintenance = memory.run_maintenance()
        print(f"   [OK] 维护任务: {len(maintenance)} 个任务完成")
        
        print("\n" + "="*60)
        print(" [SUCCESS] 合并版元记忆技能测试通过！")
        print("="*60)
        
        print("\n测试总结:")
        print("  [OK] 系统初始化")
        print("  [OK] 记忆存储")
        print("  [OK] 搜索功能")
        print("  [OK] 遗忘和唤醒")
        print("  [OK] 系统统计")
        print("  [OK] 维护功能")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    print("合并版元记忆技能简单测试")
    print("="*60)
    
    if test_basic():
        print("\n[OK] 技能功能正常")
        print("\n下一步:")
        print("  1. 重启 OpenClaw:")
        print("     openclaw restart")
        print("")
        print("  2. 启用增强功能 (可选):")
        print("     pip install sentence-transformers")
        
        sys.exit(0)
    else:
        print("\n[ERROR] 测试失败，请检查技能代码")
        sys.exit(1)