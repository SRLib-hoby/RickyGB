#!/usr/bin/env python3
"""
EPUB转Markdown工具 - Sprint 1
基础版本：EPUB解析和文本提取
"""

import os
import sys
import argparse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import html

class EPUBConverterV1:
    """EPUB转换器 - 基础版本（Sprint 1）"""
    
    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        
    def safe_read_file(self, file_path, encoding='utf-8'):
        """安全读取文件，处理编码问题"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except:
                    continue
            return f"无法读取文件: {file_path} (编码问题)"
        except Exception as e:
            return f"读取文件失败: {e}"
    
    def extract_epub_structure(self, epub_path):
        """提取EPUB基础结构（不使用ebooklib）"""
        try:
            epub_path = Path(epub_path)
            
            if not epub_path.exists():
                return {'success': False, 'error': '文件不存在'}
            
            if epub_path.suffix.lower() != '.epub':
                return {'success': False, 'error': '不是EPUB文件'}
            
            # EPUB本质是ZIP文件
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                # 获取文件列表
                file_list = epub_zip.namelist()
                
                # 查找OPF文件（内容清单）
                opf_files = [f for f in file_list if f.endswith('.opf')]
                if not opf_files:
                    return {'success': False, 'error': '找不到OPF文件'}
                
                opf_file = opf_files[0]
                
                # 读取OPF文件
                try:
                    opf_content = epub_zip.read(opf_file).decode('utf-8')
                except:
                    # 尝试其他编码
                    opf_content = epub_zip.read(opf_file).decode('latin-1')
                
                # 解析OPF文件获取元数据和内容文件
                result = {
                    'success': True,
                    'epub_file': str(epub_path),
                    'opf_file': opf_file,
                    'file_count': len(file_list),
                    'files': file_list[:20],  # 只显示前20个文件
                    'metadata': {},
                    'content_files': []
                }
                
                # 简单提取标题（从文件名）
                result['metadata']['title'] = epub_path.stem
                result['metadata']['extracted_from'] = '文件名'
                
                # 查找HTML/XML内容文件
                content_exts = ['.html', '.xhtml', '.htm', '.xml']
                for file in file_list:
                    if any(file.lower().endswith(ext) for ext in content_exts):
                        result['content_files'].append(file)
                
                return result
                
        except zipfile.BadZipFile:
            return {'success': False, 'error': '损坏的ZIP/EPUB文件'}
        except Exception as e:
            return {'success': False, 'error': f'解析失败: {e}'}
    
    def extract_text_from_epub(self, epub_path, output_dir):
        """从EPUB提取文本内容（基础版本）"""
        try:
            epub_path = Path(epub_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"处理EPUB文件: {epub_path.name}")
            
            # 提取结构信息
            structure = self.extract_epub_structure(epub_path)
            if not structure.get('success', False):
                print(f"❌ 提取结构失败: {structure.get('error', '未知错误')}")
                return {'success': False, 'error': structure.get('error')}
            
            print(f"✅ EPUB结构解析成功")
            print(f"   文件数量: {structure['file_count']}")
            print(f"   内容文件: {len(structure['content_files'])}")
            print(f"   标题: {structure['metadata']['title']}")
            
            # 创建输出文件
            output_file = output_dir / f"{epub_path.stem}_extracted.txt"
            
            with zipfile.ZipFile(epub_path, 'r') as epub_zip:
                all_text = []
                
                # 添加文件头
                all_text.append(f"# EPUB文本提取 - {structure['metadata']['title']}\n")
                all_text.append(f"源文件: {epub_path.name}\n")
                all_text.append(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                all_text.append(f"文件数量: {structure['file_count']}\n")
                all_text.append(f"内容文件: {len(structure['content_files'])}\n")
                all_text.append("=" * 80 + "\n\n")
                
                # 处理内容文件
                content_count = 0
                for i, content_file in enumerate(structure['content_files'][:50], 1):  # 限制前50个文件
                    try:
                        # 读取文件内容
                        content_bytes = epub_zip.read(content_file)
                        
                        # 尝试解码
                        try:
                            content = content_bytes.decode('utf-8')
                        except:
                            content = content_bytes.decode('latin-1', errors='ignore')
                        
                        # 简单提取文本（移除HTML标签）
                        import re
                        # 移除HTML标签
                        text = re.sub(r'<[^>]+>', ' ', content)
                        # 解码HTML实体
                        text = html.unescape(text)
                        # 合并空白字符
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        if text and len(text) > 10:  # 至少10个字符
                            all_text.append(f"## 文件 {i}: {content_file}\n")
                            all_text.append(f"长度: {len(text)} 字符\n")
                            all_text.append("-" * 40 + "\n")
                            all_text.append(text[:500] + ("..." if len(text) > 500 else ""))
                            all_text.append("\n\n")
                            content_count += 1
                            
                            if i % 10 == 0:
                                print(f"  已处理 {i}/{len(structure['content_files'])} 个内容文件")
                    
                    except Exception as e:
                        all_text.append(f"## 文件 {i}: {content_file} (处理失败)\n")
                        all_text.append(f"错误: {e}\n\n")
                
                # 写入输出文件
                output_text = ''.join(all_text)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                
                file_size = output_file.stat().st_size
                
                print(f"✅ 文本提取完成")
                print(f"   输出文件: {output_file}")
                print(f"   文件大小: {file_size:,} 字节")
                print(f"   提取内容文件: {content_count} 个")
                
                return {
                    'success': True,
                    'epub_file': str(epub_path),
                    'output_file': str(output_file),
                    'output_size': file_size,
                    'content_files_processed': content_count,
                    'total_content_files': len(structure['content_files']),
                    'title': structure['metadata']['title']
                }
                
        except Exception as e:
            print(f"❌ EPUB处理失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_directory(self, input_dir, output_dir):
        """处理目录中的所有EPUB文件"""
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        if not input_dir.exists():
            return {'success': False, 'error': '输入目录不存在'}
        
        if not input_dir.is_dir():
            return {'success': False, 'error': '输入路径不是目录'}
        
        # 查找EPUB文件
        epub_files = list(input_dir.glob("*.epub")) + list(input_dir.glob("*.EPUB"))
        
        if not epub_files:
            print(f"目录中没有EPUB文件: {input_dir}")
            return {'success': False, 'error': '没有EPUB文件'}
        
        print(f"找到 {len(epub_files)} 个EPUB文件")
        
        results = {
            'input_dir': str(input_dir),
            'output_dir': str(output_dir),
            'total_files': len(epub_files),
            'successful': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat(),
            'file_results': []
        }
        
        for i, epub_file in enumerate(epub_files, 1):
            print(f"\n处理文件 {i}/{len(epub_files)}: {epub_file.name}")
            
            # 为每个文件创建单独的输出目录
            file_output_dir = output_dir / epub_file.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            result = self.extract_text_from_epub(epub_file, file_output_dir)
            
            if result.get('success', False):
                results['successful'] += 1
                print(f"✅ 处理成功")
            else:
                results['failed'] += 1
                print(f"❌ 处理失败: {result.get('error', '未知错误')}")
            
            result['file'] = str(epub_file)
            results['file_results'].append(result)
        
        # 生成报告
        results['end_time'] = datetime.now().isoformat()
        total_time = datetime.fromisoformat(results['end_time']) - datetime.fromisoformat(results['start_time'])
        results['total_time'] = total_time.total_seconds()
        
        print(f"\n📊 批量处理完成!")
        print(f"   总文件: {results['total_files']}")
        print(f"   成功: {results['successful']}")
        print(f"   失败: {results['failed']}")
        print(f"   总时间: {results['total_time']:.1f} 秒")
        
        results['success'] = results['failed'] == 0
        return results

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试EPUB转换器基本功能")
    
    converter = EPUBConverterV1()
    
    # 检查测试目录
    test_dir = Path("test_epub_files")
    if not test_dir.exists():
        print("⚠️  测试目录不存在")
        print("   创建测试目录...")
        test_dir.mkdir(exist_ok=True)
        
        # 创建测试说明文件
        readme_file = test_dir / "README.txt"
        readme_file.write_text("""EPUB测试目录

