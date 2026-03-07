#!/usr/bin/env python3
"""
轻量级向量模型安装脚本
提供多种向量模型选项，从轻量级到完整版
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path

class VectorModelInstaller:
    """向量模型安装器"""
    
    def __init__(self):
        self.system = platform.system()
        self.python_cmd = sys.executable
        self.install_dir = Path.home() / ".openclaw" / "models"
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        # 可用的模型选项（按大小和复杂度排序）
        self.model_options = {
            "tiny": {
                "name": "all-MiniLM-L6-v2",
                "size_mb": 80,
                "description": "轻量级通用模型，适合大多数应用",
                "recommended": True
            },
            "small": {
                "name": "paraphrase-MiniLM-L3-v2",
                "size_mb": 60,
                "description": "更小的模型，适合语义相似度",
                "recommended": False
            },
            "multilingual": {
                "name": "paraphrase-multilingual-MiniLM-L12-v2",
                "size_mb": 420,
                "description": "多语言模型，支持中文更好",
                "recommended": True
            },
            "chinese": {
                "name": "shibing624/text2vec-base-chinese",
                "size_mb": 390,
                "description": "专门的中文向量模型",
                "recommended": True
            },
            "large": {
                "name": "all-mpnet-base-v2",
                "size_mb": 420,
                "description": "高质量通用模型",
                "recommended": False
            }
        }
    
    def check_dependencies(self):
        """检查依赖"""
        print("🔍 检查依赖...")
        
        # 检查Python包
        required_packages = ["torch", "transformers", "sentencepiece", "protobuf"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package}")
        
        return missing_packages
    
    def install_dependencies(self, missing_packages):
        """安装缺失的依赖"""
        if not missing_packages:
            print("✅ 所有依赖已安装")
            return True
        
        print(f"📦 安装缺失的包: {', '.join(missing_packages)}")
        
        try:
            # 使用清华镜像源加速下载
            cmd = [
                self.python_cmd, "-m", "pip", "install",
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
            ] + missing_packages
            
            print(f"运行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖安装成功")
                return True
            else:
                print(f"❌ 依赖安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 安装过程出错: {e}")
            return False
    
    def show_model_options(self):
        """显示模型选项"""
        print("\n" + "="*60)
        print("📊 可用的向量模型选项")
        print("="*60)
        
        for key, info in self.model_options.items():
            recommended = "🌟 推荐" if info["recommended"] else ""
            print(f"\n{key.upper()}: {info['name']}")
            print(f"   大小: {info['size_mb']}MB")
            print(f"   描述: {info['description']}")
            print(f"   {recommended}")
        
        print("\n" + "="*60)
    
    def download_model(self, model_key):
        """下载指定模型"""
        if model_key not in self.model_options:
            print(f"❌ 未知的模型选项: {model_key}")
            return False
        
        model_info = self.model_options[model_key]
        model_name = model_info["name"]
        
        print(f"\n🚀 开始下载模型: {model_name}")
        print(f"   预计大小: {model_info['size_mb']}MB")
        print("   这可能需要几分钟，请耐心等待...")
        
        try:
            # 创建测试脚本来下载模型
            test_script = self.install_dir / "test_model_download.py"
            test_script.write_text(f'''
import time
from sentence_transformers import SentenceTransformer

print("正在下载模型: {model_name}")
start_time = time.time()

try:
    # 下载模型
    model = SentenceTransformer('{model_name}')
    
    # 测试模型
    test_text = "这是一个测试文本"
    embedding = model.encode(test_text)
    
    download_time = time.time() - start_time
    print(f"✅ 模型下载成功!")
    print(f"   下载时间: {{download_time:.1f}}秒")
    print(f"   嵌入维度: {{embedding.shape[0]}}")
    
    # 保存模型到本地
    model_path = r"{str(self.install_dir / model_name.replace('/', '_'))}"
    model.save(model_path)
    print(f"   模型已保存到: {{model_path}}")
    
except Exception as e:
    print(f"❌ 模型下载失败: {{e}}")
    import traceback
    traceback.print_exc()
''')
            
            # 运行测试脚本
            cmd = [self.python_cmd, str(test_script)]
            print(f"运行命令: {' '.join(cmd)}")
            
            # 显示进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时输出
            for line in process.stdout:
                print(line, end='')
            
            process.wait()
            
            if process.returncode == 0:
                print(f"\n✅ 模型 '{model_name}' 下载并保存成功!")
                return True
            else:
                print(f"\n❌ 模型下载失败")
                return False
                
        except Exception as e:
            print(f"❌ 下载过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_fallback_config(self):
        """创建回退配置"""
        config = {
            "vector_search": {
                "enabled": True,
                "model": "all-MiniLM-L6-v2",
                "fallback_to_keyword": True,
                "cache_embeddings": True,
                "auto_download": True
            },
            "keyword_search": {
                "enabled": True,
                "max_keywords": 10,
                "stop_words": ["的", "了", "在", "是", "我", "有", "和", "就", "不"]
            },
            "hybrid_search": {
                "enabled": True,
                "mode": "auto",  # auto, vector_first, keyword_first, hybrid
                "weight_vector": 0.7,
                "weight_keyword": 0.3
            }
        }
        
        config_path = self.install_dir / "search_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 搜索配置已保存到: {config_path}")
        return config_path
    
    def test_search_functionality(self):
        """测试搜索功能"""
        print("\n🧪 测试搜索功能...")
        
        test_script = self.install_dir / "test_search.py"
        test_script.write_text('''
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hybrid_search import HybridSearchEngine, SearchMode
import tempfile
import json

print("创建测试数据库...")
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

# 初始化搜索引擎
print("初始化搜索引擎...")
search_engine = HybridSearchEngine(db_path)

# 测试文本
test_memories = [
    {
        "id": "test1",
        "content": "用户喜欢使用Python进行数据分析",
        "agent_id": "test_agent",
        "memory_layer": "semantic",
        "memory_type": "preference"
    },
    {
        "id": "test2", 
        "content": "昨天我们决定使用SQLite作为数据库",
        "agent_id": "test_agent",
        "memory_layer": "episodic",
        "memory_type": "decision"
    },
    {
        "id": "test3",
        "content": "机器学习模型需要大量训练数据",
        "agent_id": "test_agent",
        "memory_layer": "semantic",
        "memory_type": "fact"
    }
]

print("建立索引...")
for memory in test_memories:
    search_engine.index_memory(
        memory["id"],
        memory["content"],
        {"agent_id": memory["agent_id"]}
    )

# 测试搜索
print("\\n测试搜索功能:")
queries = [
    ("Python数据分析", "具体查询"),
    ("数据库选择", "语义查询"),
    ("机器学习", "关键词查询")
]

for query, query_type in queries:
    print(f"\\n查询: '{query}' ({query_type})")
    
    # 自动模式搜索
    results = search_engine.search(query, mode='auto', limit=3)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['search_mode']}] {result['content'][:50]}...")
    else:
        print("  无结果")

# 获取统计信息
stats = search_engine.get_search_stats()
print(f"\\n📊 搜索统计:")
print(f"  向量搜索可用: {stats['vector_available']}")
print(f"  已索引记忆: {stats['indexed_memories']}")
print(f"  关键词总数: {stats['total_keywords']}")
print(f"  向量嵌入数: {stats['vector_embeddings']}")

print("\\n✅ 搜索功能测试完成!")
''')
        
        # 运行测试
        cmd = [self.python_cmd, str(test_script)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
    
    def run(self):
        """运行安装程序"""
        print("="*60)
        print("🤖 向量模型安装助手")
        print("="*60)
        
        # 1. 检查依赖
        missing_packages = self.check_dependencies()
        if missing_packages:
            if not self.install_dependencies(missing_packages):
                print("❌ 依赖安装失败，无法继续")
                return False
        
        # 2. 显示模型选项
        self.show_model_options()
        
        # 3. 选择模型
        print("\n请选择要安装的模型:")
        print("1. tiny (all-MiniLM-L6-v2) - 推荐")
        print("2. multilingual (paraphrase-multilingual-MiniLM-L12-v2) - 多语言")
        print("3. chinese (shibing624/text2vec-base-chinese) - 中文优化")
        print("4. 跳过模型安装，仅使用关键词搜索")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            model_key = "tiny"
        elif choice == "2":
            model_key = "multilingual"
        elif choice == "3":
            model_key = "chinese"
        elif choice == "4":
            print("✅ 跳过模型安装，将仅使用关键词搜索")
            model_key = None
        else:
            print("❌ 无效选择，使用默认选项")
            model_key = "tiny"
        
        # 4. 下载模型
        if model_key:
            if not self.download_model(model_key):
                print("⚠️ 模型下载失败，将使用关键词搜索作为回退")
        
        # 5. 创建配置
        config_path = self.create_fallback_config()
        
        # 6. 测试功能
        if self.test_search_functionality():
            print("\n" + "="*60)
            print("🎉 安装完成!")
            print("="*60)
            print(f"配置位置: {config_path}")
            print(f"模型位置: {self.install_dir}")
            print("\n现在可以:")
            print("1. 使用混合搜索功能")
            print("2. 向量模型不可用时自动回退到关键词搜索")
            print("3. 根据查询自动选择最佳搜索模式")
            return True
        else:
            print("\n❌ 功能测试失败")
            return False

if __name__ == "__main__":
    installer = VectorModelInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)