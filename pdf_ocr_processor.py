#!/usr/bin/env python3
"""
PDF OCR完整处理器 - Sprint 2.3
实现端到端的OCR处理流程
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOCRProcessor:
    """PDF OCR完整处理器 - 端到端流程"""
    
    def __init__(self, lang='eng+chi_sim', enable_preprocessing=True, dpi=200):
        """
        初始化OCR处理器
        
        Args:
            lang: OCR语言
            enable_preprocessing: 是否启用图像预处理
            dpi: OCR图像分辨率
        """
        self.lang = lang
        self.enable_preprocessing = enable_preprocessing
        self.dpi = dpi
        
        # 导入OCR模块
        try:
            from pdf_ocr_module import PDFOCR
            self.ocr = PDFOCR(lang=lang, enable_preprocessing=enable_preprocessing)
            self.ocr_available = self.ocr.is_ocr_available()
            logger.info(f"✅ OCR处理器初始化成功，语言: {lang}")
        except ImportError:
            self.ocr = None
            self.ocr_available = False
            logger.warning("⚠️  OCR模块不可用")
    
    def is_available(self):
        """检查OCR功能是否可用"""
        return self.ocr_available
    
    def process_scanned_pdf(self, pdf_path, output_dir=None, pages_per_chapter=20, 
                           sample_pages=3, progress_callback=None):
        """
        处理扫描件PDF - 完整流程
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录（如为None则只分析不拆分）
            pages_per_chapter: 每章节页数
            sample_pages: 采样分析页数
            progress_callback: 进度回调函数
            
        Returns:
            dict: 处理结果
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)
        
        if not self.is_available():
            logger.error("OCR功能不可用，无法处理扫描件")
            return {'success': False, 'error': 'OCR功能不可用'}
        
        if not pdf_path.exists():
            logger.error(f"PDF文件不存在: {pdf_path}")
            return {'success': False, 'error': '文件不存在'}
        
        logger.info(f"🚀 开始处理扫描件PDF: {pdf_path.name}")
        logger.info(f"   语言: {self.lang}")
        logger.info(f"   预处理: {'启用' if self.enable_preprocessing else '禁用'}")
        logger.info(f"   分辨率: {self.dpi} DPI")
        
        # 步骤1: 分析PDF
        if progress_callback:
            progress_callback(0, "分析PDF类型...")
        
        analysis = self.ocr.analyze_scanned_document(pdf_path, sample_pages)
        scanned_prob = analysis.get('is_scanned_probability', 0)
        
        logger.info(f"📊 分析结果: 扫描件概率 {scanned_prob:.1%}")
        
        if scanned_prob < 0.3:
            logger.warning("⚠️  扫描件概率较低，建议使用文本模式处理")
        
        # 步骤2: 获取PDF信息
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                logger.info(f"📄 PDF信息: {total_pages} 页")
        except Exception as e:
            logger.error(f"获取PDF信息失败: {e}")
            return {'success': False, 'error': f'PDF读取失败: {e}'}
        
        # 如果不需要拆分，只返回分析结果
        if output_dir is None:
            elapsed = time.time() - start_time
            return {
                'success': True,
                'analysis': analysis,
                'total_pages': total_pages,
                'processing_time': elapsed,
                'action': 'analysis_only'
            }
        
        # 步骤3: 准备输出目录
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 步骤4: OCR处理并拆分
        if progress_callback:
            progress_callback(10, "开始OCR处理...")
        
        chapters = []
        chapter_texts = []  # 存储每章节的OCR文本
        
        try:
            # 分章节处理
            num_chapters = (total_pages + pages_per_chapter - 1) // pages_per_chapter
            
            for chapter_idx in range(num_chapters):
                start_page = chapter_idx * pages_per_chapter
                end_page = min(start_page + pages_per_chapter, total_pages)
                
                if progress_callback:
                    progress = 10 + (chapter_idx / num_chapters) * 80
                    progress_callback(int(progress), f"处理第 {chapter_idx + 1}/{num_chapters} 章...")
                
                logger.info(f"处理第 {chapter_idx + 1} 章: 页 {start_page + 1}-{end_page}")
                
                # 提取本章节的OCR文本
                chapter_text = ""
                for page_num in range(start_page, end_page):
                    try:
                        # 使用带预处理的OCR提取
                        page_text = self.ocr.extract_text_with_preprocessing(pdf_path, page_num)
                        if page_text:
                            chapter_text += f"\n--- 第 {page_num + 1} 页 ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"第 {page_num + 1} 页OCR失败: {e}")
                        chapter_text += f"\n--- 第 {page_num + 1} 页 [OCR失败] ---\n"
                
                chapter_texts.append(chapter_text)
                
                # 保存章节文本
                text_filename = f"{pdf_path.stem}_chapter_{chapter_idx + 1:03d}.txt"
                text_path = output_dir / text_filename
                
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(chapter_text)
                
                logger.info(f"  保存文本: {text_filename} ({len(chapter_text)} 字符)")
                
                # 创建章节PDF（使用原始PDF页面）
                try:
                    import PyPDF2
                    with open(pdf_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        chapter_pdf = PyPDF2.PdfWriter()
                        
                        for page_num in range(start_page, end_page):
                            page = pdf_reader.pages[page_num]
                            chapter_pdf.add_page(page)
                        
                        pdf_filename = f"{pdf_path.stem}_chapter_{chapter_idx + 1:03d}.pdf"
                        pdf_path_out = output_dir / pdf_filename
                        
                        with open(pdf_path_out, 'wb') as pdf_file:
                            chapter_pdf.write(pdf_file)
                        
                        chapters.append(str(pdf_path_out))
                        logger.info(f"  保存PDF: {pdf_filename}")
                        
                except Exception as e:
                    logger.error(f"创建章节PDF失败: {e}")
                    # 继续处理，至少保存了文本
            
            # 步骤5: 生成处理报告
            if progress_callback:
                progress_callback(95, "生成报告...")
            
            # 统计信息
            total_text_chars = sum(len(text) for text in chapter_texts)
            avg_chars_per_page = total_text_chars / total_pages if total_pages > 0 else 0
            
            report = {
                'pdf_name': pdf_path.name,
                'total_pages': total_pages,
                'chapters_created': len(chapters),
                'pages_per_chapter': pages_per_chapter,
                'total_text_chars': total_text_chars,
                'avg_chars_per_page': avg_chars_per_page,
                'scanned_probability': scanned_prob,
                'output_dir': str(output_dir),
                'text_files': [str(output_dir / f"{pdf_path.stem}_chapter_{i+1:03d}.txt") 
                              for i in range(len(chapter_texts))],
                'pdf_files': chapters,
                'processing_time': time.time() - start_time
            }
            
            # 保存报告
            report_filename = f"{pdf_path.stem}_ocr_report.json"
            report_path = output_dir / report_filename
            
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📋 处理报告: {report_filename}")
            
            if progress_callback:
                progress_callback(100, "处理完成!")
            
            logger.info(f"✅ 扫描件PDF处理完成!")
            logger.info(f"   处理时间: {report['processing_time']:.1f} 秒")
            logger.info(f"   生成章节: {len(chapters)}")
            logger.info(f"   总文本字符: {total_text_chars}")
            logger.info(f"   输出目录: {output_dir}")
            
            report['success'] = True
            return report
            
        except Exception as e:
            logger.error(f"处理扫描件PDF时出错: {e}")
            return {'success': False, 'error': str(e)}
    
    def batch_process(self, pdf_files, output_base_dir, **kwargs):
        """
        批量处理多个PDF文件
        
        Args:
            pdf_files: PDF文件路径列表
            output_base_dir: 输出基础目录
            **kwargs: 传递给process_scanned_pdf的参数
            
        Returns:
            dict: 批量处理结果
        """
        output_base_dir = Path(output_base_dir)
        output_base_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            'total_files': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'details': [],
            'start_time': datetime.now().isoformat()
        }
        
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                logger.error(f"文件不存在: {pdf_path}")
                results['details'].append({
                    'file': str(pdf_path),
                    'success': False,
                    'error': '文件不存在'
                })
                results['failed'] += 1
                continue
            
            logger.info(f"处理文件 {i+1}/{len(pdf_files)}: {pdf_path.name}")
            
            # 为每个文件创建单独的输出目录
            file_output_dir = output_base_dir / pdf_path.stem
            file_output_dir.mkdir(exist_ok=True)
            
            try:
                result = self.process_scanned_pdf(
                    pdf_path, 
                    output_dir=file_output_dir,
                    **kwargs
                )
                
                if result.get('success', False):
                    results['successful'] += 1
                    logger.info(f"✅ 处理成功: {pdf_path.name}")
                else:
                    results['failed'] += 1
                    logger.error(f"❌ 处理失败: {pdf_path.name}")
                
                result['file'] = str(pdf_path)
                results['details'].append(result)
                
            except Exception as e:
                logger.error(f"处理文件时出错 {pdf_path.name}: {e}")
                results['details'].append({
                    'file': str(pdf_path),
                    'success': False,
                    'error': str(e)
                })
                results['failed'] += 1
        
        results['end_time'] = datetime.now().isoformat()
        
        # 保存批量处理报告
        report_path = output_base_dir / 'batch_processing_report.json'
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 批量处理完成:")
        logger.info(f"   总文件: {results['total_files']}")
        logger.info(f"   成功: {results['successful']}")
        logger.info(f"   失败: {results['failed']}")
        logger.info(f"   报告: {report_path}")
        
        return results