将EPUB文件放入此目录进行测试。

示例EPUB文件可以从以下位置获取：
1. Project Gutenberg: https://www.gutenberg.org
2. 标准EPUB示例文件

注意：实际测试需要真实的EPUB文件。
""")
        
        print(f"✅ 创建测试目录: {test_dir}")
        print("   注意: 实际测试需要真实的EPUB文件")
    
    epub_files = list(test_dir.glob("*.epub")) + list(test_dir.glob("*.EPUB"))
    
    if not epub_files:
        print("⚠️  测试目录中没有EPUB文件")
        print("   跳过实际提取测试")
        return True  # 跳过不算失败
    
    print(f"找到 {len(epub_files)} 个EPUB文件")
    
    # 测试单个文件
    test_epub = epub_files[0]
    output_dir = Path("test_epub_output")
    
    print(f"\n🚀 测试单个文件提取: {test_epub.name}")
    
    result = converter.extract_text_from_epub(test_epub, output_dir)
    
    if result.get('success', False):
        print(f"✅ 单个文件测试通过")
        print(f"   输出文件: {result.get('output_file', '未知')}")
        print(f"   文件大小: {result.get('output_size', 0):,} 字节")
        return True
    else:
        print(f"❌ 单个文件测试失败: {result.get('error', '未知错误')}")
        return False

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='EPUB转文本工具 - Sprint 1 (基础版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取单个EPUB文件的文本
  python epub_to_markdown_v1.py --input book.epub --output ./extracted
  
  # 批量处理目录中的所有EPUB文件
  python epub_to_markdown_v1.py --dir ./epub_files --output ./text_output
  
  # 测试功能
  python epub_to_markdown_v1.py --test
        """
    )
    
    # 主要参数
    parser.add_argument('--input', '-i', type=str, help='输入EPUB文件路径')
    parser.add_argument('--output', '-o', type=str, default='./epub_output',
                       help='输出目录路径 (默认: ./epub_output)')
    parser.add_argument('--dir', '-d', type=str, help='输入目录路径（批量处理）')
    
    # 测试功能
    parser.add_argument('--test', action='store_true', help='测试功能')
    
    args = parser.parse_args()
    
    converter = EPUBConverterV1()
    
    if args.test:
        success = test_basic_functionality()
        return 0 if success else 1
    
    if args.input:
        # 处理单个文件
        print(f"🚀 开始提取EPUB文本: {args.input}")
        
        result = converter.extract_text_from_epub(args.input, args.output)
        
        if result.get('success', False):
            print(f"\n✅ 提取完成!")
            print(f"   输出文件: {result.get('output_file', '未知')}")
            print(f"   文件大小: {result.get('output_size', 0):,} 字节")
            print(f"   标题: {result.get('title', '未知')}")
            return 0
        else:
            print(f"\n❌ 提取失败: {result.get('error', '未知错误')}")
            return 1
    
    elif args.dir:
        # 批量处理目录
        print(f"🚀 开始批量处理目录: {args.dir}")
        
        result = converter.process_directory(args.dir, args.output)
        
        if result.get('success', False) or result.get('successful', 0) > 0:
            print(f"\n✅ 批量处理完成!")
            print(f"   总文件: {result['total_files']}")
            print(f"   成功: {result['successful']}")
            print(f"   失败: {result['failed']}")
            print(f"   总时间: {result['total_time']:.1f} 秒")
            return 0
        else:
            print(f"\n❌ 批量处理失败: {result.get('error', '未知错误')}")
            return 1
    
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())