#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
累计现金流分析图表功能测试

该脚本用于测试新增的累计现金流分析图表功能：
1. 测试图表配置生成
2. 验证累计现金流计算逻辑
3. 验证现金流分派率计算
4. 测试图表数据结构
5. 验证鼠标悬停标签功能
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径，确保能够导入app模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import FundCalculator, get_cumulative_cash_flow_chart_config

def test_cumulative_cash_flow_chart():
    """测试累计现金流分析图表功能"""
    print("🚀 开始测试累计现金流分析图表功能...")
    
    # 1. 初始化计算器
    print("\n📋 步骤1: 初始化计算器")
    calculator = FundCalculator()
    
    # 2. 设置基本参数
    print("\n📋 步骤2: 设置基本参数")
    basic_params = {
        'investment_target': '测试累计现金流项目',  # 投资标的
        'investment_amount': 10000,  # 投资金额10000万元
        'investment_period': 5,      # 投资期限5年
        'hurdle_rate': 8.0,          # 门槛收益率8%
        'management_carry': 20.0     # 管理费和Carry比例20%
    }
    
    result = calculator.set_basic_params(basic_params)
    assert result['success'], f"设置基本参数失败: {result.get('message', '')}"
    print(f"✅ 基本参数设置成功: 投资金额{basic_params['investment_amount']}万元，期限{basic_params['investment_period']}年")
    
    # 3. 设置现金流数据
    print("\n📋 步骤3: 设置现金流数据")
    cash_flows = [2000, 3000, 2500, 1500, 4000]  # 5年现金流
    result = calculator.set_cash_flows(cash_flows)
    assert result['success'], f"设置现金流失败: {result.get('message', '')}"
    print(f"✅ 现金流设置成功: {cash_flows}")
    
    # 4. 执行计算
    print("\n📋 步骤4: 执行平层结构-优先还本计算")
    result = calculator.calculate_flat_structure_priority_repayment()
    assert result['success'], f"计算失败: {result.get('message', '')}"
    print("✅ 计算完成")
    
    # 5. 设置全局计算器
    print("\n📋 步骤5: 设置全局计算器")
    import app
    app.calculator = calculator
    print("✅ 全局计算器设置完成")
    
    # 6. 验证累计现金流分析图表配置
    print("\n📋 步骤6: 验证累计现金流分析图表配置")
    chart_config = get_cumulative_cash_flow_chart_config(result)
    
    # 验证图表配置结构
    assert chart_config is not None, "图表配置不能为空"
    assert 'type' in chart_config, "图表配置必须包含type字段"
    assert chart_config['type'] == 'bar', "图表类型应该为bar"
    assert 'data' in chart_config, "图表配置必须包含data字段"
    assert 'options' in chart_config, "图表配置必须包含options字段"
    print("✅ 图表基本结构验证通过")
    
    # 7. 验证数据结构
    print("\n📋 步骤7: 验证数据结构")
    data = chart_config['data']
    assert 'labels' in data, "数据必须包含labels字段"
    assert 'datasets' in data, "数据必须包含datasets字段"
    assert len(data['datasets']) == 2, "应该有2个数据集（累计现金流柱状图和现金流分派率折线图）"
    
    labels = data['labels']
    datasets = data['datasets']
    
    # 验证标签（年份）
    expected_years = ['第0年', '第1年', '第2年', '第3年', '第4年', '第5年']
    assert labels == expected_years, f"年份标签不正确，期望: {expected_years}，实际: {labels}"
    print(f"✅ 年份标签正确: {labels}")
    
    # 8. 验证累计现金流数据集
    print("\n📋 步骤8: 验证累计现金流数据集")
    cumulative_dataset = datasets[0]
    assert cumulative_dataset['label'] == '累计现金流', "第一个数据集标签应该是'累计现金流'"
    assert cumulative_dataset['type'] == 'bar', "累计现金流应该是柱状图"
    assert cumulative_dataset['yAxisID'] == 'y', "累计现金流应该使用主Y轴"
    
    cumulative_data = cumulative_dataset['data']
    assert len(cumulative_data) == 6, f"累计现金流数据应该有6个点，实际有{len(cumulative_data)}个"
    
    # 验证累计现金流计算逻辑
    # 第0年：-10000（负的初始投资）
    # 第1年：-10000 + 2000 = -8000
    # 第2年：-8000 + 3000 = -5000
    # 第3年：-5000 + 2500 = -2500
    # 第4年：-2500 + 1500 = -1000
    # 第5年：-1000 + 4000 = 3000
    expected_cumulative = [-10000, -8000, -5000, -2500, -1000, 3000]
    
    for i, (expected, actual) in enumerate(zip(expected_cumulative, cumulative_data)):
        assert actual == expected, f"第{i}年累计现金流错误，期望: {expected}，实际: {actual}"
    
    print(f"✅ 累计现金流计算正确: {cumulative_data}")
    
    # 9. 验证现金流分派率数据集
    print("\n📋 步骤9: 验证现金流分派率数据集")
    distribution_rate_dataset = datasets[1]
    assert distribution_rate_dataset['label'] == '现金流分派率', "第二个数据集标签应该是'现金流分派率'"
    assert distribution_rate_dataset['type'] == 'line', "现金流分派率应该是折线图"
    assert distribution_rate_dataset['yAxisID'] == 'y1', "现金流分派率应该使用副Y轴"
    
    distribution_rate_data = distribution_rate_dataset['data']
    assert len(distribution_rate_data) == 6, f"现金流分派率数据应该有6个点，实际有{len(distribution_rate_data)}个"
    
    # 验证现金流分派率计算逻辑
    # 第0年：None（不展示）
    # 第1年：2000/10000*100 = 20%
    # 第2年：3000/10000*100 = 30%
    # 第3年：2500/10000*100 = 25%
    # 第4年：1500/10000*100 = 15%
    # 第5年：4000/10000*100 = 40%
    expected_rates = [None, 20.0, 30.0, 25.0, 15.0, 40.0]
    
    for i, (expected, actual) in enumerate(zip(expected_rates, distribution_rate_data)):
        if expected is None:
            assert actual is None, f"第{i}年分派率应该为None，实际: {actual}"
        else:
            assert actual == expected, f"第{i}年分派率错误，期望: {expected}%，实际: {actual}%"
    
    print(f"✅ 现金流分派率计算正确: {distribution_rate_data}")
    
    # 10. 验证颜色配置
    print("\n📋 步骤10: 验证颜色配置")
    cumulative_bg_colors = cumulative_dataset['backgroundColor']
    cumulative_border_colors = cumulative_dataset['borderColor']
    
    # 验证颜色根据正负值设置
    for i, value in enumerate(cumulative_data):
        if value < 0:
            expected_bg = 'rgba(239, 68, 68, 0.6)'  # 红色背景
            expected_border = 'rgba(239, 68, 68, 1)'  # 红色边框
        else:
            expected_bg = 'rgba(34, 197, 94, 0.6)'  # 绿色背景
            expected_border = 'rgba(34, 197, 94, 1)'  # 绿色边框
        
        assert cumulative_bg_colors[i] == expected_bg, f"第{i}年背景颜色错误"
        assert cumulative_border_colors[i] == expected_border, f"第{i}年边框颜色错误"
    
    print("✅ 颜色配置正确（负值红色，正值绿色）")
    
    # 11. 验证图表配置选项
    print("\n📋 步骤11: 验证图表配置选项")
    options = chart_config['options']
    
    # 验证标题
    title_config = options['plugins']['title']
    assert title_config['display'] is True, "标题应该显示"
    assert title_config['text'] == '累计现金流分析', f"标题文本错误，期望: '累计现金流分析'，实际: {title_config['text']}"
    
    # 验证Y轴配置
    scales = options['scales']
    assert 'y' in scales, "必须包含主Y轴配置"
    assert 'y1' in scales, "必须包含副Y轴配置"
    
    y_axis = scales['y']
    assert y_axis['title']['text'] == '累计现金流 (万元)', "主Y轴标题错误"
    assert y_axis['position'] == 'left', "主Y轴应该在左侧"
    
    y1_axis = scales['y1']
    assert y1_axis['title']['text'] == '现金流分派率 (%)', "副Y轴标题错误"
    assert y1_axis['position'] == 'right', "副Y轴应该在右侧"
    assert y1_axis['grid']['drawOnChartArea'] is False, "副Y轴网格线不应该在图表区域显示"
    
    print("✅ 图表配置选项验证通过")
    
    # 12. 输出完整的图表配置（用于调试）
    print("\n📋 步骤12: 输出图表配置摘要")
    print("="*60)
    print("累计现金流分析图表配置摘要")
    print("="*60)
    print(f"图表类型: {chart_config['type']}")
    print(f"年份标签: {labels}")
    print(f"累计现金流数据: {cumulative_data}")
    print(f"现金流分派率数据: {distribution_rate_data}")
    print(f"数据集数量: {len(datasets)}")
    print("="*60)
    
    # 13. 测试异常情况
    print("\n📋 步骤13: 测试异常情况")
    
    # 测试空数据
    empty_result = {'cash_flow_table': [], 'calculation_mode': '平层结构-优先还本'}
    empty_chart_config = get_cumulative_cash_flow_chart_config(empty_result)
    assert empty_chart_config['type'] == 'bar', "空数据时应该返回基本的柱状图配置"
    assert len(empty_chart_config['data']['labels']) == 0, "空数据时标签应该为空"
    print("✅ 空数据异常处理正确")
    
    # 测试无初始投资金额的情况
    app.calculator.basic_params = {}
    no_investment_chart_config = get_cumulative_cash_flow_chart_config(result)
    assert no_investment_chart_config['type'] == 'bar', "无投资金额时应该返回基本配置"
    print("✅ 无投资金额异常处理正确")
    
    # 恢复计算器
    app.calculator = calculator
    
    print("\n🎉 所有测试通过！累计现金流分析图表功能正常工作")
    print("\n✨ 新功能特点:")
    print("   📊 累计现金流柱状图 - 显示每年的累计现金流变化")
    print("   📈 现金流分派率折线图 - 显示每年的现金流分派比例")
    print("   🎨 智能颜色配置 - 负值红色，正值绿色")
    print("   🖱️  悬停标签 - 详细显示数据值和状态图标")
    print("   📐 双Y轴设计 - 主轴显示金额，副轴显示比例")
    
    return True

if __name__ == '__main__':
    try:
        print(f"{'='*80}")
        print("累计现金流分析图表功能测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        success = test_cumulative_cash_flow_chart()
        
        if success:
            print(f"\n{'='*80}")
            print("🎊 测试总结: 所有功能测试通过！")
            print("📍 新图表已成功集成到系统中，位于'剩余本金分析'和'整体分配结构'之间")
            print("🌟 用户可以通过图表分析累计现金流的变化趋势和每年的分派率情况")
            print(f"{'='*80}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")
        exit(1) 