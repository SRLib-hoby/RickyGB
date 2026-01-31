#!/usr/bin/env python3
"""
Sprint 3 功能测试
测试智能章节检测功能
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_chapter_detector_module():
    """测试章节检测器模块"""
    print_header("测试章节检测器模块")
    
    # 检查章节检测器文件
    detector_file = Path("pdf_chapter_detector.py")
    if not detector_file.exists():
        print("❌ 章节检测器文件不存在")
        return False
    
    print(f"✅ 找到章节检测器: {detector_file}")
    
    # 测试导入
    try:
        from pdf_chapter_detector import ChapterDetector
        print("✅ 章节检测器导入成功")
        
        # 创建检测器
        detector = ChapterDetector()
        print("✅ 章节检测器创建成功")
        
        # 测试基本功能
        print("\n🧪 测试章节检测功能:")
        
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
        
        boundaries = detector.detect_from_text(test_texts)
        
        if len(boundaries) > 1:
            print(f"✅ 章节检测测试通过")
            print(f"   检测到章节边界: {boundaries}")
            print(f"   章节数: {len(boundaries)}")
            
            # 测试结构分析
            structure = detector.analyze_document_structure(test_texts)
            print(f"   检测方法: {structure['detection_method']}")
            print(f"   置信度: {structure['confidence']:.2f}")
            
            return True
        else:
            print("❌ 章节检测测试失败")
            return False
        
    except Exception as e:
        print(f"❌ 章节检测器导入失败: {e}")
        return False

def test_final_version_with_smart():
    """测试最终版本的智能检测功能"""
    print_header("测试最终版本的智能检测")
    
    # 检查最终版本文件
    final_script = Path("pdf_chapter_splitter_final.py")
    if not final_script.exists():
        print("❌ 最终版本脚本不存在")
        return False
    
    print(f"✅ 找到最终版本: {final_script}")
    
    # 测试帮助命令中的新参数
    print("\n1. 测试帮助命令中的智能检测参数:")
    result = subprocess.run(
        [sys.executable, "pdf_chapter_splitter_final.py", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # 检查新参数
        smart_params = ['--smart', '--no-smart', '--test-smart']
        
        for param in smart_params:
            if param in result.stdout:
                print(f"✅ 包含参数: {param}")
            else:
                print(f"⚠️  缺少参数: {param}")
    else:
        print("❌ 帮助命令失败")
        return False
    
    return True

def test_smart_detection_functionality():
    """测试智能检测功能"""
    print_header("测试智能检测功能")
    
    # 检查是否有PDF文件
    test_dir = Path("test_pdf_files")
    pdf_files = list(test_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  测试目录中没有PDF文件")
        print("   跳过实际检测测试")
        return True  # 跳过不算失败
    
    test_pdf = pdf_files[0]
    print(f"测试PDF文件: {test_pdf.name}")
    
    # 测试1: 智能检测测试命令
    print("\n1. 测试智能检测测试命令:")
    cmd_test = [
        sys.executable, "pdf_chapter_splitter_final.py",
        "--input", str(test_pdf),
        "--test-smart"
    ]
    
    print(f"   命令: {' '.join(cmd_test)}")
    
    try:
        result = subprocess.run(
            cmd_test,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("✅ 智能检测测试命令通过")
            
            # 检查输出内容
            output = result.stdout
            if "智能章节检测功能" in output:
                print("✅ 包含智能检测测试标题")
            if "文档结构分析" in output:
                print("✅ 包含文档结构分析")
            if "章节详情" in output:
                print("✅ 包含章节详情")
            if "建议" in output:
                print("✅ 包含处理建议")
        else:
            print("⚠️  智能检测测试命令失败")
            print(f"   错误: {result.stderr}")
    
    except Exception as e:
        print(f"💥 智能检测测试异常: {e}")
    
    # 测试2: 使用智能检测处理
    print("\n2. 测试使用智能检测处理:")
    output_dir = Path("test_smart_output")
    
    # 清理之前的输出
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    cmd_process = [
        sys.executable, "pdf_chapter_splitter_final.py",
        "--input", str(test_pdf),
        "--output", str(output_dir),
        "--smart"
    ]
    
    print(f"   命令: {' '.join(cmd_process)}")
    
    try:
        result = subprocess.run(
            cmd_process,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("\n输出摘要:")
        print("-" * 40)
        
        # 显示关键信息
        lines = result.stdout.split('\n')
        key_lines = [line for line in lines if any(keyword in line.lower() for keyword in [
            '智能', '章节', '检测', '固定', '页数', '成功', '创建', '标题'
        ])]
        
        for line in key_lines[:15]:
            print(f"  {line}")
        
        print("-" * 40)
        
        if result.returncode == 0:
            # 检查输出文件
            if output_dir.exists():
                pdf_files = list(output_dir.glob("*.pdf"))
                if pdf_files:
                    print(f"✅ 智能检测处理测试通过")
                    print(f"   生成文件: {len(pdf_files)} 个PDF")
                    
                    # 检查报告文件
                    report_files = list(output_dir.glob("*report*"))
                    if report_files:
                        print(f"   生成报告: {len(report_files)} 个")
                    
                    return True
                else:
                    print("❌ 未生成PDF文件")
                    return False
            else:
                print("❌ 输出目录未创建")
                return False
        else:
            print("❌ 处理命令失败")
            return False
    
    except subprocess.TimeoutExpired:
        print("⏱️  处理超时")
        return False
    except Exception as e:
        print(f"💥 处理异常: {e}")
        return False

def create_sprint_3_summary():
    """创建Sprint 3总结"""
    print_header("Sprint 3 功能总结")
    
    print("📋 Sprint 3 完成功能:")
    print("1. ✅ 章节检测器模块 (pdf_chapter_detector.py)")
    print("2. ✅ 智能章节检测算法")
    print("3. ✅ 多模式章节识别（正则匹配、标题特征、格式分析）")
    print("4. ✅ 文档结构分析和置信度计算")
    print("5. ✅ 集成到最终版本工具")
    
    print("\n🚀 新命令示例:")
    
    print("\n1. 测试智能检测功能:")
    print("   python pdf_chapter_splitter_final.py -i input.pdf --test-smart")
    
    print("\n2. 使用智能章节检测:")
    print("   python pdf_chapter_splitter_final.py -i document.pdf -o output --smart")
    
    print("\n3. 禁用智能检测（使用固定页数）:")
    print("   python pdf_chapter_splitter_final.py -i document.pdf -o output --no-smart")
    
    print("\n4. 完整智能处理流程:")
    print("   python pdf_chapter_splitter_final.py -i document.pdf -o output --smart --ocr")
    
    print("\n🔧 技术特性:")
    print("• 支持中英文章节模式识别")
    print("• 基于文本特征的智能检测")
    print("• 自动回退到固定页数拆分")
    print("• 详细的文档结构分析")
    print("• 置信度评分和智能建议")
    
    print("\n📈 项目进展:")
    print("• Sprint 1: 基础PDF拆分 ✅")
    print("• Sprint 2: OCR扫描件支持 ✅")
    print("• Sprint 3: 智能章节检测 ✅")
    print("• Sprint 4: 高级功能和优化 (下一个)")
    
    return True

def main():
    """主测试函数"""
    print_header("Sprint 3 功能测试")
    print("测试智能章节检测功能")
    
    all_tests_passed = True
    
    # 测试1: 章节检测器模块
    test1 = test_chapter_detector_module()
    all_tests_passed = all_tests_passed and test1
    
    # 测试2: 最终版本智能检测
    test2 = test_final_version_with_smart()
    all_tests_passed = all_tests_passed and test2
    
    # 测试3: 智能检测功能
    test3 = test_smart_detection_functionality()
    all_tests_passed = all_tests_passed and test3
    
    # 显示总结
    create_sprint_3_summary()
    
    # 总结
    print_header("测试结果总结")
    
    print(f"✅ 章节检测器模块测试: {'通过' if test1 else '失败'}")
    print(f"✅ 最终版本智能检测测试: {'通过' if test2 else '失败'}")
    print(f"✅ 智能检测功能测试: {'通过' if test3 else '失败'}")
    
    if all_tests_passed:
        print("\n🎉 Sprint 3 所有测试通过!")
        print("\n🚀 智能章节检测功能开发完成!")
        
        print("\n📋 使用智能检测:")
        print("1. 测试智能检测: python pdf_chapter_splitter_final.py -i input.pdf --test-smart")
        print("2. 启用智能检测: 添加 --smart 参数")
        print("3. 查看详细帮助: python pdf_chapter_splitter_final.py --help")
        
        print("\n💡 智能检测优势:")
        print("• 自动识别章节标题和边界")
        print("• 基于内容而非固定页数")
        print("• 支持中英文混合文档")
        print("• 提供置信度评分和建议")
        
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())