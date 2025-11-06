"""
日志管理器使用示例
"""

import os
import time
from multiprocessing import Process

from logger_manager import get_logger, get_path_info, cleanup_current_process


def worker_task(worker_id: int, log_path: str):
    """
    模拟工作进程
    
    Args:
        worker_id: 工作进程ID
        log_path: 日志文件路径
    """
    # 获取logger
    logger = get_logger(log_path, name=f"worker_{worker_id}")

    # 记录当前进程信息
    pid = os.getpid()
    logger.info(f"Worker {worker_id} started with PID: {pid}")

    # 模拟工作
    for i in range(5):
        logger.info(f"Worker {worker_id} - Processing task {i + 1}")
        time.sleep(0.5)

    logger.info(f"Worker {worker_id} completed")

    # 清理
    cleanup_current_process()


def child_process_task(log_path: str):
    """
    子进程任务函数（用于示例5）
    
    Args:
        log_path: 日志文件路径
    """
    logger = get_logger(log_path, name="child")
    pid = os.getpid()
    logger.info(f"子进程 PID:{pid} 开始工作")

    for i in range(3):
        logger.info(f"子进程 PID:{pid} - 任务 {i + 1}")
        time.sleep(0.3)

    logger.info(f"子进程 PID:{pid} 完成")


def example_single_process():
    """示例1: 单进程使用"""
    print("\n=== 示例1: 单进程使用 ===")

    log_path = "./tmp/app.log"

    # 第一次获取logger
    logger1 = get_logger(log_path, name="main")
    logger1.info("这是第一条日志")

    # 第二次获取logger（应该返回相同的对象）
    logger2 = get_logger(log_path, name="main")
    logger2.info("这是第二条日志")

    # 验证是否是同一个logger
    print(f"logger1 和 logger2 是同一个对象: {logger1 is logger2}")

    # 查看路径信息
    info = get_path_info(log_path)
    print(f"日志路径信息: {info}")


def example_multi_process():
    """示例2: 多进程使用"""
    print("\n=== 示例2: 多进程使用 ===")

    log_path = "./tmp/multi_process.log"

    # 主进程也记录日志
    main_logger = get_logger(log_path, name="main")
    main_logger.info("主进程开始启动工作进程")

    # 创建多个工作进程
    processes = []
    for i in range(3):
        p = Process(target=worker_task, args=(i, log_path))
        p.start()
        processes.append(p)

    # 等待所有进程完成
    for p in processes:
        p.join()

    main_logger.info("所有工作进程已完成")

    # 查看路径信息
    info = get_path_info(log_path)
    print(f"日志路径信息: {info}")


def example_multiple_paths():
    """示例3: 多个日志路径"""
    print("\n=== 示例3: 多个日志路径 ===")

    # 不同模块使用不同的日志文件
    app_logger = get_logger("./tmp/app.log", name="app")
    error_logger = get_logger("./tmp/error.log", name="error")
    access_logger = get_logger("./tmp/access.log", name="access")

    app_logger.info("应用程序启动")
    error_logger.error("这是一个错误日志")
    access_logger.info("用户访问了首页")

    # 从LoggerManager查看所有路径
    from logger_manager import LoggerManager
    manager = LoggerManager()
    all_paths = manager.get_all_paths()
    print(f"所有日志路径: {all_paths}")


def example_environment_config():
    """示例4: 环境变量配置"""
    print("\n=== 示例4: 环境变量配置 ===")

    # 设置环境变量
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['LOG_CONSOLE'] = 'true'

    # 重新导入以应用新配置（实际使用中应在程序启动前设置）
    # 这里只是演示，实际上LoggerManager是单例
    logger = get_logger("./tmp/debug.log", name="debug")

    logger.debug("这是DEBUG级别日志")
    logger.info("这是INFO级别日志")
    logger.warning("这是WARNING级别日志")
    logger.error("这是ERROR级别日志")

    print(f"当前日志级别: {os.environ.get('LOG_LEVEL')}")
    print(f"控制台输出: {os.environ.get('LOG_CONSOLE')}")


def example_same_path_different_processes():
    """示例5: 同一路径不同进程"""
    print("\n=== 示例5: 同一路径不同进程（核心场景）===")

    log_path = "./tmp/shared.log"

    # 主进程记录
    main_logger = get_logger(log_path, name="main")
    main_logger.info(f"主进程 PID:{os.getpid()} 开始")

    # 检查初始状态
    info = get_path_info(log_path)
    print(f"启动前 - PIDs: {info['pids']}")

    # 启动子进程
    p1 = Process(target=child_process_task, args=(log_path,))
    p2 = Process(target=child_process_task, args=(log_path,))

    p1.start()
    p2.start()

    # 主进程继续记录
    for i in range(3):
        main_logger.info(f"主进程 - 任务 {i + 1}")
        time.sleep(0.3)

    p1.join()
    p2.join()

    main_logger.info(f"主进程 PID:{os.getpid()} 完成")

    # 检查最终状态
    info = get_path_info(log_path)
    print(f"完成后 - PIDs: {info['pids']}, 进程数: {info['num_processes']}")


if __name__ == "__main__":
    # 设置环境变量（在实际使用中应该在程序启动前设置）
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('LOG_CONSOLE', 'true')

    # 运行示例
    example_single_process()
    example_multiple_paths()
    example_environment_config()
    example_multi_process()
    example_same_path_different_processes()

    print("\n所有示例运行完成！请查看 ./tmp 目录下的日志文件。")
