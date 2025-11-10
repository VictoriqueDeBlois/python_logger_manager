# 多进程安全日志管理工具

一个功能完整的Python日志管理工具类，支持多进程安全的日志写入和智能的日志对象复用。

## 主要特性

✅ **智能日志对象管理**
- 自动跟踪日志路径与进程PID的映射关系
- 内部名称与显示名称分离，确保唯一性
- 同一进程同一路径复用日志对象
- 不同进程或不同路径创建独立日志对象
- 完美支持进程池（Pool）场景

✅ **多进程安全**
- 使用 `multiprocessing.Manager` 实现跨进程数据共享
- 使用 `multiprocessing.Lock` 保证并发安全
- 使用 `RotatingFileHandler` 支持多进程写入

✅ **环境变量配置**
- `LOG_LEVEL`: 控制日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `LOG_CONSOLE`: 控制是否输出到控制台 (true/false)

✅ **单例模式**
- 全局唯一的日志管理器实例
- 线程安全的单例实现

## 快速开始

### 基本使用

```python
from logger_manager import get_logger

# 获取日志对象
logger = get_logger("/var/log/myapp.log", name="myapp")

# 记录日志
logger.info("应用启动")
logger.error("发生错误")
logger.debug("调试信息")
```

### 多进程使用

```python
from multiprocessing import Process
from logger_manager import get_logger

def worker_func(worker_id):
    # 每个进程获取自己的logger
    logger = get_logger("/var/log/app.log", name=f"worker_{worker_id}")
    logger.info(f"Worker {worker_id} started")
    
    # 执行任务...
    logger.info(f"Worker {worker_id} finished")

if __name__ == "__main__":
    # 主进程
    main_logger = get_logger("/var/log/app.log", name="main")
    main_logger.info("启动工作进程")
    
    # 创建多个工作进程
    processes = []
    for i in range(5):
        p = Process(target=worker_func, args=(i,))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
    
    main_logger.info("所有工作完成")
```

### 进程池使用

```python
from multiprocessing import Pool
from logger_manager import init_manager, get_logger

# ⚠️ 重要：使用进程池前必须调用init_manager()
init_manager()

def pool_worker(task_id):
    # 在进程池中使用，PID会正确显示为子进程的真实PID
    logger = get_logger("/var/log/pool.log", name=f"Task-{task_id}")
    logger.info(f"处理任务 {task_id}")

    # 执行任务...
    result = process_task(task_id)

    logger.info(f"任务 {task_id} 完成")
    return result

if __name__ == "__main__":
    # 使用进程池处理任务
    with Pool(processes=4) as pool:
        results = pool.map(pool_worker, range(20))
```

**注意：**

- 使用 `multiprocessing.Pool` 前**必须**先调用 `init_manager()`
- 这是因为Pool的worker是daemon进程，不能创建Manager子进程
- 详见 [POOL_USAGE.md](POOL_USAGE.md) 了解更多

### 查看日志路径信息

```python
from logger_manager import get_path_info, LoggerManager

# 查看特定路径的信息
info = get_path_info("/var/log/app.log")
print(f"进程数: {info['num_processes']}")
print(f"PIDs: {info['pids']}")

# 查看所有日志路径
manager = LoggerManager()
all_paths = manager.get_all_paths()
print(all_paths)
```

## 环境变量配置

### 设置日志级别

```bash
# Linux/Mac
export LOG_LEVEL=DEBUG

# Windows
set LOG_LEVEL=DEBUG
```

可选值：
- `DEBUG`: 最详细的日志信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 控制控制台输出

```bash
# 启用控制台输出（默认）
export LOG_CONSOLE=true

# 禁用控制台输出
export LOG_CONSOLE=false
```

## 工作原理

### 1. 路径和PID映射

```
日志路径                    PIDs
/var/log/app.log    ->    [1234, 5678, 9012]
/var/log/error.log  ->    [1234]
```

### 2. 日志对象复用逻辑

```
请求: get_logger("/var/log/app.log")

判断流程:
1. 路径不存在? 
   -> 创建新logger，记录路径和PID

2. 路径存在，PID也存在?
   -> 返回缓存的logger（复用）

3. 路径存在，PID不存在?
   -> 创建新logger（多进程场景），记录新PID
```

### 3. 多进程安全机制

- **共享数据结构**: 使用 `multiprocessing.Manager().dict()` 存储跨进程数据
- **互斥锁**: 使用 `multiprocessing.Lock()` 保护关键代码段
- **文件Handler**: 使用 `RotatingFileHandler` 支持多进程写入同一文件

## API 参考

### 函数

#### `get_logger(log_path, name=None)`

获取或创建日志对象。

**参数:**
- `log_path` (str): 日志文件路径
- `name` (str, optional): 日志器名称

