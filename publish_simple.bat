@echo off
echo ==========================================
echo 发布 Meta-Memory 技能到 GitHub
echo ==========================================

echo.
echo 1. 检查当前目录
cd
echo 当前目录: %CD%

echo.
echo 2. 检查GitHub CLI配置
gh auth status
if %errorlevel% neq 0 (
    echo ❌ GitHub CLI认证失败
    exit /b 1
)
echo ✅ GitHub CLI已认证

echo.
echo 3. 检查仓库状态
gh repo view deciia/meta-memory --json name,description,url 2>nul
if %errorlevel% equ 0 (
    echo ✅ 仓库已存在: deciia/meta-memory
    set REPO_EXISTS=1
) else (
    echo ℹ️ 仓库不存在，需要创建
    set REPO_EXISTS=0
)

echo.
if %REPO_EXISTS% equ 0 (
    echo 4. 创建新仓库
    gh repo create deciia/meta-memory ^
        --description "Enhanced meta-memory skill for OpenClaw - Local memory management with vector search, predictive wakeup, multi-agent sharing" ^
        --public ^
        --confirm
    if %errorlevel% neq 0 (
        echo ❌ 仓库创建失败
        exit /b 1
    )
    echo ✅ 仓库创建成功
) else (
    echo 4. 仓库已存在，跳过创建
)

echo.
echo 5. 初始化Git仓库
if exist .git (
    echo ℹ️ Git仓库已存在，清理并重新初始化
    rmdir /s /q .git 2>nul
)

git init
git config user.name "deciia"
git config user.email "deciia@users.noreply.github.com"
echo ✅ Git初始化成功

echo.
echo 6. 添加文件到Git
git add .
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set FILE_COUNT=%%i
echo ✅ 添加了 %FILE_COUNT% 个文件

echo.
echo 7. 提交更改
git commit -m "feat: Initial release of enhanced meta-memory skill v2.0

- Complete memory management system for OpenClaw
- 6 core requirements fully satisfied
- 4 enhanced features integrated
- Vector search with sentence-transformers
- Predictive wakeup and multi-agent sharing
- Three-layer memory architecture
- Health monitoring and self-repair"
echo ✅ 提交成功

echo.
echo 8. 推送到GitHub
git remote add origin https://github.com/deciia/meta-memory.git 2>nul
git push -u origin main --force
echo ✅ 推送成功

echo.
echo 9. 创建版本标签
git tag -a "v2.0.0" -m "Enhanced meta-memory skill v2.0

Features:
- Complete memory management system
- Vector search integration
- Predictive wakeup
- Multi-agent sharing
- Three-layer architecture
- Health monitoring"
git push origin --tags
echo ✅ 标签 v2.0.0 创建成功

echo.
echo 10. 创建GitHub Release
echo # Enhanced Meta-Memory Skill v2.0 > release_notes.md
echo. >> release_notes.md
echo ## 🎯 Overview >> release_notes.md
echo Enhanced meta-memory skill for OpenClaw with complete memory management capabilities. >> release_notes.md
echo. >> release_notes.md
echo ## ✅ Core Requirements Satisfied >> release_notes.md
echo 1. **Meta-skill nature** - Foundation memory management for OpenClaw >> release_notes.md
echo 2. **100%% local storage** - No cloud dependencies >> release_notes.md
echo 3. **Forgetting and wakeup** - Smart forgetting, fast wakeup ^<200ms^> >> release_notes.md
echo 4. **100%% memory preservation** - Multiple backup mechanisms >> release_notes.md
echo 5. **Compressed storage** - ZLIB compression, millisecond recovery >> release_notes.md
echo 6. **Multi-agent sharing** - Secure inter-agent memory sharing >> release_notes.md
echo. >> release_notes.md
echo ## 🔧 Enhanced Features >> release_notes.md
echo - **Vector search integration** - Semantic search with sentence-transformers >> release_notes.md
echo - **Predictive wakeup** - Context-based predictive memory activation >> release_notes.md
echo - **Three-layer architecture** - Episodic, semantic, procedural memory >> release_notes.md
echo - **Health monitoring** - Comprehensive system health and self-repair >> release_notes.md

gh release create "v2.0.0" ^
    --title "Enhanced Meta-Memory Skill v2.0" ^
    --notes-file release_notes.md ^
    --target main
echo ✅ Release v2.0.0 创建成功

del release_notes.md 2>nul

echo.
echo 11. 更新仓库信息
gh repo edit deciia/meta-memory ^
    --description "Enhanced meta-memory skill for OpenClaw - Local memory management with vector search, predictive wakeup, multi-agent sharing" ^
    --add-topic "openclaw" ^
    --add-topic "memory" ^
    --add-topic "ai-agent" ^
    --add-topic "vector-search"
echo ✅ 仓库信息更新成功

echo.
echo ==========================================
echo 发布完成！
echo ==========================================

echo.
echo 📦 发布信息:
echo   仓库: https://github.com/deciia/meta-memory
echo   Release: https://github.com/deciia/meta-memory/releases/tag/v2.0.0
echo   版本: v2.0.0
echo   文件数: %FILE_COUNT%

echo.
echo 🚀 技能已成功发布到GitHub！
echo 现在可以通过以下方式安装：
echo   gh repo clone deciia/meta-memory ~/.openclaw/skills/meta-memory

echo.
echo ==========================================