# PDF章节拆分工具

## 🎯 项目概述

一个用于将大型PDF文件按章节拆分的工具，特别针对：
- 大文件（50MB以上）
- 无原始目录的PDF
- 扫描件PDF（后续版本支持）

## 🚀 Sprint 1: 基础功能完成

### **已完成功能**:
- ✅ 基础PDF拆分功能
- ✅ 大文件流式处理（避免内存溢出）
- ✅ 按固定页数拆分章节
- ✅ 基本的错误处理和日志
- ✅ 命令行接口

### **技术特点**:
- **轻量级依赖**: 仅需PyPDF2
- **内存优化**: 流式处理大文件
- **简单易用**: 清晰的命令行接口
- **可扩展**: 模块化设计，便于后续增强

## 📋 快速开始

### 安装依赖
```bash
pip install -r requirements_pdf_splitter.txt
```

### 基本使用
```bash
# 基本拆分（每20页一个章节）
python pdf_chapter_splitter_v1.py -i input.pdf -o output_dir

# 自定义章节页数
python pdf_chapter_splitter_v1.py -i input.pdf -o output_dir --pages 30

# 流式处理（适用于大文件）
python pdf_chapter_splitter_v1.py -i large.pdf -o chapters --streaming --chunk-size 100
```

### 参数说明
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入PDF文件路径 | **必填** |
| `--output` | `-o` | 输出目录路径 | `./pdf_chapters` |
| `--pages` | `-p` | 每个章节的页数 | `20` |
| `--streaming` | `-s` | 使用流式处理模式 | `False` |
| `--chunk-size` | `-c` | 流式处理的块大小 | `50` |

## 🔧 功能说明

### 1. 基础拆分模式
- 一次性读取整个PDF文件
- 按固定页数拆分章节
- 适用于中小型文件（<50MB）

### 2. 流式处理模式
- 分块读取PDF文件，控制内存使用
- 适用于大型文件（50MB+）
- 可配置块大小优化性能

### 3. 输出格式
生成的章节文件命名格式：
```
原始文件名_chapter_001.pdf
原始文件名_chapter_002.pdf
原始文件名_chapter_003.pdf
...
```

## 📁 文件结构

```
/workspaces/RickyGB/
├── pdf_chapter_splitter_v1.py      # 主脚本 (Sprint 1)
├── requirements_pdf_splitter.txt   # 依赖文件
├── test_pdf_splitter.py           # 测试脚本
├── README_PDF_SPLITTER.md         # 本文档
└── test_pdf_files/                # 测试文件目录（可选）
```

## 🧪 测试

### 运行测试
```bash
# 基本功能测试
python test_pdf_splitter.py

# 实际PDF测试（需要PDF文件）
# 1. 将PDF文件放入 test_pdf_files/ 目录
# 2. 运行测试脚本
```

### 测试步骤
1. 验证脚本基本功能
2. 检查依赖包安装
3. 使用实际PDF文件测试拆分功能
4. 验证输出文件完整性

## 📊 性能考虑

### 内存使用
- **标准模式**: 一次性加载整个PDF到内存
- **流式模式**: 分块加载，每块默认50页
- **建议**: 50MB以上文件使用流式模式

### 处理时间
- 与PDF文件大小和页数成正比
- 流式模式稍慢但更稳定
- 进度信息显示处理状态

## 🐛 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 手动安装核心依赖
pip install PyPDF2
```

#### 2. 内存不足错误
```bash
# 使用流式处理模式
python pdf_chapter_splitter_v1.py -i large.pdf --streaming

