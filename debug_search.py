"""
调试搜索问题
"""

import sys
import os
import tempfile
import sqlite3

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def debug_search():
    """调试搜索问题"""
    print("调试搜索问题...")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "debug.db")
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 存储测试记忆
        test_content = "测试中文搜索功能"
        memory_id = memory.remember(
            test_content,
            agent_id="test",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )
        
        print(f"存储记忆: {memory_id[:8]}")
        print(f"内容: {test_content}")
        
        # 直接测试数据库查询
        print("\n直接数据库查询测试:")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = "测试"
        
        # 测试1: 简单的LIKE查询
        print(f"\n测试1: 简单LIKE查询 '{query}':")
        cursor.execute("SELECT content FROM memories WHERE content LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        print(f"  结果: {len(results)} 条记录")
        for row in results:
            print(f"    内容: {row[0]}")
        
        # 测试2: 带权限条件的查询
        print(f"\n测试2: 带权限条件的查询:")
        sql = """
            SELECT m.* FROM memories m
            WHERE (m.owner_agent = ? OR EXISTS (
                SELECT 1 FROM sharing_permissions sp 
                WHERE sp.memory_id = m.id AND sp.agent_id = ?
            )) AND m.content LIKE ?
        """
        cursor.execute(sql, ("test", "test", f"%{query}%"))
        results = cursor.fetchall()
        print(f"  结果: {len(results)} 条记录")
        
        # 测试3: 检查表结构
        print(f"\n测试3: 检查表结构:")
        cursor.execute("PRAGMA table_info(memories)")
        columns = cursor.fetchall()
        print("  memories表列:")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
        
        # 测试4: 检查数据
        print(f"\n测试4: 检查数据:")
        cursor.execute("SELECT id, content, owner_agent FROM memories")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  ID: {row[0][:8]}, 所有者: {row[2]}")
            print(f"    内容: {row[1]}")
        
        conn.close()
        
        # 测试5: 调用search_memories方法
        print(f"\n测试5: 调用search_memories方法:")
        try:
            results = memory.storage.search_memories(query, "test")
            print(f"  search_memories结果: {len(results)} 条记录")
            
            # 查看实际执行的SQL
            print(f"\n  查看search_memories的SQL逻辑:")
            print(f"  查询: '{query}'")
            print(f"  代理: 'test'")
            
        except Exception as e:
            print(f"  search_memories错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 清理
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        print("\n调试完成")
        return True
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_search()