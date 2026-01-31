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

## 版本历史

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