**返回:**
- `logging.Logger`: 配置好的日志对象

#### `get_path_info(log_path)`

获取日志路径的详细信息。

**参数:**
- `log_path` (str): 日志文件路径

**返回:**
- `dict`: 包含路径、PIDs列表和进程数的字典

#### `cleanup_current_process()`

清理当前进程的日志缓存（进程结束时可选调用）。

### LoggerManager 类

#### 方法

- `get_logger(log_path, name=None)`: 获取日志对象
- `get_path_info(log_path)`: 获取路径信息
- `get_all_paths()`: 获取所有路径及其PIDs
- `cleanup_pid(pid=None)`: 清理指定PID的缓存

## 日志格式

默认日志格式：
```
[2025-11-06 10:30:45] [INFO] [PID:1234] [myapp_pid1234] - 这是一条日志消息
```

包含信息：
- 时间戳
- 日志级别
- 进程ID
- 日志器名称
- 日志消息

## 高级用法

### 不同模块使用不同日志文件

```python
# 应用日志
app_logger = get_logger("/var/log/app.log", name="app")

# 错误日志
error_logger = get_logger("/var/log/error.log", name="error")

# 访问日志
access_logger = get_logger("/var/log/access.log", name="access")

app_logger.info("应用启动")
error_logger.error("发生错误")
access_logger.info("用户访问")
```

### 进程结束时清理

```python
from logger_manager import get_logger, cleanup_current_process
import atexit

logger = get_logger("/var/log/app.log")

# 注册退出时清理
atexit.register(cleanup_current_process)

# ... 应用逻辑 ...
```

### 动态调整日志级别

```python
import os
import logging
from logger_manager import get_logger

# 运行时修改日志级别
logger = get_logger("/var/log/app.log")
logger.setLevel(logging.DEBUG)

# 修改handler级别
for handler in logger.handlers:
    handler.setLevel(logging.DEBUG)
```

## 测试

运行单元测试：

```bash
python test_logger_manager.py
```

运行示例程序：

```bash
python example_usage.py
```

## 注意事项

1. **日志文件轮转**: 默认单个日志文件最大100MB，保留10个备份
2. **编码**: 日志文件使用UTF-8编码
3. **性能**: 在高并发场景下，锁可能成为瓶颈，考虑使用消息队列
4. **清理**: 长期运行的应用建议定期调用 `cleanup_pid()` 清理已退出进程的缓存

## 文件结构

```
.
├── logger_manager.py       # 核心实现
├── example_usage.py        # 使用示例
├── test_logger_manager.py  # 单元测试
└── README.md              # 本文档
```

## 依赖

- Python 3.6+
- 标准库: logging, multiprocessing, pathlib

无需额外安装第三方依赖。

## 跨平台兼容性

✅ **完全兼容以下操作系统：**
- Linux (Ubuntu, CentOS, etc.)
- macOS (10.14+)
- Windows (10+)

**平台特定说明：**

### macOS
- multiprocessing 使用 `spawn` 启动模式
- 所有多进程函数已在模块级别定义
- 详见 [MACOS_COMPATIBILITY.md](MACOS_COMPATIBILITY.md)

### Windows
- 文件系统使用硬锁定机制
- 测试中已正确处理文件句柄关闭
- 详见 [WINDOWS_FIX.md](WINDOWS_FIX.md)

## 故障排除

### macOS 上的 "Can't pickle" 错误

如果你在 macOS 上遇到类似错误：
```
AttributeError: Can't pickle local object 'function_name'
```

**原因：** macOS 使用 `spawn` 模式启动进程，需要序列化所有对象。

**解决方案：** 确保所有作为 `Process` target 的函数都定义在模块级别（不要嵌套在其他函数内）。

**示例：**
```python
# ❌ 错误 - 局部函数
def main():
    def worker():
        pass
    p = Process(target=worker)  # 会失败

# ✅ 正确 - 模块级函数
def worker():
    pass

def main():
    p = Process(target=worker)  # 正常工作
```

详细说明请参考 [MACOS_COMPATIBILITY.md](MACOS_COMPATIBILITY.md)

### Windows 上的 "PermissionError" 错误

如果你在 Windows 上遇到类似错误：
```
PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。
```

**原因：** Windows文件系统在文件被打开时会锁定文件，禁止删除。

**解决方案：** 单元测试已包含正确的文件句柄清理逻辑。如果在你的代码中遇到此问题，请确保：
- 显式关闭所有logger的handlers
- 在删除文件前调用 `handler.close()`
- 必要时使用 `gc.collect()` 和短暂的 `time.sleep()`

详细说明请参考 [WINDOWS_FIX.md](WINDOWS_FIX.md)

### 快速测试

运行快速测试脚本验证安装：
```bash
python test_cross_platform_compatibility.py
```

## 许可

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
