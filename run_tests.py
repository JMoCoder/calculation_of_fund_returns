#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金收益计算器测试运行器

该脚本提供了便捷的测试运行接口，支持以下功能：
1. 运行所有测试
2. 运行指定类型的测试
3. 生成测试报告
4. 测试覆盖率统计

使用方法：
python run_tests.py                    # 运行所有测试
python run_tests.py --api              # 只运行API测试
python run_tests.py --calculations     # 只运行计算逻辑测试
python run_tests.py --charts          # 只运行图表功能测试
python run_tests.py --quick           # 快速测试（跳过耗时测试）
"""

import argparse
import sys
import os
import subprocess
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_command(command, description):
    """运行命令并返回结果"""
    print(f"\n🚀 {description}")
    print(f"命令: {command}")
    print("-" * 60)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print("✅ 测试通过")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ 测试失败")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            if result.stdout:
                print("输出信息:")
                print(result.stdout)
        
        print(f"⏱️  耗时: {elapsed_time:.2f}秒")
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行测试时发生异常: {e}")
        return False

def run_api_tests():
    """运行API接口测试"""
    return run_command(
        "python tests/test_api.py",
        "运行API接口测试"
    )

def run_calculation_tests():
    """运行计算逻辑测试"""
    return run_command(
        "python tests/test_calculations.py",
        "运行计算逻辑测试"
    )

def run_chart_tests():
    """运行图表功能测试"""
    return run_command(
        "python tests/test_charts.py",
        "运行图表功能测试"
    )

def check_server_running():
    """检查服务器是否运行"""
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="基金收益计算器测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py --api              # 只运行API测试
  python run_tests.py --calculations     # 只运行计算逻辑测试
  python run_tests.py --charts          # 只运行图表功能测试
  python run_tests.py --quick           # 快速测试
        """
    )
    
    parser.add_argument('--api', action='store_true', help='只运行API接口测试')
    parser.add_argument('--calculations', action='store_true', help='只运行计算逻辑测试')
    parser.add_argument('--charts', action='store_true', help='只运行图表功能测试')
    parser.add_argument('--quick', action='store_true', help='快速测试模式')
    parser.add_argument('--no-server-check', action='store_true', help='跳过服务器检查')
    
    args = parser.parse_args()
    
    print(f"{'='*80}")
    print("🧪 基金收益计算器测试运行器")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # 检查服务器状态（除非跳过）
    if not args.no_server_check and (args.api or args.charts or not any([args.api, args.calculations, args.charts])):
        print("\n🔍 检查服务器状态...")
        if not check_server_running():
            print("⚠️  警告: 服务器未运行 (http://localhost:5000)")
            print("   请确保使用 'python app.py' 启动服务器")
            print("   或使用 --no-server-check 跳过此检查")
            response = input("   是否继续运行测试? (y/N): ")
            if response.lower() != 'y':
                print("测试已取消")
                return 1
        else:
            print("✅ 服务器运行正常")
    
    # 统计测试结果
    total_tests = 0
    passed_tests = 0
    
    # 根据参数决定运行哪些测试
    run_all = not any([args.api, args.calculations, args.charts])
    
    if args.calculations or run_all:
        print(f"\n{'🔸'*25} 计算逻辑测试 {'🔸'*25}")
        total_tests += 1
        if run_calculation_tests():
            passed_tests += 1
            print("✅ 计算逻辑测试完成")
        else:
            print("❌ 计算逻辑测试失败")
    
    if args.api or run_all:
        print(f"\n{'🔸'*25} API接口测试 {'🔸'*25}")
        total_tests += 1
        if run_api_tests():
            passed_tests += 1
            print("✅ API接口测试完成")
        else:
            print("❌ API接口测试失败")
    
    if args.charts or run_all:
        print(f"\n{'🔸'*25} 图表功能测试 {'🔸'*25}")
        total_tests += 1
        if run_chart_tests():
            passed_tests += 1
            print("✅ 图表功能测试完成")
        else:
            print("❌ 图表功能测试失败")
    
    # 输出总结
    print(f"\n{'='*80}")
    print(f"🎊 测试总结:")
    print(f"   总测试套件: {total_tests}")
    print(f"   通过套件: {passed_tests}")
    print(f"   失败套件: {total_tests - passed_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！系统功能正常")
    else:
        print("⚠️  存在测试失败，请检查相关功能")
    
    print(f"{'='*80}")
    
    # 返回结果
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 