# 进程池使用说明

## 🐛 问题描述

在 Windows 上使用 `multiprocessing.Pool` 时，会遇到以下错误：

```
AssertionError: daemonic processes are not allowed to have children
```

## 🔍 根本原因

### 问题链条

1. **进程池的worker是daemon进程**
   ```python
   # multiprocessing.Pool内部
   worker = Process(..., daemon=True)  # daemon进程
   ```

2. **LoggerManager需要创建Manager**
   ```python
   # 在子进程中首次调用get_logger时
   LoggerManager._manager = Manager()  # 尝试创建Manager
   # Manager内部会启动一个新进程
   ```

3. **Daemon进程不允许创建子进程**
   ```
   daemon进程(pool worker)
       └─ 尝试创建Manager进程  # ❌ 不允许！
   ```

### 为什么会这样

- `multiprocessing.Manager()` 内部会启动一个**管理进程**来协调跨进程的数据共享
- **Daemon进程**不允许创建子进程（Python的安全限制）
- 进程池的worker默认是daemon进程
- 因此在pool worker中初始化LoggerManager会失败

## ✅ 解决方案

### 方案：在主进程中提前初始化

在使用进程池**之前**调用 `init_manager()` 函数：

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool

# ✅ 在主进程中提前初始化（在Pool之前）
init_manager()


def worker(task_id):
    # 现在可以安全地使用了
    logger = get_logger("/var/log/app.log", name=f"Task-{task_id}")
    logger.info(f"处理任务 {task_id}")
    return result


# 使用进程池
with Pool(processes=4) as pool:
    results = pool.map(worker, range(100))
```

### 为什么这样可以解决

```
主进程（非daemon）
    ├─ init_manager()
    │   └─ 创建Manager进程  # ✅ 允许
    │
    └─ 启动Pool
        ├─ worker 1 (daemon)
        │   └─ get_logger()  # ✅ 复用已有的Manager
        ├─ worker 2 (daemon)
        │   └─ get_logger()  # ✅ 复用已有的Manager
        └─ worker 3 (daemon)
            └─ get_logger()  # ✅ 复用已有的Manager
```

## 📋 使用场景

### 场景1: 基本的进程池使用

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool

# 提前初始化
init_manager()


def process_data(data_id):
    logger = get_logger("pipeline.log", name=f"Worker-{data_id}")
    logger.info(f"开始处理 {data_id}")

    # 处理数据...
    result = heavy_computation(data_id)

    logger.info(f"完成处理 {data_id}")
    return result


if __name__ == "__main__":
    with Pool(processes=8) as pool:
        results = pool.map(process_data, range(100))
```

### 场景2: 带初始化参数的进程池

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool


def init_worker(log_path):
    """worker初始化函数"""
    # 可以在这里做一些初始化
    pass


def worker(task):
    logger = get_logger("/var/log/pool.log")
    logger.info(f"处理任务 {task}")
    return result


if __name__ == "__main__":
    # 提前初始化Manager
    init_manager()

    # 创建进程池
    with Pool(processes=4, initializer=init_worker,
              initargs=("/var/log/pool.log",)) as pool:
        results = pool.map(worker, tasks)
```

### 场景3: 多个进程池

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool

# 只需要调用一次init_manager()
init_manager()

def worker1(task):
    logger = get_logger("pool1.log", name="Pool1")
    logger.info(f"Pool1处理 {task}")
    return result1

def worker2(task):
    logger = get_logger("pool2.log", name="Pool2")
    logger.info(f"Pool2处理 {task}")
    return result2

if __name__ == "__main__":
    # 第一个进程池
    with Pool(processes=4) as pool1:
        results1 = pool1.map(worker1, tasks1)
    
    # 第二个进程池（不需要再次init_manager）
    with Pool(processes=4) as pool2:
        results2 = pool2.map(worker2, tasks2)
```

## ❌ 错误示例

### 错误1: 忘记调用init_manager()

```python
from logger_manager import get_logger
from multiprocessing import Pool


def worker(task):
    logger = get_logger("app.log")  # ❌ 会失败
    logger.info(f"处理 {task}")


# 忘记调用init_manager()
with Pool(processes=4) as pool:
    pool.map(worker, range(10))  # ❌ AssertionError
```

### 错误2: 在Pool创建后调用init_manager()

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool


def worker(task):
    logger = get_logger("app.log")
    logger.info(f"处理 {task}")


with Pool(processes=4) as pool:
    init_manager()  # ❌ 太晚了！应该在Pool之前
    pool.map(worker, range(10))
