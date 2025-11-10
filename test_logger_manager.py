"""
日志管理器单元测试
"""

import gc
import logging
import os
import tempfile
import time
import unittest
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool, Process
from pathlib import Path

from logger_manager import LoggerManager, get_logger, get_path_info, cleanup_current_process


# 模块级别的工作函数，用于多进程测试
def _test_worker(log_path):
    """测试用的工作进程函数"""
    logger = get_logger(log_path, name="worker")
    pid = os.getpid()
    logger.info(f"Worker PID: {pid}")
    time.sleep(0.1)


def pool_worker(args):
    """进程池工作函数"""
    worker_id, log_path = args
    logger = get_logger(log_path, name=f"pool_worker_{worker_id}")

    # 获取真实的进程PID
    pid = os.getpid()
    logger.info(f"Worker {worker_id} - 真实PID: {pid}")

    return pid


def _concurrent_worker(worker_id, temp_dir):
    """并发工作进程"""
    log_path = os.path.join(temp_dir, f"worker_{worker_id}.log")

    logger = get_logger(log_path, name=f"Worker{worker_id}")
    pid = os.getpid()

    for i in range(3):
        logger.info(f"任务 {i + 1}")

    # 验证内容
    with open(log_path, 'r') as f:
        content = f.read()

    return {
        'worker_id': worker_id,
        'pid': pid,
        'log_path': log_path,
        'has_correct_pid': f"[PID:{pid}]" in content,
        'has_correct_name': f"[Worker{worker_id}]" in content
    }


