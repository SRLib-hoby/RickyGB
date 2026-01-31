#!/usr/bin/env python3
"""
PDF章节拆分工具 - 最终版本 (Sprint 2.3完成)
集成完整的OCR处理流程
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 设置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFSplitterFinal:
    """PDF拆分器 - 最终版本（完整OCR流程）"""
    
    def __init__(self, pages_per_chapter=20, use_ocr=False, ocr_lang='eng+chi_sim',
                 enable_preprocessing=True, dpi=200):
        """
        初始化PDF拆分器
        
        Args:
            pages_per_chapter: 每个章节的页数
            use_ocr: 是否使用OCR功能
            ocr_lang: OCR语言设置
            enable_preprocessing: 是否启用图像预处理
            dpi: OCR图像分辨率
        """
        self.pages_per_chapter = pages_per_chapter
        self.use_ocr = use_ocr
        self.ocr_lang = ocr_lang
        self.enable_preprocessing = enable_preprocessing
        self.dpi = dpi
        
        # 检查OCR可用性
        self.ocr_available = False
        self.ocr_processor = None
        
        # 检查章节检测可用性
        self.chapter_detector_available = False
        self.chapter_detector = None
        
        try:
            from pdf_chapter_detector import ChapterDetector
            self.chapter_detector = ChapterDetector(
                min_chapter_pages=max(5, pages_per_chapter // 2),
                max_chapter_pages=min(50, pages_per_chapter * 2)
            )
            self.chapter_detector_available = True
            logger.info("✅ 章节检测器初始化成功")
        except ImportError:
            logger.warning("⚠️  章节检测模块不可用，将使用固定页数")
        
        if self.use_ocr:
            try:
                from pdf_ocr_processor import PDFOCRProcessor
                self.ocr_processor = PDFOCRProcessor(
                    lang=ocr_lang,
                    enable_preprocessing=enable_preprocessing,
                    dpi=dpi
                )
                self.ocr_available = self.ocr_processor.is_available()
                
                if self.ocr_available:
                    logger.info(f"✅ OCR处理器初始化成功")
                    logger.info(f"   语言: {ocr_lang}")
                    logger.info(f"   预处理: {'启用' if enable_preprocessing else '禁用'}")
                    logger.info(f"   分辨率: {dpi} DPI")
                else:
                    logger.warning("⚠️  OCR功能不可用，将回退到基础模式")
                    self.use_ocr = False
                    
            except ImportError:
                logger.warning("⚠️  OCR模块不可用，将使用基础模式")
                self.use_ocr = False
        
        if not self.use_ocr:
            logger.info(f"初始化PDF拆分器（基础模式）")
        
        logger.info(f"每章节页数: {pages_per_chapter}")
    
    def smart_process_pdf(self, input_path, output_dir, force_ocr=False, use_smart_detection=True):
        """
        智能处理PDF - 完整流程
        
        Args:
            input_path: 输入PDF文件路径
            output_dir: 输出目录路径
            force_ocr: 强制使用OCR模式
            use_smart_detection: 是否使用智能章节检测
            
        Returns:
            dict: 处理结果
        """
        start_time = datetime.now()
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        # 验证输入文件
        if not input_path.exists():
            logger.error(f"输入文件不存在: {input_path}")
            return {'success': False, 'error': '文件不存在'}
        
        if not input_path.suffix.lower() == '.pdf':
            logger.error(f"文件不是PDF格式: {input_path}")
            return {'success': False, 'error': '不是PDF文件'}
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 开始智能处理PDF: {input_path.name}")
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"OCR模式: {'启用' if self.use_ocr else '禁用'}")
        
        # 步骤1: 检测PDF类型
        logger.info("🔍 检测PDF类型...")
        pdf_type = self.detect_pdf_type(input_path, detailed=False)
        
        # 步骤2: 决定处理模式
        use_ocr_mode = False
        
        if force_ocr:
            use_ocr_mode = True
            logger.info("强制使用OCR模式")
        elif pdf_type == 'scanned':
            use_ocr_mode = True
            logger.info("检测到扫描件，使用OCR模式")
        elif pdf_type == 'unknown' and self.use_ocr:
            use_ocr_mode = True
            logger.info("PDF类型未知，尝试OCR模式")
        else:
            logger.info("使用文本模式处理")
        
        # 步骤3: 执行处理
        if use_ocr_mode and self.ocr_available:
            # OCR处理模式
            logger.info("🔄 开始OCR处理流程...")
            
            def progress_callback(percent, message):
                logger.info(f"进度: {percent}% - {message}")
            
            result = self.ocr_processor.process_scanned_pdf(
                input_path,
                output_dir,
                pages_per_chapter=self.pages_per_chapter,
                progress_callback=progress_callback
            )
            
            if result.get('success', False):
                result['processing_mode'] = 'ocr'
                result['pdf_type'] = pdf_type
            else:
                # OCR失败，回退到基础模式
                logger.warning("OCR处理失败，回退到基础模式")
                result = self._basic_split_pdf(input_path, output_dir, use_smart_detection=use_smart_detection)
                result['processing_mode'] = 'basic_fallback'
                result['pdf_type'] = pdf_type
            
        else:
            # 基础处理模式
            logger.info("📄 使用基础拆分模式...")
            result = self._basic_split_pdf(input_path, output_dir, use_smart_detection=use_smart_detection)
            result['processing_mode'] = 'basic'
            result['pdf_type'] = pdf_type
        
        # 步骤4: 生成最终报告
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result['input_file'] = str(input_path)
        result['output_dir'] = str(output_dir)
        result['processing_time'] = processing_time
        result['start_time'] = start_time.isoformat()
        result['end_time'] = end_time.isoformat()
        
        # 保存报告
        report_path = output_dir / f"{input_path.stem}_processing_report.json"
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 处理报告: {report_path}")
        
        # 显示结果摘要
        self._print_result_summary(result)
        
        return result
    
    def _basic_split_pdf(self, input_path, output_dir, use_smart_detection=True):
        """PDF拆分（支持智能章节检测）"""
        try:
            import PyPDF2
            
            input_path = Path(input_path)
            output_dir = Path(output_dir)
            
            with open(input_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                if total_pages == 0:
                    return {'success': False, 'error': 'PDF文件没有页面'}
                
                # 决定使用哪种拆分方式
                split_method = 'fixed'
                chapter_boundaries = []
                
                if use_smart_detection and self.chapter_detector_available:
                    # 尝试智能章节检测
                    logger.info("尝试智能章节检测...")
                    
                    # 提取页面文本
                    page_texts = {}
                    sample_pages = min(20, total_pages)  # 采样部分页面以提高速度
                    
                    for page_num in range(sample_pages):
                        try:
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            if text and len(text.strip()) > 5:
                                page_texts[page_num] = text.strip()
                        except:
                            continue
                    
                    if page_texts:
                        # 使用章节检测器
                        chapter_boundaries = self.chapter_detector.detect_from_text(page_texts)
                        
                        if len(chapter_boundaries) > 1:
                            split_method = 'smart'
                            logger.info(f"✅ 智能检测到 {len(chapter_boundaries)} 个章节")
                        else:
                            logger.info("⚠️  智能检测未找到章节，使用固定页数")
                    else:
                        logger.info("⚠️  无法提取文本，使用固定页数")
                
                # 如果没有智能检测结果，使用固定页数
                if split_method == 'fixed':
                    num_chapters = (total_pages + self.pages_per_chapter - 1) // self.pages_per_chapter
                    chapter_boundaries = [i * self.pages_per_chapter for i in range(num_chapters)]
                    logger.info(f"使用固定页数拆分: {num_chapters} 个章节")
                
                # 创建章节
                chapters = []
                chapter_details = []
                
                for chapter_idx in range(len(chapter_boundaries)):
                    start_page = chapter_boundaries[chapter_idx]
                    end_page = chapter_boundaries[chapter_idx + 1] if chapter_idx + 1 < len(chapter_boundaries) else total_pages
                    
                    # 提取章节标题（如果可能）
                    chapter_title = f"第 {chapter_idx + 1} 章"
                    if start_page < total_pages:
                        try:
                            page = pdf_reader.pages[start_page]
                            text = page.extract_text()
                            if text:
                                lines = text.split('\n')
                                if lines and len(lines[0].strip()) > 3:
                                    chapter_title = lines[0].strip()[:50]
                        except:
                            pass
                    
                    # 创建章节PDF
                    chapter_pdf = PyPDF2.PdfWriter()
                    
                    for page_num in range(start_page, end_page):
                        page = pdf_reader.pages[page_num]
                        chapter_pdf.add_page(page)
                    
                    # 保存章节文件
                    chapter_filename = f"{input_path.stem}_chapter_{chapter_idx + 1:03d}.pdf"
                    chapter_path = output_dir / chapter_filename
                    
                    with open(chapter_path, 'wb') as chapter_file:
                        chapter_pdf.write(chapter_file)
                    
                    chapters.append(str(chapter_path))
                    chapter_details.append({
                        'chapter_number': chapter_idx + 1,
                        'start_page': start_page,
                        'end_page': end_page,
                        'page_count': end_page - start_page,
                        'title': chapter_title,
                        'filename': chapter_filename
                    })
                    
                    logger.info(f"创建章节 {chapter_idx + 1}: {chapter_filename}")
                    logger.info(f"  页面范围: {start_page + 1}-{end_page} ({end_page - start_page} 页)")
                    logger.info(f"  章节标题: {chapter_title}")
                
                return {
                    'success': True,
                    'total_pages': total_pages,
                    'chapters_created': len(chapters),
                    'chapters': chapters,
                    'chapter_details': chapter_details,
                    'split_method': split_method,
                    'pages_per_chapter': self.pages_per_chapter if split_method == 'fixed' else 'variable'
                }
                
        except Exception as e:
            logger.error(f"PDF拆分失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_pdf_type(self, pdf_path, detailed=False):
        """
        检测PDF类型（简化版本）
        
        Args:
            pdf_path: PDF文件路径
            detailed: 是否详细分析
            
        Returns:
            str: 'text', 'scanned', 'unknown'
        """
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 检查前几页是否有文本
                sample_pages = min(3, total_pages)
                text_found = False
                
                for page_num in range(sample_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and len(text.strip()) > 10:
                            text_found = True
                            break
                    except:
                        continue
                
                if text_found:
                    return 'text'
                else:
                    # 如果有OCR功能，进一步分析
                    if self.ocr_available and detailed:
                        try:
                            from pdf_ocr_module import PDFOCR
                            ocr = PDFOCR()
                            analysis = ocr.analyze_scanned_document(pdf_path, sample_pages=2)
                            scanned_prob = analysis.get('is_scanned_probability', 0)
                            
                            if scanned_prob > 0.5:
                                return 'scanned'
                            else:
                                return 'unknown'
                        except:
                            return 'unknown'
                    else:
                        return 'scanned' if not text_found else 'text'
                        
        except Exception as e:
            logger.warning(f"PDF类型检测失败: {e}")
            return 'unknown'
    
    def _print_result_summary(self, result):
        """打印结果摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 处理结果摘要")
        logger.info("=" * 60)
        
        if result.get('success', False):
            logger.info(f"✅ 处理成功!")
            logger.info(f"   处理模式: {result.get('processing_mode', '未知')}")
            logger.info(f"   PDF类型: {result.get('pdf_type', '未知')}")
            logger.info(f"   总页数: {result.get('total_pages', 0)}")
            logger.info(f"   生成章节: {result.get('chapters_created', 0)}")
            logger.info(f"   处理时间: {result.get('processing_time', 0):.1f} 秒")
            logger.info(f"   输出目录: {result.get('output_dir', '')}")
            
            if 'total_text_chars' in result:
                logger.info(f"   总文本字符: {result.get('total_text_chars', 0)}")
                logger.info(f"   平均字符/页: {result.get('avg_chars_per_page', 0):.0f}")
            
            # 显示生成的章节
            chapters = result.get('chapters', [])
            if chapters:
                logger.info(f"\n📁 生成的章节文件:")
                for i, chapter in enumerate(chapters[:5], 1):  # 显示前5个
                    chapter_path = Path(chapter)
                    size_kb = chapter_path.stat().st_size / 1024 if chapter_path.exists() else 0
                    logger.info(f"   {i:2d}. {chapter_path.name} ({size_kb:.1f} KB)")
                
                if len(chapters) > 5:
                    logger.info(f"   ... 还有 {len(chapters) - 5} 个文件")
            
            # 显示文本文件（如果存在）
            text_files = result.get('text_files', [])
            if text_files:
                logger.info(f"\n📝 生成的文本文件:")
                for i, text_file in enumerate(text_files[:3], 1):  # 显示前3个
                    text_path = Path(text_file)
                    if text_path.exists():
                        size_kb = text_path.stat().st_size / 1024
                        logger.info(f"   {i:2d}. {text_path.name} ({size_kb:.1f} KB)")
        
        else:
            logger.error(f"❌ 处理失败!")
            logger.error(f"   错误: {result.get('error', '未知错误')}")
        
        logger.info("=" * 60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF章节拆分工具 - 最终版本（完整OCR流程）')
    
    # 主要参数
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='输入PDF文件路径')
    parser.add_argument('--output', '-o', type=str, default='./pdf_chapters',
                       help='输出目录路径 (默认: ./pdf_chapters)')
    
    # 拆分参数
    parser.add_argument('--pages', '-p', type=int, default=20,
                       help='每个章节的页数 (默认: 20)')
    
    # OCR参数
    parser.add_argument('--ocr', action='store_true',
                       help='启用OCR功能（处理扫描件）')
    parser.add_argument('--force-ocr', action='store_true',
                       help='强制使用OCR模式（忽略类型检测）')
    parser.add_argument('--ocr-lang', type=str, default='eng+chi_sim',
                       help='OCR语言设置 (默认: eng+chi_sim)')
    parser.add_argument('--no-preprocess', action='store_true',
                       help='禁用图像预处理')
    parser.add_argument('--dpi', type=int, default=200,
                       help='OCR图像分辨率 (默认: 200)')
    
    # 章节检测参数
    parser.add_argument('--smart', action='store_true',
                       help='启用智能章节检测（Sprint 3功能）')
    parser.add_argument('--no-smart', action='store_true',
                       help='禁用智能章节检测，使用固定页数')
    
    # 其他功能
    parser.add_argument('--detect-type', action='store_true',
                       help='检测PDF类型')
    parser.add_argument('--test-ocr', action='store_true',
                       help='测试OCR功能')
    parser.add_argument('--test-smart', action='store_true',
                       help='测试智能章节检测功能')
    
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始PDF处理任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出目录: {args.output}")
    
    # 创建拆分器
    splitter = PDFSplitterFinal(
        pages_per_chapter=args.pages,
        use_ocr=args.ocr,
        ocr_lang=args.ocr_lang,
        enable_preprocessing=not args.no_preprocess,
        dpi=args.dpi
    )
    
    # OCR测试模式
    if args.test_ocr:
        logger.info("🧪 测试OCR功能...")
        
        if not args.ocr:
            logger.warning("OCR测试需要启用OCR功能，添加 --ocr 参数")
            args.ocr = True
        
        # 简单测试OCR可用性
        if splitter.ocr_available:
            logger.info("✅ OCR功能可用")
            
            # 测试PDF类型检测
            pdf_type = splitter.detect_pdf_type(args.input)
            logger.info(f"PDF类型: {pdf_type}")
            
            if pdf_type == 'scanned':
                logger.info("💡 建议: 使用OCR模式处理此文件")
            else:
                logger.info("💡 建议: 可尝试使用OCR模式，或使用基础模式")
        else:
            logger.error("❌ OCR功能不可用")
            logger.info("请安装依赖: pip install pytesseract pdf2image Pillow")
        
        return 0
    
    # 智能检测测试模式
    if args.test_smart:
        logger.info("🧪 测试智能章节检测功能...")
        
        if splitter.chapter_detector_available:
            logger.info("✅ 章节检测器可用")
            
            # 测试章节检测
            try:
                import PyPDF2
                with open(args.input, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                    
                    # 提取样本文本
                    page_texts = {}
                    sample_pages = min(10, total_pages)
                    
                    for page_num in range(sample_pages):
                        try:
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            if text and len(text.strip()) > 5:
                                page_texts[page_num] = text.strip()
                        except:
                            continue
                    
                    if page_texts:
                        # 分析文档结构
                        structure = splitter.chapter_detector.analyze_document_structure(page_texts)
                        
                        logger.info(f"📊 文档结构分析:")
                        logger.info(f"   总页数: {structure['total_pages']}")
                        logger.info(f"   检测章节数: {structure['detected_chapters']}")
                        logger.info(f"   检测方法: {structure['detection_method']}")
                        logger.info(f"   置信度: {structure['confidence']:.2f}")
                        
                        logger.info(f"\n📝 章节详情:")
                        for chapter in structure['chapters'][:5]:  # 显示前5章
                            logger.info(f"   第{chapter['chapter_number']}章: "
                                      f"页 {chapter['start_page']+1}-{chapter['end_page']}, "
                                      f"{chapter['page_count']}页, 标题: {chapter['title']}")
                        
                        if structure['detection_method'] == 'smart':
                            logger.info("💡 建议: 使用智能章节检测 (添加 --smart 参数)")
                        else:
                            logger.info("💡 建议: 使用固定页数拆分")
                    else:
                        logger.warning("⚠️  无法提取文本，智能检测不可用")
                        logger.info("💡 建议: 使用固定页数或OCR模式")
            
            except Exception as e:
                logger.error(f"智能检测测试失败: {e}")
        else:
            logger.error("❌ 章节检测器不可用")
        
        return 0
    
    # PDF类型检测模式
    if args.detect_type:
        logger.info("🔍 检测PDF类型...")
        pdf_type = splitter.detect_pdf_type(args.input, detailed=True)
        logger.info(f"检测结果: {pdf_type}")
        
        # 建议
        if pdf_type == 'text':
            logger.info("💡 建议: 使用基础模式 (无需 --ocr 参数)")
        elif pdf_type == 'scanned':
            logger.info("💡 建议: 使用OCR模式 (添加 --ocr 参数)")
        else:
            logger.info("💡 建议: 尝试OCR模式或使用 --force-ocr 参数")
        
        return 0
    
    # 执行智能处理
    logger.info(f"每章节页数: {args.pages}")
    logger.info(f"OCR模式: {'启用' if args.ocr else '禁用'}")
    logger.info(f"智能章节检测: {'启用' if args.smart and not args.no_smart else '禁用'}")
    
    if args.ocr:
        logger.info(f"OCR语言: {args.ocr_lang}")
        logger.info(f"图像预处理: {'启用' if not args.no_preprocess else '禁用'}")
        logger.info(f"图像分辨率: {args.dpi} DPI")
    
    # 决定是否使用智能检测
    use_smart_detection = args.smart and not args.no_smart
    
    result = splitter.smart_process_pdf(
        args.input,
        args.output,
        force_ocr=args.force_ocr,
        use_smart_detection=use_smart_detection
    )
    
    if result.get('success', False):
        return 0
    else:
        logger.error(f"处理失败: {result.get('error', '未知错误')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())