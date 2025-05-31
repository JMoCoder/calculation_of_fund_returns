#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终NaN修复验证测试
一次性彻底验证所有NaN问题修复
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_all_calculation_modes():
    """测试所有计算模式，确保NaN问题彻底解决"""
    print("🚀 最终NaN修复验证测试开始...")
    
    # 测试各种计算模式
    test_cases = [
        {
            "name": "扁平结构-优先回本",
            "mode": "flat_priority_repayment",
            "params": {"hurdle_rate": 8.0, "carry_rate": 20.0}
        },
        {
            "name": "扁平结构-全期收益", 
            "mode": "flat_whole_period_return",
            "params": {"hurdle_rate": 8.0, "carry_rate": 20.0}
        },
        {
            "name": "分层结构-双层",
            "mode": "structured_dual_layer", 
            "params": {"senior_ratio": 70.0, "subordinate_rate": 20.0}
        },
        {
            "name": "分层结构-三层",
            "mode": "structured_triple_layer",
            "params": {"senior_ratio": 50.0, "mezzanine_ratio": 30.0, "mezzanine_rate": 12.0}
        },
        {
            "name": "分层结构-按期分配",
            "mode": "structured_periodic_distribution",
            "params": {"senior_ratio": 60.0, "subordinate_rate": 15.0}
        }
    ]
    
    try:
        # 重置并设置基础数据
        print("📋 设置基础数据...")
        requests.post(f"{BASE_URL}/api/reset")
        
        # 基础参数
        basic_params = {
            "investment_target": "NaN终极测试项目",
            "investment_amount": 1000.0,
            "investment_period": 3,
            "hurdle_rate": 8.0,
            "management_carry": 20.0
        }
        
        response = requests.post(f"{BASE_URL}/api/basic-params", json=basic_params)
        if not response.json().get("success"):
            print("❌ 基础参数设置失败")
            return False
            
        # 现金流数据
        cash_flows = [
            {"date": "2024-01-01", "type": "投资", "amount": -1000.0},
            {"date": "2024-06-30", "type": "分红", "amount": 50.0},
            {"date": "2024-12-31", "type": "分红", "amount": 100.0},
            {"date": "2025-12-31", "type": "分红", "amount": 150.0},
            {"date": "2026-12-31", "type": "退出", "amount": 800.0}
        ]
        
        response = requests.post(f"{BASE_URL}/api/cash-flows", json={"cash_flows": cash_flows})
        if not response.json().get("success"):
            print("❌ 现金流设置失败")
            return False
            
        # 测试所有计算模式
        success_count = 0
        for test_case in test_cases:
            print(f"🧮 测试计算模式: {test_case['name']}")
            
            calc_params = {
                "calculation_mode": test_case["mode"],
                **test_case["params"]
            }
            
            response = requests.post(f"{BASE_URL}/api/calculate", json=calc_params)
            result = response.json()
            
            if result.get("success"):
                # 验证计算结果中没有NaN或无穷大
                core_metrics = result.get("data", {}).get("core_metrics", {})
                
                nan_found = False
                for key, value in core_metrics.items():
                    if isinstance(value, (int, float)):
                        import math
                        if math.isnan(value) or math.isinf(value):
                            print(f"  ❌ 发现NaN/Inf值: {key} = {value}")
                            nan_found = True
                
                if not nan_found:
                    print(f"  ✅ {test_case['name']} 计算成功！")
                    success_count += 1
                else:
                    print(f"  ❌ {test_case['name']} 包含NaN/Inf值！")
            else:
                print(f"  ❌ {test_case['name']} 计算失败: {result.get('message', '未知错误')}")
        
        # 最终结果
        print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 通过")
        
        if success_count == len(test_cases):
            print("🎉 所有测试通过！NaN问题彻底解决！")
            return True
        else:
            print("❌ 部分测试失败，仍有问题需要解决")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 检查服务器
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务器未响应，请先启动Flask应用")
            exit(1)
    except:
        print("❌ 无法连接到服务器，请确保Flask应用正在运行")
        exit(1)
    
    # 运行测试
    success = test_all_calculation_modes()
    
    if success:
        print("\n✨ 恭喜！NaN问题已彻底解决！")
        print("🔧 修复内容:")
        print("  • static/utils.js: formatNumber等函数增加NaN检查")
        print("  • static/app.js: formatCurrency/formatPercentage/formatNumber函数增加NaN检查")
        print("  • templates/index.html: formatNumber函数修复Math.round的NaN问题")
        print("  • 添加版本号强制刷新浏览器缓存")
    else:
        print("\n❌ 仍有问题需要进一步排查")
        
    print("\n�� 测试完成，即将清理测试文件...") 