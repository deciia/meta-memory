#!/usr/bin/env python3
"""
增强版元记忆系统安装和配置脚本
"""

import os
import sys
import json
import shutil
from pathlib import Path

def setup_meta_memory():
    """安装和配置增强版元记忆系统"""
    
    print("="*60)
    print("[TOOLS] 增强版元记忆系统安装")
    print("="*60)
    
    # 1. 确定安装路径
    workspace_dir = Path.home() / ".openclaw" / "workspace"
    skills_dir = workspace_dir / "skills"
    meta_memory_dir = skills_dir / "meta-memory"
    
    print(f"工作空间: {workspace_dir}")
    print(f"技能目录: {skills_dir}")
    print(f"元记忆目录: {meta_memory_dir}")
    
    # 2. 创建目录结构
    print("\n1. [FOLDER] 创建目录结构...")
    meta_memory_dir.mkdir(parents=True, exist_ok=True)
    
    src_dir = meta_memory_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    print(f"[OK] 目录创建完成: {meta_memory_dir}")
    
    # 3. 复制文件
    print("\n2. 📄 复制文件...")
    
    # 当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 需要复制的文件列表
    files_to_copy = [
        ("src/hybrid_search.py", "混合搜索引擎"),
        ("src/enhanced_core.py", "增强核心系统"),
        ("example_enhanced.py", "使用示例"),
        ("install_lightweight_model.py", "轻量级模型安装器"),
        ("setup_enhanced.py", "安装脚本")
    ]
    
    for file_path, description in files_to_copy:
        source = current_dir / file_path
        if source.exists():
            destination = meta_memory_dir / file_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            print(f"  ✅ {description}: {file_path}")
        else:
            print(f"  ⚠️ 文件不存在: {file_path}")
    
    # 4. 创建SKILL.md
    print("\n3. 📝 创建技能文档...")
    
    skill_md_content = """---
name: meta-memory-enhanced
description: Enhanced meta-memory skill with hybrid search, reflection, health monitoring, Q-value episodic memory, and context anchors. Integrates best practices from 10+ reference skills.
version: 3.0.0
author: 小艾
metadata:
  openclaw:
    emoji: "🧠"
    category: "memory"
    requires:
      bins: ["python3"]
    install:
      - id: "install-meta-memory"
        kind: "script"
        script: "python setup_enhanced.py"
        label: "Install Enhanced Meta-Memory"
---

# 增强版元记忆技能 🧠

基于第二批10+参考技能优化的元记忆系统，集成以下增强功能：

## 🚀 核心增强功能

### 1. 混合搜索系统
- **向量搜索**: 支持sentence-transformers模型
- **关键词搜索**: 传统关键词匹配
- **自动回退**: 向量不可用时自动使用关键词搜索
- **智能模式选择**: 根据查询自动选择最佳搜索模式

### 2. 反思和问题生成（参考continuity）
- **会话后反思**: 自动分析会话并提取结构化记忆
- **置信度评分**: 4级置信度（明确、暗示、推断、推测）
- **问题生成**: 从反思中生成有意义的后续问题
- **身份认知更新**: 跟踪代理的成长和叙事

### 3. 健康监控（参考neuroboost-elixir）
- **健康评分**: 综合评分系统（0-100分）
- **5级健康状态**: 优秀、良好、一般、差、严重
- **性能监控**: 搜索性能、压缩率、成功率等
- **自我修复**: 自动重新索引、清理、优化、备份

### 4. Q值情景记忆（参考guava-memory）
- **任务情景记录**: 记录任务和结果
- **Q值评分**: 基于成功/失败动态调整
- **成功模式提取**: 识别重复成功的模式
- **反模式识别**: 识别需要避免的模式

### 5. 上下文锚点（参考context-anchor）
- **会话快照**: 记录会话的关键信息
- **恢复简报**: 压缩后快速恢复上下文
- **未完成事项跟踪**: 跟踪开放循环
- **下一步行动**: 记录计划中的行动

### 6. 知识图谱增强（参考cortex-memory）
- **实体提取**: 自动识别实体
- **关系跟踪**: 跟踪实体间关系
- **结构化存储**: 支持复杂的记忆结构

## 📦 安装

### 基础安装
```bash
# 在技能目录中运行
python setup_enhanced.py
```

### 安装向量模型（可选）
```bash
# 安装轻量级向量模型
python install_lightweight_model.py

# 选择模型（推荐选项1）:
# 1. all-MiniLM-L6-v2 (80MB) - 轻量级通用模型
# 2. paraphrase-multilingual-MiniLM-L12-v2 (420MB) - 多语言模型
# 3. shibing624/text2vec-base-chinese (390MB) - 中文优化模型
# 4. 跳过，仅使用关键词搜索
```

## 🚀 快速开始

```python
from src.enhanced_core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority

# 初始化
memory = MetaMemoryEnhanced({
    'db_path': 'meta_memory.db',
    'reflection_enabled': True,
    'context_anchor_enabled': True
})

# 存储记忆
memory_id = memory.remember(
    content="用户喜欢Python进行数据分析",
    agent_id="assistant",
    memory_layer=MemoryLayer.SEMANTIC,
    memory_type=MemoryType.PREFERENCE,
    priority=MemoryPriority.HIGH,
    confidence=0.95
)

# 搜索记忆
results = memory.recall("Python数据分析", agent_id="assistant")

# 健康检查
health = memory.check_health()
print(f"健康评分: {health.health_score:.1f}/100")

# 系统维护
maintenance = memory.run_maintenance()
```

## 🔧 配置选项

```python
config = {
    'db_path': 'meta_memory.db',           # 数据库路径
    'backup_dir': 'backups',               # 备份目录
    'reflection_enabled': True,            # 启用反思功能
    'reflection_threshold': 1800,          # 反思触发阈值（秒）
    'context_anchor_enabled': True,        # 启用上下文锚点
    'vector_model': 'all-MiniLM-L6-v2',    # 向量模型名称
    'auto_maintenance': True,              # 自动维护
    'maintenance_interval_hours': 24       # 维护间隔
}
```

## 📊 系统命令

### 健康检查
```python
# 获取健康报告
report = memory.get_health_report()
print(json.dumps(report, indent=2, ensure_ascii=False))
```

### 自我修复
```python
# 运行自我修复
repairs = memory.perform_self_repair()
```

### 系统统计
```python
# 获取系统统计
stats = memory.get_system_stats()
```

### 备份和恢复
```python
# 备份数据库
backup_path = memory.backup_database()

# 恢复数据库
memory.restore_database(backup_path)
```

### 导入导出
```python
# 导出记忆
memory.export_memories('memories.json', format='json')

# 导入记忆
imported = memory.import_memories('memories.json', format='json')
```

## 🧪 测试

运行完整演示：
```bash
python example_enhanced.py
```

## 🔒 安全特性

- **本地存储**: 所有数据存储在本地SQLite数据库
- **无云依赖**: 不依赖外部云服务（向量模型可选）
- **权限控制**: 多代理间的安全记忆共享
- **数据备份**: 自动备份和恢复机制
- **隐私保护**: 不收集或发送用户数据

## 📈 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 搜索延迟 | < 200ms | 混合搜索响应时间 |
| 记忆唤醒 | < 100ms | 压缩记忆恢复时间 |
| 压缩率 | 60-75% | 存储空间节省 |
| 健康评分 | > 75 | 系统健康状态 |
| 成功率 | > 80% | 任务执行成功率 |

## 🔄 维护计划

### 每日
- 自动健康检查
- 增量备份

### 每周
- 完整系统维护
- 深度清理和优化
- 健康报告生成

### 每月
- 数据库归档
- 性能调优
- 功能验证

## 🆘 故障排除

### 常见问题

1. **向量搜索不可用**
   ```
   # 安装依赖
   pip install sentence-transformers
   
   # 或使用纯关键词搜索
   config['vector_model'] = None
   ```

2. **数据库性能下降**
   ```
   # 运行维护
   memory.run_maintenance()
   
   # 优化数据库
   memory._optimize_database()
   ```

3. **记忆丢失**
   ```
   # 从备份恢复
   memory.restore_database('backups/latest_backup.db.gz')
   ```

4. **搜索无结果**
   ```
   # 重新索引
   memory._reindex_memories()
   
   # 检查搜索模式
   results = memory.recall(query, search_mode='keyword')
   ```

## 📚 参考技能

本技能集成了以下参考技能的最佳实践：

1. **continuity** - 反思和问题生成
2. **cortex-memory** - 知识图谱和实体关系
3. **neuroboost-elixir** - 健康监控和自我修复
4. **guava-memory** - Q值情景记忆
5. **context-anchor** - 上下文恢复
6. **elite-longterm-memory** - 混合搜索架构
7. **agent-memory-ultimate** - 本地存储和安全
8. **daily-memory-save** - 定期维护
9. **session-memory** - 会话连续性
10. **braindb** - 语义搜索性能

## 🎯 设计原则

1. **渐进增强**: 基础功能必须稳定，增强功能可选
2. **自动回退**: 高级功能失败时自动回退到基础功能
3. **配置驱动**: 所有功能可通过配置启用/禁用
4. **本地优先**: 所有数据100%本地存储
5. **安全第一**: 严格的权限控制和数据保护

---

*版本: 3.0.0 | 更新: 2026-03-07 | 作者: 小艾*"""
    
    skill_md_path = meta_memory_dir / "SKILL.md"
    skill_md_path.write_text(skill_md_content, encoding='utf-8')
    print(f"✅ 技能文档: SKILL.md")
    
    # 5. 创建OpenClaw配置
    print("\n4. ⚙️ 创建OpenClaw配置...")
    
    openclaw_config = {
        "skills": {
            "entries": {
                "meta-memory-enhanced": {
                    "enabled": True,
                    "config": {
                        "db_path": str(workspace_dir / "meta_memory.db"),
                        "backup_dir": str(workspace_dir / "backups"),
                        "reflection_enabled": True,
                        "context_anchor_enabled": True,
                        "auto_maintenance": True,
                        "maintenance_interval_hours": 24
                    }
                }
            }
        }
    }
    
    config_path = meta_memory_dir / "openclaw_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(openclaw_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenClaw配置: openclaw_config.json")
    
    # 6. 创建requirements.txt
    print("\n5. 📦 创建依赖文件...")
    
    requirements_content = """# 增强版元记忆系统依赖

## 核心依赖
sqlite3>=3.35.0

## 可选依赖（向量搜索）
# sentence-transformers>=2.2.0
# torch>=2.0.0
# transformers>=4.30.0

## 工具依赖
# 用于模型下载和测试
# requests>=2.28.0
# numpy>=1.24.0

## 安装命令
# pip install sqlite3
# pip install sentence-transformers torch transformers
"""
    
    requirements_path = meta_memory_dir / "requirements.txt"
    requirements_path.write_text(requirements_content, encoding='utf-8')
    print(f"✅ 依赖文件: requirements.txt")
    
    # 7. 创建测试脚本
    print("\n6. 🧪 创建测试脚本...")
    
    test_script = meta_memory_dir / "test_basic.py"
    test_content = """#!/usr/bin/env python3
"""
    test_script.write_text(test_content, encoding='utf-8')
    print(f"✅ 测试脚本: test_basic.py")
    
    # 8. 完成安装
    print("\n" + "="*60)
    print("🎉 安装完成!")
    print("="*60)
    
    print(f"\n📁 安装位置: {meta_memory_dir}")
    print(f"📄 主要文件:")
    print(f"  • SKILL.md - 技能文档")
    print(f"  • src/enhanced_core.py - 核心系统")
    print(f"  • src/hybrid_search.py - 混合搜索引擎")
    print(f"  • example_enhanced.py - 使用示例")
    print(f"  • install_lightweight_model.py - 模型安装器")
    
    print(f"\n🚀 下一步:")
    print(f"  1. 运行演示: python example_enhanced.py")
    print(f"  2. 安装向量模型: python install_lightweight_model.py")
    print(f"  3. 集成到OpenClaw: 将配置添加到openclaw.json")
    
    print(f"\n💡 提示:")
    print(f"  • 向量模型是可选的，系统会自动回退到关键词搜索")
    print(f"  • 建议安装all-MiniLM-L6-v2模型（80MB）")
    print(f"  • 定期运行健康检查和维护")
    
    return True

if __name__ == "__main__":
    try:
        success = setup_meta_memory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)