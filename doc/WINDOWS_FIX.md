# Windows 兼容性说明

## 问题描述

在Windows系统上运行单元测试时，会遇到以下错误：

```
PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。
'C:\\Users\\haoran\\AppData\\Local\\Temp\\tmploeuvnpt\\test.log'
```

## 根本原因

这是 **Windows 和 Linux 文件系统的根本性差异**导致的：

### 文件锁定机制对比

| 特性          | Linux                 | Windows                |
|-------------|-----------------------|------------------------|
| **文件锁定**    | 软锁定（advisory locking） | 硬锁定（mandatory locking） |
| **删除打开的文件** | ✅ 允许（延迟删除）            | ❌ 禁止（立即报错）             |
| **文件句柄行为**  | 可以删除仍在使用的文件           | 必须先关闭文件句柄              |
| **inode机制** | 有（引用计数）               | 无（直接锁定）                |

### Linux 行为

```python
# Linux允许删除打开的文件
file = open("test.log", "w")
os.remove("test.log")  # ✅ 成功！
# 文件在磁盘上标记为删除，但inode仍然存在
# 当file.close()时，文件才真正从磁盘删除
```

### Windows 行为

```python
# Windows禁止删除打开的文件
file = open("test.log", "w")
os.remove("test.log")  # ❌ PermissionError: [WinError 32]
# 必须先 file.close()，然后才能删除
```

## 单元测试中的问题

### 问题代码

```python
def tearDown(self):
    """测试后清理"""
    import shutil
    if os.path.exists(self.temp_dir):
        shutil.rmtree(self.temp_dir)  # ❌ Windows上失败
```

### 问题分析

1. **测试创建logger** → `logger = get_logger("test.log")`
2. **Handler打开文件** → `RotatingFileHandler` 持有文件句柄
3. **测试结束** → `tearDown()` 被调用
4. **尝试删除目录** → `shutil.rmtree()` 尝试删除 `test.log`
5. **Windows检测到文件被占用** → 抛出 `PermissionError`

### 为什么Linux上没问题

在Linux上，即使文件被打开，`shutil.rmtree()` 也能成功"删除"它：

- 文件在目录中被移除（unlink）
- 但inode和数据块仍然存在
- 当最后一个文件句柄关闭时，文件才真正删除

## 解决方案

### 修改后的 tearDown

```python
def tearDown(self):
    """测试后清理"""
    import shutil
    import logging
    import gc
    import time

    # 1. 关闭所有logger的handlers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()  # 关闭文件句柄
            logger.removeHandler(handler)

    # 2. 关闭root logger的handlers
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)

    # 3. 强制垃圾回收
    gc.collect()

    # 4. 等待Windows释放文件锁
    time.sleep(0.1)

    # 5. 清理临时文件
    if os.path.exists(self.temp_dir):
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            time.sleep(0.2)  # 再等一下
            shutil.rmtree(self.temp_dir)
```

### 关键步骤解释

#### 步骤1-2: 关闭所有handlers

```python
handler.close()  # 释放文件句柄
logger.removeHandler(handler)  # 从logger中移除
```

必须关闭**所有**logger的handlers，包括：

- 测试中创建的logger
- root logger
- 任何子logger

#### 步骤3: 强制垃圾回收

```python
gc.collect()
```

确保Python立即清理不再使用的对象，释放它们持有的资源。

#### 步骤4: 等待文件锁释放

```python
time.sleep(0.1)
```

Windows需要一点时间来释放文件锁，这是操作系统层面的延迟。

#### 步骤5: 重试机制

```python
try:
    shutil.rmtree(self.temp_dir)
except PermissionError:
    time.sleep(0.2)
    shutil.rmtree(self.temp_dir)
```

如果第一次失败，等待更长时间再重试。

## 其他常见Windows文件锁问题

### 1. 防病毒软件

**问题：** Windows Defender或其他杀毒软件可能扫描新创建的文件

**解决：**

- 将测试目录添加到杀毒软件的排除列表
- 或使用更长的等待时间

### 2. 文件索引服务

**问题：** Windows Search索引服务可能打开文件

**解决：**

- 禁用临时目录的索引
- 或在测试前关闭索引服务

### 3. 文件系统缓存

**问题：** Windows文件系统缓存可能延迟释放句柄

**解决：**

- 使用 `gc.collect()` 强制清理
- 增加等待时间

## 最佳实践

### 1. 总是显式关闭文件句柄

```python
# 好 ✅
handler = RotatingFileHandler("test.log")
try:
    # 使用handler
    pass
finally:
    handler.close()

# 更好 ✅✅
with open("test.log", "w") as f:
    # 使用f
    pass  # 自动关闭
```

### 2. 测试中使用上下文管理器

```python
class TestCase(unittest.TestCase):
    def test_something(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 使用tmpdir
            pass
        # 自动清理，即使在Windows上也没问题
```

### 3. 添加重试逻辑

```python
def safe_rmtree(path, retries=3, delay=0.1):
    """安全删除目录，带重试机制"""
    import shutil
    import time
    
    for i in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise
```

## 调试技巧

### 查看打开的文件句柄

在Windows上，可以使用Process Explorer查看哪个进程打开了文件：

1. 下载 [Process Explorer](https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer)
2. 运行测试到失败点
3. 在Process Explorer中搜索文件名
4. 查看哪个句柄没有被关闭

### Python中列出打开的文件

```python
import psutil
import os

def list_open_files():
    """列出当前进程打开的所有文件"""
    process = psutil.Process(os.getpid())
    for file in process.open_files():
        print(f"Open file: {file.path}")
```

## 验证修复

运行测试确认修复成功：

```bash
# Windows命令行
python test_logger_manager.py
```

**预期输出：**

```
test_cleanup_pid ... ok
test_console_output_from_env ... ok
test_create_new_logger ... ok
test_log_level_from_env ... ok
test_multiple_log_paths ... ok
test_multiprocess_logging ... ok
test_path_info_single_process ... ok
test_path_normalization ... ok
test_reuse_same_logger ... ok
test_singleton_pattern ... ok

----------------------------------------------------------------------
Ran 10 tests in X.XXXs

OK
```

## 总结

- ✅ **问题根源**: Windows文件系统的硬锁定机制
- ✅ **解决方案**: 在删除前显式关闭所有文件句柄
- ✅ **关键步骤**: close() → gc.collect() → sleep() → rmtree()
- ✅ **跨平台**: 修复后在Linux、macOS和Windows上都能正常工作

这不是代码bug，而是需要适配不同操作系统的文件系统特性。
