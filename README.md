# Meta-Memory

Enhanced meta-memory skill for OpenClaw - Local memory management with vector search, predictive wakeup, multi-agent sharing.

## Features

- **Local Storage**: All data stored in `C:\Users\Administrator\.meta-memory`
- **Vector Search**: Using Ollama with local embedding model
- **Three-Layer Memory**: Short-term / Mid-term / Long-term retrieval
- **Auto Inference**: Automatic context analysis without trigger words
- **Predictive Wakeup**: Intelligent memory activation
- **Multi-Agent Sharing**: Share memories between agents

## Storage Structure

```
C:\Users\Administrator\.meta-memory\
├── index\              # Vector index (builtin memories)
├── backups\           # Auto backups
├── memory.db          # SQLite database
└── vector_db\        # ChromaDB (optional)
```

## Usage

```python
from meta_memory_enhancer import deep_recall, auto_infer, search

# Deep recall (with timeout protection)
result = deep_recall("what did I do recently")

# Auto inference
result = auto_infer("from meta-memory get my preferences")

# Basic search
results = search("user preferences")
```

## Requirements

- Python 3.13+
- Ollama with locusai/all-minilm-l6-v2 model

## Installation

```bash
# Install Ollama model
ollama pull locusai/all-minilm-l6-v2
```
