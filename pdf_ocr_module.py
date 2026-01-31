#!/usr/bin/env python3
"""
PDF OCR模块 - Sprint 2.1
基础OCR集成，只实现文本提取功能
"""

import os
import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOCR:
    """PDF OCR处理器 - 改进版本（Sprint 2.2）"""
    
    def __init__(self, lang='eng+chi_sim', enable_preprocessing=True):
        """
        初始化OCR处理器
        
        Args:
            lang: OCR语言，默认英文+简体中文
            enable_preprocessing: 是否启用图像预处理
        """
        self.lang = lang
        self.enable_preprocessing = enable_preprocessing
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查OCR依赖是否可用"""
        try:
            import pytesseract
            self.tesseract_available = True
            logger.info(f"✅ pytesseract可用，语言: {self.lang}")
        except ImportError:
            self.tesseract_available = False
            logger.warning("⚠️  pytesseract未安装，OCR功能不可用")
            logger.info("安装命令: pip install pytesseract")
        
        try:
            import pdf2image
            self.pdf2image_available = True
            logger.info("✅ pdf2image可用")
        except ImportError:
            self.pdf2image_available = False
            logger.warning("⚠️  pdf2image未安装，OCR功能不可用")
            logger.info("安装命令: pip install pdf2image")
        
        try:
            from PIL import Image
            self.pil_available = True
            logger.info("✅ PIL/Pillow可用")
        except ImportError:
            self.pil_available = False
            logger.warning("⚠️  PIL/Pillow未安装，OCR功能不可用")
            logger.info("安装命令: pip install Pillow")
    
    def is_ocr_available(self):
        """检查OCR功能是否可用"""
        return all([
            self.tesseract_available,
            self.pdf2image_available,
            self.pil_available
        ])
    
    def extract_text_from_page(self, pdf_path, page_num):
        """
        从PDF的指定页面提取文本（OCR）
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页面编号（从0开始）
            
        Returns:
            str: 提取的文本，如果失败返回空字符串
        """
        if not self.is_ocr_available():
            logger.error("OCR功能不可用，请安装依赖")
            return ""
        
        try:
            import pytesseract
            import pdf2image
            from PIL import Image
            
            # 验证文件
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return ""
            
            # 获取PDF总页数
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                    
                    if page_num >= total_pages:
                        logger.error(f"页面编号超出范围: {page_num} (总页数: {total_pages})")
                        return ""
            except Exception as e:
                logger.warning(f"无法获取PDF页数: {e}")
                # 继续尝试，假设页面存在
            
            logger.info(f"开始OCR处理: {pdf_path.name} 第 {page_num + 1} 页")
            
            # 将PDF页面转换为图像
            # 注意：pdf2image需要poppler，这里使用简单模式
            try:
                # 尝试直接使用pdf2image
                images = pdf2image.convert_from_path(
                    str(pdf_path),
                    first_page=page_num + 1,
                    last_page=page_num + 1,
                    dpi=150  # 中等分辨率
                )
                
                if not images:
                    logger.error("无法将PDF页面转换为图像")
                    return ""
                
                image = images[0]
                
            except Exception as e:
                logger.error(f"PDF转图像失败: {e}")
                logger.info("请确保已安装poppler: sudo apt-get install poppler-utils")
                return ""
            
            # OCR处理
            try:
                text = pytesseract.image_to_string(image, lang=self.lang)
                logger.info(f"✅ OCR完成，提取 {len(text)} 个字符")
                return text.strip()
                
            except Exception as e:
                logger.error(f"OCR处理失败: {e}")
                return ""
                
        except Exception as e:
            logger.error(f"提取文本时发生错误: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path, pages=None):
        """
        从PDF的多个页面提取文本
        
        Args:
            pdf_path: PDF文件路径
            pages: 页面列表，如[0, 1, 2]，None表示所有页面
            
        Returns:
            dict: {页面编号: 文本内容}
        """
        if not self.is_ocr_available():
            logger.error("OCR功能不可用，请安装依赖")
            return {}
        
        try:
            import PyPDF2
            
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return {}
            
            # 获取PDF总页数
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
            
            # 确定要处理的页面
            if pages is None:
                pages_to_process = list(range(total_pages))
            else:
                pages_to_process = [p for p in pages if 0 <= p < total_pages]
            
            logger.info(f"开始批量OCR处理: {pdf_path.name}")
            logger.info(f"总页数: {total_pages}, 处理页数: {len(pages_to_process)}")
            
            results = {}
            for page_num in pages_to_process:
                text = self.extract_text_from_page(pdf_path, page_num)
                results[page_num] = text
            
            # 统计
            total_chars = sum(len(text) for text in results.values())
            non_empty_pages = sum(1 for text in results.values() if text.strip())
            
            logger.info(f"批量OCR完成:")
            logger.info(f"  处理页面: {len(results)}")
            logger.info(f"  非空页面: {non_empty_pages}")
            logger.info(f"  总字符数: {total_chars}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量提取文本时发生错误: {e}")
            return {}
    
    def analyze_scanned_document(self, pdf_path, sample_pages=3):
        """
        分析扫描件文档特征
        
        Args:
            pdf_path: PDF文件路径
            sample_pages: 采样页面数
            
        Returns:
            dict: 分析结果
        """
        if not self.is_ocr_available():
            logger.error("OCR功能不可用")
            return {}
        
        try:
            import PyPDF2
            import pdf2image
            from PIL import Image
            import numpy as np
            
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"PDF文件不存在: {pdf_path}")
                return {}
            
            # 获取PDF总页数
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                sample_pages = min(sample_pages, total_pages)
            
            logger.info(f"分析扫描件特征: {pdf_path.name}")
            logger.info(f"采样页面: {sample_pages}/{total_pages}")
            
            results = {
                'pdf_name': pdf_path.name,
                'total_pages': total_pages,
                'sample_pages': sample_pages,
                'is_scanned_probability': 0.0,
                'detection_metrics': {},
                'recommendation': ''
            }
            
            # 检测指标
            metrics = {
                'text_density': 0.0,      # 文本密度
                'image_quality': 0.0,     # 图像质量
                'noise_level': 0.0,       # 噪声水平
                'contrast_score': 0.0,    # 对比度评分
            }
            
            page_samples = []
            
            # 采样分析
            for i in range(sample_pages):
                try:
                    # 转换为图像
                    images = pdf2image.convert_from_path(
                        str(pdf_path),
                        first_page=i + 1,
                        last_page=i + 1,
                        dpi=100  # 低分辨率用于分析
                    )
                    
                    if not images:
                        continue
                    
                    image = images[0]
                    
                    # 转换为灰度图
                    gray_image = image.convert('L')
                    img_array = np.array(gray_image)
                    
                    # 计算基础指标
                    # 1. 文本密度（通过边缘检测近似）
                    edges = np.abs(np.diff(img_array, axis=1)).mean()
                    metrics['text_density'] += edges / 255.0
                    
                    # 2. 图像质量（通过方差）
                    metrics['image_quality'] += np.var(img_array) / 10000.0
                    
                    # 3. 噪声水平（通过局部方差）
                    local_var = np.var(img_array[:50, :50]) if img_array.shape[0] > 50 and img_array.shape[1] > 50 else 0
                    metrics['noise_level'] += local_var / 1000.0
                    
                    # 4. 对比度评分
                    min_val, max_val = img_array.min(), img_array.max()
                    if max_val > min_val:
                        metrics['contrast_score'] += (max_val - min_val) / 255.0
                    
                    page_samples.append(i)
                    
                except Exception as e:
                    logger.warning(f"分析页面 {i + 1} 时出错: {e}")
                    continue
            
            if page_samples:
                # 计算平均指标
                for key in metrics:
                    metrics[key] /= len(page_samples)
                
                # 计算扫描件概率
                # 文本密度低 + 图像质量高 = 可能是扫描件
                text_density_score = 1.0 - min(metrics['text_density'], 1.0)
                image_quality_score = min(metrics['image_quality'], 1.0)
                
                scanned_probability = (text_density_score * 0.6 + image_quality_score * 0.4)
                
                results['is_scanned_probability'] = round(scanned_probability, 3)
                results['detection_metrics'] = {k: round(v, 3) for k, v in metrics.items()}
                
                # 生成建议
                if scanned_probability > 0.7:
                    results['recommendation'] = '高概率扫描件，建议使用OCR模式'
                elif scanned_probability > 0.4:
                    results['recommendation'] = '可能包含扫描页面，建议测试OCR'
                else:
                    results['recommendation'] = '可能是文本PDF，可直接处理'
            
            logger.info(f"扫描件分析完成:")
            logger.info(f"  扫描件概率: {results['is_scanned_probability']:.1%}")
            logger.info(f"  文本密度: {metrics['text_density']:.3f}")
            logger.info(f"  图像质量: {metrics['image_quality']:.3f}")
            logger.info(f"  建议: {results['recommendation']}")
            
            return results
            
        except Exception as e:
            logger.error(f"分析扫描件特征时出错: {e}")
            return {}
    
    def preprocess_image(self, image):
        """
        预处理图像以提高OCR准确性
        
        Args:
            image: PIL Image对象
            
        Returns:
            PIL Image: 预处理后的图像
        """
        if not self.enable_preprocessing:
            return image
        
        try:
            from PIL import Image, ImageFilter, ImageOps
            import numpy as np
            
            logger.debug("开始图像预处理")
            
            # 1. 转换为灰度图
            if image.mode != 'L':
                gray_image = image.convert('L')
            else:
                gray_image = image
            
            # 2. 基础去噪（中值滤波）
            try:
                denoised = gray_image.filter(ImageFilter.MedianFilter(size=3))
            except:
                denoised = gray_image  # 如果失败，使用原图
            
            # 3. 增强对比度（直方图均衡化）
            try:
                enhanced = ImageOps.equalize(denoised)
            except:
                enhanced = denoised
            
            # 4. 二值化（自适应阈值）
            try:
                img_array = np.array(enhanced)
                # 简单阈值处理
                threshold = np.median(img_array)
                binary_array = (img_array > threshold).astype(np.uint8) * 255
                binary_image = Image.fromarray(binary_array)
            except:
                binary_image = enhanced
            
            logger.debug("图像预处理完成")
            return binary_image
            
        except Exception as e:
            logger.warning(f"图像预处理失败: {e}, 使用原图")
            return image
    
    def extract_text_with_preprocessing(self, pdf_path, page_num):
        """
        提取文本（带预处理）
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页面编号
            
        Returns:
            str: 提取的文本
        """
        if not self.is_ocr_available():
            logger.error("OCR功能不可用")
            return ""
        
        try:
            import pytesseract
            import pdf2image
            from PIL import Image
            
            pdf_path = Path(pdf_path)
            
            # 将PDF页面转换为图像
            images = pdf2image.convert_from_path(
                str(pdf_path),
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=200  # 较高分辨率用于OCR
            )
            
            if not images:
                logger.error("无法将PDF页面转换为图像")
                return ""
            
            image = images[0]
            
            # 预处理图像
            if self.enable_preprocessing:
                processed_image = self.preprocess_image(image)
                logger.debug(f"使用预处理图像进行OCR")
            else:
                processed_image = image
                logger.debug(f"使用原始图像进行OCR")
            
            # OCR处理
            text = pytesseract.image_to_string(processed_image, lang=self.lang)
            
            char_count = len(text)
            logger.info(f"OCR完成: 第 {page_num + 1} 页，提取 {char_count} 字符")
            
            if char_count < 10:
                logger.warning(f"提取文本较少，可能页面空白或OCR失败")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"带预处理的OCR提取失败: {e}")
            return ""

def test_ocr_functionality():
    """测试OCR功能"""
    print("🧪 测试OCR基础功能")
    
    # 创建OCR处理器
    ocr = PDFOCR()
    
    if not ocr.is_ocr_available():
        print("❌ OCR依赖不完整，无法测试")
        print("请安装: pip install pytesseract pdf2image Pillow")
        return False
    
    print("✅ OCR依赖检查通过")
    
    # 测试文本提取（模拟）
    print("\n📄 OCR功能测试:")
    print("1. 依赖检查: 通过")
    print("2. 语言支持: 英文+简体中文")
    print("3. 图像转换: pdf2image")
    print("4. OCR引擎: Tesseract")
    
    # 检查是否有测试PDF
    test_dir = Path("test_pdf_files")
    if test_dir.exists():
        pdf_files = list(test_dir.glob("*.pdf"))
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"\n📋 找到测试PDF: {test_pdf.name}")
            print("运行命令测试:")
            print(f"  python pdf_chapter_splitter_v2.py -i {test_pdf} --ocr-test")
        else:
            print("\n📋 测试目录中没有PDF文件")
    else:
        print("\n📋 测试目录不存在")
    
    return True

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF OCR测试工具')
    parser.add_argument('--test', action='store_true', help='测试OCR功能')
    parser.add_argument('--pdf', type=str, help='PDF文件路径')
    parser.add_argument('--page', type=int, default=0, help='页面编号（从0开始）')
    parser.add_argument('--lang', type=str, default='eng+chi_sim', help='OCR语言')
    
    args = parser.parse_args()
    
    if args.test:
        test_ocr_functionality()
        return
    
    if args.pdf:
        ocr = PDFOCR(lang=args.lang)
        
        if not ocr.is_ocr_available():
            print("❌ OCR功能不可用")
            print("请安装依赖: pip install pytesseract pdf2image Pillow")
            return
        
        text = ocr.extract_text_from_page(args.pdf, args.page)
        
        if text:
            print(f"\n✅ 第 {args.page + 1} 页OCR结果:")
            print("-" * 50)
            print(text[:500] + ("..." if len(text) > 500 else ""))
            print("-" * 50)
            print(f"总字符数: {len(text)}")
        else:
            print("❌ OCR提取失败")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()