#!/usr/bin/env python3
"""
快速测试脚本 - 验证 macOS 兼容性
"""

import os
import sys
import tempfile
from multiprocessing import Process
from logger_manager import get_logger


def simple_worker(log_path, worker_id):
    """简单的工作进程"""
    logger = get_logger(log_path, name=f"worker_{worker_id}")
    logger.info(f"Worker {worker_id} - PID: {os.getpid()}")


def test_basic_multiprocessing():
    """测试基本的多进程功能"""
    print("测试1: 基本多进程日志...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_path = f.name
    
    try:
        # 主进程
        main_logger = get_logger(log_path, name="main")
        main_logger.info(f"主进程 - PID: {os.getpid()}")
        
        # 启动子进程
        processes = []
        for i in range(3):
            p = Process(target=simple_worker, args=(log_path, i))
            p.start()
            processes.append(p)
        
        # 等待完成
        for p in processes:
            p.join()
        
        main_logger.info("所有子进程完成")
        
        # 验证日志
        with open(log_path, 'r') as f:
            content = f.read()
            assert "主进程" in content, "缺少主进程日志"
            assert "Worker 0" in content, "缺少Worker 0日志"
            assert "Worker 1" in content, "缺少Worker 1日志"
            assert "Worker 2" in content, "缺少Worker 2日志"
        
        print("✅ 测试1通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理
        if os.path.exists(log_path):
            os.remove(log_path)


def test_same_path_multiple_processes():
    """测试同一路径多进程写入"""
    print("\n测试2: 同一路径多进程写入...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_path = f.name
    
    try:
        # 创建多个进程同时写入
        processes = []
        for i in range(5):
            p = Process(target=simple_worker, args=(log_path, i))
            p.start()
            processes.append(p)
        
        for p in processes:
            p.join()
        
        # 验证所有进程都写入了日志
        with open(log_path, 'r') as f:
            content = f.read()
            for i in range(5):
                assert f"Worker {i}" in content, f"缺少Worker {i}日志"
        
        print("✅ 测试2通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("macOS 兼容性快速测试")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {sys.platform}")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(test_basic_multiprocessing())
    results.append(test_same_path_multiple_processes())
    
    # 汇总
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！macOS兼容性正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('LOG_CONSOLE', 'false')
    
    sys.exit(main())
