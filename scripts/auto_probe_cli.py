# -*- coding: utf-8 -*-
"""
Meta-Memory 自动推测 CLI
用于测试和演示自动推测功能
"""

import sys
import os

# 获取正确的工作目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

# 改变工作目录以便正确导入
os.chdir(project_dir)

from src.auto_probe import AutoProbeEngine, create_auto_probe


def test_auto_probe():
    """测试自动推测功能"""
    print("=== Meta-Memory 自动推测测试 ===\n")
    
    # 1. 初始化记忆系统
    print("[1] 初始化 Meta-Memory...")
    from src.core import MetaMemoryEnhanced
    memory = MetaMemoryEnhanced()
    print(f"    OK: Meta-Memory 初始化成功")
    
    # 2. 初始化自动推测引擎
    print("\n[2] 初始化自动推测引擎...")
    probe = create_auto_probe(memory)
    status = probe.get_status()
    print(f"    Ollama: {'在线' if status['ollama_health'] else '离线'}")
    print(f"    向量模型: {status['vector_model']}")
    
    # 3. 添加一些测试记忆
    print("\n[3] 添加测试记忆...")
    from src.core import MemoryPriority, MemoryType
    
    # 映射字符串到枚举
    type_map = {
        "skill": MemoryType.SKILL,
        "project": MemoryType.TEXT,
        "person": MemoryType.FACT,
        "preference": MemoryType.PREFERENCE,
        "fact": MemoryType.FACT
    }
    
    test_memories = [
        ("2026-03-07: 安装了 desktop-control 技能，用于桌面自动化控制", "skill", ["技能", "桌面", "自动化"]),
        ("2026-03-11: 部署了完整的安全防御矩阵，包括红线规则和夜间巡检", "project", ["安全", "防御", "部署"]),
        ("异恒是团队负责人，创建了多智能体系统架构", "person", ["异恒", "负责人", "架构"]),
        ("用户喜欢简洁的回复风格，不要太啰嗦", "preference", ["偏好", "风格"]),
        ("Meta-memory 是元记忆技能，管理长期记忆存储", "fact", ["记忆", "技能"])
    ]
    
    for content, mem_type_str, tags in test_memories:
        memory.remember(
            content, 
            tags=tags, 
            memory_type=type_map.get(mem_type_str, MemoryType.TEXT),  # 使用枚举
            priority=MemoryPriority.HIGH  # 使用枚举
        )
    
    print(f"    OK: 添加了 {len(test_memories)} 条记忆")
    
    # 4. 测试自动推测
    print("\n[4] 测试自动推测...")
    
    test_queries = [
        "我之前做的安全项目怎样了",
        "我安装了哪些技能",
        "异恒是谁",
        "我的回复风格偏好是什么"
    ]
    
    for query in test_queries:
        print(f"\n    --- 查询: {query} ---")
        result = probe.probe_and_inject(query, "test_user")
        
        print(f"    置信度: {result.confidence:.2f}")
        print(f"    提取话题: {result.injected_topics}")
        
        if result.memories:
            print(f"    推测记忆 Top 3:")
            for i, mem in enumerate(result.memories[:3], 1):
                source_emoji = {'short_term': '[S]', 'medium_term': '[M]', 'long_term': '[L]'}.get(mem.get('source', ''), '[*]')
                print(f"      {i}. {source_emoji} {mem['content'][:50]}... (score: {mem['weighted_score']:.2f})")
        else:
            print(f"    未找到相关记忆")
    
    # 5. 测试深度回忆
    print("\n\n[5] 测试深度回忆...")
    deep_results = probe.deep_recall("技能安装", depth=3)
    print(f"    找到 {len(deep_results)} 条相关记忆:")
    for i, r in enumerate(deep_results[:5], 1):
        print(f"    {i}. [{r['layer']}] {r['content'][:50]}... (得分: {r['score']:.2f})")
    
    # 6. 状态检查
    print("\n\n[6] 系统状态:")
    final_status = probe.get_status()
    print(f"    Ollama: {'在线' if final_status['ollama_health'] else '离线'}")
    print(f"    用户画像数: {final_status['user_profiles']}")
    
    print("\n=== 测试完成 ===")


def test_ollama_only():
    """仅测试 Ollama 连接"""
    print("=== Ollama 连接测试 ===\n")
    
    from src.auto_probe import OllamaClient
    
    client = OllamaClient()
    
    print(f"服务健康: {client.health_check()}")
    
    if client.health_check():
        # 测试嵌入
        text = "测试文本嵌入"
        emb = client.get_embedding(text)
        if emb:
            print(f"嵌入维度: {len(emb)}")
            print(f"前5维: {emb[:5]}")
        
        # 测试相似度
        sim = client.compute_similarity("我喜欢编程", "编程是我的爱好")
        print(f"\n相似度测试: '我喜欢编程' vs '编程是我的爱好' = {sim:.3f}")
    else:
        print("Ollama 服务未启动")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Meta-Memory Auto Probe CLI')
    parser.add_argument('--ollama-only', action='store_true', help='仅测试 Ollama 连接')
    args = parser.parse_args()
    
    if args.ollama_only:
        test_ollama_only()
    else:
        test_auto_probe()