# 减小块大小
python pdf_chapter_splitter_v1.py -i large.pdf --streaming --chunk-size 20
```

#### 3. 输出目录权限问题
```bash
# 确保有写入权限
mkdir -p output_dir
chmod 755 output_dir
```

#### 4. PDF文件损坏
- 验证PDF文件是否可以正常打开
- 尝试使用其他PDF阅读器打开
- 检查文件完整性

### 错误信息
- **"输入文件不存在"**: 检查文件路径
- **"文件不是PDF格式"**: 确保文件扩展名为.pdf
- **"需要安装PyPDF2库"**: 安装依赖包
- **"PDF文件没有页面"**: PDF文件可能损坏

## 🔄 开发路线图 (Scrum方式完成)

### Sprint 1: 基础PDF拆分功能 ✅
- ✅ 基础PDF拆分（按固定页数）
- ✅ 大文件流式处理（避免内存溢出）
- ✅ 命令行接口和基本错误处理
- **文件**: `pdf_chapter_splitter_v1.py`

### Sprint 2.1: OCR基础集成 ✅
- ✅ OCR模块创建 (`pdf_ocr_module.py`)
- ✅ PDF类型检测功能
- ✅ OCR命令行集成
- **文件**: `pdf_chapter_splitter_v2.py`

### Sprint 2.2: 扫描件检测改进 ✅
- ✅ 改进的扫描件检测算法
- ✅ 基础图像预处理
- ✅ 详细PDF分析报告
- ✅ 智能操作建议
- **文件**: 更新 `pdf_ocr_module.py` 和 `pdf_chapter_splitter_v2.py`

### Sprint 2.3: 完整OCR处理流程 ✅
- ✅ OCR完整处理器 (`pdf_ocr_processor.py`)
- ✅ 端到端OCR处理流程
- ✅ 智能模式选择（文本/扫描件）
- ✅ 完整的最终版本工具
- **文件**: `pdf_chapter_splitter_final.py`

## 🚀 可用工具版本

### 1. 基础版本 (Sprint 1)
```bash
python pdf_chapter_splitter_v1.py -i input.pdf -o output_dir
```
- 基础PDF拆分功能
- 大文件流式处理
- 简单易用

### 2. OCR集成版本 (Sprint 2.1-2.2)
```bash
# 检测PDF类型
python pdf_chapter_splitter_v2.py -i input.pdf --detect-type --detailed

# 启用OCR处理
python pdf_chapter_splitter_v2.py -i scanned.pdf -o output --ocr

# 测试OCR功能
python pdf_chapter_splitter_v2.py -i test.pdf --ocr-test --ocr
```
- OCR基础集成
- 详细PDF分析
- 图像预处理

### 3. 最终版本 (Sprint 2.3)
```bash
# 智能处理（自动检测类型）
python pdf_chapter_splitter_final.py -i input.pdf -o output

# 强制OCR模式
python pdf_chapter_splitter_final.py -i document.pdf -o output --ocr --force-ocr

# 完整工作流程
python pdf_chapter_splitter_final.py -i scanned.pdf -o output --ocr --ocr-lang eng+chi_sim
```
- 完整OCR处理流程
- 智能模式选择
- 详细处理报告
- 批量处理支持

## 📝 使用示例

### 示例1: 拆分技术文档
```bash
# 技术文档通常每章约30页
python pdf_chapter_splitter_v1.py \
  -i technical_manual.pdf \
  -o manual_chapters \
  --pages 30 \
  --streaming
```

### 示例2: 拆分扫描版书籍
```bash
# 扫描件通常文件较大，使用流式处理
python pdf_chapter_splitter_v1.py \
  -i scanned_book.pdf \
  -o book_chapters \
  --pages 25 \
  --streaming \
  --chunk-size 30
```

### 示例3: 快速测试
```bash
# 快速拆分，每10页一个章节
python pdf_chapter_splitter_v1.py \
  -i test.pdf \
  -o test_output \
  --pages 10
```

## 🎯 设计原则

### 1. 渐进增强
- 每个Sprint增加有限功能
- 确保每个版本都可工作
- 逐步解决复杂问题

### 2. 实用主义
- 优先解决核心需求
- 避免过度设计
- 保持代码简单

### 3. 可扩展性
- 模块化设计
- 清晰的接口
- 便于后续增强

## 📄 许可证

MIT License

## 🤝 贡献

### 报告问题
1. 描述具体问题
2. 提供PDF文件示例（如可能）
3. 包含错误信息和环境信息

### 功能建议
1. 描述使用场景
2. 说明预期行为
3. 提供参考实现（如可能）

## 🔗 相关项目

- [PyPDF2](https://github.com/py-pdf/PyPDF2) - PDF处理库
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF文本提取
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR库（后续使用）

---

**Sprint 1 已完成！基础PDF拆分功能可用。** 🚀