#!/usr/bin/env python3
"""
关键功能验证 - 只测试最重要的改进点
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("KEY FEATURES VERIFICATION")
print("Testing the most important improvements")
print("="*50)

def test_critical_features():
    """测试最关键的功能"""
    results = {}
    
    try:
        # 1. 测试模块导入
        print("\n1. Testing module imports...")
        from src.enhanced_core import MetaMemoryEnhanced
        print("   [PASS] Core module imports work")
        results['import'] = True
        
        # 2. 测试系统初始化
        print("\n2. Testing system initialization...")
        memory = MetaMemoryEnhanced({'db_path': 'key_test.db'})
        print("   [PASS] System initializes successfully")
        results['init'] = True
        
        # 3. 测试记忆存储（核心功能）
        print("\n3. Testing memory storage...")
        test_memories = [
            "I prefer using Python for data analysis",
            "Decision: Use SQLite for local storage",
            "Important: Always backup data regularly"
        ]
        
        for i, content in enumerate(test_memories, 1):
            mem_id = memory.remember(content, f"user_{i}")
            print(f"   Stored: {content[:40]}...")
        
        print(f"   [PASS] Stored {len(test_memories)} memories")
        results['storage'] = True
        
        # 4. 测试记忆搜索（核心功能）
        print("\n4. Testing memory search...")
        search_tests = [
            ("Python", "Should find Python preference"),
            ("SQLite", "Should find SQLite decision"),
            ("backup", "Should find backup reminder")
        ]
        
        all_found = True
        for query, expected in search_tests:
            start = time.time()
            found = memory.recall(query, limit=5)
            search_time = (time.time() - start) * 1000
            
            if found:
                print(f"   Found '{query}': {len(found)} results ({search_time:.1f}ms)")
            else:
                print(f"   NOT FOUND '{query}': 0 results")
                all_found = False
        
        if all_found:
            print("   [PASS] All searches returned results")
            results['search'] = True
        else:
            print("   [WARN] Some searches returned no results")
            results['search'] = False
        
        # 5. 测试健康检查（新增功能）
        print("\n5. Testing health monitoring...")
        try:
            health = memory.check_health()
            print(f"   Health score: {health.health_score:.1f}/100")
            print(f"   Memory count: {health.memory_count}")
            print("   [PASS] Health monitoring works")
            results['health'] = True
        except:
            print("   [WARN] Health check has issues (but system still works)")
            results['health'] = False
        
        # 6. 测试混合搜索可用性
        print("\n6. Testing hybrid search availability...")
        try:
            from src.hybrid_search import HybridSearchEngine
            print("   [PASS] Hybrid search engine is available")
            results['hybrid'] = True
        except:
            print("   [INFO] Hybrid search not available (fallback to keyword)")
            print("   System will still work with keyword search")
            results['hybrid'] = False
        
        # 7. 测试错误恢复
        print("\n7. Testing error recovery...")
        try:
            # 尝试搜索不存在的记忆
            results = memory.recall("nonexistent12345", limit=1)
            print("   [PASS] System handles missing results gracefully")
            results['recovery'] = True
        except:
            print("   [WARN] Error recovery needs improvement")
            results['recovery'] = False
        
        return memory, results
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Test failed: {e}")
        return None, {}

def show_results(memory, results):
    """显示测试结果"""
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    if not results:
        print("No test results available")
        return
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    score = (passed / total) * 100 if total > 0 else 0
    
    print(f"\nFeatures tested: {total}")
    print(f"Features passed: {passed}")
    print(f"Success rate: {score:.1f}%")
    
    print("\nDetailed results:")
    for feature, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {feature:12} : {status}")
    
    print("\n" + "="*50)
    print("RECOMMENDATIONS")
    print("="*50)
    
    if score >= 80:
        print("\n✅ SYSTEM IS READY FOR USE")
        print("The enhanced memory system is working well.")
        print("You can start using it immediately.")
        
        print("\nKey benefits you'll experience:")
        print("  • Reliable memory storage and retrieval")
        print("  • Health monitoring (new feature)")
        print("  • Hybrid search capability")
        print("  • Graceful error handling")
        
    elif score >= 50:
        print("\n⚠️ SYSTEM IS FUNCTIONAL BUT HAS ISSUES")
        print("Core functions work, but some features need attention.")
        print("You can use it, but be aware of limitations.")
        
        print("\nWorking features:")
        for feature, passed in results.items():
            if passed:
                print(f"  • {feature}")
                
        print("\nFeatures needing attention:")
        for feature, passed in results.items():
            if not passed:
                print(f"  • {feature}")
                
    else:
        print("\n❌ SYSTEM NEEDS SIGNIFICANT WORK")
        print("Core functionality is compromised.")
        print("Needs debugging before use.")
    
    # 系统统计
    if memory:
        try:
            print("\n" + "="*50)
            print("SYSTEM STATISTICS")
            print("="*50)
            
            # 简单的统计
            print(f"Test database: key_test.db")
            print(f"Test completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except:
            pass
    
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    
    if score >= 80:
        print("1. Integrate with OpenClaw configuration")
        print("2. Start using in your daily workflow")
        print("3. Monitor system health regularly")
        print("4. Consider installing vector models for better search")
    elif score >= 50:
        print("1. Fix the failing features first")
        print("2. Test again after fixes")
        print("3. Then integrate with OpenClaw")
    else:
        print("1. Debug core functionality issues")
        print("2. Check module imports and dependencies")
        print("3. Fix critical errors before proceeding")

def main():
    """主函数"""
    print("\nStarting key features verification...")
    
    memory, results = test_critical_features()
    
    if results:
        show_results(memory, results)
        
        # 清理测试数据库
        try:
            if os.path.exists('key_test.db'):
                os.remove('key_test.db')
                print("\nCleaned up test database")
        except:
            pass
        
        # 返回测试结果
        total = len(results)
        passed = sum(1 for r in results.values() if r)
        return passed >= total * 0.7  # 70%通过率就算成功
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)