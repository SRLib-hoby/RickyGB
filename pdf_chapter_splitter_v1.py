#!/usr/bin/env python3
"""
PDF章节拆分工具 - 版本1 (基础功能)
Sprint 1: 实现基础PDF拆分功能
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

class PDFSplitter:
    """PDF拆分器 - 基础版本"""
    
    def __init__(self, pages_per_chapter=20):
        """
        初始化PDF拆分器
        
        Args:
            pages_per_chapter: 每个章节的页数（基础版本使用固定页数）
        """
        self.pages_per_chapter = pages_per_chapter
        logger.info(f"初始化PDF拆分器，每章节页数: {pages_per_chapter}")
    
    def split_pdf(self, input_path, output_dir):
        """
        拆分PDF文件 - 基础版本（按固定页数拆分）
        
        Args:
            input_path: 输入PDF文件路径
            output_dir: 输出目录路径
            
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
            
            # 导入PyPDF2（延迟导入，避免不必要的依赖）
            try:
                import PyPDF2
            except ImportError:
                logger.error("需要安装PyPDF2库: pip install PyPDF2")
                return []
            
            # 读取PDF文件
            chapters = []
            try:
                with open(input_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    
                    logger.info(f"PDF总页数: {total_pages}")
                    
                    if total_pages == 0:
                        logger.error("PDF文件没有页面")
                        return []
                    
                    # 计算章节数量
                    num_chapters = (total_pages + self.pages_per_chapter - 1) // self.pages_per_chapter
                    logger.info(f"预计拆分章节数: {num_chapters}")
                    
                    # 分章节处理
                    for chapter_num in range(num_chapters):
                        start_page = chapter_num * self.pages_per_chapter
                        end_page = min((chapter_num + 1) * self.pages_per_chapter, total_pages)
                        
                        # 创建章节PDF
                        chapter_pdf = PyPDF2.PdfWriter()
                        
                        # 添加页面到章节
                        for page_num in range(start_page, end_page):
                            page = pdf_reader.pages[page_num]
                            chapter_pdf.add_page(page)
                        
                        # 保存章节文件
                        chapter_filename = f"{input_path.stem}_chapter_{chapter_num + 1:03d}.pdf"
                        chapter_path = output_dir / chapter_filename
                        
                        with open(chapter_path, 'wb') as chapter_file:
                            chapter_pdf.write(chapter_file)
                        
                        chapters.append(str(chapter_path))
                        logger.info(f"创建章节 {chapter_num + 1}: {chapter_filename} (页 {start_page+1}-{end_page})")
                    
                    logger.info(f"PDF拆分完成! 共生成 {len(chapters)} 个章节文件")
                    
            except Exception as e:
                logger.error(f"处理PDF文件时出错: {e}")
                return []
            
            return chapters
            
        except Exception as e:
            logger.error(f"拆分PDF时发生错误: {e}")
            return []
    
    def split_pdf_streaming(self, input_path, output_dir, chunk_size=50):
        """
        流式拆分PDF - 适用于大文件
        
        Args:
            input_path: 输入PDF文件路径
            output_dir: 输出目录路径
            chunk_size: 每次处理的页数（控制内存使用）
            
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
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始流式处理PDF文件: {input_path.name}")
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"处理块大小: {chunk_size} 页")
            
            # 导入PyPDF2
            try:
                import PyPDF2
            except ImportError:
                logger.error("需要安装PyPDF2库: pip install PyPDF2")
                return []
            
            chapters = []
            chapter_num = 1
            
            try:
                with open(input_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    
                    logger.info(f"PDF总页数: {total_pages}")
                    
                    if total_pages == 0:
                        logger.error("PDF文件没有页面")
                        return []
                    
                    # 分块处理大文件
                    for chunk_start in range(0, total_pages, chunk_size):
                        chunk_end = min(chunk_start + chunk_size, total_pages)
                        
                        # 在当前块内分章节
                        pages_in_chunk = chunk_end - chunk_start
                        chapters_in_chunk = (pages_in_chunk + self.pages_per_chapter - 1) // self.pages_per_chapter
                        
                        for chunk_chapter in range(chapters_in_chunk):
                            chapter_start = chunk_start + chunk_chapter * self.pages_per_chapter
                            chapter_end = min(chapter_start + self.pages_per_chapter, chunk_end)
                            
                            if chapter_start >= chapter_end:
                                break
                            
                            # 创建章节PDF
                            chapter_pdf = PyPDF2.PdfWriter()
                            
                            # 添加页面到章节
                            for page_num in range(chapter_start, chapter_end):
                                page = pdf_reader.pages[page_num]
                                chapter_pdf.add_page(page)
                            
                            # 保存章节文件
                            chapter_filename = f"{input_path.stem}_chapter_{chapter_num:03d}.pdf"
                            chapter_path = output_dir / chapter_filename
                            
                            with open(chapter_path, 'wb') as chapter_file:
                                chapter_pdf.write(chapter_file)
                            
                            chapters.append(str(chapter_path))
                            logger.info(f"创建章节 {chapter_num}: {chapter_filename} (页 {chapter_start+1}-{chapter_end})")
                            chapter_num += 1
                    
                    logger.info(f"PDF流式拆分完成! 共生成 {len(chapters)} 个章节文件")
                    
            except Exception as e:
                logger.error(f"流式处理PDF时出错: {e}")
                return []
            
            return chapters
            
        except Exception as e:
            logger.error(f"流式拆分PDF时发生错误: {e}")
            return []

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF章节拆分工具 - 基础版本')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='输入PDF文件路径')
    parser.add_argument('--output', '-o', type=str, default='./pdf_chapters',
                       help='输出目录路径 (默认: ./pdf_chapters)')
    parser.add_argument('--pages', '-p', type=int, default=20,
                       help='每个章节的页数 (默认: 20)')
    parser.add_argument('--chunk-size', '-c', type=int, default=50,
                       help='流式处理的块大小 (默认: 50页)')
    parser.add_argument('--streaming', '-s', action='store_true',
                       help='使用流式处理模式（适用于大文件）')
    
    args = parser.parse_args()
    
    # 创建拆分器
    splitter = PDFSplitter(pages_per_chapter=args.pages)
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始PDF拆分任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出目录: {args.output}")
    logger.info(f"每章节页数: {args.pages}")
    
    # 执行拆分
    if args.streaming:
        logger.info("使用流式处理模式")
        chapters = splitter.split_pdf_streaming(args.input, args.output, args.chunk_size)
    else:
        logger.info("使用标准处理模式")
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
        
        # 显示生成的章节文件
        logger.info(f"📁 生成的章节文件:")
        for i, chapter in enumerate(chapters, 1):
            chapter_path = Path(chapter)
            size_kb = chapter_path.stat().st_size / 1024 if chapter_path.exists() else 0
            logger.info(f"   {i:2d}. {chapter_path.name} ({size_kb:.1f} KB)")
        
        return 0
    else:
        logger.error(f"❌ PDF拆分失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())