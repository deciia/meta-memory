# -*- coding: utf-8 -*-
"""
批量导入 MEMORY.md 到 meta-memory
快速将历史记忆导入到增强版元记忆系统
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import MetaMemoryEnhanced, MemoryPriority, MemoryType, MemoryLayer
from datetime import datetime


def parse_memory_md(file_path: str):
    """解析 MEMORY.md 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按日期分割 - 匹配 **2026-03-07 15:15**:
    entries = []
    pattern = r'\*\*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\*\*:?(.+?)(?=\n\*\*\d{4}-\d{2}-\d{2} |\Z)'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        date_str = match.group(1)
        body = match.group(2).strip()
        
        # 提取第一行作为标题
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        title = lines[0] if lines else "无标题"
        if title.startswith('-'):
            title = lines[1] if len(lines) > 1 else title
        
        # 提取tags
        tags = []
        body_lower = body.lower()
        if 'skill' in body_lower or '技能' in body:
            tags.append('技能')
        if 'agent' in body_lower or '智能体' in body:
            tags.append('智能体')
        if '安全' in body:
            tags.append('安全')
        if '配置' in body or '绑定' in body:
            tags.append('配置')
        if '飞书' in body or 'feishu' in body_lower:
            tags.append('飞书')
        
        if tags:
            entries.append({
                'date': date_str,
                'title': title[:100],
                'content': body[:2000],
                'tags': tags
            })
    
    return entries


def batch_import(memory_file: str, meta_memory_path: str):
    """批量导入"""
    print(f"=== 批量导入 MEMORY.md ===\n")
    
    # 解析
    print(f"[1] 解析 MEMORY.md...")
    entries = parse_memory_md(memory_file)
    print(f"    找到 {len(entries)} 条记忆\n")
    
    # 初始化
    print(f"[2] 初始化 Meta-Memory...")
    memory = MetaMemoryEnhanced()
    print(f"    OK\n")
    
    # 导入
    print(f"[3] 批量导入...")
    for i, entry in enumerate(entries, 1):
        try:
            # 确定记忆类型
            mem_type = MemoryType.TEXT
            if '技能' in entry['tags']:
                mem_type = MemoryType.SKILL
            elif '智能体' in entry['tags']:
                mem_type = MemoryType.FACT
            
            # 确定优先级
            priority = MemoryPriority.HIGH
            if '安全' in entry['tags']:
                priority = MemoryPriority.CRITICAL
            
            # 存储
            memory.remember(
                content=entry['content'],
                tags=entry['tags'],
                memory_type=mem_type,
                priority=priority,
                memory_layer=MemoryLayer.SEMANTIC
            )
            
            print(f"    {i}. [{entry['date']}] {entry['title'][:50]}...")
            
        except Exception as e:
            print(f"    {i}. Error: {e}")
    
    print(f"\n[4] 完成! 共导入 {len(entries)} 条记忆")


if __name__ == "__main__":
    # MEMORY.md 路径
    memory_file = r"C:\Users\Administrator\.openclaw\workspace\MEMORY.md"
    
    # 执行导入
    batch_import(memory_file, None)
