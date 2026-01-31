#!/usr/bin/env python3
"""
Markdown合并工具测试
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_basic_functionality():
    """测试基本功能"""
    print_header("测试基本功能")
    
    # 检查脚本是否存在
    script_path = Path("merge_markdown.py")
    if not script_path.exists():
        print("❌ 主脚本不存在")
        return False
    
    print(f"✅ 找到脚本: {script_path}")
    
    # 测试导入
    try:
        from merge_markdown import MarkdownMerger
        print("✅ 模块导入成功")
        
        # 创建合并器
        merger = MarkdownMerger()
        print("✅ 合并器创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_command_line_interface():
    """测试命令行接口"""
    print_header("测试命令行接口")
    
    # 测试帮助命令
    result = subprocess.run(
        [sys.executable, "merge_markdown.py", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 帮助命令正常")
        
        # 检查关键参数
        required_params = ['--dir', '--output', '--recursive', '--no-toc', '--test']
        
        for param in required_params:
            if param in result.stdout:
                print(f"✅ 包含参数: {param}")
            else:
                print(f"⚠️  缺少参数: {param}")
        
        return True
    else:
        print("❌ 帮助命令失败")
        print(f"错误: {result.stderr}")
        return False

def test_sample_creation():
    """测试示例文件创建"""
    print_header("测试示例文件创建")
    
    cmd = [
        sys.executable, "merge_markdown.py",
        "--test",
        "--sample-count", "3"
    ]
    
    print(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ 示例创建测试通过")
            
            # 检查输出
            output = result.stdout
            if "测试Markdown合并功能" in output:
                print("✅ 包含测试标题")
            if "创建示例文件" in output:
                print("✅ 包含示例创建信息")
            if "测试成功" in output:
                print("✅ 包含测试成功信息")
            
            # 检查生成的文件
            sample_dir = Path("sample_markdown")
            if sample_dir.exists():
                md_files = list(sample_dir.glob("*.md"))
                if len(md_files) >= 3:
                    print(f"✅ 创建了 {len(md_files)} 个示例文件")
                    
                    # 检查合并文件
                    merged_file = Path("test_merged.md")
                    if merged_file.exists():
                        size = merged_file.stat().st_size
                        print(f"✅ 生成了合并文件: {merged_file} ({size:,} 字节)")
                        return True
                    else:
                        print("❌ 未生成合并文件")
                        return False
                else:
                    print(f"❌ 示例文件数量不足: {len(md_files)}")
                    return False
            else:
                print("❌ 示例目录未创建")
                return False
                
        else:
            print("❌ 示例创建测试失败")
            print(f"错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️  测试超时")
        return False
    except Exception as e:
        print(f"💥 测试异常: {e}")
        return False

def test_actual_merge():
    """测试实际合并功能"""
    print_header("测试实际合并功能")
    
    # 创建测试目录结构
    test_dir = Path("test_markdown_merge")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文件
    test_files = [
        ("intro.md", "# 介绍\n\n这是介绍文档。"),
        ("chapter1.md", "# 第一章 基础\n\n基础内容。"),
        ("chapter2.md", "# 第二章 进阶\n\n进阶内容。"),
        ("summary.md", "# 总结\n\n文档总结。")
    ]
    
    for filename, content in test_files:
        file_path = test_dir / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"创建测试文件: {file_path}")
    
    # 测试合并
    output_file = Path("merged_test_output.md")
    
    cmd = [
        sys.executable, "merge_markdown.py",
        "--dir", str(test_dir),
        "--output", str(output_file),
        "--recursive"
    ]
    
    print(f"\n命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("\n输出摘要:")
        print("-" * 40)
        
        # 显示关键信息
        lines = result.stdout.split('\n')
        key_lines = [line for line in lines if any(keyword in line.lower() for keyword in [
            '开始', '找到', '处理', '完成', '输出', '文件', '行数'
        ])]
        
        for line in key_lines[:10]:
            print(f"  {line}")
        
        print("-" * 40)
        
        if result.returncode == 0:
            # 检查输出文件
            if output_file.exists():
                content = output_file.read_text(encoding='utf-8')
                
                # 检查关键内容
                checks = [
                    ("目录", "📚 目录" in content),
                    ("文件标题", "介绍" in content and "基础" in content and "进阶" in content),
                    ("文件信息", "**文件**" in content and "**大小**" in content),
                    ("统计信息", "合并统计" in content)
                ]
                
                all_passed = True
                for check_name, check_result in checks:
                    if check_result:
                        print(f"✅ 包含 {check_name}")
                    else:
                        print(f"❌ 缺少 {check_name}")
                        all_passed = False
                
                if all_passed:
                    size = output_file.stat().st_size
                    print(f"\n✅ 合并测试通过!")
                    print(f"   输出文件: {output_file} ({size:,} 字节)")
                    print(f"   包含 {len(test_files)} 个文件内容")
                    return True
                else:
                    print("\n❌ 合并内容检查失败")
                    return False
            else:
                print("❌ 输出文件未创建")
                return False
        else:
            print("❌ 合并命令失败")
            print(f"错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 合并测试异常: {e}")
        return False

def create_usage_examples():
    """创建使用示例"""
    print_header("使用示例")
    
    print("1. 合并当前目录的所有.md文件:")
    print("   python merge_markdown.py --dir . --output merged.md")
    
    print("\n2. 递归合并子目录:")
    print("   python merge_markdown.py --dir docs --output combined.md --recursive")
    
    print("\n3. 不生成目录:")
    print("   python merge_markdown.py --dir . --output simple.md --no-toc")
    
    print("\n4. 测试功能:")
    print("   python merge_markdown.py --test --sample-count 5")
    
    print("\n5. 合并特定目录:")
    print("   python merge_markdown.py --dir /path/to/markdown --output all_docs.md")
    
    return True

def main():
    """主测试函数"""
    print_header("Markdown合并工具测试")
    
    all_tests_passed = True
    
    # 测试1: 基本功能
    test1 = test_basic_functionality()
    all_tests_passed = all_tests_passed and test1
    
    # 测试2: 命令行接口
    test2 = test_command_line_interface()
    all_tests_passed = all_tests_passed and test2
    
    # 测试3: 示例创建
    test3 = test_sample_creation()
    all_tests_passed = all_tests_passed and test3
    
    # 测试4: 实际合并
    test4 = test_actual_merge()
    all_tests_passed = all_tests_passed and test4
    
    # 显示使用示例
    create_usage_examples()
    
    # 总结
    print_header("测试结果总结")
    
    print(f"✅ 基本功能测试: {'通过' if test1 else '失败'}")
    print(f"✅ 命令行接口测试: {'通过' if test2 else '失败'}")
    print(f"✅ 示例创建测试: {'通过' if test3 else '失败'}")
    print(f"✅ 实际合并测试: {'通过' if test4 else '失败'}")
    
    if all_tests_passed:
        print("\n🎉 所有测试通过!")
        print("\n🚀 Markdown合并工具开发完成!")
        
        print("\n📋 主要功能:")
        print("• 自动扫描目录中的.md文件")
        print("• 智能提取文件标题")
        print("• 生成带链接的目录")
        print("• 保持原始格式和链接")
        print("• 详细的合并统计")
        
        print("\n💡 使用场景:")
        print("• 合并项目文档")
        print("• 整理学习笔记")
        print("• 生成完整报告")
        print("• 备份Markdown文件")
        
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())