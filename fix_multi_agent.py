"""
修复多代理共享问题
"""

import sys
import os
import tempfile
import json
import sqlite3

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def fix_coordinator():
    """修复coordinator中的share_memory方法"""
    print("修复coordinator中的share_memory方法...")
    
    # 读取core.py文件
    core_path = os.path.join(os.path.dirname(__file__), "src", "core.py")
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找share_memory方法
    if "def share_memory(self, memory_id, target_agent_id, permission, agent_id):" in content:
        # 找到方法定义
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "def share_memory(self, memory_id, target_agent_id, permission, agent_id):" in line:
                # 替换方法实现
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                new_implementation = f"""{indent_str}    def share_memory(self, memory_id, target_agent_id, permission, agent_id):
{indent_str}        # 实际实现：在数据库中设置共享权限
{indent_str}        try:
{indent_str}            cursor = self.storage.conn.cursor()
{indent_str}            
{indent_str}            # 检查记忆是否存在且属于发起代理
{indent_str}            cursor.execute(
{indent_str}                "SELECT owner_agent FROM memories WHERE id = ?",
{indent_str}                (memory_id,)
{indent_str}            )
{indent_str}            memory = cursor.fetchone()
{indent_str}            
{indent_str}            if not memory:
{indent_str}                return False
{indent_str}            
{indent_str}            owner_agent = memory[0]
{indent_str}            if owner_agent != agent_id:
{indent_str}                # 只有记忆所有者可以共享
{indent_str}                return False
{indent_str}            
{indent_str}            # 设置共享权限
{indent_str}            cursor.execute(
{indent_str}                \"\"\"
{indent_str}                INSERT OR REPLACE INTO sharing_permissions 
{indent_str}                (memory_id, agent_id, permission, granted_at)
{indent_str}                VALUES (?, ?, ?, datetime('now'))
{indent_str}                \"\"\",
{indent_str}                (memory_id, target_agent_id, permission)
{indent_str}            )
{indent_str}            
{indent_str}            self.storage.conn.commit()
{indent_str}            return True
{indent_str}            
{indent_str}        except Exception as e:
{indent_str}            print(f"[ERROR] 设置共享权限失败: {{e}}")
{indent_str}            return False"""
                
                # 找到方法结束的位置（下一个def或类结束）
                for j in range(i+1, len(lines)):
                    if lines[j].strip().startswith('def ') or lines[j].strip().startswith('class '):
                        # 替换从i到j-1的行
                        lines[i:j] = new_implementation.split('\n')
                        break
                
                # 写回文件
                with open(core_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("[OK] share_memory方法已修复")
                return True
    
    print("[ERROR] 未找到share_memory方法")
    return False

def add_get_permissions_method():
    """添加get_permissions方法"""
    print("添加get_permissions方法...")
    
    core_path = os.path.join(os.path.dirname(__file__), "src", "core.py")
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在share方法后添加get_permissions方法
    if "def share(self, memory_id: str, target_agent_id: str," in content:
        # 找到share方法
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "def share(self, memory_id: str, target_agent_id: str," in line:
                # 找到share方法结束的位置
                for j in range(i, len(lines)):
                    if j > i and lines[j].strip() == '' and lines[j+1].strip().startswith('def '):
                        # 在空行后插入新方法
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        
                        new_method = f"""{indent_str}    def get_permissions(self, memory_id: str) -> Dict:
{indent_str}        \"\"\"
{indent_str}        获取记忆的权限信息
{indent_str}        
{indent_str}        Args:
{indent_str}            memory_id: 记忆ID
{indent_str}        
{indent_str}        Returns:
{indent_str}            权限信息字典
{indent_str}        \"\"\"
{indent_str}        try:
{indent_str}            cursor = self.storage.conn.cursor()
{indent_str}            
{indent_str}            # 获取记忆所有者
{indent_str}            cursor.execute(
{indent_str}                "SELECT owner_agent FROM memories WHERE id = ?",
{indent_str}                (memory_id,)
{indent_str}            )
{indent_str}            memory = cursor.fetchone()
{indent_str}            
{indent_str}            if not memory:
{indent_str}                return {{"error": "Memory not found"}}
{indent_str}            
{indent_str}            owner_agent = memory[0]
{indent_str}            
{indent_str}            # 获取共享权限
{indent_str}            cursor.execute(
{indent_str}                "SELECT agent_id, permission FROM sharing_permissions WHERE memory_id = ?",
{indent_str}                (memory_id,)
{indent_str}            )
{indent_str}            shared_permissions = cursor.fetchall()
{indent_str}            
{indent_str}            permissions = {{
{indent_str}                "memory_id": memory_id,
{indent_str}                "owner": owner_agent,
{indent_str}                "shared_with": {{agent: perm for agent, perm in shared_permissions}}
{indent_str}            }}
{indent_str}            
{indent_str}            return permissions
{indent_str}            
{indent_str}        except Exception as e:
{indent_str}            return {{"error": str(e)}}"""
                        
                        # 插入新方法
                        lines.insert(j+1, '')
                        lines.insert(j+2, new_method)
                        
                        # 写回文件
                        with open(core_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(lines))
                        
                        print("[OK] get_permissions方法已添加")
                        return True
    
    print("[ERROR] 未找到share方法")
    return False

def add_get_memory_method():
    """添加get_memory方法"""
    print("添加get_memory方法...")
    
    core_path = os.path.join(os.path.dirname(__file__), "src", "core.py")
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在get_permissions方法后添加get_memory方法
    if "def get_permissions(self, memory_id: str) -> Dict:" in content:
        # 找到get_permissions方法
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "def get_permissions(self, memory_id: str) -> Dict:" in line:
                # 找到方法结束的位置
                for j in range(i, len(lines)):
                    if j > i and lines[j].strip() == '' and lines[j+1].strip().startswith('def '):
                        # 在空行后插入新方法
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        
                        new_method = f"""{indent_str}    def get_memory(self, memory_id: str, agent_id: str = "system") -> Optional[Any]:
{indent_str}        \"\"\"
{indent_str}        直接获取记忆
{indent_str}        
{indent_str}        Args:
{indent_str}            memory_id: 记忆ID
{indent_str}            agent_id: 代理ID
{indent_str}        
{indent_str}        Returns:
{indent_str}            记忆记录或None
{indent_str}        \"\"\"
{indent_str}        from .core import MemoryRecord
{indent_str}        
{indent_str}        # 使用storage的retrieve_memory方法
{indent_str}        memory = self.storage.retrieve_memory(memory_id, agent_id)
{indent_str}        
{indent_str}        if memory:
{indent_str}            logger.info(f"Retrieved memory {{memory_id}} for agent {{agent_id}}")
{indent_str}        
{indent_str}        return memory"""
                        
                        # 插入新方法
                        lines.insert(j+1, '')
                        lines.insert(j+2, new_method)
                        
                        # 写回文件
                        with open(core_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(lines))
                        
                        print("[OK] get_memory方法已添加")
                        return True
    
    print("[ERROR] 未找到get_permissions方法，将直接添加")
    
    # 如果没找到，在文件末尾添加
    with open(core_path, 'a', encoding='utf-8') as f:
        f.write('\n\n    def get_memory(self, memory_id: str, agent_id: str = "system") -> Optional[Any]:\n')
        f.write('        """\n')
        f.write('        直接获取记忆\n')
        f.write('        \n')
        f.write('        Args:\n')
        f.write('            memory_id: 记忆ID\n')
        f.write('            agent_id: 代理ID\n')
        f.write('        \n')
        f.write('        Returns:\n')
        f.write('            记忆记录或None\n')
        f.write('        """\n')
        f.write('        from .core import MemoryRecord\n')
        f.write('        \n')
        f.write('        # 使用storage的retrieve_memory方法\n')
        f.write('        memory = self.storage.retrieve_memory(memory_id, agent_id)\n')
        f.write('        \n')
        f.write('        if memory:\n')
        f.write('            logger.info(f"Retrieved memory {memory_id} for agent {agent_id}")\n')
        f.write('        \n')
        f.write('        return memory\n')
    
    print("[OK] get_memory方法已添加到文件末尾")
    return True

def fix_encoding_issue():
    """修复编码问题"""
    print("修复编码问题...")
    
    # 1. 修复storage_enhanced.py中的压缩/解压缩编码
    storage_path = os.path.join(os.path.dirname(__file__), "src", "storage_enhanced.py")
    with open(storage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找_decompress_content方法
    if "def _decompress_content(self, compressed_content: bytes, algorithm: str) -> str:" in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "def _decompress_content(self, compressed_content: bytes, algorithm: str) -> str:" in line:
                # 找到方法体
                for j in range(i, len(lines)):
                    if "return decompressed.decode('utf-8')" in lines[j]:
                        # 修复解码，添加错误处理
                        lines[j] = '            try:\n' + \
                                  '                return decompressed.decode(\'utf-8\')\n' + \
                                  '            except UnicodeDecodeError:\n' + \
                                  '                # 尝试其他编码\n' + \
                                  '                try:\n' + \
                                  '                    return decompressed.decode(\'gbk\')\n' + \
                                  '                except:\n' + \
                                  '                    return decompressed.decode(\'utf-8\', errors=\'replace\')'
                        break
        
        # 写回文件
        with open(storage_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("[OK] 压缩/解压缩编码问题已修复")
    
    # 2. 修复日志输出编码
    core_path = os.path.join(os.path.dirname(__file__), "src", "core.py")
    with open(core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在文件开头添加编码声明
    if not content.startswith('# -*- coding: utf-8 -*-'):
        content = '# -*- coding: utf-8 -*-\n' + content
        
        with open(core_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] 添加了文件编码声明")
    
    return True

def test_fixes():
    """测试修复"""
    print("\n测试修复...")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test_fix.db")
        
        # 初始化系统
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 注册代理
        memory.register_agent("agent1", "测试代理1")
        memory.register_agent("agent2", "测试代理2")
        
        # 代理1存储记忆
        memory_id = memory.remember(
            "测试修复后的共享功能",
            agent_id="agent1",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )
        
        print(f"存储记忆: {memory_id[:8]}")
        
        # 测试get_permissions
        permissions = memory.get_permissions(memory_id)
        print(f"权限信息: {json.dumps(permissions, indent=2, ensure_ascii=False)}")
        
        # 共享记忆
        share_success = memory.share(memory_id, "agent2", "read", "agent1")
        print(f"共享结果: {'成功' if share_success else '失败'}")
        
        # 再次检查权限
        permissions = memory.get_permissions(memory_id)
        print(f"共享后权限: {json.dumps(permissions, indent=2, ensure_ascii=False)}")
        
        # 代理2搜索记忆
        results = memory.recall("测试", agent_id="agent2")
        print(f"代理2搜索结果: {len(results)} 条记录")
        
        # 代理2直接获取记忆
        direct_memory = memory.get_memory(memory_id, "agent2")
        print(f"代理2直接获取: {'成功' if direct_memory else '失败'}")
        
        # 清理
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if share_success and len(results) > 0 and direct_memory:
            print("\n[OK] 所有修复测试通过！")
            return True
        else:
            print("\n[ERROR] 部分测试失败")
            return False
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始修复元记忆技能问题...")
    print("="*60)
    
    # 修复问题
    fixes = [
        ("修复coordinator中的share_memory方法", fix_coordinator),
        ("添加get_permissions方法", add_get_permissions_method),
        ("添加get_memory方法", add_get_memory_method),
        ("修复编码问题", fix_encoding_issue),
    ]
    
    all_success = True
    for name, fix_func in fixes:
        print(f"\n{name}:")
        try:
            success = fix_func()
            if not success:
                all_success = False
        except Exception as e:
            print(f"[ERROR] 修复失败: {e}")
            all_success = False
    
    if all_success:
        print("\n" + "="*60)
        print("所有修复完成，开始测试...")
        print("="*60)
        
        test_result = test_fixes()
        
        if test_result:
            print("\n" + "="*60)
            print("🎉 所有问题修复成功！")
            print("="*60)
            print("\n修复的问题:")
            print("1. ✅ 多代理共享记忆功能")
            print("2. ✅ 添加了get_permissions和get_memory方法")
            print("3. ✅ 修复了压缩/解压缩编码问题")
            print("4. ✅ 修复了文件编码声明")
        else:
            print("\n" + "="*60)
            print("⚠️ 修复完成但测试失败")
            print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 部分修复失败")
        print("="*60)
    
    return all_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n修复被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n修复失败: {e}")
        sys.exit(1)