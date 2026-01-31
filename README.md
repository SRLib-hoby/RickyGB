# XLSX to Markdown Converter

一个将Excel文件转换为Markdown格式的工具，方便导入大模型作为基础数据，同时也便于查看。

## 🎯 最新更新 (2026-01-31)

### 🔧 修复内容
1. **修复xls文件转换问题** - 智能引擎选择，自动处理格式兼容性问题
2. **增加幂等检测功能** - 自动跳过已转换的文件，避免重复工作
3. **添加Force选项** - 支持强制重新转换所有文件
4. **改进错误处理** - 更清晰的错误信息和调试输出

### 🚀 新功能
- ✅ 智能引擎选择：根据文件扩展名自动选择最佳引擎
- ✅ 幂等检测：通过文件名匹配自动跳过已转换文件
- ✅ Force选项：`-f`参数强制重新转换
- ✅ 支持更多格式：`.xlsx`, `.xls`, `.xlsm`, `.xlsb`

## 功能特点

- 支持 `.xlsx`, `.xls`, `.xlsm`, `.xlsb` 文件格式
- 智能引擎选择：自动处理格式兼容性问题
- 幂等检测：避免重复转换相同文件
- 处理多个sheet页
- 支持大文件分块处理（可配置分块大小）
- 生成结构化的Markdown文档
- 保留原始数据格式信息
- 支持强制重新转换（Force模式）

## 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装所需包：

```bash
pip install pandas openpyxl xlrd tqdm
```

## 使用方法

### 基本用法
```bash
# 转换单个文件
python xlsx2md.py --input data.xlsx --output data.md

# 转换目录下所有Excel文件
python xlsx2md.py --dir ./excel_files --output_dir ./markdown_files

# 强制重新转换（忽略幂等检测）
python xlsx2md.py --dir ./excel_files --output_dir ./markdown_files --force

# 查看帮助
python xlsx2md.py --help
```

### 参数说明
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 单个输入文件路径 | - |
| `--output` | `-o` | 单个输出文件路径 | - |
| `--dir` | `-d` | 输入目录路径 | - |
| `--output_dir` | `-od` | 输出目录路径 | `./markdown_output` |
| `--force` | `-f` | 强制重新转换 | `False` |
| `--chunk_size` | `-c` | 分块处理的行数 | `1000` |
| `--max_rows` | `-m` | 每个Markdown页面的最大行数 | `500` |

### 使用示例

#### 示例1：转换整个目录
```bash
# 第一次转换 - 所有文件都会被转换
python xlsx2md.py -d ./data -od ./output

# 第二次转换 - 已转换的文件会被自动跳过
python xlsx2md.py -d ./data -od ./output
# 输出: ✓ 检测到已转换文件: data.xlsx，跳过
```

#### 示例2：强制重新转换
```bash
# 强制重新转换所有文件（忽略幂等检测）
python xlsx2md.py -d ./data -od ./output -f
```

#### 示例3：转换单个文件
```bash
# 转换单个.xlsx文件
python xlsx2md.py -i data.xlsx -o data.md

# 转换单个.xls文件
python xlsx2md.py -i old_data.xls -o old_data.md
```

## 输出格式

生成的Markdown文件包含：

### 1. 文件元信息
- 源文件名和路径
- 转换时间戳
- 文件哈希值（用于幂等检测）
- Sheet页数量统计

### 2. 每个sheet页的独立表格
- 完整的表格数据
- 分页处理（超过500行自动分页）
- 保留原始数据格式

### 3. 文件摘要（JSON格式）
```json
{
  "file_name": "data.xlsx",
  "file_hash": "abc123...",
  "total_sheets": 3,
  "conversion_time": "2026-01-31 12:00:00",
  "sheets_info": {
    "Sheet1": {
      "rows": 100,
      "columns": 5,
      "column_names": ["ID", "Name", "Value", "Date", "Notes"]
    }
  }
}
```

### 4. 智能引擎选择日志
- 显示使用的引擎（openpyxl/xlrd）
- 读取sheet页的统计信息
- 错误处理和重试信息

## 技术细节

### 引擎选择逻辑
```python
if 文件扩展名 == '.xlsx':
    尝试: openpyxl → xlrd
elif 文件扩展名 == '.xls':
    尝试: xlrd → openpyxl
else:
    尝试: openpyxl → xlrd
```

### 幂等检测机制
1. 检查输出文件是否存在
2. 搜索源文件名（多种格式匹配）
3. 验证JSON摘要中的文件信息
4. 如果检测到已转换，显示跳过消息

### 错误处理
- 清晰的错误消息和调试信息
- 引擎失败时的自动重试
- 支持多种文件格式的兼容性处理

