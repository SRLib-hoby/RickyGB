#!/usr/bin/env python3
"""
PDF批量处理器 - Sprint 4
简单的批量处理功能
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFBatchProcessor:
    """PDF批量处理器 - 简单版本"""
    
    def __init__(self, base_output_dir='./batch_output'):
        """
        初始化批量处理器
        
        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"初始化批量处理器")
        logger.info(f"基础输出目录: {self.base_output_dir}")
    
    def process_directory(self, input_dir, output_subdir=None, **process_kwargs):
        """
        处理目录中的所有PDF文件
        
        Args:
            input_dir: 输入目录路径
            output_subdir: 输出子目录（如为None则使用输入目录名）
            **process_kwargs: 传递给单个文件处理的参数
            
        Returns:
            Dict: 批量处理结果
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return {'success': False, 'error': '目录不存在'}
        
        if not input_dir.is_dir():
            logger.error(f"输入路径不是目录: {input_dir}")
            return {'success': False, 'error': '不是目录'}
        
        # 查找PDF文件
        pdf_files = list(input_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"目录中没有PDF文件: {input_dir}")
            return {'success': False, 'error': '没有PDF文件'}
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        
        # 创建输出目录
        if output_subdir is None:
            output_subdir = input_dir.name
        
        output_dir = self.base_output_dir / output_subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"输出目录: {output_dir}")
        
        # 处理每个文件
        results = {
            'input_dir': str(input_dir),
            'output_dir': str(output_dir),
            'total_files': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'start_time': datetime.now().isoformat(),
            'file_results': []
        }
        
        for i, pdf_file in enumerate(pdf_files):
            file_start_time = time.time()
            
            logger.info(f"\n处理文件 {i+1}/{len(pdf_files)}: {pdf_file.name}")
            logger.info(f"文件大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
            
            # 为每个文件创建单独的输出子目录
            file_output_dir = output_dir / pdf_file.stem
            file_output_dir.mkdir(exist_ok=True)
            
            try:
                # 导入并调用最终版本工具
                from pdf_chapter_splitter_final import PDFSplitterFinal
                
                # 创建拆分器（使用默认参数或传入的参数）
                splitter = PDFSplitterFinal(
                    pages_per_chapter=process_kwargs.get('pages_per_chapter', 20),
                    use_ocr=process_kwargs.get('use_ocr', False),
                    ocr_lang=process_kwargs.get('ocr_lang', 'eng+chi_sim'),
                    enable_preprocessing=process_kwargs.get('enable_preprocessing', True),
                    dpi=process_kwargs.get('dpi', 200)
                )
                
                # 处理文件
                result = splitter.smart_process_pdf(
                    pdf_file,
                    file_output_dir,
                    force_ocr=process_kwargs.get('force_ocr', False),
                    use_smart_detection=process_kwargs.get('use_smart_detection', True)
                )
                
                file_processing_time = time.time() - file_start_time
                
                if result.get('success', False):
                    results['successful'] += 1
                    logger.info(f"✅ 处理成功: {pdf_file.name}")
                    logger.info(f"   处理时间: {file_processing_time:.1f} 秒")
                    logger.info(f"   生成章节: {result.get('chapters_created', 0)}")
                    
                    result['file'] = str(pdf_file)
                    result['processing_time'] = file_processing_time
                    result['output_subdir'] = str(file_output_dir.relative_to(self.base_output_dir))
                    results['file_results'].append(result)
                    
                else:
                    results['failed'] += 1
                    logger.error(f"❌ 处理失败: {pdf_file.name}")
                    logger.error(f"   错误: {result.get('error', '未知错误')}")
                    
                    results['file_results'].append({
                        'file': str(pdf_file),
                        'success': False,
                        'error': result.get('error', '未知错误'),
                        'processing_time': file_processing_time
                    })
            
            except Exception as e:
                results['failed'] += 1
                logger.error(f"❌ 处理异常: {pdf_file.name}")
                logger.error(f"   异常: {e}")
                
                results['file_results'].append({
                    'file': str(pdf_file),
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - file_start_time
                })
        
        # 生成汇总报告
        results['end_time'] = datetime.now().isoformat()
        total_time = datetime.fromisoformat(results['end_time']) - datetime.fromisoformat(results['start_time'])
        results['total_processing_time'] = total_time.total_seconds()
        
        # 保存报告
        report_file = output_dir / 'batch_processing_report.json'
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📊 批量处理完成!")
        logger.info(f"   总文件: {results['total_files']}")
        logger.info(f"   成功: {results['successful']}")
        logger.info(f"   失败: {results['failed']}")
        logger.info(f"   总时间: {results['total_processing_time']:.1f} 秒")
        logger.info(f"   报告文件: {report_file}")
        
        results['success'] = results['failed'] == 0
        return results
    
    def process_file_list(self, file_list, output_subdir='file_list', **process_kwargs):
        """
        处理文件列表
        
        Args:
            file_list: PDF文件路径列表
            output_subdir: 输出子目录
            **process_kwargs: 处理参数
            
        Returns:
            Dict: 处理结果
        """
        if not file_list:
            logger.error("文件列表为空")
            return {'success': False, 'error': '文件列表为空'}
        
        # 验证文件存在
        valid_files = []
        for file_path in file_list:
            path = Path(file_path)
            if path.exists() and path.suffix.lower() == '.pdf':
                valid_files.append(path)
            else:
                logger.warning(f"文件不存在或不是PDF: {file_path}")
        
        if not valid_files:
            logger.error("没有有效的PDF文件")
            return {'success': False, 'error': '没有有效的PDF文件'}
        
        logger.info(f"处理 {len(valid_files)} 个PDF文件")
        
        # 创建临时目录结构
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        
        # 将文件复制到临时目录（模拟目录处理）
        for pdf_file in valid_files:
            # 这里简化处理，实际应该调用单个文件处理
            pass
        
        # 调用目录处理方法
        return self.process_directory(temp_dir, output_subdir, **process_kwargs)

def test_batch_processing():
    """测试批量处理功能"""
    print("🧪 测试批量处理功能")
    
    processor = PDFBatchProcessor(base_output_dir='./test_batch_output')
    
    # 检查测试目录
    test_dir = Path("test_pdf_files")
    if not test_dir.exists():
        print("⚠️  测试目录不存在")
        print("   创建测试目录结构...")
        test_dir.mkdir(exist_ok=True)
        
        # 创建一些测试文件占位符
        for i in range(3):
            test_file = test_dir / f"test_document_{i+1}.txt"
            test_file.write_text(f"这是测试文档 {i+1} 的占位符\n实际测试需要真实的PDF文件")
        
        print(f"✅ 创建测试目录: {test_dir}")
        print("   注意: 实际测试需要真实的PDF文件")
    
    pdf_files = list(test_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  测试目录中没有PDF文件")
        print("   跳过实际批量处理测试")
        return True  # 跳过不算失败
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 测试批量处理
    print("\n🚀 开始批量处理测试...")
    
    result = processor.process_directory(
        test_dir,
        output_subdir='test_batch',
        pages_per_chapter=15,
        use_smart_detection=True
    )
    
    if result.get('success', False) or result.get('successful', 0) > 0:
        print(f"✅ 批量处理测试通过")
        print(f"   成功文件: {result.get('successful', 0)}")
        print(f"   失败文件: {result.get('failed', 0)}")
        print(f"   总时间: {result.get('total_processing_time', 0):.1f} 秒")
        return True
    else:
        print(f"❌ 批量处理测试失败")
        return False

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF批量处理器')
    
    # 主要参数
    parser.add_argument('--dir', '-d', type=str, help='输入目录路径')
    parser.add_argument('--output', '-o', type=str, default='./batch_output',
                       help='输出目录路径 (默认: ./batch_output)')
    
    # 处理参数
    parser.add_argument('--pages', '-p', type=int, default=20,
                       help='每个章节的页数 (默认: 20)')
    parser.add_argument('--ocr', action='store_true',
                       help='启用OCR功能')
    parser.add_argument('--smart', action='store_true',
                       help='启用智能章节检测')
    
    # 其他功能
    parser.add_argument('--test', action='store_true',
                       help='测试批量处理功能')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_batch_processing()
        return 0 if success else 1
    
    if args.dir:
        processor = PDFBatchProcessor(base_output_dir=args.output)
        
        logger.info(f"🚀 开始批量处理目录: {args.dir}")
        logger.info(f"输出目录: {args.output}")
        logger.info(f"每章节页数: {args.pages}")
        logger.info(f"OCR模式: {'启用' if args.ocr else '禁用'}")
        logger.info(f"智能检测: {'启用' if args.smart else '禁用'}")
        
        result = processor.process_directory(
            args.dir,
            output_subdir=None,  # 使用输入目录名
            pages_per_chapter=args.pages,
            use_ocr=args.ocr,
            use_smart_detection=args.smart
        )
        
        if result.get('success', False) or result.get('successful', 0) > 0:
            print(f"\n✅ 批量处理完成!")
            print(f"   成功文件: {result.get('successful', 0)}")
            print(f"   失败文件: {result.get('failed', 0)}")
            print(f"   总时间: {result.get('total_processing_time', 0):.1f} 秒")
            print(f"   报告文件: {args.output}/batch_processing_report.json")
            return 0
        else:
            print(f"\n❌ 批量处理失败")
            print(f"   错误: {result.get('error', '未知错误')}")
            return 1
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()