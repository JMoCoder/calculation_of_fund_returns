#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API功能测试脚本
测试新增的累计现金流图表API功能
"""

import requests
import json

def test_api():
    """测试API功能"""
    base_url = "http://localhost:5000"
    
    print("🚀 开始测试API功能...")
    
    # 1. 测试健康检查
    print("\n📋 步骤1: 测试健康检查")
    response = requests.get(f"{base_url}/api/health")
    assert response.status_code == 200, f"健康检查失败: {response.status_code}"
    health_data = response.json()
    print(f"✅ 健康检查通过: {health_data['status']}")
    
    # 2. 设置基本参数
    print("\n📋 步骤2: 设置基本参数")
    basic_params = {
        "investment_target": "测试累计现金流项目",
        "investment_amount": 10000,
        "investment_period": 5,
        "hurdle_rate": 8.0,
        "management_carry": 20.0
    }
    
    response = requests.post(f"{base_url}/api/basic-params", json=basic_params)
    assert response.status_code == 200, f"设置基本参数失败: {response.status_code}"
    result = response.json()
    assert result['success'], f"设置基本参数失败: {result.get('message', '')}"
    print("✅ 基本参数设置成功")
    
    # 3. 设置现金流数据
    print("\n📋 步骤3: 设置现金流数据")
    cash_flows = {
        "cash_flows": [2000, 3000, 2500, 1500, 4000]
    }
    
    response = requests.post(f"{base_url}/api/cash-flows", json=cash_flows)
    assert response.status_code == 200, f"设置现金流失败: {response.status_code}"
    result = response.json()
    assert result['success'], f"设置现金流失败: {result.get('message', '')}"
    print("✅ 现金流数据设置成功")
    
    # 4. 执行计算
    print("\n📋 步骤4: 执行计算")
    calculation_params = {
        "mode": "flat_priority_repayment"
    }
    
    response = requests.post(f"{base_url}/api/calculate", json=calculation_params)
    assert response.status_code == 200, f"计算失败: {response.status_code}"
    result = response.json()
    assert result['success'], f"计算失败: {result.get('message', '')}"
    print("✅ 计算完成")
    
    # 5. 获取图表数据
    print("\n📋 步骤5: 获取图表数据")
    response = requests.get(f"{base_url}/api/chart-data")
    assert response.status_code == 200, f"获取图表数据失败: {response.status_code}"
    chart_data = response.json()
    assert chart_data['success'], f"获取图表数据失败: {chart_data.get('message', '')}"
    print("✅ 图表数据获取成功")
    
    # 6. 验证累计现金流图表配置
    print("\n📋 步骤6: 验证累计现金流图表配置")
    chart_configs = chart_data['data']['chart_configs']
    
    # 检查是否包含新的累计现金流图表
    assert 'cumulative_cash_flow_chart' in chart_configs, "图表配置中缺少累计现金流图表"
    
    cumulative_chart = chart_configs['cumulative_cash_flow_chart']
    assert cumulative_chart['type'] == 'bar', "累计现金流图表类型应该为bar"
    assert 'data' in cumulative_chart, "累计现金流图表必须包含data字段"
    assert 'options' in cumulative_chart, "累计现金流图表必须包含options字段"
    
    # 验证数据结构
    data = cumulative_chart['data']
    assert 'labels' in data, "数据必须包含labels字段"
    assert 'datasets' in data, "数据必须包含datasets字段"
    assert len(data['datasets']) == 2, "应该有2个数据集"
    
    labels = data['labels']
    datasets = data['datasets']
    
    # 验证年份标签
    expected_years = ['第0年', '第1年', '第2年', '第3年', '第4年', '第5年']
    assert labels == expected_years, f"年份标签不正确，期望: {expected_years}，实际: {labels}"
    
    # 验证累计现金流数据
    cumulative_dataset = datasets[0]
    assert cumulative_dataset['label'] == '累计现金流', "第一个数据集标签应该是'累计现金流'"
    cumulative_data = cumulative_dataset['data']
    expected_cumulative = [-10000, -8000.0, -5000.0, -2500.0, -1000.0, 3000.0]
    assert cumulative_data == expected_cumulative, f"累计现金流数据不正确，期望: {expected_cumulative}，实际: {cumulative_data}"
    
    # 验证现金流分派率数据
    distribution_rate_dataset = datasets[1]
    assert distribution_rate_dataset['label'] == '现金流分派率', "第二个数据集标签应该是'现金流分派率'"
    distribution_rate_data = distribution_rate_dataset['data']
    expected_rates = [None, 20.0, 30.0, 25.0, 15.0, 40.0]
    assert distribution_rate_data == expected_rates, f"现金流分派率数据不正确，期望: {expected_rates}，实际: {distribution_rate_data}"
    
    print("✅ 累计现金流图表配置验证通过")
    
    # 7. 验证图表标题
    print("\n📋 步骤7: 验证图表标题")
    title_config = cumulative_chart['options']['plugins']['title']
    assert title_config['display'] is True, "标题应该显示"
    assert title_config['text'] == '累计现金流分析', f"标题文本错误，期望: '累计现金流分析'，实际: {title_config['text']}"
    print("✅ 图表标题验证通过")
    
    # 8. 输出图表配置摘要
    print("\n📋 步骤8: 输出图表配置摘要")
    print("="*60)
    print("API返回的累计现金流图表配置摘要")
    print("="*60)
    print(f"图表类型: {cumulative_chart['type']}")
    print(f"年份标签: {labels}")
    print(f"累计现金流数据: {cumulative_data}")
    print(f"现金流分派率数据: {distribution_rate_data}")
    print(f"数据集数量: {len(datasets)}")
    print("="*60)
    
    print("\n🎉 所有API测试通过！累计现金流图表功能在API层面正常工作")
    return True

if __name__ == '__main__':
    try:
        print(f"{'='*80}")
        print("累计现金流图表API功能测试")
        print(f"{'='*80}")
        
        success = test_api()
        
        if success:
            print(f"\n{'='*80}")
            print("🎊 API测试总结: 所有功能测试通过！")
            print("📍 新的累计现金流图表已成功集成到API中")
            print("🌐 前端可以正常获取和显示累计现金流图表")
            print(f"{'='*80}")
            
    except Exception as e:
        print(f"\n❌ API测试失败: {str(e)}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")
        exit(1) 