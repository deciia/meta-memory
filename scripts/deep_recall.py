#!/usr/bin/env python3
"""
元记忆深度回忆调用脚本
用于从 meta-memory 中检索记忆并结合 session-memory 生成回复
"""

import sys
import os
from pathlib import Path

# 添加技能路径 - 支持直接运行和模块导入
skill_dir = Path(__file__).parent.parent
src_dir = skill_dir / "src"

# 确保 src 是可导入的包
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 修复相对导入问题 - 模拟包环境
import importlib.util

# 加载 storage_enhanced
storage_spec = importlib.util.spec_from_file_location(
    "storage_enhanced", 
    src_dir / "storage_enhanced.py"
)
storage_enhanced = importlib.util.module_from_spec(storage_spec)

# 先加载依赖模块
vector_spec = importlib.util.spec_from_file_location(
    "vector_search",
    src_dir / "vector_search.py"
)
vector_search = importlib.util.module_from_spec(vector_spec)
vector_spec.loader.exec_module(vector_search)

predictive_spec = importlib.util.spec_from_file_location(
    "predictive_wakeup",
    src_dir / "predictive_wakeup.py"
)
predictive_wakeup = importlib.util.module_from_spec(predictive_spec)
predictive_spec.loader.exec_module(predictive_wakeup)

three_layer_spec = importlib.util.spec_from_file_location(
    "three_layer_memory",
    src_dir / "three_layer_memory.py"
)
three_layer_memory = importlib.util.module_from_spec(three_layer_spec)
three_layer_spec.loader.exec_module(three_layer_memory)

# 注入到 sys.modules
sys.modules['storage_enhanced'] = storage_enhanced
sys.modules['vector_search'] = vector_search
sys.modules['predictive_wakeup'] = predictive_wakeup
sys.modules['three_layer_memory'] = three_layer_memory

# 加载并执行 storage_enhanced
storage_spec.loader.exec_module(storage_enhanced)

# 现在可以安全导入 core
from core import MetaMemoryEnhanced, MemoryLayer, MemoryType
import json

def deep_recall(query: str, agent_id: str = "main", limit: int = 10):
    """
    深度回忆：从 meta-memory 中检索相关记忆
    
    Args:
        query: 检索关键词/问题
        agent_id: 智能体ID
        limit: 返回记忆数量
    
    Returns:
        检索到的记忆列表
    """
    # 初始化元记忆系统
    memory = MetaMemoryEnhanced()
    
    print(f"🔍 正在检索: {query}")
    print(f"📊 目标智能体: {agent_id}")
    print("-" * 50)
    
    # 从元记忆检索
    results = memory.recall(
        query=query,
        agent_id=agent_id,
        limit=limit
    )
    
    if not results:
        print("❌ 未找到相关记忆")
        return []
    
    print(f"✅ 找到 {len(results)} 条相关记忆:\n")
    
    # 格式化输出
    formatted_results = []
    for i, record in enumerate(results, 1):
        layer_name = record.memory_layer.value if hasattr(record, 'memory_layer') else 'unknown'
        importance = getattr(record, 'importance', 0)
        
        result = {
            "index": i,
            "content": record.content,
            "layer": layer_name,
            "importance": importance,
            "created_at": getattr(record, 'created_at', 'unknown')
        }
        formatted_results.append(result)
        
        print(f"【记忆 {i}】({layer_name}, 重要度: {importance:.2f})")
        print(f"  {record.content}")
        print()
    
    return formatted_results


def get_recent_memories(agent_id: str = "main", days: int = 7, limit: int = 20):
    """
    获取最近N天的所有记忆
    
    Args:
        agent_id: 智能体ID
        days: 天数
        limit: 返回数量
    
    Returns:
        最近记忆列表
    """
    memory = MetaMemoryEnhanced()
    
    print(f"📅 获取最近 {days} 天的记忆...\n")
    
    # 获取统计信息
    stats = memory.get_stats()
    print(f"📊 系统统计: {json.dumps(stats, ensure_ascii=False, indent=2)}\n")
    
    # 检索所有记忆（按相关性排序）
    results = memory.recall(
        query="",  # 空查询获取所有
        agent_id=agent_id,
        limit=limit
    )
    
    return results


def store_memory(content: str, agent_id: str = "main", 
                 memory_layer: MemoryLayer = MemoryLayer.SEMANTIC,
                 memory_type: MemoryType = MemoryType.TEXT,
                 tags: list = None):
    """
    存储记忆到元记忆系统
    
    Args:
        content: 记忆内容
        agent_id: 智能体ID
        memory_layer: 记忆层次
        memory_type: 记忆类型
        tags: 标签列表
    
    Returns:
        记忆ID
    """
    memory = MetaMemoryEnhanced()
    
    memory_id = memory.remember(
        content=content,
        agent_id=agent_id,
        memory_layer=memory_layer,
        memory_type=memory_type,
        tags=tags or []
    )
    
    print(f"✅ 记忆已存储: {memory_id}")
    return memory_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="元记忆深度回忆工具")
    parser.add_argument("action", choices=["recall", "recent", "store"],
                        help="操作类型")
    parser.add_argument("-q", "--query", default="", help="检索关键词")
    parser.add_argument("-a", "--agent", default="main", help="智能体ID")
    parser.add_argument("-l", "--limit", type=int, default=10, help="返回数量")
    parser.add_argument("-d", "--days", type=int, default=7, help="天数（仅recent有效）")
    parser.add_argument("-c", "--content", default="", help="存储内容（仅store有效）")
    parser.add_argument("-t", "--tags", default="", help="标签，逗号分隔")
    
    args = parser.parse_args()
    
    if args.action == "recall":
        deep_recall(args.query, args.agent, args.limit)
    elif args.action == "recent":
        get_recent_memories(args.agent, args.days, args.limit)
    elif args.action == "store":
        tags = args.tags.split(",") if args.tags else []
        store_memory(args.content, args.agent, tags=tags)
