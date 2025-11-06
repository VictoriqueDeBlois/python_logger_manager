# Changelog

All notable changes to the logger_manager project will be documented in this file.

## [1.0.2] - 2025-11-06

### Fixed
- **Windows兼容性问题**: 修复了在Windows上运行单元测试时的 `PermissionError: [WinError 32]` 错误
  - 在 `tearDown()` 方法中添加显式的文件句柄关闭逻辑
  - 关闭所有logger的handlers后再删除临时文件
  - 添加垃圾回收和重试机制，确保文件锁被正确释放

### Added
- 新增 `WINDOWS_FIX.md` 文档，详细说明Windows文件锁定机制和解决方案
- 在 `README.md` 中添加Windows兼容性说明

### Technical Details
- **问题根源**: Windows使用硬锁定机制，不允许删除正在被打开的文件
- **解决方案**: 在删除前显式关闭所有文件句柄，并等待系统释放文件锁
- **影响范围**: 仅影响测试清理代码，核心功能无变化

## [1.0.1] - 2025-11-06

### Fixed
- **macOS兼容性问题**: 修复了在macOS上运行多进程测试时的 `AttributeError: Can't pickle local object` 错误
  - 将 `test_logger_manager.py` 中的局部函数 `worker()` 移到模块级别为 `_test_worker()`
  - 将 `example_usage.py` 中的局部函数 `child_process()` 移到模块级别为 `child_process_task()`
  - 所有多进程目标函数现在都可以在 macOS、Linux 和 Windows 上正常序列化

### Added
- 新增 `MACOS_FIX.md` 文档，详细说明macOS兼容性问题和解决方案
- 新增 `test_cross_platform_compatibility.py` 快速测试脚本，用于验证跨平台兼容性
- 在 `README.md` 中添加跨平台兼容性说明

### Technical Details
- **问题根源**: macOS 使用 `spawn` 启动模式而非 `fork`，需要pickle序列化所有对象
- **解决方案**: 确保所有 `Process` 的 target 函数都在模块级别定义
- **影响范围**: 仅影响测试和示例代码，核心 `logger_manager.py` 无需修改

## [1.0.0] - 2025-11-06

### Added
- 初始版本发布
- 核心功能:
  - 多进程安全的日志管理
  - 日志路径与PID映射跟踪
  - 智能日志对象复用
  - 环境变量配置支持 (LOG_LEVEL, LOG_CONSOLE)
  - 单例模式实现
  - 自动日志文件轮转 (100MB, 10个备份)
  
- 组件:
  - `logger_manager.py`: 核心实现
  - `example_usage.py`: 使用示例
  - `test_logger_manager.py`: 单元测试套件
  - `README.md`: 完整文档

### Features
- ✅ 跨进程数据共享使用 `multiprocessing.Manager`
- ✅ 并发安全使用 `multiprocessing.Lock`
- ✅ 支持多进程同时写入同一日志文件
- ✅ UTF-8编码支持
- ✅ 自定义日志格式包含时间戳、级别、PID和名称
- ✅ 防止日志传播到root logger

### Testing
- 10个单元测试覆盖所有核心功能
- 5个示例程序展示不同使用场景
- 所有测试在Linux环境通过

---

## 版本说明

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

版本格式: MAJOR.MINOR.PATCH

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复
