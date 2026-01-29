#!/usr/bin/env python3
"""
基础测试 - 验证代码结构（不依赖外部包）
"""

import os
import sys
import ast
from pathlib import Path

def test_file_structure():
    """测试文件结构"""
    print("📁 测试文件结构...")
    
    required_files = [
        'xlsx2md.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        'TESTING.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

def test_python_syntax():
    """测试Python语法（不导入）"""
    print("\n🐍 测试Python语法...")
    
    try:
        # 使用ast解析语法
        with open('xlsx2md.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析语法树
        tree = ast.parse(content)
        
        # 检查主要类是否存在
        class_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)
        
        if 'ExcelToMarkdownConverter' in class_names:
            print("✅ ExcelToMarkdownConverter 类存在")
        else:
            print("❌ ExcelToMarkdownConverter 类不存在")
            return False
        
        # 检查主函数是否存在
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        if 'main' in function_names:
            print("✅ main 函数存在")
        else:
            print("❌ main 函数不存在")
            return False
        
        print("✅ xlsx2md.py 语法正确")
        return True
        
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 解析错误: {e}")
        return False

def test_requirements():
    """测试requirements文件"""
    print("\n📦 测试requirements.txt...")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        required_packages = ['pandas', 'openpyxl', 'markdown']
        found_packages = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                for pkg in required_packages:
                    if pkg in line.lower():
                        found_packages.append(pkg)
        
        missing = set(required_packages) - set(found_packages)
        if missing:
            print(f"❌ 缺少包: {missing}")
            return False
        else:
            print("✅ requirements.txt 包含所有必需包")
            return True
            
    except Exception as e:
        print(f"❌ 读取requirements.txt失败: {e}")
        return False

def test_readme_content():
    """测试README内容"""
    print("\n📖 测试README内容...")
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            '功能特点',
            '安装依赖',
            '使用方法',
            '输出格式'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ README缺少章节: {missing_sections}")
            return False
        else:
            print("✅ README内容完整")
            return True
            
    except Exception as e:
        print(f"❌ 读取README失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("Excel转Markdown工具 - 基础测试")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_python_syntax,
        test_requirements,
        test_readme_content
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过!")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())