```

## 🔧 其他多进程场景

### Process（不需要init_manager）

使用 `multiprocessing.Process` **不需要**调用 `init_manager()`：

```python
from logger_manager import get_logger
from multiprocessing import Process


def worker():
    logger = get_logger("app.log")
    logger.info("工作中")


# ✅ Process不是daemon，可以直接使用
p = Process(target=worker)
p.start()
p.join()
```

### 什么时候需要init_manager()

| 场景                                       | 是否需要  | 原因              |
|------------------------------------------|-------|-----------------|
| `multiprocessing.Pool`                   | ✅ 需要  | worker是daemon进程 |
| `concurrent.futures.ProcessPoolExecutor` | ✅ 需要  | 内部也是daemon进程    |
| `multiprocessing.Process`                | ❌ 不需要 | 默认非daemon       |
| `multiprocessing.Process(daemon=True)`   | ✅ 需要  | 显式设置为daemon     |
| 单进程                                      | ❌ 不需要 | 没有多进程           |

## 🧪 测试验证

### 测试代码

```python
from logger_manager import init_manager, get_logger
from multiprocessing import Pool
import os


def test_pool_worker(task_id):
    logger = get_logger("/tmp/test_pool.log", name=f"Task-{task_id}")
    pid = os.getpid()
    logger.info(f"Task {task_id} - PID: {pid}")
    return pid


if __name__ == "__main__":
    # 提前初始化
    init_manager()

    # 测试进程池
    with Pool(processes=3) as pool:
        pids = pool.map(test_pool_worker, range(5))

    print(f"工作进程PIDs: {set(pids)}")

    # 验证日志
    with open("/tmp/test_pool.log") as f:
        print(f.read())
```

### 预期输出

```
工作进程PIDs: {12345, 12346, 12347}
[2025-11-07 10:30:45] [INFO] [PID:12345] [Task-0] - Task 0 - PID: 12345
[2025-11-07 10:30:45] [INFO] [PID:12346] [Task-1] - Task 1 - PID: 12346
[2025-11-07 10:30:45] [INFO] [PID:12347] [Task-2] - Task 2 - PID: 12347
...
```

## 📊 技术细节

### init_manager() 做了什么

```python
def init_manager():
    """提前初始化LoggerManager"""
    # 创建LoggerManager实例
    _ = LoggerManager()

    # LoggerManager.__init__会：
    # 1. 创建multiprocessing.Manager()
    # 2. 创建共享的dict和Lock
    # 3. 这些都在主进程中完成
```

### Manager进程的生命周期

```
主进程启动
    ↓
调用 init_manager()
    ↓
创建 Manager 进程（独立进程）
    ↓
Manager进程启动并等待
    ↓
启动Pool（多个worker进程）
    ↓
worker进程通过Manager共享数据
    ↓
Pool关闭
    ↓
主进程结束
    ↓
Manager进程自动清理
```

## 💡 最佳实践

### 1. 始终在主进程开始时初始化

```python
if __name__ == "__main__":
    # 第一件事：初始化Manager
    init_manager()

    # 然后才是其他逻辑
    main()
```

### 2. 在模块导入时初始化（高级用法）

```python
# worker_module.py
from logger_manager import get_logger


def process_task(task):
    logger = get_logger("app.log")
    logger.info(f"处理 {task}")
    return result


# main.py
from logger_manager import init_manager
from worker_module import process_task
from multiprocessing import Pool

if __name__ == "__main__":
    # 提前初始化
    init_manager()

    # 使用进程池
    with Pool(processes=4) as pool:
        pool.map(process_task, tasks)
```

### 3. 文档化要求

在使用进程池的代码中添加注释：

```python
if __name__ == "__main__":
    # 注意：使用进程池前必须调用init_manager()
    # 参考：https://your-doc-link/POOL_USAGE.md
    init_manager()

    with Pool(processes=4) as pool:
        pool.map(worker, tasks)
```

## 🎯 总结

- ✅ **问题**: Daemon进程不能创建Manager子进程
- ✅ **解决**: 在主进程中调用 `init_manager()`
- ✅ **时机**: Pool创建**之前**
- ✅ **频率**: 整个程序只需调用一次
- ✅ **影响**: 轻微（Manager创建开销约10-50ms）

记住这个简单的规则：

```python
# 使用Pool前，先init_manager()
init_manager()
with Pool(...) as pool:
    ...
```

就这么简单！🚀
