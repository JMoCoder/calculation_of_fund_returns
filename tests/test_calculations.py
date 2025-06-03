#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化-息息本本模式计算逻辑测试脚本

主要测试内容：
1. 期初本金的逐年更新是否正确
2. 收益计算是否基于正确的期初本金
3. 还本逻辑是否符合息息本本模式
4. 数据与预期表格的对比验证
"""

import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import FundCalculator

def test_structured_interest_principal_logic():
    """
    测试结构化-息息本本模式的计算逻辑
    
    使用提供的表格数据进行验证：
    - 投资金额：应该能从表格数据推算出来
    - 优先级比例：从表格数据分析
    - 劣后级收益率：从表格数据分析
    """
    print("=" * 80)
    print("🧪 结构化-息息本本模式计算逻辑测试")
    print("=" * 80)
    
    # 创建计算器实例
    calculator = FundCalculator()
    
    # 从提供的表格数据分析参数（第1年数据）
    # 净现金流第1年：1,549,641万元
    # 优先级期初本金：13,646,686万元 
    # 劣后级期初本金：1,516,298万元
    # 总投资金额 = 13,646,686 + 1,516,298 = 15,162,984万元
    
    investment_amount = 15162984  # 万元
    senior_amount = 13646686      # 万元  
    subordinate_amount = 1516298  # 万元
    
    # 计算比例
    senior_ratio = (senior_amount / investment_amount) * 100  # 约90%
    subordinate_ratio = (subordinate_amount / investment_amount) * 100  # 约10%
    
    print(f"📊 基础参数分析：")
    print(f"   总投资金额: {investment_amount:,.0f} 万元")
    print(f"   优先级金额: {senior_amount:,.0f} 万元 ({senior_ratio:.1f}%)")
    print(f"   劣后级金额: {subordinate_amount:,.0f} 万元 ({subordinate_ratio:.1f}%)")
    print()
    
    # 从表格分析收益率
    # 第1年优先级期间收益：1,091,735万元
    # 优先级收益率 = 1,091,735 / 13,646,686 ≈ 8%
    # 第1年劣后级期间收益：151,630万元  
    # 劣后级收益率 = 151,630 / 1,516,298 ≈ 10%
    
    hurdle_rate = 8.0  # 优先级收益率（门槛收益率）
    subordinate_rate = 10.0  # 劣后级收益率
    management_carry = 20.0  # 管理费Carry比例
    
    # 构造现金流数据（从表格提取前几年）
    cash_flows = [
        1549641,  # 第1年
        1536728,  # 第2年  
        1523558,  # 第3年
        1703941,  # 第4年
        1690238,  # 第5年
    ]
    
    investment_period = len(cash_flows)  # 投资期限与现金流数据长度保持一致
    
    print(f"🔧 测试参数设置：")
    print(f"   门槛收益率（优先级）: {hurdle_rate}%")
    print(f"   劣后级收益率: {subordinate_rate}%") 
    print(f"   管理费Carry: {management_carry}%")
    print(f"   测试年数: {len(cash_flows)}年")
    print()
    
    # 设置基本参数
    basic_params = {
        'investment_target': '测试基金项目',
        'investment_amount': investment_amount,
        'investment_period': investment_period,
        'hurdle_rate': hurdle_rate,
        'management_carry': management_carry
    }
    
    result = calculator.set_basic_params(basic_params)
    if not result['success']:
        print(f"❌ 设置基本参数失败: {result['message']}")
        return
    
    # 设置现金流
    result = calculator.set_cash_flows(cash_flows)
    if not result['success']:
        print(f"❌ 设置现金流失败: {result['message']}")
        return
    
    # 执行计算
    print("🚀 开始计算...")
    result = calculator.calculate_structured_interest_principal(senior_ratio, subordinate_rate)
    
    if not result['success']:
        print(f"❌ 计算失败: {result['message']}")
        return
    
    print("✅ 计算成功!")
    print()
    
    # 验证计算结果
    print("📋 计算结果验证：")
    print("-" * 80)
    
    # 表头
    headers = [
        "年份", "净现金流", "分派率", "优先级期初", "优先级收益", 
        "劣后级期初", "劣后级收益", "优先级还本", "劣后级还本"
    ]
    
    # 格式化输出表头
    print(f"{'年份':>4} {'净现金流':>12} {'分派率':>8} {'优先期初':>12} {'优先收益':>12} {'劣后期初':>12} {'劣后收益':>12} {'优先还本':>12} {'劣后还本':>12}")
    print("-" * 120)
    
    # 预期数据（从用户提供的表格）
    expected_data = [
        # [净现金流, 优先级期初, 优先级收益, 劣后级期初, 劣后级收益, 优先级还本]
        [1549641, 13646686, 1091735, 1516298, 151630, 306276],
        [1536728, 13646686, 1091735, 1516298, 151630, 293364], 
        [1523558, 13646686, 1091735, 1516298, 151630, 280193],
        [1703941, 13646686, 1091735, 1516298, 151630, 460576],
        [1690238, 13646686, 1091735, 1516298, 151630, 446873],
    ]
    
    # 输出计算结果并对比
    for i, row in enumerate(result['cash_flow_table']):
        year = row['year']
        net_cash_flow = row['net_cash_flow']
        rate = row['cash_flow_distribution_rate']
        senior_begin = row['senior_beginning_principal']
        senior_return = row['senior_periodic_return']
        sub_begin = row['subordinate_beginning_principal']
        sub_return = row['subordinate_periodic_return']
        senior_repay = row['senior_principal_repayment']
        sub_repay = row['subordinate_principal_repayment']
        
        print(f"{year:>4} {net_cash_flow:>12.0f} {rate:>7.2f}% {senior_begin:>12.0f} {senior_return:>12.0f} {sub_begin:>12.0f} {sub_return:>12.0f} {senior_repay:>12.0f} {sub_repay:>12.0f}")
        
        # 验证与预期数据的差异
        if i < len(expected_data):
            expected = expected_data[i]
            
            # 检查关键数据点
            issues = []
            
            # 检查净现金流
            if abs(net_cash_flow - expected[0]) > 1:
                issues.append(f"净现金流差异: {net_cash_flow:.0f} vs {expected[0]:.0f}")
            
            # 检查优先级期初本金（这是我们修复的关键点）
            if i == 0:  # 第一年应该等于初始金额
                if abs(senior_begin - expected[1]) > 1:
                    issues.append(f"优先级期初本金差异: {senior_begin:.0f} vs {expected[1]:.0f}")
            
            # 检查优先级收益
            expected_senior_return = senior_begin * (hurdle_rate / 100)
            if abs(senior_return - expected_senior_return) > 1:
                issues.append(f"优先级收益计算差异: {senior_return:.0f} vs {expected_senior_return:.0f}")
            
            # 检查劣后级收益
            expected_sub_return = sub_begin * (subordinate_rate / 100)
            if abs(sub_return - expected_sub_return) > 1:
                issues.append(f"劣后级收益计算差异: {sub_return:.0f} vs {expected_sub_return:.0f}")
            
            if issues:
                print(f"    ⚠️  第{year}年存在差异:")
                for issue in issues:
                    print(f"       • {issue}")
    
    print("-" * 120)
    
    # 总结
    summary = result['summary'] 
    print("\n📈 计算总结：")
    print(f"   优先级总收益: {summary['total_senior_return']:,.0f} 万元")
    print(f"   劣后级总收益: {summary['total_subordinate_return']:,.0f} 万元")
    print(f"   优先级总还本: {summary['total_senior_principal']:,.0f} 万元")
    print(f"   劣后级总还本: {summary['total_subordinate_principal']:,.0f} 万元")
    print(f"   CarryLP: {summary['total_carry_lp']:,.0f} 万元")
    print(f"   CarryGP: {summary['total_carry_gp']:,.0f} 万元")
    
    # 核心指标
    metrics = result['core_metrics']
    print(f"\n📊 核心指标：")
    print(f"   IRR: {metrics['irr']}")
    print(f"   DPI: {metrics['dpi']}")
    print(f"   静态回本期: {metrics['static_payback_period']}")
    print(f"   动态回本期: {metrics['dynamic_payback_period']}")
    
    print("\n✨ 测试完成！")
    
    # 验证关键修复点
    print("\n🔍 关键修复验证：")
    print("1. 期初本金逐年更新 - 检查第2年期初本金是否正确减少")
    
    if len(result['cash_flow_table']) >= 2:
        year1_senior_begin = result['cash_flow_table'][0]['senior_beginning_principal']
        year1_senior_repay = result['cash_flow_table'][0]['senior_principal_repayment']
        year2_senior_begin = result['cash_flow_table'][1]['senior_beginning_principal']
        
        expected_year2_begin = year1_senior_begin - year1_senior_repay
        
        print(f"   第1年优先级期初: {year1_senior_begin:,.0f}")
        print(f"   第1年优先级还本: {year1_senior_repay:,.0f}")
        print(f"   第2年优先级期初: {year2_senior_begin:,.0f}")
        print(f"   预期第2年期初: {expected_year2_begin:,.0f}")
        
        if abs(year2_senior_begin - expected_year2_begin) < 1:
            print("   ✅ 期初本金更新逻辑正确")
        else:
            print("   ❌ 期初本金更新逻辑仍有问题")
    
    return result

if __name__ == "__main__":
    test_structured_interest_principal_logic() 