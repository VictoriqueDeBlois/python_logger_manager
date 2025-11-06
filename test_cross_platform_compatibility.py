#!/usr/bin/env python3
"""
快速测试脚本 - 验证 macOS 兼容性
"""

import os
import sys
import tempfile
import unittest
from multiprocessing import Process

from logger_manager import get_logger


def _simple_worker(log_path, worker_id):
    """简单的工作进程"""
    logger = get_logger(log_path, name=f"worker_{worker_id}")
    logger.info(f"Worker {worker_id} - PID: {os.getpid()}")


class TestCrossPlatformCompatibility(unittest.TestCase):

    def setUp(self):
        """运行所有测试"""
        # 设置环境变量
        os.environ.setdefault('LOG_LEVEL', 'INFO')
        os.environ.setdefault('LOG_CONSOLE', 'false')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            self.log_path = f.name

    def tearDown(self):
        # 清理
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_basic_multiprocessing(self):
        """测试基本的多进程功能"""
        # 主进程
        main_logger = get_logger(self.log_path, name="main")
        main_logger.info(f"主进程 - PID: {os.getpid()}")

        # 启动子进程
        processes = []
        for i in range(3):
            p = Process(target=_simple_worker, args=(self.log_path, i))
            p.start()
            processes.append(p)

        # 等待完成
        for p in processes:
            p.join()

        main_logger.info("所有子进程完成")

        # 验证日志
        with open(self.log_path, 'r') as f:
            content = f.read()
            assert "主进程" in content, "缺少主进程日志"
            assert "Worker 0" in content, "缺少Worker 0日志"
            assert "Worker 1" in content, "缺少Worker 1日志"
            assert "Worker 2" in content, "缺少Worker 2日志"

    def test_same_path_multiple_processes(self):
        """测试同一路径多进程写入"""
        # 创建多个进程同时写入
        processes = []
        for i in range(5):
            p = Process(target=_simple_worker, args=(self.log_path, i))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        # 验证所有进程都写入了日志
        with open(self.log_path, 'r') as f:
            content = f.read()
            for i in range(5):
                assert f"Worker {i}" in content, f"缺少Worker {i}日志"


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCrossPlatformCompatibility)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("跨平台兼容性快速测试")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {sys.platform}")
    print("=" * 60)
    success = run_tests()
    exit(0 if success else 1)
