#!/usr/bin/env python3
"""
简化版安装脚本 - 避免Unicode编码问题
"""

import os
import sys
import json
import shutil
from pathlib import Path

def setup_meta_memory():
    """安装和配置增强版元记忆系统"""
    
    print("="*60)
    print("增强版元记忆系统安装")
    print("="*60)
    
    # 1. 确定安装路径
    workspace_dir = Path.home() / ".openclaw" / "workspace"
    skills_dir = workspace_dir / "skills"
    meta_memory_dir = skills_dir / "meta-memory"
    
    print(f"工作空间: {workspace_dir}")
    print(f"技能目录: {skills_dir}")
    print(f"元记忆目录: {meta_memory_dir}")
    
    # 2. 创建目录结构
    print("\n1. 创建目录结构...")
    meta_memory_dir.mkdir(parents=True, exist_ok=True)
    
    src_dir = meta_memory_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    print(f"[OK] 目录创建完成: {meta_memory_dir}")
    
    # 3. 复制核心文件
    print("\n2. 复制核心文件...")
    
    # 当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 复制hybrid_search.py
    hybrid_source = current_dir / "src" / "hybrid_search.py"
    hybrid_dest = src_dir / "hybrid_search.py"
    if hybrid_source.exists():
        shutil.copy2(hybrid_source, hybrid_dest)
        print(f"  [OK] 混合搜索引擎: hybrid_search.py")
    
    # 复制enhanced_core.py (合并两个部分)
    print("  [INFO] 创建增强核心文件...")
    enhanced_content = ""
    
    # 读取第一部分
    part1_path = current_dir / "src" / "enhanced_core.py"
    if part1_path.exists():
        with open(part1_path, 'r', encoding='utf-8') as f:
            enhanced_content = f.read()
    
    # 读取第二部分
    part2_path = current_dir / "src" / "enhanced_core_continued.py"
    if part2_path.exists():
        with open(part2_path, 'r', encoding='utf-8') as f:
            # 找到第一部分结束的位置，追加第二部分
            if "def _test_search_performance(self) -> float:" in enhanced_content:
                # 只取第二部分中这个函数之后的内容
                part2_content = f.read()
                # 找到函数开始位置
                func_start = part2_content.find("def _test_search_performance(self) -> float:")
                if func_start != -1:
                    enhanced_content += "\n" + part2_content[func_start:]
    
    # 写入合并后的文件
    enhanced_dest = src_dir / "enhanced_core.py"
    with open(enhanced_dest, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    print(f"  [OK] 增强核心系统: enhanced_core.py")
    
    # 复制其他文件
    files_to_copy = [
        ("example_enhanced.py", "使用示例"),
        ("install_lightweight_model.py", "轻量级模型安装器")
    ]
    
    for file_name, description in files_to_copy:
        source = current_dir / file_name
        if source.exists():
            destination = meta_memory_dir / file_name
            shutil.copy2(source, destination)
            print(f"  [OK] {description}: {file_name}")
    
    # 4. 创建简化的SKILL.md
    print("\n3. 创建技能文档...")
    
    skill_md_content = """---
name: meta-memory-enhanced
description: Enhanced meta-memory skill with hybrid search, reflection, health monitoring, Q-value episodic memory, and context anchors.
version: 3.0.0
author: Xiao Ai
metadata:
  openclaw:
    emoji: "brain"
    category: "memory"
    requires:
      bins: ["python3"]
---

# Enhanced Meta-Memory Skill

Version 3.0.0 - Integrated optimization from 10+ reference skills.

## Core Features

1. **Hybrid Search System**
   - Vector search with sentence-transformers
   - Keyword search fallback
   - Automatic mode selection

2. **Reflection & Question Generation**
   - Post-session analysis
   - Confidence scoring
   - Question generation

3. **Health Monitoring**
   - Health score (0-100)
   - Self-repair capabilities
   - Performance metrics

4. **Q-value Episodic Memory**
   - Task episode recording
   - Success/failure patterns
   - Q-value scoring

5. **Context Anchors**
   - Session snapshots
   - Recovery briefing
   - Open loops tracking

## Quick Start

```python
from src.enhanced_core import MetaMemoryEnhanced

# Initialize
memory = MetaMemoryEnhanced({
    'db_path': 'meta_memory.db',
    'reflection_enabled': True
})

# Store memory
memory_id = memory.remember(
    content="User prefers Python for data analysis",
    agent_id="assistant"
)

# Search memories
results = memory.recall("Python data analysis")
```

## Installation

1. Run this setup script
2. Install vector model (optional):
   ```bash
   python install_lightweight_model.py
   ```

## Configuration

See `example_enhanced.py` for complete usage examples.

---
*Version: 3.0.0 | Updated: 2026-03-07*
"""
    
    skill_md_path = meta_memory_dir / "SKILL.md"
    skill_md_path.write_text(skill_md_content, encoding='utf-8')
    print(f"[OK] 技能文档: SKILL.md")
    
    # 5. 创建配置文件
    print("\n4. 创建配置文件...")
    
    config = {
        "db_path": str(workspace_dir / "meta_memory.db"),
        "backup_dir": str(workspace_dir / "backups"),
        "reflection_enabled": True,
        "context_anchor_enabled": True,
        "auto_maintenance": True
    }
    
    config_path = meta_memory_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 配置文件: config.json")
    
    # 6. 创建requirements.txt
    print("\n5. 创建依赖文件...")
    
    requirements_content = """# Enhanced Meta-Memory Dependencies

# Core
sqlite3

# Optional (for vector search)
# sentence-transformers
# torch
# transformers
"""
    
    requirements_path = meta_memory_dir / "requirements.txt"
    requirements_path.write_text(requirements_content, encoding='utf-8')
    print(f"[OK] 依赖文件: requirements.txt")
    
    # 7. 完成安装
    print("\n" + "="*60)
    print("安装完成!")
    print("="*60)
    
    print(f"\n安装位置: {meta_memory_dir}")
    print(f"\n主要文件:")
    print(f"  - SKILL.md - Documentation")
    print(f"  - src/enhanced_core.py - Core system")
    print(f"  - src/hybrid_search.py - Hybrid search engine")
    print(f"  - example_enhanced.py - Usage examples")
    print(f"  - install_lightweight_model.py - Model installer")
    
    print(f"\n下一步:")
    print(f"  1. 运行演示: python example_enhanced.py")
    print(f"  2. 安装向量模型: python install_lightweight_model.py")
    print(f"  3. 测试功能")
    
    print(f"\n提示:")
    print(f"  - 向量模型是可选的，系统会自动回退到关键词搜索")
    print(f"  - 建议安装 all-MiniLM-L6-v2 模型 (80MB)")
    
    return True

if __name__ == "__main__":
    try:
        success = setup_meta_memory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] 安装失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)