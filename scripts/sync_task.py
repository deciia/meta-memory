"""
Meta-Memory 自动同步脚本
由 OpenClaw cron 每小时调用
"""

import sys
from pathlib import Path

# 添加路径
skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

from meta_memory_enhancer import get_system

def main():
    print("[MetaMemory Sync] Starting sync...")
    
    try:
        system = get_system()
        system.initialize()
        
        result = system.sync()
        print(f"[MetaMemory Sync] Done - indexed: {result['total_indexed']}")
        
    except Exception as e:
        print(f"[MetaMemory Sync] Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
