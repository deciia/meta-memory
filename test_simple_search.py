"""
简单搜索测试
"""

import sys
import os
import tempfile

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_simple():
    """简单测试"""
    print("简单搜索测试...")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "simple.db")
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 存储英文记忆
        memory_id = memory.remember(
            "User preference: dark theme, Chinese interface",
            agent_id="test",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.PREFERENCE,
            priority=MemoryPriority.HIGH
        )
        
        print(f"存储英文记忆: {memory_id[:8]}")
        
        # 搜索英文
        results = memory.recall("dark", agent_id="test")
        print(f"搜索'dark': 找到 {len(results)} 条记录")
        
        if results:
            print(f"内容: {results[0].content}")
        
        # 存储中文记忆
        chinese_id = memory.remember(
            "测试中文搜索功能",
            agent_id="test",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.MEDIUM
        )
        
        print(f"\n存储中文记忆: {chinese_id[:8]}")
        
        # 搜索中文 - 使用不同的查询方式
        queries = ["测试", "中文", "搜索", "功能", "测试中文"]
        
        for query in queries:
            print(f"\n搜索 '{query}':")
            try:
                # 直接调用storage的search_memories
                results = memory.storage.search_memories(query, "test")
                print(f"  storage.search_memories: {len(results)} 条记录")
            except Exception as e:
                print(f"  storage.search_memories 错误: {e}")
            
            try:
                # 使用recall方法
                results = memory.recall(query, agent_id="test")
                print(f"  memory.recall: {len(results)} 条记录")
            except Exception as e:
                print(f"  memory.recall 错误: {e}")
        
        # 测试空查询
        print(f"\n搜索空字符串:")
        results = memory.recall("", agent_id="test")
        print(f"  找到 {len(results)} 条记录 (应该返回所有记忆)")
        
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
    test_simple()