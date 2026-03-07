"""
测试搜索问题修复
"""

import sys
import os
import tempfile

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_search_issue():
    """测试搜索问题"""
    print("测试搜索问题...")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "search_test.db")
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 注册代理
        memory.register_agent("agent1", "代理1")
        memory.register_agent("agent2", "代理2")
        
        # 存储测试记忆
        test_content = "用户偏好设置：喜欢深色主题，使用中文界面"
        memory_id = memory.remember(
            test_content,
            agent_id="agent1",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.PREFERENCE,
            priority=MemoryPriority.HIGH
        )
        
        print(f"存储记忆: {memory_id[:8]}")
        print(f"内容: {test_content}")
        
        # 测试代理1搜索
        print("\n1. 代理1搜索:")
        queries = ["偏好", "中文", "主题", "用户", test_content[:5]]
        for query in queries:
            results = memory.recall(query, agent_id="agent1")
            print(f"  查询 '{query}': 找到 {len(results)} 条记录")
            if results:
                print(f"    内容: {results[0].content[:50]}...")
        
        # 共享记忆
        print("\n2. 共享记忆给代理2:")
        share_success = memory.share(memory_id, "agent2", "read", "agent1")
        print(f"  共享结果: {'成功' if share_success else '失败'}")
        
        # 测试代理2搜索
        print("\n3. 代理2搜索:")
        for query in queries:
            results = memory.recall(query, agent_id="agent2")
            print(f"  查询 '{query}': 找到 {len(results)} 条记录")
            if results:
                print(f"    内容: {results[0].content[:50]}...")
        
        # 测试直接获取
        print("\n4. 代理2直接获取:")
        direct = memory.get_memory(memory_id, "agent2")
        if direct:
            print(f"  成功获取: {direct.content[:50]}...")
        else:
            print("  获取失败")
        
        # 检查数据库
        print("\n5. 检查数据库:")
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查记忆表
        cursor.execute("SELECT id, content, owner_agent FROM memories")
        memories = cursor.fetchall()
        print(f"  记忆表: {len(memories)} 条记录")
        for mem in memories:
            print(f"    ID: {mem[0][:8]}, 所有者: {mem[2]}")
        
        # 检查共享表
        cursor.execute("SELECT memory_id, agent_id, permission FROM sharing_permissions")
        shared = cursor.fetchall()
        print(f"  共享表: {len(shared)} 条记录")
        for share in shared:
            print(f"    记忆ID: {share[0][:8]}, 代理: {share[1]}, 权限: {share[2]}")
        
        # 检查FTS表
        try:
            cursor.execute("SELECT count(*) FROM memories_fts")
            fts_count = cursor.fetchone()[0]
            print(f"  FTS表: {fts_count} 条记录")
        except:
            print("  FTS表不存在或查询失败")
        
        conn.close()
        
        # 清理
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        print("\n测试完成")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_search_issue()