@echo off
REM 元记忆深度回忆调用脚本

cd /d "%~dp0.."
python -c "
import sys
from pathlib import Path

# Add skill directory to path
skill_dir = Path(r'%~dp0').parent
sys.path.insert(0, str(skill_dir))
sys.path.insert(0, str(skill_dir / 'src'))

from core import MetaMemoryEnhanced, MemoryLayer, MemoryType
import json

def deep_recall(query, agent_id='main', limit=10):
    memory = MetaMemoryEnhanced()
    results = memory.recall(query=query, agent_id=agent_id, limit=limit)
    
    print(f'🔍 检索: {query}')
    print(f'📊 找到 {len(results)} 条记忆:\n')
    
    for i, r in enumerate(results, 1):
        layer = r.memory_layer.value if hasattr(r, 'memory_layer') else 'unknown'
        print(f'【{i}】({layer})')
        print(f'   {r.content[:200]}')
        print()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', nargs='?')
    parser.add_argument('-q', '--query', default='')
    parser.add_argument('-l', '--limit', type=int, default=10)
    args = parser.parse_args()
    
    if args.action == 'recall':
        deep_recall(args.query, limit=args.limit)
    else:
        print('用法: recall.bat -q "关键词"')
"
