# 快速开始指南

## 🚀 5分钟上手

### 1. 安装

无需安装任何依赖！只需要Python 3.6+和标准库。

```bash
# 将 logger_manager.py 放到你的项目目录
cp logger_manager.py /path/to/your/project/
```

### 2. 最简单的使用

```python
from logger_manager import get_logger

# 获取日志对象
logger = get_logger("app.log")

# 开始记录日志
logger.info("应用启动")
logger.error("发生错误")
```

就这么简单！

### 3. 设置环境变量（可选）

```bash
# Linux/Mac
export LOG_LEVEL=DEBUG
export LOG_CONSOLE=true

# Windows
set LOG_LEVEL=DEBUG
set LOG_CONSOLE=true
```

或在Python代码中设置：

```python
import os

os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_CONSOLE'] = 'true'
```

### 4. 多进程场景

```python
from multiprocessing import Process
from logger_manager import get_logger

def worker(worker_id):
    logger = get_logger("app.log", name=f"worker_{worker_id}")
    logger.info(f"Worker {worker_id} started")
    # 做一些工作...
    logger.info(f"Worker {worker_id} finished")

if __name__ == "__main__":
    # 主进程
    logger = get_logger("app.log", name="main")
    logger.info("启动工作进程")
    
    # 创建子进程
    processes = [Process(target=worker, args=(i,)) for i in range(5)]
    for p in processes: p.start()
    for p in processes: p.join()
    
    logger.info("所有工作完成")
```

### 5. 验证安装

```bash
# 运行测试
python test_logger_manager.py

# 运行示例
python example_usage.py

# 快速测试跨平台兼容性
python test_cross_platform_compatibility.py
```

## 📝 常见使用场景

### 场景1: Web应用日志

```python
from logger_manager import get_logger

# 不同类型的日志
access_logger = get_logger("logs/access.log", name="access")
error_logger = get_logger("logs/error.log", name="error")
app_logger = get_logger("logs/app.log", name="app")

# 使用
access_logger.info("GET /api/users 200")
error_logger.error("Database connection failed")
app_logger.info("Server started on port 8000")
```

### 场景2: 数据处理管道

```python
from multiprocessing import Pool
from logger_manager import get_logger


def process_data(data_id):
    logger = get_logger("logs/pipeline.log", name=f"worker_{data_id}")
    logger.info(f"Processing data {data_id}")

    try:
        # 处理数据
        result = heavy_computation(data_id)
        logger.info(f"Data {data_id} processed successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to process data {data_id}: {e}")
        raise


if __name__ == "__main__":
    with Pool(processes=4) as pool:
        results = pool.map(process_data, range(100))
```

### 场景3: 定时任务

```python
import schedule
from logger_manager import get_logger

logger = get_logger("logs/tasks.log", name="scheduler")


def backup_database():
    logger.info("Starting database backup")
    # 执行备份...
    logger.info("Database backup completed")


def cleanup_old_files():
    logger.info("Starting file cleanup")
    # 清理文件...
    logger.info("File cleanup completed")


# 设置定时任务
schedule.every().day.at("02:00").do(backup_database)
schedule.every().hour.do(cleanup_old_files)

logger.info("Scheduler started")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 🔧 配置选项

### 环境变量

| 变量            | 可选值                               | 默认值  | 说明       |
|---------------|-----------------------------------|------|----------|
| `LOG_LEVEL`   | DEBUG/INFO/WARNING/ERROR/CRITICAL | INFO | 日志级别     |
| `LOG_CONSOLE` | true/false/1/0/yes/no             | true | 是否输出到控制台 |

### 日志格式

默认格式：

```
[2025-11-06 10:30:45] [INFO] [PID:1234] [logger_name] - 日志消息
```

包含信息：

- 时间戳
- 日志级别
- 进程ID
- Logger名称
- 日志消息

### 文件轮转

- 单个文件最大: 100MB
- 保留备份数: 10个
- 自动创建: `app.log`, `app.log.1`, `app.log.2`, ...

## 💡 最佳实践

### 1. 为不同模块使用不同的logger名称

```python
# 好的做法 ✅
user_logger = get_logger("app.log", name="user_module")
auth_logger = get_logger("app.log", name="auth_module")
db_logger = get_logger("app.log", name="database")

# 不推荐 ❌
logger1 = get_logger("app.log")
logger2 = get_logger("app.log")
```

### 2. 使用不同文件分类日志

```python
# 按重要性分类
info_logger = get_logger("logs/info.log", name="info")
error_logger = get_logger("logs/error.log", name="error")

# 按功能分类
api_logger = get_logger("logs/api.log", name="api")
db_logger = get_logger("logs/database.log", name="db")
cache_logger = get_logger("logs/cache.log", name="cache")
```

### 3. 在生产环境禁用控制台输出

```bash
# 生产环境
export LOG_LEVEL=INFO
export LOG_CONSOLE=false

# 开发环境
export LOG_LEVEL=DEBUG
export LOG_CONSOLE=true
```

### 4. 结构化日志消息

```python
# 好的做法 ✅
logger.info(f"User {user_id} logged in from {ip_address}")
logger.error(f"Failed to connect to database: {error_message}")

# 不够详细 ❌
logger.info("User logged in")
logger.error("Database error")
```

### 5. 及时记录重要事件

```python
def process_payment(amount, user_id):
    logger.info(f"Payment processing started: amount={amount}, user={user_id}")

    try:
        result = payment_gateway.charge(amount)
        logger.info(f"Payment successful: transaction_id={result.id}")
        return result
    except Exception as e:
        logger.error(f"Payment failed: {e}", exc_info=True)
        raise
```

## 🎯 性能提示

### 1. 合理设置日志级别

```python
# 开发环境 - 记录所有细节
os.environ['LOG_LEVEL'] = 'DEBUG'

# 生产环境 - 只记录重要信息
os.environ['LOG_LEVEL'] = 'INFO'

# 关键系统 - 只记录错误
os.environ['LOG_LEVEL'] = 'ERROR'
```

### 2. 避免在循环中过度记录

```python
# 不好 ❌
for i in range(1000000):
    logger.debug(f"Processing item {i}")  # 太多日志！

# 好 ✅
logger.info(f"Starting to process {len(items)} items")
for i, item in enumerate(items):
    if i % 10000 == 0:
        logger.info(f"Processed {i} items")
logger.info("Processing complete")
```

### 3. 使用合适的日志级别

```python
logger.debug("Detailed debugging information")  # 开发调试
logger.info("Normal operational messages")  # 常规信息
logger.warning("Warning messages")  # 警告
logger.error("Error messages")  # 错误
logger.critical("Critical problems")  # 严重错误
```

## 📞 获取帮助

- 查看完整文档: [README.md](README.md)
- macOS问题: [MACOS_COMPATIBILITY.md](MACOS_COMPATIBILITY.md)
- 版本历史: [CHANGELOG.md](CHANGELOG.md)
- 运行示例: `python example_usage.py`
- 运行测试: `python test_logger_manager.py`

## 🎉 开始使用

现在你已经准备好了！只需三步：

1. 导入: `from logger_manager import get_logger`
2. 获取: `logger = get_logger("app.log")`
3. 使用: `logger.info("Hello, logging!")`

就这么简单！祝你使用愉快！ 🚀
