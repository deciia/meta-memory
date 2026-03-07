"""
合并版元记忆技能使用示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority

def main():
    """基本使用示例"""
    print("=== 合并版元记忆技能使用示例 ===")
    
    # 1. 初始化系统
    print("\n1. 初始化系统...")
    memory = MetaMemoryEnhanced()
    print("   系统初始化完成")
    
    # 2. 注册代理
    print("\n2. 注册代理...")
    memory.register_agent("assistant", "助手")
    memory.register_agent("user", "用户")
    print("   注册了2个代理")
    
    # 3. 存储三层次记忆
    print("\n3. 存储三层次记忆...")
    
    # 情景记忆 (具体事件)
    episodic_id = memory.remember(
        "用户今天提出了元记忆技能的改进需求",
        agent_id="assistant",
        memory_layer=MemoryLayer.EPISODIC,
        memory_type=MemoryType.CONVERSATION,
        tags=["meeting", "requirement"],
        priority=MemoryPriority.HIGH
    )
    print(f"   情景记忆: {episodic_id[:8]}")
    
    # 语义记忆 (事实知识)
    semantic_id = memory.remember(
        "元记忆技能应该支持向量搜索和智能唤醒",
        agent_id="assistant",
        memory_layer=MemoryLayer.SEMANTIC,
        memory_type=MemoryType.FACT,
        tags=["fact", "design"],
        priority=MemoryPriority.CRITICAL
    )
    print(f"   语义记忆: {semantic_id[:8]}")
    
    # 程序记忆 (技能流程)
    procedural_id = memory.remember(
        "安装 sentence-transformers: pip install sentence-transformers",
        agent_id="assistant",
        memory_layer=MemoryLayer.PROCEDURAL,
        memory_type=MemoryType.SKILL,
        tags=["tutorial", "installation"],
        priority=MemoryPriority.MEDIUM
    )
    print(f"   程序记忆: {procedural_id[:8]}")
    
    # 4. 搜索记忆 (混合搜索)
    print("\n4. 搜索记忆...")
    results = memory.recall("向量搜索", agent_id="assistant")
    print(f"   搜索'向量搜索': 找到 {len(results)} 个相关记忆")
    
    # 5. 共享记忆
    print("\n5. 共享记忆...")
    success = memory.share(semantic_id, "user", "read", "assistant")
    print(f"   共享语义记忆给用户: {'成功' if success else '失败'}")
    
    # 6. 遗忘和唤醒
    print("\n6. 遗忘和唤醒...")
    
    # 遗忘不重要记忆
    memory.forget(episodic_id, "assistant", permanent=False)
    print(f"   遗忘情景记忆: {episodic_id[:8]}")
    
    # 唤醒记忆
    woken = memory.wakeup(episodic_id, "assistant", urgency="normal")
    if woken:
        print(f"   唤醒记忆: {woken.content[:50]}...")
    
    # 7. 获取统计
    print("\n7. 系统统计...")
    stats = memory.get_stats()
    print(f"   总记忆数: {stats.get('base', {}).get('storage', {}).get('total_memories', 0)}")
    
    # 8. 运行维护
    print("\n8. 运行维护...")
    maintenance = memory.run_maintenance()
    print(f"   完成 {len(maintenance)} 个维护任务")
    
    print("\n=== 示例完成 ===")
    print("\n增强版功能:")
    print("  [OK] 向量搜索集成 (需安装 sentence-transformers)")
    print("  [OK] 智能预测唤醒")
    print("  [OK] 三层次记忆架构")
    print("  [OK] 完善监控维护")
    print("  [OK] 100%本地存储 + 本地备份")

if __name__ == "__main__":
    main()