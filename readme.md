# XLSX to Markdown Converter

一个将Excel文件转换为Markdown格式的工具，方便导入大模型作为基础数据，同时也便于查看。

## 功能特点

- 支持 `.xlsx` 和 `.xls` 文件格式
- 处理多个sheet页
- 处理合并单元格
- 支持大文件分块处理
- 生成结构化的Markdown文档
- 保留原始数据格式信息

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
# 转换单个文件
python xlsx2md.py --input data.xlsx --output data.md

# 转换目录下所有Excel文件
python xlsx2md.py --dir ./excel_files --output_dir ./markdown_files

# 查看帮助
python xlsx2md.py --help
```

## 输出格式

生成的Markdown文件包含：
- 文件元信息
- 每个sheet页的独立表格
- 合并单元格的标记
- 数据类型的说明
- 分页导航（对于大文件）