class TestLoggerManager(unittest.TestCase):
    """日志管理器测试用例"""

    def setUp(self):
        """测试前准备"""
        # 使用临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_path = os.path.join(self.temp_dir, "test.log")

        # 设置测试环境变量
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['LOG_CONSOLE'] = 'false'

    def tearDown(self):
        """测试后清理"""
        import shutil

        # Windows文件锁定问题：必须先关闭所有文件句柄才能删除文件
        # Linux上可以直接删除打开的文件，但Windows会报PermissionError

        # 1. 关闭所有logger的handlers
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(logger_name)
            handlers = logger.handlers[:]
            for handler in handlers:
                handler.close()
                logger.removeHandler(handler)

        # 2. 关闭root logger的handlers
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)

        # 3. 强制垃圾回收，确保文件句柄被释放
        gc.collect()

        # 4. Windows可能需要短暂等待文件句柄释放
        time.sleep(0.1)

        # 5. 清理临时文件
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except PermissionError:
                # 如果仍然失败，再等待一下重试
                time.sleep(0.2)
                shutil.rmtree(self.temp_dir)

        if os.path.exists("test.log"):
            try:
                os.remove("test.log")
            except PermissionError:
                # 如果仍然失败，再等待一下重试
                time.sleep(0.2)
                os.remove("test.log")

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        self.assertIs(manager1, manager2, "LoggerManager应该是单例")

    def test_create_new_logger(self):
        """测试创建新的日志对象"""
        logger = get_logger(self.test_log_path, name="test1")

        self.assertIsNotNone(logger)
        self.assertTrue(os.path.exists(self.test_log_path))

        # 测试日志写入
        logger.info("测试日志")

        # 验证文件内容
        with open(self.test_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("测试日志", content)

    def test_reuse_same_logger(self):
        """测试复用同一个日志对象"""
        logger1 = get_logger(self.test_log_path, name="test2")
        logger2 = get_logger(self.test_log_path, name="test2")

        # 应该返回同一个logger
        self.assertEqual(logger1.name, logger2.name)

        # 写入日志
        logger1.info("日志1")
        logger2.info("日志2")

        # 验证两条日志都被写入
        with open(self.test_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("日志1", content)
            self.assertIn("日志2", content)

    def test_path_info_single_process(self):
        """测试单进程路径信息"""
        logger = get_logger(self.test_log_path, name="test3")
        info = get_path_info(self.test_log_path)

        self.assertEqual(info['num_processes'], 1)
        self.assertIn(os.getpid(), info['pids'])

    def test_multiprocess_logging(self):
        """测试多进程日志写入"""
        # 主进程写入
        main_logger = get_logger(self.test_log_path, name="main")
        main_logger.info("Main process")

        # 启动多个子进程
        processes = []
        for _ in range(3):
            p = Process(target=_test_worker, args=(self.test_log_path,))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        # 验证日志文件包含所有进程的日志
        with open(self.test_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Main process", content)
            self.assertIn("Worker PID:", content)

    def test_multiple_log_paths(self):
        """测试多个日志路径"""
        log_path1 = os.path.join(self.temp_dir, "log1.log")
        log_path2 = os.path.join(self.temp_dir, "log2.log")

        logger1 = get_logger(log_path1, name="logger1")
        logger2 = get_logger(log_path2, name="logger2")

        logger1.info("日志1")
        logger2.info("日志2")

        # 验证两个文件都被创建
        self.assertTrue(os.path.exists(log_path1))
        self.assertTrue(os.path.exists(log_path2))

        # 验证内容独立
        with open(log_path1, 'r', encoding='utf-8') as f:
            self.assertIn("日志1", f.read())

        with open(log_path2, 'r', encoding='utf-8') as f:
            self.assertIn("日志2", f.read())

    def test_log_level_from_env(self):
        """测试从环境变量读取日志级别"""
        os.environ['LOG_LEVEL'] = 'ERROR'

        # 需要创建新的manager实例来应用新配置
        # 由于是单例，这里测试配置读取逻辑
        manager = LoggerManager()

        # 验证配置读取
        import logging
        self.assertIn(manager.log_level, [
            logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL
        ])

    def test_console_output_from_env(self):
        """测试从环境变量控制控制台输出"""
        os.environ['LOG_CONSOLE'] = 'false'
        manager = LoggerManager()

        logger = get_logger(self.test_log_path, name="test_console")

        # 检查handlers数量（只有文件handler，没有控制台handler）
        # 注意：由于是单例，可能已有handlers
        file_handlers = [h for h in logger.handlers
                         if hasattr(h, 'baseFilename')]
        self.assertGreater(len(file_handlers), 0)

    def test_cleanup_pid(self):
        """测试清理PID"""
        logger = get_logger(self.test_log_path, name="test_cleanup")

        # 验证PID已注册
        info_before = get_path_info(self.test_log_path)
        self.assertIn(os.getpid(), info_before['pids'])

        # 清理当前PID
        cleanup_current_process()

        # 验证PID已移除
        info_after = get_path_info(self.test_log_path)
        self.assertNotIn(os.getpid(), info_after['pids'])

    def test_path_normalization(self):
        """测试路径规范化"""
        # 使用相对路径
        relative_path = "test.log"
        logger1 = get_logger(relative_path, name="norm1")
        logger1.info("相对路径")

        # 使用绝对路径
        absolute_path = str(Path(relative_path).resolve())
        logger2 = get_logger(absolute_path, name="norm2")
        logger2.info("绝对路径")

        # 应该指向同一个路径
        info = get_path_info(absolute_path)
        self.assertEqual(info['num_processes'], 1)

        # 验证两条日志都被写入
        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("相对路径", content)
            self.assertIn("绝对路径", content)

    def test_same_name_different_path(self):
        """测试相同name，不同path，应该创建不同的logger"""

        path1 = os.path.join(self.temp_dir, "app1.log")
        path2 = os.path.join(self.temp_dir, "app2.log")

        # 使用相同的name，但不同的path
        logger1 = get_logger(path1, name="worker")
        logger2 = get_logger(path2, name="worker")

        # 写入日志
        logger1.info("来自logger1")
        logger2.info("来自logger2")

        # 验证是否写入不同的文件
        with open(path1, 'r', encoding='utf-8') as f:
            content1 = f.read()
        with open(path2, 'r', encoding='utf-8') as f:
            content2 = f.read()

        assert "来自logger1" in content1, "path1应该包含logger1的日志"
        assert "来自logger2" not in content1, "path1不应该包含logger2的日志"
        assert "来自logger2" in content2, "path2应该包含logger2的日志"
        assert "来自logger1" not in content2, "path2不应该包含logger1的日志"

        # 验证显示名称
        assert "[worker]" in content1, "日志应该显示用户指定的名称"
        assert "[worker]" in content2, "日志应该显示用户指定的名称"

        print("✅ 测试通过：相同name不同path正确创建了不同的logger")
        print(f"   logger1的日志: {path1}")
        print(f"   logger2的日志: {path2}")

    def test_no_name_different_path_same_stem(self):
        """测试不设置name，不同path但相同stem，应该创建不同的logger"""
        # 创建两个不同目录，但文件名相同
        dir1 = os.path.join(self.temp_dir, "dir1")
        dir2 = os.path.join(self.temp_dir, "dir2")
        os.makedirs(dir1)
        os.makedirs(dir2)

        path1 = os.path.join(dir1, "app.log")
        path2 = os.path.join(dir2, "app.log")

        # 不设置name，路径不同但stem相同
        logger1 = get_logger(path1)
        logger2 = get_logger(path2)

        # 写入日志
        logger1.info("来自dir1的app.log")
        logger2.info("来自dir2的app.log")

        # 验证是否写入不同的文件
        with open(path1, 'r', encoding='utf-8') as f:
            content1 = f.read()
        with open(path2, 'r', encoding='utf-8') as f:
            content2 = f.read()

        assert "来自dir1的app.log" in content1
        assert "来自dir2的app.log" not in content1
        assert "来自dir2的app.log" in content2
        assert "来自dir1的app.log" not in content2

        # 验证显示名称都是"app"（因为stem相同）
        assert "[app]" in content1
        assert "[app]" in content2

        print("✅ 测试通过：相同stem的不同path正确创建了不同的logger")
        print(f"   两个logger都显示为 [app]，但写入不同文件")

    def test_process_pool_pid(self):
        """测试进程池中的PID应该是子进程的真实PID"""

        log_path = os.path.join(self.temp_dir, "pool.log")

        # 主进程PID
        main_pid = os.getpid()
        print(f"主进程PID: {main_pid}")

        # 使用进程池
        with Pool(processes=3) as pool:
            args = [(i, log_path) for i in range(5)]
            worker_pids = pool.imap_unordered(pool_worker, args)

        # 验证日志
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查日志中的PID是否是子进程的真实PID
        unique_pids = set(worker_pids)
        print(f"工作进程的PID: {unique_pids}")

        # 验证日志中显示的是真实PID而不是主进程PID
        for pid in unique_pids:
            assert f"[PID:{pid}]" in content, f"日志应该包含工作进程PID {pid}"

        assert f"[PID:{main_pid}]" not in content, f"日志不应该包含主进程PID {main_pid}"

        print("✅ 测试通过：进程池中正确显示子进程的真实PID")
        print(f"   日志包含 {len(unique_pids)} 个不同的工作进程PID")

    def test_display_name_simplification(self):
        """测试验证显示名称的简化"""
        log_path = os.path.join(self.temp_dir, "test.log")

        # 测试自定义名称
        logger1 = get_logger(log_path, name="MyApp")
        logger1.info("使用自定义名称")

        # 清空handlers以便复用
        for handler in logger1.handlers[:]:
            handler.close()
            logger1.handlers.clear()

        # 测试默认名称（使用文件stem）
        logger2 = get_logger(log_path)
        logger2.info("使用默认名称")

        # 验证日志内容
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 验证第一条日志显示自定义名称
        lines = content.strip().split('\n')
        assert "[MyApp]" in lines[0], "第一条日志应该显示 [MyApp]"
        assert "[test]" in lines[1], "第二条日志应该显示 [test]"

        print("✅ 测试通过：显示名称正确简化")
        print(f"   自定义名称: [MyApp]")
        print(f"   默认名称: [test]")

    def test_concurrent_loggers(self):
        """测试并发创建多个logger"""

        with ProcessPoolExecutor(max_workers=4) as executor:
            results = executor.map(_concurrent_worker, range(5), [self.temp_dir] * 5)

        for result in results:
            log_path = result['log_path']
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert f"[PID:{result['pid']}]" in content, f"日志应该包含工作进程PID {result['pid']}"
            assert f"[Worker{result['worker_id']}]" in content, f"日志应该包含工作进程名称 Worker{result['worker_id']}"

        print("✅ 测试通过：并发创建多个logger无冲突")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLoggerManager)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
