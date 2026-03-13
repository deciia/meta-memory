"""
元记忆增强层 - 内置记忆读取模块
读取 OpenClaw 内置记忆系统，但不修改任何内容
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import re

# OpenClaw 工作空间
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
DAILY_DIR = WORKSPACE / "memory"


def read_memory_md() -> List[Dict[str, Any]]:
    """读取 MEMORY.md 内容"""
    if not MEMORY_FILE.exists():
        return []
    
    content = MEMORY_FILE.read_text(encoding='utf-8')
    
    # 提取所有文本内容（保留结构）
    sections = []
    current_section = {"title": "MEMORY.md", "content": "", "source": "MEMORY.md"}
    
    lines = content.split('\n')
    for line in lines:
        # 检测标题行作为分隔
        if line.startswith('#'):
            if current_section["content"].strip():
                sections.append(current_section)
            # 新section
            current_section = {"title": line.strip(), "content": line + "\n", "source": "MEMORY.md"}
        else:
            current_section["content"] += line + "\n"
    
    if current_section["content"].strip():
        sections.append(current_section)
    
    return [
        {
            "id": hashlib.md5(s["content"].encode()).hexdigest()[:12],
            "source": "MEMORY.md",
            "title": s["title"],
            "content": s["content"].strip(),
            "type": "longterm"
        }
        for s in sections if s["content"].strip()
    ]


def read_daily_logs() -> List[Dict[str, Any]]:
    """读取 daily logs"""
    if not DAILY_DIR.exists():
        return []
    
    memories = []
    
    # 读取所有 md 文件（排除当天）
    for md_file in DAILY_DIR.glob("*.md"):
        if md_file.name == "2026-03-14.md":  # 跳过今天
            continue
            
        content = md_file.read_text(encoding='utf-8')
        
        # 简单分块 - 按 ## 标题分段
        chunks = []
        current_chunk = ""
        
        for line in content.split('\n'):
            if line.startswith('##'):
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        for chunk in chunks:
            memories.append({
                "id": hashlib.md5(chunk.encode()).hexdigest()[:12],
                "source": str(md_file.name),
                "title": chunk.split('\n')[0][:50],
                "content": chunk,
                "type": "daily"
            })
    
    return memories


def read_session_context() -> List[Dict[str, Any]]:
    """读取 session 上下文（如果有）"""
    # TODO: 通过 OpenClaw API 读取当前 session
    # 当前返回空列表，等待后续集成
    return []


def get_all_built_in_memories() -> List[Dict[str, Any]]:
    """
    获取所有内置记忆（只读，不修改）
    返回结构化列表
    """
    all_memories = []
    
    # 1. MEMORY.md
    all_memories.extend(read_memory_md())
    
    # 2. Daily logs
    all_memories.extend(read_daily_logs())
    
    # 3. Session context (future)
    # all_memories.extend(read_session_context())
    
    return all_memories


def get_memory_stats() -> Dict[str, int]:
    """获取内置记忆统计"""
    memories = get_all_built_in_memories()
    
    return {
        "total": len(memories),
        "longterm": len(read_memory_md()),
        "daily": len(read_daily_logs()),
        "session": 0
    }


if __name__ == "__main__":
    import sys
    # 测试
    print("=== Built-in Memory Stats ===")
    stats = get_memory_stats()
    print(f"Total: {stats['total']}")
    print(f"  - Longterm: {stats['longterm']}")
    print(f"  - Daily: {stats['daily']}")
    print(f"  - Session: {stats['session']}")
    
    print("\n=== Read Sample ===")
    memories = get_all_built_in_memories()[:2]
    for m in memories:
        print(f"\n[{m['source']}] {m['title'][:40]}")
        print(f"  [content preview]")
