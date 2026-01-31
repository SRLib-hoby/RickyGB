#!/usr/bin/env python3
"""
XLSX to Markdown Converter
将Excel文件转换为Markdown格式，便于导入大模型和查看。
修复版本：支持.xls文件并增加幂等检测
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
from tqdm import tqdm
import json
import hashlib

warnings.filterwarnings('ignore')


class ExcelToMarkdownConverter:
    """Excel文件转Markdown转换器 - 修复版本"""

    def __init__(self, chunk_size: int = 1000, max_rows_per_page: int = 500):
        """
        初始化转换器

        Args:
            chunk_size: 分块处理的行数
            max_rows_per_page: 每个Markdown页面的最大行数
        """
        self.chunk_size = chunk_size
        self.max_rows_per_page = max_rows_per_page

    def get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名"""
        return Path(file_path).suffix.lower()

    def get_engine_for_file(self, file_path: str) -> str:
        """根据文件扩展名获取合适的引擎"""
        ext = self.get_file_extension(file_path)

        if ext == '.xlsx':
            return 'openpyxl'
        elif ext == '.xls':
            # 尝试使用xlrd引擎，如果失败则使用openpyxl
            try:
                import xlrd
                return 'xlrd'
            except ImportError:
                print("警告: xlrd未安装，尝试使用openpyxl读取.xls文件")
                return 'openpyxl'
        else:
            # 默认使用openpyxl
            return 'openpyxl'

    def read_excel_file(self, file_path: str) -> Dict:
        """
        读取Excel文件，处理多个sheet页 - 增强版本

        Args:
            file_path: Excel文件路径

        Returns:
            包含sheet名和DataFrame的字典
        """
        file_ext = self.get_file_extension(file_path)
        file_name = Path(file_path).name

        # 尝试的引擎顺序
        engines_to_try = []

        if file_ext == '.xlsx':
            engines_to_try = ['openpyxl', 'xlrd']
        elif file_ext == '.xls':
            engines_to_try = ['xlrd', 'openpyxl']
        else:
            engines_to_try = ['openpyxl', 'xlrd']

        last_error = None

        for engine in engines_to_try:
            try:
                print(f"尝试使用 {engine} 引擎读取 {file_name}...")

                # 使用当前引擎读取Excel文件
                excel_file = pd.ExcelFile(file_path, engine=engine)
                sheets = {}

                for sheet_name in excel_file.sheet_names:
                    try:
                        # 读取每个sheet页
                        df = pd.read_excel(
                            excel_file,
                            sheet_name=sheet_name,
                            dtype=str,  # 将所有数据读为字符串，保持原始格式
                            na_filter=False,  # 不将空字符串转为NaN
                            engine=engine
                        )
                        sheets[sheet_name] = df
                        print(f"  ✓ 读取sheet页: {sheet_name} ({len(df)}行×{len(df.columns)}列)")

                    except Exception as e:
                        print(f"  ✗ 读取sheet页 {sheet_name} 时出错: {e}")
                        # 尝试使用不同的参数读取
                        try:
                            df = pd.read_excel(
                                excel_file,
                                sheet_name=sheet_name,
                                dtype=object,  # 使用object类型
                                na_filter=False,
                                engine=engine
                            )
                            sheets[sheet_name] = df
                            print(f"  ✓ 使用备用参数读取sheet页: {sheet_name}")
                        except Exception as e2:
                            print(f"  ✗ 备用参数也失败: {e2}")
                            # 创建空的DataFrame
                            sheets[sheet_name] = pd.DataFrame()

                print(f"✓ 使用 {engine} 引擎成功读取 {file_name}")
                return sheets

            except Exception as e:
                last_error = e
                print(f"✗ 使用 {engine} 引擎失败: {e}")
                continue

        # 所有引擎都失败
        print(f"❌ 所有引擎都无法读取文件 {file_name}")
        print(f"最后错误: {last_error}")
        return {}

    def detect_merged_cells(self, file_path: str, sheet_name: str) -> List[Tuple]:
        """
        检测合并单元格（简化版本）
        实际应用中可能需要使用openpyxl直接读取来获取准确的合并单元格信息

        Args:
            file_path: Excel文件路径
            sheet_name: sheet页名称

        Returns:
            合并单元格的列表，格式为[(start_row, start_col, end_row, end_col), ...]
        """
        # 这里返回空列表，实际实现需要使用openpyxl
        # from openpyxl import load_workbook
        # wb = load_workbook(file_path, data_only=True)
        # ws = wb[sheet_name]
        # return ws.merged_cells.ranges
        return []

    def dataframe_to_markdown_table(self, df: pd.DataFrame,
                                   sheet_name: str = "",
                                   page_num: int = 1,
                                   total_pages: int = 1) -> str:
        """
        将DataFrame转换为Markdown表格

        Args:
            df: DataFrame数据
            sheet_name: sheet页名称
            page_num: 当前页码
            total_pages: 总页数

        Returns:
            Markdown格式的表格字符串
        """
        if df.empty:
            return f"### {sheet_name} (空表格)\n\n"

        # 获取列名
        headers = df.columns.tolist()

        # 创建Markdown表格头部
        markdown_lines = []

        # 添加标题
        if sheet_name:
            markdown_lines.append(f"## 📋 {sheet_name}")
            if total_pages > 1:
                markdown_lines.append(f"*页面 {page_num}/{total_pages}*")
            markdown_lines.append("")

        # 表格头部
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

        markdown_lines.append(header_line)
        markdown_lines.append(separator_line)

        # 添加数据行
        for _, row in df.iterrows():
            row_values = []
            for col in headers:
                value = row[col]
                # 处理NaN和None值
                if pd.isna(value) or value is None:
                    row_values.append("")
                else:
                    # 转义Markdown特殊字符
                    cell_value = str(value).replace("|", "\\|").replace("\n", "<br>")
                    row_values.append(cell_value)

            row_line = "| " + " | ".join(row_values) + " |"
            markdown_lines.append(row_line)

        markdown_lines.append("")  # 空行分隔
        return "\n".join(markdown_lines)

    def process_large_dataframe(self, df: pd.DataFrame, sheet_name: str) -> List[str]:
        """
        处理大型DataFrame，分页生成Markdown

        Args:
            df: 原始DataFrame
            sheet_name: sheet页名称

        Returns:
            分页的Markdown字符串列表
        """
        if df.empty:
            return [self.dataframe_to_markdown_table(df, sheet_name)]

        total_rows = len(df)
        if total_rows <= self.max_rows_per_page:
            return [self.dataframe_to_markdown_table(df, sheet_name)]

        # 分页处理
        pages = []
        num_pages = (total_rows + self.max_rows_per_page - 1) // self.max_rows_per_page

        for page in range(num_pages):
            start_idx = page * self.max_rows_per_page
            end_idx = min((page + 1) * self.max_rows_per_page, total_rows)
            page_df = df.iloc[start_idx:end_idx]

            page_md = self.dataframe_to_markdown_table(
                page_df, sheet_name, page + 1, num_pages
            )
            pages.append(page_md)

        return pages

    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值，用于幂等检测"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            print(f"计算文件哈希时出错: {e}")
            return ""

    def check_if_already_converted(self, input_file: Path, output_file: Path) -> bool:
        """
        检查文件是否已经转换过（幂等检测）- 增强版本
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            
        Returns:
            True: 已经转换过，无需再次转换
            False: 需要转换
        """
        # 检查输出文件是否存在
        if not output_file.exists():
            return False
        
        try:
            # 读取输出文件的元数据
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # 读取更多内容确保找到元数据
            
            input_filename = input_file.name
            input_stem = input_file.stem
            
            # 检查是否包含源文件名（多种可能的格式）
            patterns_to_check = [
                f"源文件: `{input_filename}`",
                f"**源文件:** `{input_filename}`",
                f"Excel文件转换结果: {input_filename}",
                f"# Excel文件转换结果: {input_filename}",
                f"文件名称: {input_filename}",
                f"**文件名称:** {input_filename}",
            ]
            
            for pattern in patterns_to_check:
                if pattern in content:
                    print(f"✓ 检测到已转换文件: {input_filename} (匹配模式: {pattern})")
                    return True
            
            # 检查是否包含文件名（不含扩展名）
            if input_stem and f"{input_stem}" in content:
                # 进一步确认这是正确的文件
                lines = content.split('\n')
                for line in lines[:20]:  # 只检查前20行
                    if input_filename in line or input_stem in line:
                        print(f"✓ 检测到已转换文件: {input_filename} (在内容中找到匹配)")
                        return True
            
            # 检查文件摘要中的JSON
            if '"file_name":' in content:
                import json
                import re
                # 尝试提取JSON部分
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    try:
                        summary = json.loads(json_match.group(1))
                        if summary.get('file_name') == input_filename:
                            print(f"✓ 检测到已转换文件: {input_filename} (JSON摘要匹配)")
                            return True
                    except:
                        pass
            
            return False
                
        except Exception as e:
            print(f"检查输出文件时出错: {e}")
            return False

    def convert_single_file(self, input_path: str, output_path: str, force: bool = False) -> bool:
        """
        转换单个Excel文件 - 增加幂等检测

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            force: 是否强制重新转换

        Returns:
            是否成功
        """
        try:
            input_file = Path(input_path)
            output_file = Path(output_path)

            print(f"处理文件: {input_file.name}")

            # 幂等检测：检查是否已经转换过
            if not force and self.check_if_already_converted(input_file, output_file):
                return True

            # 读取Excel文件
            sheets = self.read_excel_file(input_path)
            if not sheets:
                print(f"文件 {input_file.name} 中没有数据或读取失败")
                return False

            # 生成Markdown内容
            markdown_content = []
            markdown_content.append(f"# Excel文件转换结果: {input_file.name}")
            markdown_content.append(f"**源文件:** `{input_path}`")
            markdown_content.append(f"**转换时间:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_content.append(f"**Sheet页数量:** {len(sheets)}")

            # 添加文件哈希（用于幂等检测）
            file_hash = self.calculate_file_hash(input_path)
            if file_hash:
                markdown_content.append(f"**文件哈希:** `{file_hash}`")

            markdown_content.append("")
            markdown_content.append("---")
            markdown_content.append("")

            # 处理每个sheet页
            for sheet_name, df in tqdm(sheets.items(), desc="处理Sheet页"):
                markdown_content.append(f"## 📄 Sheet: {sheet_name}")
                markdown_content.append(f"**行数:** {len(df)}, **列数:** {len(df.columns)}")
                markdown_content.append("")

                # 分页处理大型表格
                pages = self.process_large_dataframe(df, sheet_name)
                for page in pages:
                    markdown_content.append(page)

                markdown_content.append("---")
                markdown_content.append("")

            # 添加文件摘要
            markdown_content.append("## 📊 文件摘要")
            markdown_content.append("```json")
            summary = {
                "file_name": input_file.name,
                "file_hash": file_hash,
                "total_sheets": len(sheets),
                "conversion_time": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                "sheets_info": {
                    sheet_name: {
                        "rows": len(df),
                        "columns": len(df.columns.tolist()),
                        "column_names": df.columns.tolist()
                    }
                    for sheet_name, df in sheets.items()
                }
            }
            markdown_content.append(json.dumps(summary, indent=2, ensure_ascii=False))
            markdown_content.append("```")

            # 写入输出文件
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(markdown_content))

            print(f"✓ 转换完成: {output_file}")
            return True

        except Exception as e:
            print(f"转换文件 {input_path} 时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def convert_directory(self, input_dir: str, output_dir: str, force: bool = False) -> Dict[str, bool]:
        """
        转换目录下的所有Excel文件 - 增加幂等检测

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            force: 是否强制重新转换所有文件

        Returns:
            转换结果字典 {文件名: 是否成功}
        """
        results = {}

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 查找所有Excel文件
        excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
        excel_files = []
        for ext in excel_extensions:
            excel_files.extend(Path(input_dir).glob(f"*{ext}"))

        if not excel_files:
            print(f"在目录 {input_dir} 中没有找到Excel文件")
            print(f"支持的扩展名: {', '.join(excel_extensions)}")
            return results

        print(f"找到 {len(excel_files)} 个Excel文件")

        # 处理每个文件
        for excel_file in tqdm(excel_files, desc="处理文件"):
            output_file = output_path / f"{excel_file.stem}.md"
            success = self.convert_single_file(str(excel_file), str(output_file), force)
            results[excel_file.name] = success

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将Excel文件转换为Markdown格式 - 修复版本')
    parser.add_argument('--input', '-i', type=str, help='输入Excel文件路径')
    parser.add_argument('--output', '-o', type=str, help='输出Markdown文件路径')
    parser.add_argument('--dir', '-d', type=str, help='输入目录路径（转换所有Excel文件）')
    parser.add_argument('--output_dir', '-od', type=str, default='./markdown_output',
                       help='输出目录路径（默认: ./markdown_output）')
    parser.add_argument('--chunk_size', '-c', type=int, default=1000,
                       help='分块处理的行数（默认: 1000）')
    parser.add_argument('--max_rows', '-m', type=int, default=500,
                       help='每个Markdown页面的最大行数（默认: 500）')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制重新转换，即使输出文件已存在')

    args = parser.parse_args()

    # 创建转换器
    converter = ExcelToMarkdownConverter(
        chunk_size=args.chunk_size,
        max_rows_per_page=args.max_rows
    )

    # 处理单个文件
    if args.input:
        if not args.output:
            # 自动生成输出文件名
            input_path = Path(args.input)
            args.output = f"{input_path.stem}.md"

        success = converter.convert_single_file(args.input, args.output, args.force)
        sys.exit(0 if success else 1)

    # 处理目录
    elif args.dir:
        results = converter.convert_directory(args.dir, args.output_dir, args.force)

        # 统计结果
        total = len(results)
        successful = sum(1 for success in results.values() if success)

        print(f"\n{'='*50}")
        print(f"转换完成!")
        print(f"成功: {successful}/{total}")
        print(f"失败: {total - successful}")

        if total - successful > 0:
            print("\n失败的文件:")
            for filename, success in results.items():
                if not success:
                    print(f"  - {filename}")

        sys.exit(0 if successful == total else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()