def test_ocr_processor():
    """测试OCR处理器"""
    print("🧪 测试OCR完整处理器")
    
    processor = PDFOCRProcessor()
    
    if not processor.is_available():
        print("❌ OCR功能不可用")
        print("请安装依赖: pip install pytesseract pdf2image Pillow PyPDF2")
        return False
    
    print("✅ OCR处理器初始化成功")
    
    # 检查测试PDF
    test_dir = Path("test_pdf_files")
    if test_dir.exists():
        pdf_files = list(test_dir.glob("*.pdf"))
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"\n📋 找到测试PDF: {test_pdf.name}")
            print("运行完整处理测试:")
            print(f"  python pdf_chapter_splitter_final.py -i {test_pdf} --ocr-full")
        else:
            print("\n📋 测试目录中没有PDF文件")
    else:
        print("\n📋 测试目录不存在")
    
    return True

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF OCR完整处理器')
    parser.add_argument('--test', action='store_true', help='测试OCR功能')
    parser.add_argument('--pdf', type=str, help='PDF文件路径')
    parser.add_argument('--output', '-o', type=str, help='输出目录')
    parser.add_argument('--pages', '-p', type=int, default=20, help='每章节页数')
    parser.add_argument('--lang', type=str, default='eng+chi_sim', help='OCR语言')
    
    args = parser.parse_args()
    
    if args.test:
        test_ocr_processor()
        return
    
    if args.pdf and args.output:
        processor = PDFOCRProcessor(lang=args.lang)
        
        if not processor.is_available():
            print("❌ OCR功能不可用")
            print("请安装依赖: pip install pytesseract pdf2image Pillow")
            return
        
        print(f"🚀 开始处理: {args.pdf}")
        print(f"   输出到: {args.output}")
        print(f"   语言: {args.lang}")
        print(f"   每章节页数: {args.pages}")
        
        def progress_callback(percent, message):
            print(f"进度: {percent}% - {message}")
        
        result = processor.process_scanned_pdf(
            args.pdf,
            args.output,
            pages_per_chapter=args.pages,
            progress_callback=progress_callback
        )
        
        if result.get('success', False):
            print(f"\n✅ 处理成功!")
            print(f"   章节数: {result.get('chapters_created', 0)}")
            print(f"   处理时间: {result.get('processing_time', 0):.1f}秒")
            print(f"   输出目录: {result.get('output_dir', '')}")
        else:
            print(f"\n❌ 处理失败: {result.get('error', '未知错误')}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()