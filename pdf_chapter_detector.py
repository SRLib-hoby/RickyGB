#!/usr/bin/env python3
"""
PDF章节检测器 - Sprint 3
智能识别PDF中的章节边界
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChapterDetector:
    """章节检测器 - 智能识别章节边界"""
    
    def __init__(self, min_chapter_pages=5, max_chapter_pages=50):
        """
        初始化章节检测器
        
        Args:
            min_chapter_pages: 最小章节页数
            max_chapter_pages: 最大章节页数
        """
        self.min_chapter_pages = min_chapter_pages
        self.max_chapter_pages = max_chapter_pages
        
        # 章节标题模式
        self.chapter_patterns = [
            # 中文章节模式
            r'第[零一二三四五六七八九十百千万\d]+章',
            r'第[零一二三四五六七八九十百千万\d]+节',
            r'[零一二三四五六七八九十]、',  # 一、二、
            r'\d+[\.、]',  # 1. 1、
            r'[A-Z]\.',  # A. B.
            
            # 英文章节模式
            r'Chapter\s+\d+',
            r'Chapter\s+[IVXLCDM]+',  # Roman numerals
            r'Section\s+\d+',
            r'Part\s+\d+',
            
            # 通用模式
            r'^\s*\d+\.\s+',  # 数字开头
            r'^\s*[A-Z]\s+',  # 大写字母开头
        ]
        
        # 编译正则表达式
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.chapter_patterns]
        
        logger.info(f"初始化章节检测器")
        logger.info(f"最小章节页数: {min_chapter_pages}")
        logger.info(f"最大章节页数: {max_chapter_pages}")
    
    def detect_from_text(self, page_texts: Dict[int, str]) -> List[int]:
        """
        从页面文本中检测章节边界
        
        Args:
            page_texts: 页面编号到文本的映射
            
        Returns:
            List[int]: 章节起始页码列表
        """
        if not page_texts:
            return []
        
        total_pages = max(page_texts.keys()) + 1
        logger.info(f"开始章节检测，总页数: {total_pages}")
        
        # 收集所有可能的章节起始页
        candidate_pages = []
        
        for page_num, text in page_texts.items():
            if not text or len(text.strip()) < 10:
                continue
            
            # 检查是否为章节起始
            is_chapter_start, confidence, reason = self._is_chapter_start(text, page_num)
            
            if is_chapter_start:
                candidate_pages.append({
                    'page': page_num,
                    'confidence': confidence,
                    'reason': reason,
                    'text_preview': text[:100]
                })
        
        # 如果没有检测到章节，使用固定页数
        if not candidate_pages:
            logger.info("未检测到章节标题，使用固定页数拆分")
            return self._fallback_to_fixed_pages(total_pages)
        
        # 按页码排序
        candidate_pages.sort(key=lambda x: x['page'])
        
        logger.info(f"检测到 {len(candidate_pages)} 个可能的章节起始")
        for i, candidate in enumerate(candidate_pages[:5]):  # 显示前5个
            logger.info(f"  候选 {i+1}: 页 {candidate['page']+1}, 置信度: {candidate['confidence']:.2f}, 原因: {candidate['reason']}")
        
        # 选择章节边界
        chapter_boundaries = self._select_chapter_boundaries(candidate_pages, total_pages)
        
        logger.info(f"确定章节边界: {len(chapter_boundaries)} 个章节")
        for i, boundary in enumerate(chapter_boundaries):
            logger.info(f"  第 {i+1} 章起始: 页 {boundary+1}")
        
        return chapter_boundaries
    
    def _is_chapter_start(self, text: str, page_num: int) -> Tuple[bool, float, str]:
        """
        判断文本是否为章节起始
        
        Returns:
            (是否章节起始, 置信度, 原因)
        """
        text = text.strip()
        
        # 规则1: 检查章节模式
        for pattern in self.patterns:
            if pattern.search(text):
                # 检查是否在文本开头附近
                lines = text.split('\n')
                for line in lines[:3]:  # 只检查前3行
                    if pattern.search(line.strip()):
                        match_text = pattern.search(line.strip()).group()
                        return True, 0.8, f"匹配模式: {match_text}"
        
        # 规则2: 检查标题特征（短文本、大写开头等）
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        if len(first_line) < 100 and len(first_line) > 5:
            # 检查是否像标题
            title_features = 0
            
            # 特征1: 以数字或大写字母开头
            if first_line and (first_line[0].isdigit() or first_line[0].isupper()):
                title_features += 1
            
            # 特征2: 不包含句号（可能不是段落）
            if '.' not in first_line:
                title_features += 1
            
            # 特征3: 行数少
            if len(lines) <= 3:
                title_features += 1
            
            if title_features >= 2:
                return True, 0.6, f"标题特征: {title_features}/3"
        
        # 规则3: 页面位置（文档开头几页可能是章节）
        if page_num < 5:
            # 检查是否包含"目录"、"前言"等
            if any(keyword in text for keyword in ['目录', '前言', '引言', '摘要', 'abstract', 'contents']):
                return True, 0.7, "文档起始部分"
        
        return False, 0.0, "不符合章节特征"
    
    def _select_chapter_boundaries(self, candidates: List[Dict], total_pages: int) -> List[int]:
        """
        从候选页面中选择章节边界
        
        Args:
            candidates: 候选页面列表
            total_pages: 总页数
            
        Returns:
            List[int]: 选择的章节边界
        """
        if not candidates:
            return self._fallback_to_fixed_pages(total_pages)
        
        # 按置信度排序
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        selected_boundaries = []
        
        # 总是从第0页开始
        selected_boundaries.append(0)
        
        # 选择高置信度的候选
        high_confidence = [c for c in candidates if c['confidence'] > 0.7]
        
        for candidate in high_confidence:
            page_num = candidate['page']
            
            # 检查是否与已有边界太近
            if selected_boundaries:
                last_boundary = selected_boundaries[-1]
                pages_since_last = page_num - last_boundary
                
                if pages_since_last >= self.min_chapter_pages and pages_since_last <= self.max_chapter_pages:
                    selected_boundaries.append(page_num)
                elif pages_since_last < self.min_chapter_pages:
                    logger.debug(f"跳过页 {page_num+1}: 距离上一章节太近 ({pages_since_last} 页)")
                else:
                    logger.debug(f"跳过页 {page_num+1}: 距离上一章节太远 ({pages_since_last} 页)")
            else:
                selected_boundaries.append(page_num)
        
        # 确保覆盖所有页面
        if selected_boundaries[-1] + self.max_chapter_pages < total_pages:
            # 添加中间边界
            current_page = selected_boundaries[-1]
            while current_page + self.max_chapter_pages < total_pages:
                current_page += self.max_chapter_pages
                selected_boundaries.append(current_page)
        
        # 排序并去重
        selected_boundaries = sorted(set(selected_boundaries))
        
        return selected_boundaries
    
    def _fallback_to_fixed_pages(self, total_pages: int) -> List[int]:
        """回退到固定页数拆分"""
        boundaries = []
        avg_pages = (self.min_chapter_pages + self.max_chapter_pages) // 2
        
        for start in range(0, total_pages, avg_pages):
            boundaries.append(start)
        
        return boundaries
    
    def analyze_document_structure(self, page_texts: Dict[int, str]) -> Dict:
        """
        分析文档结构
        
        Returns:
            Dict: 结构分析结果
        """
        if not page_texts:
            return {'error': '无页面文本'}
        
        total_pages = max(page_texts.keys()) + 1
        
        # 检测章节
        chapter_boundaries = self.detect_from_text(page_texts)
        
        # 分析文本特征
        text_stats = self._analyze_text_statistics(page_texts)
        
        # 构建结构
        structure = {
            'total_pages': total_pages,
            'detected_chapters': len(chapter_boundaries),
            'chapter_boundaries': chapter_boundaries,
            'text_statistics': text_stats,
            'detection_method': 'smart' if len(chapter_boundaries) > 1 else 'fixed',
            'confidence': self._calculate_confidence(chapter_boundaries, page_texts)
        }
        
        # 添加章节详情
        chapters = []
        for i in range(len(chapter_boundaries)):
            start_page = chapter_boundaries[i]
            end_page = chapter_boundaries[i + 1] if i + 1 < len(chapter_boundaries) else total_pages
            
            # 提取章节标题
            chapter_title = "未知章节"
            if start_page in page_texts:
                first_page_text = page_texts[start_page]
                lines = first_page_text.split('\n')
                if lines:
                    chapter_title = lines[0].strip()[:50]
            
            chapters.append({
                'chapter_number': i + 1,
                'start_page': start_page,
                'end_page': end_page,
                'page_count': end_page - start_page,
                'title': chapter_title
            })
        
        structure['chapters'] = chapters
        
        return structure
    
    def _analyze_text_statistics(self, page_texts: Dict[int, str]) -> Dict:
        """分析文本统计信息"""
        if not page_texts:
            return {}
        
        total_chars = sum(len(text) for text in page_texts.values())
        avg_chars_per_page = total_chars / len(page_texts) if page_texts else 0
        
        # 计算文本密度变化
        char_counts = [len(page_texts.get(i, '')) for i in range(max(page_texts.keys()) + 1)]
        
        return {
            'total_pages_analyzed': len(page_texts),
            'total_characters': total_chars,
            'avg_characters_per_page': avg_chars_per_page,
            'max_characters_per_page': max(char_counts) if char_counts else 0,
            'min_characters_per_page': min([c for c in char_counts if c > 0]) if char_counts else 0
        }
    
    def _calculate_confidence(self, boundaries: List[int], page_texts: Dict[int, str]) -> float:
        """计算检测置信度"""
        if len(boundaries) <= 1:
            return 0.3  # 低置信度
        
        # 基于边界数量和分布计算置信度
        total_pages = max(page_texts.keys()) + 1 if page_texts else 1
        
        # 检查边界分布是否合理
        chapter_lengths = []
        for i in range(len(boundaries) - 1):
            length = boundaries[i + 1] - boundaries[i]
            chapter_lengths.append(length)
        
        if chapter_lengths:
            avg_length = sum(chapter_lengths) / len(chapter_lengths)
            # 计算长度一致性
            variance = sum((length - avg_length) ** 2 for length in chapter_lengths) / len(chapter_lengths)
            consistency = 1.0 / (1.0 + variance)  # 方差越小，一致性越高
            
            # 综合置信度
            confidence = 0.3 + 0.5 * consistency + 0.2 * (len(boundaries) / (total_pages / 20))
            return min(confidence, 1.0)
        
        return 0.5

def test_chapter_detection():
    """测试章节检测功能"""
    print("🧪 测试章节检测功能")
    
    detector = ChapterDetector()
    
    # 创建测试数据
    test_texts = {
        0: "第一章 引言\n\n本文介绍PDF章节检测技术...",
        1: "这是引言部分的继续内容...",
        2: "更多引言内容...",
        3: "第二章 技术实现\n\n本章介绍具体实现方法...",
        4: "技术细节部分...",
        5: "更多技术内容...",
        6: "第三章 实验结果\n\n展示实验数据和结果...",
        7: "结果分析...",
        8: "结论部分...",
    }
    
    print(f"测试数据: {len(test_texts)} 页")
    
    # 检测章节
    boundaries = detector.detect_from_text(test_texts)
    
    print(f"\n检测结果:")
    print(f"章节边界: {boundaries}")
    print(f"章节数: {len(boundaries)}")
    
    # 分析结构
    structure = detector.analyze_document_structure(test_texts)
    
    print(f"\n文档结构分析:")
    print(f"检测方法: {structure['detection_method']}")
    print(f"置信度: {structure['confidence']:.2f}")
    
    print(f"\n章节详情:")
    for chapter in structure['chapters']:
        print(f"  第{chapter['chapter_number']}章: 页 {chapter['start_page']+1}-{chapter['end_page']}, "
              f"{chapter['page_count']}页, 标题: {chapter['title']}")
    
    return len(boundaries) > 1

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF章节检测器')
    parser.add_argument('--test', action='store_true', help='测试功能')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_chapter_detection()
        if success:
            print("\n✅ 章节检测测试通过")
            return 0
        else:
            print("\n❌ 章节检测测试失败")
            return 1
    
    parser.print_help()

if __name__ == "__main__":
    main()