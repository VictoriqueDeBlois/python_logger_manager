# 项目文件说明

本项目包含9个文件，下面是每个文件的详细说明。

## 📦 核心文件

### 1. logger_manager.py
**核心实现文件** - 多进程安全的日志管理器

- **大小**: ~10KB
- **功能**:
  - `LoggerManager` 类（单例模式）
  - `get_logger()` 便捷函数
  - `get_path_info()` 查询函数
  - `cleanup_current_process()` 清理函数
- **特性**:
  - 多进程安全的日志管理
  - 日志路径与PID映射
  - 环境变量配置支持
  - 自动文件轮转
- **依赖**: 仅Python标准库

**你需要将这个文件复制到你的项目中使用。**

## 🧪 测试和示例文件

### 2. test_logger_manager.py
**单元测试套件**

- **大小**: ~7KB
- **内容**: 10个单元测试
- **测试覆盖**:
  - ✅ 单例模式
  - ✅ 日志对象创建和复用
  - ✅ 多进程日志写入
  - ✅ 路径信息跟踪
  - ✅ 环境变量配置
  - ✅ PID清理
  - ✅ 路径规范化
- **运行**: `python test_logger_manager.py`
- **状态**: ✅ 所有测试通过（包括macOS）

### 3. example_usage.py
**使用示例程序**

- **大小**: ~6KB
- **包含示例**:
  1. 单进程使用
  2. 多进程使用
  3. 多个日志路径
  4. 环境变量配置
  5. 同一路径不同进程（核心场景）
- **运行**: `python example_usage.py`
- **输出**: 在 `/tmp` 目录生成示例日志文件

### 4. quick_test_macos.py
**快速验证脚本**（macOS用户推荐）

- **大小**: ~4KB
- **功能**:
  - 快速测试多进程功能
  - 验证macOS兼容性
  - 2个简单测试用例
- **运行**: `python quick_test_macos.py`
- **适用**: 想快速验证安装的用户

## 📚 文档文件

### 5. README.md
**主文档** - 项目完整文档

- **大小**: ~7KB
- **内容**:
  - 项目介绍和特性
  - 快速开始指南
  - API参考
  - 使用示例
  - 环境变量配置
  - 跨平台兼容性说明
  - 故障排除
  - 最佳实践
- **适用**: 所有用户的主要参考文档

### 6. QUICKSTART.md
**快速开始指南** - 5分钟上手

- **大小**: ~6KB
- **内容**:
  - 最简单的使用方法
  - 常见使用场景代码
  - 配置选项说明
  - 最佳实践建议
  - 性能提示
- **适用**: 想快速上手的用户

### 7. MACOS_COMPATIBILITY.md
**macOS兼容性总结文档**

- **大小**: ~6KB
- **内容**:
  - 问题报告和根本原因
  - 详细的解决方案
  - 修改文件列表
  - 验证测试方法
  - 跨平台兼容性表格
  - 最佳实践和调试技巧
- **适用**: macOS用户或遇到pickle错误的用户

### 8. MACOS_FIX.md
**macOS兼容性技术文档**

- **大小**: ~3KB
- **内容**:
  - 技术问题描述
  - 原因分析（fork vs spawn）
  - 代码修复前后对比
  - multiprocessing启动方法说明
  - 参考资料链接
- **适用**: 想了解技术细节的开发者

### 9. CHANGELOG.md
**版本变更记录**

- **大小**: ~2KB
- **内容**:
  - v1.0.1: macOS兼容性修复
  - v1.0.0: 初始版本
  - 遵循语义化版本规范
- **适用**: 想了解版本历史的用户

## 📊 文件关系图

```
logger_manager/
│
├── 核心实现
│   └── logger_manager.py ⭐ (必需)
│
├── 测试验证
│   ├── test_logger_manager.py (单元测试)
│   ├── example_usage.py (示例程序)
│   └── quick_test_macos.py (快速测试)
│
└── 文档
    ├── README.md ⭐ (主文档)
    ├── QUICKSTART.md (快速指南)
    ├── MACOS_COMPATIBILITY.md (macOS总结)
    ├── MACOS_FIX.md (技术细节)
    └── CHANGELOG.md (版本历史)
```

## 🎯 如何使用这些文件

### 最小安装（只想使用功能）
只需要：
- ✅ `logger_manager.py`

### 推荐安装（想了解和测试）
需要：
- ✅ `logger_manager.py`
- ✅ `README.md`
- ✅ `test_logger_manager.py`
- ✅ `example_usage.py`

### 完整安装（想深入了解）
所有9个文件

### macOS用户特别推荐
- ✅ `logger_manager.py`
- ✅ `README.md`
- ✅ `MACOS_COMPATIBILITY.md`
- ✅ `quick_test_macos.py`

## 📝 文件大小总览

| 文件 | 大小 | 类型 |
|------|------|------|
| logger_manager.py | ~10KB | Python代码 |
| test_logger_manager.py | ~7KB | Python测试 |
| example_usage.py | ~6KB | Python示例 |
| quick_test_macos.py | ~4KB | Python测试 |
| README.md | ~7KB | Markdown文档 |
| QUICKSTART.md | ~6KB | Markdown文档 |
| MACOS_COMPATIBILITY.md | ~6KB | Markdown文档 |
| MACOS_FIX.md | ~3KB | Markdown文档 |
| CHANGELOG.md | ~2KB | Markdown文档 |
| **总计** | **~51KB** | - |

所有文件加起来只有约51KB，非常轻量！

## 🚀 推荐阅读顺序

### 对于新用户
1. `README.md` - 了解项目
2. `QUICKSTART.md` - 快速上手
3. `example_usage.py` - 查看示例
4. `test_logger_manager.py` - 了解功能

### 对于macOS用户（遇到错误）
1. `MACOS_COMPATIBILITY.md` - 问题总结
2. `quick_test_macos.py` - 快速验证
3. `MACOS_FIX.md` - 技术细节（可选）

### 对于贡献者
1. `README.md` - 项目概览
2. `logger_manager.py` - 核心代码
3. `test_logger_manager.py` - 测试用例
4. `CHANGELOG.md` - 版本历史

## ✨ 下一步

1. **开始使用**: 复制 `logger_manager.py` 到你的项目
2. **快速测试**: 运行 `quick_test_macos.py` (macOS) 或 `test_logger_manager.py`
3. **查看示例**: 运行 `example_usage.py`
4. **阅读文档**: 参考 `README.md` 和 `QUICKSTART.md`

祝使用愉快！🎉
