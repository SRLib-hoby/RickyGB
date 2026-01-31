#!/usr/bin/env python3
"""
PDF章节拆分工具 - 版本2 (Sprint 2.1: OCR基础集成)
在v1基础上添加OCR文本提取功能
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

# 导入OCR模块
try:
    from pdf_ocr_module import PDFOCR
    OCR_AVAILABLE = True
except ImportError:
    logger.warning("OCR模块不可用，将使用基础模式")
    OCR_AVAILABLE = False

class PDFSplitterV2:
    """PDF拆分器 - 版本2（支持OCR）"""
    
    def __init__(self, pages_per_chapter=20, use_ocr=False, ocr_lang='eng+chi_sim'):
        """
        初始化PDF拆分器
        
        Args:
            pages_per_chapter: 每个章节的页数
            use_ocr: 是否使用OCR提取文本
            ocr_lang: OCR语言设置
        """
        self.pages_per_chapter = pages_per_chapter
        self.use_ocr = use_ocr and OCR_AVAILABLE
        self.ocr_lang = ocr_lang
        
        if self.use_ocr:
            self.ocr_processor = PDFOCR(lang=ocr_lang)
            logger.info(f"初始化PDF拆分器（OCR模式），语言: {ocr_lang}")
        else:
            logger.info(f"初始化PDF拆分器（基础模式）")
        
        logger.info(f"每章节页数: {pages_per_chapter}")
    
    def detect_pdf_type(self, pdf_path, detailed=False):
        """
        检测PDF类型：文本PDF或扫描件（改进版本）
        
        Args:
            pdf_path: PDF文件路径
            detailed: 是否返回详细分析
            
        Returns:
            str 或 dict: 类型或详细分析结果
        """
        try:
            import PyPDF2
            
            pdf_path = Path(pdf_path)
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 方法1: 检查文本提取
                sample_pages = min(5, total_pages)
                text_pages = 0
                total_text_chars = 0
                
                for page_num in range(sample_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and len(text.strip()) > 5:
                            text_pages += 1
                            total_text_chars += len(text.strip())
                    except:
                        continue
                
                # 计算文本提取指标
                text_page_ratio = text_pages / sample_pages if sample_pages > 0 else 0
                avg_text_per_page = total_text_chars / text_pages if text_pages > 0 else 0
                
                # 方法2: 如果启用了OCR，使用扫描件分析
                scanned_analysis = {}
                if self.use_ocr and OCR_AVAILABLE:
                    scanned_analysis = self.ocr_processor.analyze_scanned_document(pdf_path, sample_pages=3)
                
                # 综合判断
                is_text_pdf = text_page_ratio > 0.7 or avg_text_per_page > 100
                is_scanned = False
                
                if scanned_analysis and 'is_scanned_probability' in scanned_analysis:
                    scanned_prob = scanned_analysis['is_scanned_probability']
                    is_scanned = scanned_prob > 0.6
                
                # 生成结果
                if detailed:
                    result = {
                        'pdf_name': pdf_path.name,
                        'total_pages': total_pages,
                        'sampled_pages': sample_pages,
                        'text_page_ratio': round(text_page_ratio, 3),
                        'avg_text_per_page': round(avg_text_per_page, 1),
                        'is_text_pdf': is_text_pdf,
                        'scanned_analysis': scanned_analysis,
                        'detected_type': 'text' if is_text_pdf else ('scanned' if is_scanned else 'mixed/unknown'),
                        'confidence': 'high' if (is_text_pdf or is_scanned) else 'low'
                    }
                    
                    logger.info(f"详细PDF类型分析:")
                    logger.info(f"  文件: {pdf_path.name}")
                    logger.info(f"  总页数: {total_pages}")
                    logger.info(f"  文本页面比例: {text_page_ratio:.1%}")
                    logger.info(f"  平均文本长度: {avg_text_per_page:.0f} 字符")
                    
                    if scanned_analysis:
                        logger.info(f"  扫描件概率: {scanned_analysis.get('is_scanned_probability', 0):.1%}")
                        logger.info(f"  建议: {scanned_analysis.get('recommendation', '')}")
                    
                    logger.info(f"  检测类型: {result['detected_type']}")
                    logger.info(f"  置信度: {result['confidence']}")
                    
                    return result
                else:
                    # 简单类型判断
                    if is_text_pdf:
                        detected_type = 'text'
                        logger.info(f"检测到文本PDF: {pdf_path.name} (置信度: 高)")
                    elif is_scanned:
                        detected_type = 'scanned'
                        logger.info(f"检测到扫描件PDF: {pdf_path.name} (置信度: 中)")
                    else:
                        detected_type = 'unknown'
                        logger.info(f"PDF类型未知: {pdf_path.name} (建议使用--detect-type详细分析)")
                    
                    return detected_type
                    
        except Exception as e:
            logger.warning(f"PDF类型检测失败: {e}")
            return 'unknown' if not detailed else {'error': str(e), 'detected_type': 'unknown'}
    
    def extract_page_text(self, pdf_path, page_num, use_preprocessing=True):
        """
        提取页面文本（智能选择方法，改进版本）
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页面编号
            use_preprocessing: 是否使用图像预处理
            
        Returns:
            str: 提取的文本
        """
        try:
            import PyPDF2
            
            # 首先尝试直接提取文本
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if page_num < len(pdf_reader.pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text and len(text.strip()) > 5:
                        logger.debug(f"直接提取第 {page_num + 1} 页文本: {len(text.strip())} 字符")
                        return text.strip()
            
            # 如果直接提取失败且启用了OCR，使用OCR
            if self.use_ocr:
                logger.info(f"使用OCR提取第 {page_num + 1} 页文本")
                
                # 使用改进的OCR提取（带预处理）
                if hasattr(self.ocr_processor, 'extract_text_with_preprocessing'):
                    ocr_text = self.ocr_processor.extract_text_with_preprocessing(pdf_path, page_num)
                else:
                    # 回退到基础OCR
                    ocr_text = self.ocr_processor.extract_text_from_page(pdf_path, page_num)
                
                if ocr_text:
                    logger.info(f"OCR提取成功: {len(ocr_text)} 字符")
                else:
                    logger.warning(f"OCR提取失败或文本为空")
                
                return ocr_text
            
            logger.debug(f"第 {page_num + 1} 页无文本内容")
            return ""
            
        except Exception as e:
            logger.error(f"提取页面文本失败: {e}")
            return ""
    
    def analyze_chapter_boundaries(self, pdf_path, sample_rate=0.1):
        """
        分析章节边界（基础版本）
        
        Args:
            pdf_path: PDF文件路径
            sample_rate: 采样率（0-1）
            
        Returns:
            list: 建议的章节起始页码
        """
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # 基础版本：按固定页数拆分
                # 后续Sprint会实现智能检测
                boundaries = []
                for start in range(0, total_pages, self.pages_per_chapter):
                    boundaries.append(start)
                
                logger.info(f"分析章节边界: 固定每 {self.pages_per_chapter} 页")
                logger.info(f"建议章节数: {len(boundaries)}")
                
                return boundaries
                
        except Exception as e:
            logger.error(f"分析章节边界失败: {e}")
            return []
    
    def split_pdf(self, input_path, output_dir, use_smart_split=False):
        """
        拆分PDF文件
        
        Args:
            input_path: 输入PDF文件路径
            output_dir: 输出目录路径
            use_smart_split: 是否使用智能拆分（预留功能）
            
        Returns:
            list: 生成的章节文件路径列表
        """
        try:
            input_path = Path(input_path)
            output_dir = Path(output_dir)
            
            # 验证输入文件
            if not input_path.exists():
                logger.error(f"输入文件不存在: {input_path}")
                return []
            
            if not input_path.suffix.lower() == '.pdf':
                logger.error(f"文件不是PDF格式: {input_path}")
                return []
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始处理PDF文件: {input_path.name}")
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"OCR模式: {'启用' if self.use_ocr else '禁用'}")
            
            # 检测PDF类型
            pdf_type = self.detect_pdf_type(input_path)
            logger.info(f"PDF类型: {pdf_type}")
            
            # 导入PyPDF2
            try:
                import PyPDF2
            except ImportError:
                logger.error("需要安装PyPDF2库: pip install PyPDF2")
                return []
            
            chapters = []
            try:
                with open(input_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    
                    logger.info(f"PDF总页数: {total_pages}")
                    
                    if total_pages == 0:
                        logger.error("PDF文件没有页面")
                        return []
                    
                    # 获取章节边界
                    if use_smart_split and self.use_ocr:
                        logger.info("使用智能章节检测（预留功能）")
                        # 后续Sprint实现
                        boundaries = self.analyze_chapter_boundaries(input_path)
                    else:
                        # 基础版本：按固定页数
                        num_chapters = (total_pages + self.pages_per_chapter - 1) // self.pages_per_chapter
                        boundaries = list(range(0, total_pages, self.pages_per_chapter))
                        logger.info(f"固定页数拆分，章节数: {num_chapters}")
                    
                    # 分章节处理
                    for chapter_idx, start_page in enumerate(boundaries):
                        if start_page >= total_pages:
                            break
                            
                        end_page = min(start_page + self.pages_per_chapter, total_pages)
                        
                        # 创建章节PDF
                        chapter_pdf = PyPDF2.PdfWriter()
                        
                        # 添加页面到章节
                        for page_num in range(start_page, end_page):
                            page = pdf_reader.pages[page_num]
                            chapter_pdf.add_page(page)
                        
                        # 保存章节文件
                        chapter_filename = f"{input_path.stem}_chapter_{chapter_idx + 1:03d}.pdf"
                        chapter_path = output_dir / chapter_filename
                        
                        with open(chapter_path, 'wb') as chapter_file:
                            chapter_pdf.write(chapter_file)
                        
                        chapters.append(str(chapter_path))
                        
                        # 如果启用了OCR，提取章节标题
                        chapter_title = f"第 {chapter_idx + 1} 章"
                        if self.use_ocr:
                            # 尝试从第一页提取标题
                            first_page_text = self.extract_page_text(input_path, start_page)
                            if first_page_text:
                                # 简单提取前几行作为标题
                                lines = first_page_text.split('\n')
                                if lines and len(lines[0].strip()) > 3:
                                    chapter_title = lines[0].strip()[:50]
                        
                        logger.info(f"创建章节 {chapter_idx + 1}: {chapter_filename}")
                        logger.info(f"  页面范围: {start_page + 1}-{end_page}")
                        logger.info(f"  章节标题: {chapter_title}")
                        logger.info(f"  文件大小: {chapter_path.stat().st_size / 1024:.1f} KB")
                    
                    logger.info(f"PDF拆分完成! 共生成 {len(chapters)} 个章节文件")
                    
            except Exception as e:
                logger.error(f"处理PDF文件时出错: {e}")
                return []
            
            return chapters
            
        except Exception as e:
            logger.error(f"拆分PDF时发生错误: {e}")
            return []
    
    def ocr_test(self, pdf_path, pages=None):
        """
        OCR功能测试
        
        Args:
            pdf_path: PDF文件路径
            pages: 要测试的页面列表
            
        Returns:
            bool: 测试是否成功
        """
        if not self.use_ocr:
            logger.error("OCR功能未启用")
            return False
        
        logger.info(f"开始OCR测试: {Path(pdf_path).name}")
        
        if pages is None:
            # 测试前3页
            pages = [0, 1, 2]
        
        results = {}
        for page_num in pages:
            text = self.extract_page_text(pdf_path, page_num)
            results[page_num] = text
            
            if text:
                logger.info(f"第 {page_num + 1} 页: 提取 {len(text)} 字符")
                # 显示前100个字符
                preview = text[:100] + ("..." if len(text) > 100 else "")
                logger.info(f"  预览: {preview}")
            else:
                logger.warning(f"第 {page_num + 1} 页: 未提取到文本")
        
        # 统计
        successful = sum(1 for text in results.values() if text)
        total_chars = sum(len(text) for text in results.values())
        
        logger.info(f"OCR测试完成:")
        logger.info(f"  测试页面: {len(results)}")
        logger.info(f"  成功页面: {successful}")
        logger.info(f"  总字符数: {total_chars}")
        
        return successful > 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF章节拆分工具 - 版本2 (支持OCR)')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='输入PDF文件路径')
    parser.add_argument('--output', '-o', type=str, default='./pdf_chapters',
                       help='输出目录路径 (默认: ./pdf_chapters)')
    parser.add_argument('--pages', '-p', type=int, default=20,
                       help='每个章节的页数 (默认: 20)')
    parser.add_argument('--ocr', action='store_true',
                       help='启用OCR功能（处理扫描件）')
    parser.add_argument('--ocr-lang', type=str, default='eng+chi_sim',
                       help='OCR语言设置 (默认: eng+chi_sim)')
    parser.add_argument('--ocr-test', action='store_true',
                       help='运行OCR功能测试')
    parser.add_argument('--detect-type', action='store_true',
                       help='检测PDF类型')
    parser.add_argument('--detailed', action='store_true',
                       help='详细分析模式')
    
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始PDF拆分任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出目录: {args.output}")
    
    # 创建拆分器
    splitter = PDFSplitterV2(
        pages_per_chapter=args.pages,
        use_ocr=args.ocr,
        ocr_lang=args.ocr_lang
    )
    
    # OCR测试模式
    if args.ocr_test:
        if not args.ocr:
            logger.warning("OCR测试需要启用OCR功能，添加 --ocr 参数")
            args.ocr = True
            splitter.use_ocr = True
        
        success = splitter.ocr_test(args.input)
        return 0 if success else 1
    
    # PDF类型检测模式
    if args.detect_type:
        if args.detailed:
            # 详细分析模式
            analysis = splitter.detect_pdf_type(args.input, detailed=True)
            
            if isinstance(analysis, dict):
                logger.info("\n📊 详细PDF分析报告:")
                logger.info("=" * 50)
                
                # 基本信息
                logger.info(f"文件名称: {analysis.get('pdf_name', '未知')}")
                logger.info(f"总页数: {analysis.get('total_pages', 0)}")
                logger.info(f"采样页数: {analysis.get('sampled_pages', 0)}")
                
                # 文本分析
                logger.info(f"\n📝 文本分析:")
                logger.info(f"  文本页面比例: {analysis.get('text_page_ratio', 0):.1%}")
                logger.info(f"  平均文本长度: {analysis.get('avg_text_per_page', 0):.0f} 字符")
                logger.info(f"  是否为文本PDF: {'是' if analysis.get('is_text_pdf', False) else '否'}")
                
                # 扫描件分析
                scanned_analysis = analysis.get('scanned_analysis', {})
                if scanned_analysis:
                    logger.info(f"\n🖨️  扫描件分析:")
                    logger.info(f"  扫描件概率: {scanned_analysis.get('is_scanned_probability', 0):.1%}")
                    
                    metrics = scanned_analysis.get('detection_metrics', {})
                    if metrics:
                        logger.info(f"  检测指标:")
                        for metric, value in metrics.items():
                            logger.info(f"    {metric}: {value:.3f}")
                    
                    logger.info(f"  建议: {scanned_analysis.get('recommendation', '')}")
                
                # 综合结论
                logger.info(f"\n🎯 综合结论:")
                logger.info(f"  检测类型: {analysis.get('detected_type', '未知')}")
                logger.info(f"  置信度: {analysis.get('confidence', '低')}")
                
                logger.info("=" * 50)
                
                # 操作建议
                detected_type = analysis.get('detected_type', '')
                if 'text' in detected_type:
                    logger.info("\n💡 操作建议: 可直接使用基础拆分模式")
                elif 'scanned' in detected_type:
                    logger.info("\n💡 操作建议: 建议使用OCR模式 (添加 --ocr 参数)")
                else:
                    logger.info("\n💡 操作建议: 建议先测试OCR功能 (添加 --ocr-test 参数)")
            else:
                logger.info(f"PDF类型: {analysis}")
        else:
            # 简单检测模式
            pdf_type = splitter.detect_pdf_type(args.input)
            logger.info(f"PDF类型检测结果: {pdf_type}")
            
            # 简单建议
            if pdf_type == 'text':
                logger.info("💡 建议: 可直接使用基础拆分模式")
            elif pdf_type == 'scanned':
                logger.info("💡 建议: 使用OCR模式处理 (添加 --ocr 参数)")
            else:
                logger.info("💡 建议: 使用详细分析模式 (添加 --detailed 参数)")
        
        return 0
    
    # 执行拆分
    logger.info(f"每章节页数: {args.pages}")
    logger.info(f"OCR模式: {'启用' if args.ocr else '禁用'}")
    
    chapters = splitter.split_pdf(args.input, args.output)
    
    # 记录结束时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if chapters:
        logger.info(f"✅ PDF拆分成功!")
        logger.info(f"📊 统计信息:")
        logger.info(f"   生成章节数: {len(chapters)}")
        logger.info(f"   处理时间: {duration:.2f} 秒")
        logger.info(f"   输出目录: {args.output}")
        
        return 0
    else:
        logger.error(f"❌ PDF拆分失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())