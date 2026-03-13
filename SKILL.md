---
name: meta-memory
description: 元记忆增强技能 - 继承原有功能并增强 OpenClaw 内置记忆系统
homepage: https://github.com/deciia/meta-memory
metadata:
  openclaw:
    emoji: "🧠"
    requires:
      bins: ["python"]
      env: []
    category: "memory"
    tags: ["memory", "storage", "search", "builtin", "enhancer", "vector"]
---

# Meta-Memory Skill

## 概述

元记忆增强技能，继承原有元记忆核心功能，同时增强 OpenClaw 内置记忆系统。

## 核心特性

- 本地存储: 所有数据存储在 `C:\Users\Administrator\.meta-memory`
- 向量搜索: 使用 Ollama 本地向量模型
- 三层记忆: 短期 / 中期 / 长期检索
- 自动推测: 无需触发词自动分析上下文
- 预测唤醒: 智能记忆激活
- 多代理共享: Agent 间共享记忆

## 双层存储架构

```
[用户对话] → [内置记忆] ←→ [元记忆增强层]
                      ├── 读取 (只读)
                      ├── 向量化 (Ollama)
                      └── 提供增强搜索
```

## 存储结构

```
C:\Users\Administrator\.meta-memory\
├── index\              # 向量索引 (内置记忆)
├── backups\           # 自动备份
├── memory.db          # SQLite 数据库
└── vector_db\        # ChromaDB (可选)
```

## 功能接口

### 原有接口
```python
remember(content, agent_id, memory_layer, memory_type, priority)
recall(query, agent_id)
forget(memory_id, agent_id)
wakeup(memory_id, agent_id, urgency)
```

### 增强接口
```python
search(query, top_k)         # 语义搜索
deep_recall(query, timeout)   # 深度回忆 (带超时保护)
auto_infer(query)            # 自动推测
get_stats()                  # 统计信息
```

## 依赖

- Python 3.13+
- Ollama (本地向量模型)
- 模型: locusai/all-minilm-l6-v2

## 安装

```bash
# 安装 Ollama 向量模型
ollama pull locusai/all-minilm-l6-v2
```

## 版本

- 3.0.0 - 增强版，统一存储到 .meta-memory
