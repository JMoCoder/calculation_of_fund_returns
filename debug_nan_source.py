#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NaN源头精确调试脚本
专门用于定位NaN值的产生位置
"""

import requests
import json
import traceback

BASE_URL = "http://localhost:5000"

def debug_calculation():
    """调试具体的计算过程"""
    print("🔍 开始精确NaN源头调试...")
    
    try:
        # 重置系统
        print("1️⃣ 重置系统...")
        response = requests.post(f"{BASE_URL}/api/reset")
        
        # 设置基本参数
        print("2️⃣ 设置基本参数...")
        basic_params = {
            "investment_target": "调试测试项目",
            "investment_amount": 1000.0,
            "investment_period": 3,
            "hurdle_rate": 8.0,
            "management_carry": 20.0
        }
        
        response = requests.post(f"{BASE_URL}/api/basic-params", json=basic_params)
        if not response.json().get("success"):
            print(f"❌ 基本参数设置失败: {response.json()}")
            return
        
        # 设置现金流
        print("3️⃣ 设置现金流...")
        cash_flows = [100.0, 200.0, 300.0]
        response = requests.post(f"{BASE_URL}/api/cash-flows", json={"cash_flows": cash_flows})
        if not response.json().get("success"):
            print(f"❌ 现金流设置失败: {response.json()}")
            return
        
        # 执行计算并详细分析结果
        print("4️⃣ 执行计算...")
        calc_data = {"mode": "flat_priority_repayment"}
        response = requests.post(f"{BASE_URL}/api/calculate", json=calc_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 计算响应状态: {result.get('success')}")
            
            if result.get("success"):
                print("🔍 分析计算结果中的数值...")
                
                # 检查核心指标
                core_metrics = result.get('core_metrics', {})
                print(f"IRR: {core_metrics.get('irr')} (类型: {type(core_metrics.get('irr'))})")
                print(f"DPI: {core_metrics.get('dpi')} (类型: {type(core_metrics.get('dpi'))})")
                print(f"静态回本周期: {core_metrics.get('static_payback_period')} (类型: {type(core_metrics.get('static_payback_period'))})")
                
                # 检查现金流表格数据
                cash_flow_table = result.get('cash_flow_table', [])
                print(f"现金流表格行数: {len(cash_flow_table)}")
                
                for i, row in enumerate(cash_flow_table[:3]):  # 只检查前3行
                    print(f"第{i+1}行数据:")
                    for key, value in row.items():
                        if isinstance(value, (int, float)):
                            is_nan = value != value  # NaN check
                            is_inf = value == float('inf') or value == float('-inf')
                            if is_nan or is_inf:
                                print(f"  ⚠️  {key}: {value} (类型: {type(value)}) - 异常值!")
                            else:
                                print(f"  ✅ {key}: {value} (类型: {type(value)})")
                        else:
                            print(f"  📝 {key}: {value} (类型: {type(value)})")
                
                # 检查JSON序列化问题
                print("5️⃣ 测试JSON序列化...")
                try:
                    json_str = json.dumps(result)
                    print("✅ JSON序列化成功")
                except Exception as e:
                    print(f"❌ JSON序列化失败: {e}")
                    
            else:
                print(f"❌ 计算失败: {result.get('message')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 调试过程异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_calculation() 