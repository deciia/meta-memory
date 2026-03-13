# 元记忆深度回忆 - PowerShell 调用脚本
# 用法: powershell -File recall.ps1 -Query "关键词" -Limit 10

param(
    [string]$Query = "",
    [int]$Limit = 10,
    [string]$Agent = "main",
    [string]$Action = "recall"
)

$SkillDir = Split-Path -Parent $PSScriptRoot
$SrcDir = Join-Path $SkillDir "src"

$pythonCode = @"
import sys
from pathlib import Path

sys.path.insert(0, r'$SkillDir')
sys.path.insert(0, r'$SrcDir')

from core import MetaMemoryEnhanced, MemoryLayer, MemoryType
import json

def deep_recall(query, agent_id='$Agent', limit=$Limit):
    memory = MetaMemoryEnhanced()
    results = memory.recall(query=query, agent_id=agent_id, limit=limit)
    
    print(f'🔍 检索: {query}')
    print(f'📊 找到 {len(results)} 条记忆:')
    print('-' * 50)
    
    if not results:
        print('❌ 未找到相关记忆')
        return
    
    for i, r in enumerate(results, 1):
        layer = r.memory_layer.value if hasattr(r, 'memory_layer') else 'unknown'
        importance = getattr(r, 'importance', 0)
        print(f'')
        print(f'【记忆 {i}】({layer}, 重要度: {importance:.2f})')
        print(f'  {r.content}')
        print('')

if __name__ == '__main__':
    deep_recall('$Query', limit=$Limit)
"@

if ($Action -eq "recall") {
    if (-not $Query) {
        Write-Host "用法: .\recall.ps1 -Query '关键词' [-Limit 10]"
        exit 1
    }
    echo $pythonCode | python -
} elseif ($Action -eq "recent") {
    $recentCode = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$SkillDir')
sys.path.insert(0, r'$SrcDir')

from core import MetaMemoryEnhanced
import json

memory = MetaMemoryEnhanced()
stats = memory.get_stats()
print('📊 系统统计:')
print(json.dumps(stats, ensure_ascii=False, indent=2))
"@
    echo $recentCode | python -
}
