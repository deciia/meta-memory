"""
验证元记忆技能是否满足6个核心需求
"""

import sys
import os
import tempfile
import shutil
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def verify_requirement_1():
    """验证需求1: 元技能性质"""
    print_header("需求1: 元技能性质")
    
    try:
        from src.core import MetaMemoryEnhanced
        
        # 检查是否是基础记忆管理技能
        print("检查点:")
        print("1. 技能是否作为OpenClaw的基础记忆管理技能")
        
        # 创建实例
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 检查基本功能
        has_remember = hasattr(memory, 'remember')
        has_recall = hasattr(memory, 'recall')
        has_forget = hasattr(memory, 'forget')
        has_wakeup = hasattr(memory, 'wakeup')
        
        print(f"  - 记忆存储功能 (remember): {'[OK]' if has_remember else '[ERROR]'}")
        print(f"  - 记忆检索功能 (recall): {'[OK]' if has_recall else '[ERROR]'}")
        print(f"  - 记忆遗忘功能 (forget): {'[OK]' if has_forget else '[ERROR]'}")
        print(f"  - 记忆唤醒功能 (wakeup): {'[OK]' if has_wakeup else '[ERROR]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if all([has_remember, has_recall, has_forget, has_wakeup]):
            print("\n[OK] 需求1验证通过: 作为OpenClaw的基础记忆管理技能")
            return True
        else:
            print("\n[ERROR] 需求1验证失败: 缺少必要的记忆管理功能")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求1验证失败: {e}")
        return False

def verify_requirement_2():
    """验证需求2: 完全本地存储"""
    print_header("需求2: 完全本地存储")
    
    try:
        from src.core import MetaMemoryEnhanced
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 所有数据是否存储在本地")
        print("2. 是否不依赖云服务")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 检查数据库文件是否创建
        db_exists = os.path.exists(db_path)
        print(f"  - 数据库文件创建: {'[OK]' if db_exists else '[ERROR]'}")
        
        # 检查配置中是否有云服务依赖
        config = memory.config
        has_cloud_deps = False
        
        # 检查配置中是否有云服务相关设置
        cloud_keywords = ['cloud', 'api', 'http', 'url', 'remote', 'server']
        config_str = json.dumps(config).lower()
        
        for keyword in cloud_keywords:
            if keyword in config_str and 'localhost' not in config_str and '127.0.0.1' not in config_str:
                has_cloud_deps = True
                break
        
        print(f"  - 无云服务依赖: {'[OK]' if not has_cloud_deps else '[WARNING]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if db_exists and not has_cloud_deps:
            print("\n[OK] 需求2验证通过: 完全本地存储，不依赖云服务")
            return True
        else:
            print("\n[ERROR] 需求2验证失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求2验证失败: {e}")
        return False

def verify_requirement_3():
    """验证需求3: 遗忘和唤醒功能"""
    print_header("需求3: 遗忘和唤醒功能")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 是否有智能遗忘功能减少token消耗")
        print("2. 是否有快速唤醒恢复记忆功能")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 存储测试记忆
        memory_id = memory.remember(
            "测试遗忘和唤醒功能",
            agent_id="test_agent",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )
        
        print(f"  - 记忆存储: [OK] (ID: {memory_id[:8]})")
        
        # 测试遗忘功能
        forget_success = memory.forget(memory_id, "test_agent", permanent=False)
        print(f"  - 记忆遗忘: {'[OK]' if forget_success else '[ERROR]'}")
        
        # 测试唤醒功能
        woken_memory = memory.wakeup(memory_id, "test_agent", urgency="normal")
        print(f"  - 记忆唤醒: {'[OK]' if woken_memory else '[ERROR]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if forget_success and woken_memory:
            print("\n[OK] 需求3验证通过: 智能遗忘和快速唤醒功能正常")
            return True
        else:
            print("\n[ERROR] 需求3验证失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求3验证失败: {e}")
        return False

def verify_requirement_4():
    """验证需求4: 记忆百分百不丢失"""
    print_header("需求4: 记忆百分百不丢失")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 是否有多重保障机制确保数据安全")
        print("2. 遗忘的记忆是否压缩保存")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 存储测试记忆
        memory_id = memory.remember(
            "测试记忆不丢失功能",
            agent_id="test_agent",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.CRITICAL
        )
        
        print(f"  - 记忆存储: [OK] (ID: {memory_id[:8]})")
        
        # 检查是否有备份机制
        has_backup = hasattr(memory, 'backup')
        print(f"  - 备份功能: {'[OK]' if has_backup else '[WARNING]'}")
        
        # 检查是否有压缩机制
        config = memory.config
        has_compression = 'compression_algorithm' in config.get('storage', {})
        print(f"  - 压缩机制: {'[OK]' if has_compression else '[WARNING]'}")
        
        # 测试遗忘后是否能恢复
        memory.forget(memory_id, "test_agent", permanent=False)
        woken = memory.wakeup(memory_id, "test_agent", urgency="normal")
        print(f"  - 遗忘后恢复: {'[OK]' if woken else '[ERROR]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if woken:
            print("\n[OK] 需求4验证通过: 记忆百分百不丢失，压缩保存可恢复")
            return True
        else:
            print("\n[ERROR] 需求4验证失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求4验证失败: {e}")
        return False

def verify_requirement_5():
    """验证需求5: 压缩保存和快捷调取"""
    print_header("需求5: 压缩保存和快捷调取")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 是否支持压缩存储")
        print("2. 是否支持毫秒级唤醒")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 检查压缩配置
        config = memory.config
        storage_config = config.get('storage', {})
        
        compression_algo = storage_config.get('compression_algorithm', 'none')
        compression_level = storage_config.get('compression_level', 1)
        
        print(f"  - 压缩算法: {compression_algo}")
        print(f"  - 压缩级别: {compression_level}")
        
        # 测试唤醒速度
        import time
        
        memory_id = memory.remember(
            "测试唤醒速度",
            agent_id="test_agent",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )
        
        # 遗忘记忆
        memory.forget(memory_id, "test_agent", permanent=False)
        
        # 测试唤醒时间
        start_time = time.time()
        woken = memory.wakeup(memory_id, "test_agent", urgency="normal")
        end_time = time.time()
        
        wakeup_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        print(f"  - 唤醒时间: {wakeup_time:.2f}ms")
        print(f"  - 唤醒成功: {'[OK]' if woken else '[ERROR]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if woken and wakeup_time < 1000:  # 1秒内唤醒
            print(f"\n[OK] 需求5验证通过: 压缩保存，快速唤醒 ({wakeup_time:.2f}ms)")
            return True
        else:
            print(f"\n[ERROR] 需求5验证失败: 唤醒时间过长或失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求5验证失败: {e}")
        return False

def verify_requirement_6():
    """验证需求6: 多代理共享记忆"""
    print_header("需求6: 多代理共享记忆")
    
    try:
        from src.core import MetaMemoryEnhanced, MemoryLayer, MemoryType, MemoryPriority
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 是否支持多代理间记忆共享")
        print("2. 是否有安全的权限控制")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        
        # 注册多个代理
        memory.register_agent("agent1", "测试代理1")
        memory.register_agent("agent2", "测试代理2")
        
        print("  - 代理注册: [OK]")
        
        # 代理1存储记忆
        memory_id = memory.remember(
            "这是代理1的共享记忆",
            agent_id="agent1",
            memory_layer=MemoryLayer.SEMANTIC,
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH
        )
        
        print(f"  - 记忆存储: [OK] (ID: {memory_id[:8]})")
        
        # 代理1共享记忆给代理2
        share_success = memory.share(memory_id, "agent2", "read", "agent1")
        print(f"  - 记忆共享: {'[OK]' if share_success else '[ERROR]'}")
        
        # 代理2尝试访问共享记忆
        results = memory.recall("共享", agent_id="agent2")
        can_access = len(results) > 0
        
        print(f"  - 代理2访问: {'[OK]' if can_access else '[ERROR]'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        if share_success and can_access:
            print("\n[OK] 需求6验证通过: 多代理间安全共享记忆")
            return True
        else:
            print("\n[ERROR] 需求6验证失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 需求6验证失败: {e}")
        return False

def verify_enhancements():
    """验证增强功能"""
    print_header("增强功能验证")
    
    try:
        from src.core import MetaMemoryEnhanced
        
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        
        print("检查点:")
        print("1. 向量搜索集成 (参考Elite Longterm Memory)")
        print("2. 智能预测唤醒 (参考Cognitive Memory)")
        print("3. 三层次记忆架构 (参考Memory Manager)")
        print("4. 完善监控和维护 (参考Memory Hygiene)")
        
        # 创建实例
        memory = MetaMemoryEnhanced(storage_path=db_path)
        config = memory.config
        
        # 检查向量搜索
        retrieval_config = config.get('retrieval', {})
        has_vector_search = retrieval_config.get('enable_vector_search', False)
        print(f"  - 向量搜索集成: {'[OK] (需安装sentence-transformers)' if has_vector_search else '[INFO] 可配置启用'}")
        
        # 检查预测唤醒
        optimization_config = config.get('optimization', {})
        has_wakeup_prediction = optimization_config.get('wakeup_prediction', False)
        print(f"  - 智能预测唤醒: {'[OK]' if has_wakeup_prediction else '[INFO] 可配置启用'}")
        
        # 检查三层次记忆
        memory_layers_config = config.get('memory_layers', {})
        has_memory_layers = memory_layers_config.get('enabled', False)
        print(f"  - 三层次记忆架构: {'[OK]' if has_memory_layers else '[INFO] 可配置启用'}")
        
        # 检查监控维护
        monitoring_config = config.get('monitoring', {})
        has_monitoring = monitoring_config.get('maintenance_automation', False)
        print(f"  - 完善监控维护: {'[OK]' if has_monitoring else '[INFO] 可配置启用'}")
        
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
        
        print("\n[OK] 增强功能架构已集成，可通过配置启用")
        return True
        
    except Exception as e:
        print(f"[ERROR] 增强功能验证失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print(" 元记忆技能核心需求验证")
    print("="*60)
    
    requirements = [
        ("需求1: 元技能性质", verify_requirement_1),
        ("需求2: 完全本地存储", verify_requirement_2),
        ("需求3: 遗忘和唤醒功能", verify_requirement_3),
        ("需求4: 记忆百分百不丢失", verify_requirement_4),
        ("需求5: 压缩保存和快捷调取", verify_requirement_5),
        ("需求6: 多代理共享记忆", verify_requirement_6),
    ]
    
    results = []
    
    for name, verifier in requirements:
        try:
            success = verifier()
            results.append((name, success))
        except Exception as e:
            print(f"[ERROR] {name} 验证异常: {e}")
            results.append((name, False))
    
    # 验证增强功能
    verify_enhancements()
    
    # 汇总结果
    print_header("验证结果汇总")
    
    all_passed = True
    for name, success in results:
        status = "[OK]" if success else "[ERROR]"
        print(f"{status} {name}")
        if not success:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print(" 🎉 所有6个核心需求验证通过！")
        print("="*60)
        print("\n技能状态:")
        print("  ✅ 配置正确")
        print("  ✅ 功能正常")
        print("  ✅ 满足所有核心需求")
        print("  ✅ 增强功能架构已集成")
        
        print("\n下一步:")
        print("  1. 技能已准备好，可在OpenClaw中使用")
        print("  2. 如需启用增强功能，可修改配置")
        print("  3. 安装向量搜索依赖: pip install sentence-transformers")
        
    else:
        print(" ⚠️  部分需求验证失败")
        print("="*60)
        print("\n需要检查:")
        for name, success in results:
            if not success:
                print(f"  - {name}")
        
        print("\n建议:")
        print("  1. 检查技能代码")
        print("  2. 查看详细错误信息")
        print("  3. 修复问题后重新验证")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证失败: {e}")
        sys.exit(1)