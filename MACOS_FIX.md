# macOS 兼容性修复说明

## 问题描述

在 macOS 系统上运行多进程测试时，会遇到以下错误：

```
AttributeError: Can't pickle local object 'TestLoggerManager.test_multiprocess_logging.<locals>.worker'
```

## 原因分析

这是因为：

1. **macOS 的 multiprocessing 默认使用 `spawn` 启动模式**（而不是 Linux 的 `fork`）
2. `spawn` 模式需要序列化（pickle）所有传递给子进程的对象
3. **嵌套/局部函数无法被 pickle**，因此会导致错误

## 解决方案

将所有用作 `Process` target 的函数移到**模块级别**（不要作为嵌套函数定义）。

### 修复前（错误示例）

```python
def test_multiprocess_logging(self):
    """测试多进程日志写入"""
    def worker():  # ❌ 局部函数，无法pickle
        logger = get_logger(self.test_log_path, name="worker")
        logger.info("Worker")
    
    p = Process(target=worker)  # ❌ 在macOS上会失败
    p.start()
```

### 修复后（正确示例）

```python
# 在模块级别定义函数
def _test_worker(log_path):  # ✅ 模块级函数，可以pickle
    logger = get_logger(log_path, name="worker")
    logger.info("Worker")

class TestLoggerManager(unittest.TestCase):
    def test_multiprocess_logging(self):
        """测试多进程日志写入"""
        p = Process(target=_test_worker, args=(self.test_log_path,))  # ✅ 正常工作
        p.start()
```

## 已修复的文件

### 1. test_logger_manager.py

**修改内容：**
- 添加模块级函数 `_test_worker(log_path)`
- 更新 `test_multiprocess_logging` 方法使用该函数

**修改原因：**
原代码中的 `worker()` 是 `test_multiprocess_logging` 方法内的局部函数。

### 2. example_usage.py

**修改内容：**
- 添加模块级函数 `child_process_task(log_path)`
- 更新 `example_same_path_different_processes` 函数使用该函数

**修改原因：**
原代码中的 `child_process()` 是 `example_same_path_different_processes` 函数内的局部函数。

## 跨平台兼容性说明

修复后的代码现在完全兼容：

- ✅ **Linux**: 使用 `fork` 或 `spawn` 模式都能正常工作
- ✅ **macOS**: `spawn` 模式正常工作
- ✅ **Windows**: `spawn` 模式正常工作

## 其他注意事项

### 为什么不用 `if __name__ == '__main__'`？

有些人建议使用：
```python
if __name__ == '__main__':
    # 启动进程
```

这是必要的，但**不能解决局部函数的问题**。局部函数依然无法被pickle，必须移到模块级别。

### multiprocessing 启动方法

可以显式设置启动方法：

```python
import multiprocessing

# 设置启动方法（必须在创建任何进程之前）
multiprocessing.set_start_method('spawn')  # 或 'fork'（仅Linux）
```

但**最佳实践**是编写兼容所有启动方法的代码（即使用模块级函数）。

## 测试验证

修复后运行测试：

```bash
# 运行所有测试
python test_logger_manager.py

# 运行示例
python example_usage.py
```

所有测试应该通过，无论在哪个操作系统上。

## 参考资料

- [Python multiprocessing 文档](https://docs.python.org/3/library/multiprocessing.html)
- [pickle 协议说明](https://docs.python.org/3/library/pickle.html)
- [multiprocessing 启动方法](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods)
