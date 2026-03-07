"""
直接搜索测试 - 避免编码问题
"""

import sys
import os
import tempfile

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_direct():
    """直接测试"""
    print("直接搜索测试...")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "direct.db")
        
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
        
        # 直接测试搜索
        print("\n直接测试搜索:")
        
        # 方法1: 直接调用storage
        print("方法1 - 直接调用storage.search_memories:")
        query = "测试"
        print(f"  查询: '{query}' (长度: {len(query)}, 类型: {type(query)})")
        
        try:
            results = memory.storage.search_memories(query, "test")
            print(f"  结果: {len(results)} 条记录")
            if results:
                print(f"  第一条内容: {results[0].content}")
        except Exception as e:
            print(f"  错误: {e}")
        
        # 方法2: 使用INSTR函数替代LIKE
        print("\n方法2 - 使用数据库INSTR函数:")
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 直接查询数据库
        cursor.execute("""
            SELECT content FROM memories 
            WHERE INSTR(content, ?) > 0
        """, (query,))
        
        db_results = cursor.fetchall()
        print(f"  数据库查询结果: {len(db_results)} 条记录")
        for row in db_results:
            print(f"    内容: {row[0]}")
        
        conn.close()
        
        # 方法3: 测试英文搜索
        print("\n方法3 - 测试英文搜索:")
        memory_id2 = memory.remember(
            "Test English search function",
            agent_id="test",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.MEDIUM
        )
        
        print(f"存储英文记忆: {memory_id2[:8]}")
        
        results = memory.recall("English", agent_id="test")
        print(f"搜索'English': 找到 {len(results)} 条记录")
        
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
    test_direct()