## 常见问题

### Q: .xls文件转换失败怎么办？
A: 工具会自动尝试多种引擎。如果xlrd失败，会自动尝试openpyxl。

### Q: 如何强制重新转换已存在的文件？
A: 使用 `-f` 或 `--force` 参数。

### Q: 转换大文件时内存不足？
A: 使用 `-c` 参数调整分块大小，或使用 `-m` 参数调整每页最大行数。

### Q: 如何跳过已转换的文件？
A: 默认启用幂等检测，第二次运行时会自动跳过已转换的文件。

## 🆕 Clawdbot网关心跳检测系统

### 概述
一个用于监控Clawdbot网关活跃状态的心跳检测系统，特别适用于GitHub Codespace环境，防止网关自动停止。

### 功能特点
- ✅ **定时心跳检测** - 每5分钟自动发送测试消息
- ✅ **三级重试机制** - 30秒 → 40秒 → 50秒逐步重试
- ✅ **自动重启网关** - 所有重试失败后自动重启网关
- ✅ **容器环境优化** - 专为GitHub Codespace设计
- ✅ **完整日志系统** - 详细的运行记录和错误日志

### 快速开始
```bash
# 1. 设置权限
chmod +x setup_heartbeat.sh

# 2. 运行安装脚本
./setup_heartbeat.sh

# 3. 启动服务（容器环境）
./run_heartbeat_background.sh start

# 4. 检查状态
./run_heartbeat_background.sh status
```

### 管理命令
```bash
# 启动服务
./run_heartbeat_background.sh start

# 停止服务
./run_heartbeat_background.sh stop

# 重启服务
./run_heartbeat_background.sh restart

# 查看状态
./run_heartbeat_background.sh status

# 查看日志
./run_heartbeat_background.sh logs

# 单次测试
./run_heartbeat_background.sh test
```

### 检测逻辑
```
每5分钟发送心跳消息 → 等待30秒 → 检查网关响应
    ↓ (无响应)
发送第二次 → 等待40秒 → 检查响应
    ↓ (无响应)  
发送第三次 → 等待50秒 → 检查响应
    ↓ (无响应)
自动重启网关 → 验证重启结果
```

### 文件说明
- `gateway_heartbeat.py` - 主检测脚本
- `run_heartbeat_background.sh` - 容器环境管理脚本
- `setup_heartbeat.sh` - 安装脚本
- `README_HEARTBEAT.md` - 详细使用文档
- `heartbeat_config.json` - 配置文件模板

### 日志位置
```
~/.clawdbot/logs/
├── gateway_heartbeat.log          # 主日志文件
├── heartbeat-background.log       # 后台进程日志
└── heartbeat-service.log          # 服务日志（如果可用）
```

## 🆕 PDF章节拆分工具 (Sprint 1完成)

### 概述
一个用于将大型PDF文件按章节拆分的工具，特别针对大文件、无目录PDF和扫描件。

### Sprint 1完成功能
- ✅ **基础PDF拆分** - 按固定页数拆分章节
- ✅ **大文件流式处理** - 支持50MB+文件，避免内存溢出
- ✅ **命令行接口** - 简单易用的参数配置
- ✅ **基本错误处理** - 清晰的错误信息和日志

### 快速开始
```bash
# 安装依赖
pip install -r requirements_pdf_splitter.txt

# 基本使用
python pdf_chapter_splitter_v1.py -i input.pdf -o output_dir

# 流式处理（大文件）
python pdf_chapter_splitter_v1.py -i large.pdf -o chapters --streaming
```

### 详细文档
- [README_PDF_SPLITTER.md](README_PDF_SPLITTER.md) - 完整使用指南
- `test_pdf_splitter.py` - 测试脚本
- `requirements_pdf_splitter.txt` - 依赖文件

### 开发路线
- **Sprint 1** (已完成): 基础拆分功能
- **Sprint 2** (计划中): OCR扫描件支持
- **Sprint 3** (计划中): 智能章节检测
- **Sprint 4** (计划中): 高级功能和优化

## 版本历史

### v1.2.0 (2026-01-31) - 新增
- 添加Clawdbot网关心跳检测系统
- 支持三级重试机制和自动重启
- 优化容器环境适配

### v1.1.0 (2026-01-31)
- 修复xls文件转换问题
- 增加幂等检测功能
- 添加Force选项支持
- 改进错误处理和日志输出

### v1.0.0 (初始版本)
- 基本Excel转Markdown功能
- 支持.xlsx和.xls格式
- 分块处理大文件
- 多sheet页支持

## 许可证

MIT License