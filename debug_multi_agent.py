"""
调试多代理共享记忆问题
"""

import sys
import os
import tempfile
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def debug_multi_agent():
    """调试多代理共享问题"""
    print_header("调试多代理共享记忆问题")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        # 创建临时数据库
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "debug.db")
        
        print(f"数据库路径: {db_path}")
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path)
        print("系统初始化完成")
        
        # 1. 注册多个代理
        print("\n1. 注册代理:")
        memory.register_agent("agent1", "测试代理1")
        memory.register_agent("agent2", "测试代理2")
        memory.register_agent("agent3", "测试代理3")
        print("   [OK] 注册了3个代理")
        
        # 2. 代理1存储记忆
        print("\n2. 代理1存储记忆:")
        memory_id = memory.remember(
            "这是代理1的共享记忆内容，包含关键词'共享'和'测试'",
            agent_id="agent1",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH,
            tags=["shared", "test"]
        )
        print(f"   [OK] 存储记忆: {memory_id[:8]}")
        
        # 3. 检查代理1是否能搜索到自己的记忆
        print("\n3. 代理1搜索自己的记忆:")
        results_agent1 = memory.recall("共享", agent_id="agent1")
        print(f"   代理1搜索结果: {len(results_agent1)} 条记录")
        for i, result in enumerate(results_agent1[:3]):
            print(f"     {i+1}. {result.content[:50]}...")
        
        # 4. 检查代理2在共享前是否能搜索到记忆
        print("\n4. 代理2在共享前搜索:")
        results_agent2_before = memory.recall("共享", agent_id="agent2")
        print(f"   代理2搜索结果: {len(results_agent2_before)} 条记录")
        
        # 5. 代理1共享记忆给代理2
        print("\n5. 代理1共享记忆给代理2:")
        share_success = memory.share(memory_id, "agent2", "read", "agent1")
        print(f"   共享结果: {'[OK] 成功' if share_success else '[ERROR] 失败'}")
        
        # 6. 检查共享权限
        print("\n6. 检查共享权限:")
        try:
            permissions = memory.get_permissions(memory_id)
            print(f"   权限信息: {json.dumps(permissions, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"   [ERROR] 获取权限失败: {e}")
        
        # 7. 代理2在共享后搜索记忆
        print("\n7. 代理2在共享后搜索:")
        results_agent2_after = memory.recall("共享", agent_id="agent2")
        print(f"   代理2搜索结果: {len(results_agent2_after)} 条记录")
        for i, result in enumerate(results_agent2_after[:3]):
            print(f"     {i+1}. {result.content[:50]}...")
        
        # 8. 检查代理3（未共享）是否能搜索到
        print("\n8. 代理3（未共享）搜索:")
        results_agent3 = memory.recall("共享", agent_id="agent3")
        print(f"   代理3搜索结果: {len(results_agent3)} 条记录")
        
        # 9. 检查数据库中的共享记录
        print("\n9. 检查数据库记录:")
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查记忆表
            cursor.execute("SELECT id, content, agent_id, is_compressed FROM memories")
            memories = cursor.fetchall()
            print(f"   记忆表记录数: {len(memories)}")
            for mem in memories:
                print(f"     - ID: {mem[0][:8]}, 代理: {mem[2]}, 压缩: {mem[3]}")
            
            # 检查共享表
            cursor.execute("SELECT memory_id, agent_id, permission FROM shared_memories")
            shared = cursor.fetchall()
            print(f"   共享表记录数: {len(shared)}")
            for share in shared:
                print(f"     - 记忆ID: {share[0][:8]}, 代理: {share[1]}, 权限: {share[2]}")
            
            conn.close()
        except Exception as e:
            print(f"   [ERROR] 数据库检查失败: {e}")
        
        # 10. 测试直接获取记忆
        print("\n10. 代理2直接获取记忆:")
        try:
            direct_memory = memory.get_memory(memory_id, "agent2")
            if direct_memory:
                print(f"   [OK] 直接获取成功: {direct_memory.content[:50]}...")
            else:
                print("   [ERROR] 直接获取失败: 返回None")
        except Exception as e:
            print(f"   [ERROR] 直接获取失败: {e}")
        
        # 清理
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        print_header("调试完成")
        
        # 总结问题
        print("\n问题分析:")
        if len(results_agent2_after) > 0:
            print("[OK] 代理2可以访问共享记忆")
        else:
            print("[ERROR] 代理2无法访问共享记忆")
            print("可能原因:")
            print("  1. 搜索函数中的代理过滤逻辑问题")
            print("  2. 共享权限未正确设置")
            print("  3. 数据库查询条件错误")
        
        return len(results_agent2_after) > 0
        
    except Exception as e:
        print(f"[ERROR] 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_multi_agent()
    sys.exit(0 if success else 1)