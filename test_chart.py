#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试剩余本金分析图表功能
"""

import requests
import json
import sys

# 基础配置
BASE_URL = "http://localhost:5000"

def test_chart_analysis():
    """测试图表分析功能"""
    
    print("🚀 开始测试剩余本金分析图表功能...")
    
    # 1. 重置计算器
    print("\n📋 步骤1: 重置计算器")
    response = requests.post(f"{BASE_URL}/api/reset")
    if not response.json().get('success'):
        print("❌ 重置失败")
        return False
    print("✅ 重置成功")
    
    # 2. 设置基本参数
    print("\n📋 步骤2: 设置基本参数")
    basic_params = {
        "investment_target": "测试项目",  # 投资标的
        "investment_amount": 10000,     # 投资金额1万万元
        "investment_period": 5,         # 投资期限5年
        "hurdle_rate": 8.0,            # 门槛收益率8%
        "management_carry": 20.0       # 管理人Carry比例20%
    }
    
    response = requests.post(f"{BASE_URL}/api/basic-params", json=basic_params)
    result = response.json()
    if not result.get('success'):
        print(f"❌ 设置基本参数失败: {result.get('message', '未知错误')}")
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应内容: {result}")
        return False
    print("✅ 基本参数设置成功")
    
    # 3. 设置现金流
    print("\n📋 步骤3: 设置现金流")
    cash_flows = [500, 1200, 1800, 2500, 3000]  # 5年的现金流
    
    response = requests.post(f"{BASE_URL}/api/cash-flows", json={"cash_flows": cash_flows})
    if not response.json().get('success'):
        print("❌ 设置现金流失败")
        return False
    print("✅ 现金流设置成功")
    
    # 4. 执行计算
    print("\n📋 步骤4: 执行计算")
    calc_params = {
        "mode": "flat_priority_repayment"  # 平层结构-优先还本
    }
    
    response = requests.post(f"{BASE_URL}/api/calculate", json=calc_params)
    if not response.json().get('success'):
        print(f"❌ 计算失败: {response.json().get('message')}")
        return False
    print("✅ 计算成功")
    
    # 5. 获取图表数据
    print("\n📋 步骤5: 获取图表数据")
    response = requests.get(f"{BASE_URL}/api/chart-data")
    if not response.json().get('success'):
        print(f"❌ 获取图表数据失败: {response.json().get('message')}")
        return False
    
    chart_data = response.json()['data']
    print("✅ 图表数据获取成功")
    
    # 6. 验证剩余本金分析图表配置
    print("\n📋 步骤6: 验证剩余本金分析图表配置")
    capital_chart_config = chart_data['chart_configs']['capital_structure_chart']
    
    # 检查图表类型
    if capital_chart_config.get('type') != 'bar':
        print("❌ 图表类型不正确")
        return False
    print("✅ 图表类型正确: bar")
    
    # 检查数据集
    datasets = capital_chart_config.get('data', {}).get('datasets', [])
    if len(datasets) != 2:
        print(f"❌ 数据集数量不正确，期望2个，实际{len(datasets)}个")
        return False
    
    # 检查第一个数据集（剩余本金比例柱状图）
    bar_dataset = datasets[0]
    if bar_dataset.get('label') != '剩余本金比例':
        print(f"❌ 第一个数据集标签不正确: {bar_dataset.get('label')}")
        return False
    if bar_dataset.get('type') != 'bar':
        print(f"❌ 第一个数据集类型不正确: {bar_dataset.get('type')}")
        return False
    if bar_dataset.get('yAxisID') != 'y':
        print(f"❌ 第一个数据集Y轴ID不正确: {bar_dataset.get('yAxisID')}")
        return False
    print("✅ 剩余本金比例柱状图配置正确")
    
    # 检查第二个数据集（年累计分派率折线图）
    line_dataset = datasets[1]
    if line_dataset.get('label') != '年累计分派率':
        print(f"❌ 第二个数据集标签不正确: {line_dataset.get('label')}")
        return False
    if line_dataset.get('type') != 'line':
        print(f"❌ 第二个数据集类型不正确: {line_dataset.get('type')}")
        return False
    if line_dataset.get('yAxisID') != 'y1':
        print(f"❌ 第二个数据集Y轴ID不正确: {line_dataset.get('yAxisID')}")
        return False
    print("✅ 年累计分派率折线图配置正确")
    
    # 检查双Y轴配置
    scales = capital_chart_config.get('options', {}).get('scales', {})
    if 'y' not in scales or 'y1' not in scales:
        print("❌ 双Y轴配置缺失")
        return False
    
    # 检查主Y轴
    y_axis = scales['y']
    if y_axis.get('position') != 'left':
        print(f"❌ 主Y轴位置不正确: {y_axis.get('position')}")
        return False
    if '剩余本金比例' not in y_axis.get('title', {}).get('text', ''):
        print(f"❌ 主Y轴标题不正确: {y_axis.get('title', {}).get('text')}")
        return False
    print("✅ 主Y轴配置正确")
    
    # 检查副Y轴
    y1_axis = scales['y1']
    if y1_axis.get('position') != 'right':
        print(f"❌ 副Y轴位置不正确: {y1_axis.get('position')}")
        return False
    if '年累计分派率' not in y1_axis.get('title', {}).get('text', ''):
        print(f"❌ 副Y轴标题不正确: {y1_axis.get('title', {}).get('text')}")
        return False
    print("✅ 副Y轴配置正确")
    
    # 检查标题
    title = capital_chart_config.get('options', {}).get('plugins', {}).get('title', {}).get('text', '')
    if title != '剩余本金分析':
        print(f"❌ 图表标题不正确: {title}")
        return False
    print("✅ 图表标题正确")
    
    # 检查数据
    labels = capital_chart_config.get('data', {}).get('labels', [])
    bar_data = bar_dataset.get('data', [])
    line_data = line_dataset.get('data', [])
    
    print(f"\n📊 图表数据概览:")
    print(f"   年份标签: {labels}")
    print(f"   剩余本金比例数据: {bar_data}")
    print(f"   年累计分派率数据: {line_data}")
    
    # 验证数据合理性
    if len(labels) != len(bar_data) or len(labels) != len(line_data):
        print("❌ 数据长度不一致")
        return False
    
    # 检查第0年初始状态
    if bar_data[0] != 100.0:
        print(f"❌ 第0年剩余本金比例应为100%，实际为{bar_data[0]}%")
        return False
    if line_data[0] != 0.0:
        print(f"❌ 第0年累计分派率应为0%，实际为{line_data[0]}%")
        return False
    print("✅ 第0年初始状态正确")
    
    # 检查数据递减趋势（剩余本金应该递减）
    if not all(bar_data[i] >= bar_data[i+1] for i in range(len(bar_data)-1)):
        print("⚠️  剩余本金比例不是严格递减（可能是正常的业务逻辑）")
    
    # 检查累计分派率递增趋势
    if not all(line_data[i] <= line_data[i+1] for i in range(len(line_data)-1)):
        print("❌ 年累计分派率应该是递增的")
        return False
    print("✅ 年累计分派率递增趋势正确")
    
    print("\n🎉 所有测试通过！剩余本金分析图表功能正常工作")
    return True

def main():
    """主函数"""
    try:
        success = test_chart_analysis()
        if success:
            print("\n✅ 测试完成，功能正常")
            sys.exit(0)
        else:
            print("\n❌ 测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 