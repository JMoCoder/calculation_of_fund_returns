#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合图表功能测试脚本

该脚本整合了所有图表相关的测试功能：
1. 剩余本金分析图表测试 
2. 累计现金流分析图表测试
3. API层面的图表数据验证
4. 图表配置和数据结构验证
"""

import requests
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径，确保能够导入app模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import FundCalculator, get_cumulative_cash_flow_chart_config

# 基础配置
BASE_URL = "http://localhost:5000"

class ChartTestSuite:
    """图表测试套件类"""
    
    def __init__(self):
        """初始化测试套件"""
        self.success_count = 0
        self.total_tests = 0
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        self.total_tests += 1
        if success:
            self.success_count += 1
            print(f"✅ {test_name}: 通过")
            if message:
                print(f"   {message}")
        else:
            print(f"❌ {test_name}: 失败")
            if message:
                print(f"   {message}")
    
    def get_summary(self):
        """获取测试总结"""
        return f"{self.success_count}/{self.total_tests} 测试通过"

def test_capital_structure_chart():
    """测试剩余本金分析图表功能（双Y轴混合图表）"""
    
    print("🚀 开始测试剩余本金分析图表功能...")
    test_suite = ChartTestSuite()
    
    try:
        # 1. 重置计算器
        print("\n📋 步骤1: 重置计算器")
        response = requests.post(f"{BASE_URL}/api/reset")
        test_suite.log_test_result(
            "重置计算器", 
            response.json().get('success', False)
        )
        
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
        test_suite.log_test_result(
            "设置基本参数", 
            result.get('success', False),
            f"投资金额: {basic_params['investment_amount']}万元"
        )
        
        # 3. 设置现金流
        print("\n📋 步骤3: 设置现金流")
        cash_flows = [500, 1200, 1800, 2500, 3000]  # 5年的现金流
        
        response = requests.post(f"{BASE_URL}/api/cash-flows", json={"cash_flows": cash_flows})
        test_suite.log_test_result(
            "设置现金流", 
            response.json().get('success', False),
            f"现金流: {cash_flows}"
        )
        
        # 4. 执行计算
        print("\n📋 步骤4: 执行计算")
        calc_params = {
            "mode": "flat_priority_repayment"  # 平层结构-优先还本
        }
        
        response = requests.post(f"{BASE_URL}/api/calculate", json=calc_params)
        test_suite.log_test_result(
            "执行计算", 
            response.json().get('success', False)
        )
        
        # 5. 获取图表数据
        print("\n📋 步骤5: 获取图表数据")
        response = requests.get(f"{BASE_URL}/api/chart-data")
        chart_data_success = response.json().get('success', False)
        test_suite.log_test_result("获取图表数据", chart_data_success)
        
        if not chart_data_success:
            return False
            
        chart_data = response.json()['data']
        
        # 6. 验证剩余本金分析图表配置
        print("\n📋 步骤6: 验证剩余本金分析图表配置")
        capital_chart_config = chart_data['chart_configs']['capital_structure_chart']
        
        # 检查图表类型
        test_suite.log_test_result(
            "图表类型验证", 
            capital_chart_config.get('type') == 'bar'
        )
        
        # 检查数据集
        datasets = capital_chart_config.get('data', {}).get('datasets', [])
        test_suite.log_test_result(
            "数据集数量验证", 
            len(datasets) == 2,
            f"期望2个数据集，实际{len(datasets)}个"
        )
        
        if len(datasets) >= 2:
            # 检查第一个数据集（剩余本金比例柱状图）
            bar_dataset = datasets[0]
            bar_config_ok = (
                bar_dataset.get('label') == '剩余本金比例' and
                bar_dataset.get('type') == 'bar' and
                bar_dataset.get('yAxisID') == 'y'
            )
            test_suite.log_test_result("剩余本金比例柱状图配置", bar_config_ok)
            
            # 检查第二个数据集（年累计分派率折线图）
            line_dataset = datasets[1]
            line_config_ok = (
                line_dataset.get('label') == '年累计分派率' and
                line_dataset.get('type') == 'line' and
                line_dataset.get('yAxisID') == 'y1'
            )
            test_suite.log_test_result("年累计分派率折线图配置", line_config_ok)
        
        # 检查双Y轴配置
        scales = capital_chart_config.get('options', {}).get('scales', {})
        dual_axis_ok = 'y' in scales and 'y1' in scales
        test_suite.log_test_result("双Y轴配置", dual_axis_ok)
        
        if dual_axis_ok:
            # 检查主Y轴
            y_axis = scales['y']
            y_axis_ok = (
                y_axis.get('position') == 'left' and
                '剩余本金比例' in y_axis.get('title', {}).get('text', '')
            )
            test_suite.log_test_result("主Y轴配置", y_axis_ok)
            
            # 检查副Y轴
            y1_axis = scales['y1']
            y1_axis_ok = (
                y1_axis.get('position') == 'right' and
                '年累计分派率' in y1_axis.get('title', {}).get('text', '')
            )
            test_suite.log_test_result("副Y轴配置", y1_axis_ok)
        
        # 检查标题
        title = capital_chart_config.get('options', {}).get('plugins', {}).get('title', {}).get('text', '')
        test_suite.log_test_result("图表标题", title == '剩余本金分析')
        
        # 验证数据合理性
        labels = capital_chart_config.get('data', {}).get('labels', [])
        if len(datasets) >= 2:
            bar_data = datasets[0].get('data', [])
            line_data = datasets[1].get('data', [])
            
            # 检查数据长度一致性
            data_length_ok = len(labels) == len(bar_data) == len(line_data)
            test_suite.log_test_result("数据长度一致性", data_length_ok)
            
            if len(bar_data) > 0 and len(line_data) > 0:
                # 检查第0年初始状态
                initial_state_ok = bar_data[0] == 100.0 and line_data[0] == 0.0
                test_suite.log_test_result(
                    "第0年初始状态", 
                    initial_state_ok,
                    f"剩余本金: {bar_data[0]}%, 累计分派率: {line_data[0]}%"
                )
                
                # 检查累计分派率递增趋势
                if len(line_data) > 1:
                    increasing_trend = all(line_data[i] <= line_data[i+1] for i in range(len(line_data)-1))
                    test_suite.log_test_result("年累计分派率递增趋势", increasing_trend)
        
        print(f"\n📊 剩余本金分析图表测试完成: {test_suite.get_summary()}")
        return test_suite.success_count == test_suite.total_tests
        
    except Exception as e:
        print(f"❌ 剩余本金分析图表测试异常: {e}")
        return False

def test_cumulative_cash_flow_chart():
    """测试累计现金流分析图表功能（直接函数调用）"""
    
    print("\n🚀 开始测试累计现金流分析图表功能...")
    test_suite = ChartTestSuite()
    
    try:
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
        test_suite.log_test_result(
            "设置基本参数", 
            result['success'],
            f"投资金额{basic_params['investment_amount']}万元，期限{basic_params['investment_period']}年"
        )
        
        # 3. 设置现金流数据
        print("\n📋 步骤3: 设置现金流数据")
        cash_flows = [2000, 3000, 2500, 1500, 4000]  # 5年现金流
        result = calculator.set_cash_flows(cash_flows)
        test_suite.log_test_result(
            "设置现金流", 
            result['success'],
            f"现金流: {cash_flows}"
        )
        
        # 4. 执行计算
        print("\n📋 步骤4: 执行平层结构-优先还本计算")
        result = calculator.calculate_flat_structure_priority_repayment()
        test_suite.log_test_result("执行计算", result['success'])
        
        if not result['success']:
            return False
        
        # 5. 设置全局计算器
        print("\n📋 步骤5: 设置全局计算器")
        import app
        app.calculator = calculator
        test_suite.log_test_result("设置全局计算器", True)
        
        # 6. 验证累计现金流分析图表配置
        print("\n📋 步骤6: 验证累计现金流分析图表配置")
        chart_config = get_cumulative_cash_flow_chart_config(result)
        
        # 验证图表配置结构
        basic_structure_ok = (
            chart_config is not None and
            'type' in chart_config and
            chart_config['type'] == 'bar' and
            'data' in chart_config and
            'options' in chart_config
        )
        test_suite.log_test_result("图表基本结构", basic_structure_ok)
        
        if not basic_structure_ok:
            return False
        
        # 7. 验证数据结构
        print("\n📋 步骤7: 验证数据结构")
        data = chart_config['data']
        data_structure_ok = (
            'labels' in data and
            'datasets' in data and
            len(data['datasets']) == 2
        )
        test_suite.log_test_result(
            "数据结构", 
            data_structure_ok,
            "包含2个数据集（累计现金流柱状图和现金流分派率折线图）"
        )
        
        if not data_structure_ok:
            return False
        
        labels = data['labels']
        datasets = data['datasets']
        
        # 验证标签（年份）
        expected_years = ['第0年', '第1年', '第2年', '第3年', '第4年', '第5年']
        labels_ok = labels == expected_years
        test_suite.log_test_result(
            "年份标签", 
            labels_ok,
            f"标签: {labels}"
        )
        
        # 8. 验证累计现金流数据集
        print("\n📋 步骤8: 验证累计现金流数据集")
        cumulative_dataset = datasets[0]
        cumulative_config_ok = (
            cumulative_dataset['label'] == '累计现金流' and
            cumulative_dataset['type'] == 'bar' and
            cumulative_dataset['yAxisID'] == 'y'
        )
        test_suite.log_test_result("累计现金流数据集配置", cumulative_config_ok)
        
        if cumulative_config_ok:
            cumulative_data = cumulative_dataset['data']
            data_length_ok = len(cumulative_data) == 6
            test_suite.log_test_result(
                "累计现金流数据长度", 
                data_length_ok,
                f"应该有6个点，实际有{len(cumulative_data)}个"
            )
            
            # 验证累计现金流计算逻辑
            expected_cumulative = [-10000, -8000, -5000, -2500, -1000, 3000]
            calculation_ok = cumulative_data == expected_cumulative
            test_suite.log_test_result(
                "累计现金流计算逻辑", 
                calculation_ok,
                f"数据: {cumulative_data}"
            )
        
        # 9. 验证现金流分派率数据集
        print("\n📋 步骤9: 验证现金流分派率数据集")
        distribution_rate_dataset = datasets[1]
        rate_config_ok = (
            distribution_rate_dataset['label'] == '现金流分派率' and
            distribution_rate_dataset['type'] == 'line' and
            distribution_rate_dataset['yAxisID'] == 'y1'
        )
        test_suite.log_test_result("现金流分派率数据集配置", rate_config_ok)
        
        if rate_config_ok:
            distribution_rate_data = distribution_rate_dataset['data']
            rate_data_length_ok = len(distribution_rate_data) == 6
            test_suite.log_test_result(
                "现金流分派率数据长度", 
                rate_data_length_ok,
                f"应该有6个点，实际有{len(distribution_rate_data)}个"
            )
            
            # 验证现金流分派率计算逻辑
            expected_rates = [None, 20.0, 30.0, 25.0, 15.0, 40.0]
            rate_calculation_ok = distribution_rate_data == expected_rates
            test_suite.log_test_result(
                "现金流分派率计算逻辑", 
                rate_calculation_ok,
                f"数据: {distribution_rate_data}"
            )
        
        # 10. 验证颜色配置
        print("\n📋 步骤10: 验证颜色配置")
        if cumulative_config_ok:
            cumulative_bg_colors = cumulative_dataset['backgroundColor']
            cumulative_border_colors = cumulative_dataset['borderColor']
            cumulative_data = cumulative_dataset['data']
            
            # 验证颜色根据正负值设置
            color_ok = True
            for i, value in enumerate(cumulative_data):
                if value < 0:
                    expected_bg = 'rgba(239, 68, 68, 0.6)'  # 红色背景
                    expected_border = 'rgba(239, 68, 68, 1)'  # 红色边框
                else:
                    expected_bg = 'rgba(34, 197, 94, 0.6)'  # 绿色背景
                    expected_border = 'rgba(34, 197, 94, 1)'  # 绿色边框
                
                if (cumulative_bg_colors[i] != expected_bg or 
                    cumulative_border_colors[i] != expected_border):
                    color_ok = False
                    break
            
            test_suite.log_test_result(
                "颜色配置", 
                color_ok,
                "负值红色，正值绿色"
            )
        
        # 11. 验证图表配置选项
        print("\n📋 步骤11: 验证图表配置选项")
        options = chart_config['options']
        
        # 验证标题
        title_config = options['plugins']['title']
        title_ok = (
            title_config['display'] is True and
            title_config['text'] == '累计现金流分析'
        )
        test_suite.log_test_result("图表标题配置", title_ok)
        
        # 验证Y轴配置
        scales = options['scales']
        y_axis_config_ok = (
            'y' in scales and 'y1' in scales and
            scales['y']['title']['text'] == '累计现金流 (万元)' and
            scales['y']['position'] == 'left' and
            scales['y1']['title']['text'] == '现金流分派率 (%)' and
            scales['y1']['position'] == 'right' and
            scales['y1']['grid']['drawOnChartArea'] is False
        )
        test_suite.log_test_result("Y轴配置", y_axis_config_ok)
        
        # 12. 测试异常情况
        print("\n📋 步骤12: 测试异常情况")
        
        # 测试空数据
        empty_result = {'cash_flow_table': [], 'calculation_mode': '平层结构-优先还本'}
        empty_chart_config = get_cumulative_cash_flow_chart_config(empty_result)
        empty_data_ok = (
            empty_chart_config['type'] == 'bar' and
            len(empty_chart_config['data']['labels']) == 0
        )
        test_suite.log_test_result("空数据异常处理", empty_data_ok)
        
        # 测试无初始投资金额的情况
        app.calculator.basic_params = {}
        no_investment_chart_config = get_cumulative_cash_flow_chart_config(result)
        no_investment_ok = no_investment_chart_config['type'] == 'bar'
        test_suite.log_test_result("无投资金额异常处理", no_investment_ok)
        
        # 恢复计算器
        app.calculator = calculator
        
        print(f"\n📊 累计现金流分析图表测试完成: {test_suite.get_summary()}")
        return test_suite.success_count == test_suite.total_tests
        
    except Exception as e:
        print(f"❌ 累计现金流分析图表测试异常: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")
        return False

def test_api_cumulative_cash_flow_chart():
    """测试累计现金流图表API功能"""
    
    print("\n🚀 开始测试累计现金流图表API功能...")
    test_suite = ChartTestSuite()
    
    try:
        # 1. 测试健康检查
        print("\n📋 步骤1: 测试健康检查")
        response = requests.get(f"{BASE_URL}/api/health")
        health_ok = response.status_code == 200
        test_suite.log_test_result("健康检查", health_ok)
        
        if health_ok:
            health_data = response.json()
            test_suite.log_test_result(
                "健康状态", 
                health_data['status'] == 'ok',
                f"状态: {health_data['status']}"
            )
        
        # 2. 设置基本参数
        print("\n📋 步骤2: 设置基本参数")
        basic_params = {
            "investment_target": "测试累计现金流项目",
            "investment_amount": 10000,
            "investment_period": 5,
            "hurdle_rate": 8.0,
            "management_carry": 20.0
        }
        
        response = requests.post(f"{BASE_URL}/api/basic-params", json=basic_params)
        basic_params_ok = response.status_code == 200 and response.json().get('success', False)
        test_suite.log_test_result("设置基本参数", basic_params_ok)
        
        # 3. 设置现金流数据
        print("\n📋 步骤3: 设置现金流数据")
        cash_flows = {
            "cash_flows": [2000, 3000, 2500, 1500, 4000]
        }
        
        response = requests.post(f"{BASE_URL}/api/cash-flows", json=cash_flows)
        cash_flows_ok = response.status_code == 200 and response.json().get('success', False)
        test_suite.log_test_result("设置现金流数据", cash_flows_ok)
        
        # 4. 执行计算
        print("\n📋 步骤4: 执行计算")
        calculation_params = {
            "mode": "flat_priority_repayment"
        }
        
        response = requests.post(f"{BASE_URL}/api/calculate", json=calculation_params)
        calculation_ok = response.status_code == 200 and response.json().get('success', False)
        test_suite.log_test_result("执行计算", calculation_ok)
        
        # 5. 获取图表数据
        print("\n📋 步骤5: 获取图表数据")
        response = requests.get(f"{BASE_URL}/api/chart-data")
        chart_data_ok = response.status_code == 200 and response.json().get('success', False)
        test_suite.log_test_result("获取图表数据", chart_data_ok)
        
        if not chart_data_ok:
            return False
        
        chart_data = response.json()
        
        # 6. 验证累计现金流图表配置
        print("\n📋 步骤6: 验证累计现金流图表配置")
        chart_configs = chart_data['data']['chart_configs']
        
        # 检查是否包含新的累计现金流图表
        cumulative_chart_exists = 'cumulative_cash_flow_chart' in chart_configs
        test_suite.log_test_result("累计现金流图表存在", cumulative_chart_exists)
        
        if not cumulative_chart_exists:
            return False
        
        cumulative_chart = chart_configs['cumulative_cash_flow_chart']
        
        # 验证图表基本结构
        basic_structure_ok = (
            cumulative_chart['type'] == 'bar' and
            'data' in cumulative_chart and
            'options' in cumulative_chart
        )
        test_suite.log_test_result("图表基本结构", basic_structure_ok)
        
        # 验证数据结构
        data = cumulative_chart['data']
        data_structure_ok = (
            'labels' in data and
            'datasets' in data and
            len(data['datasets']) == 2
        )
        test_suite.log_test_result("数据结构", data_structure_ok)
        
        if data_structure_ok:
            labels = data['labels']
            datasets = data['datasets']
            
            # 验证年份标签
            expected_years = ['第0年', '第1年', '第2年', '第3年', '第4年', '第5年']
            labels_ok = labels == expected_years
            test_suite.log_test_result(
                "年份标签", 
                labels_ok,
                f"期望: {expected_years}，实际: {labels}"
            )
            
            # 验证累计现金流数据
            cumulative_dataset = datasets[0]
            cumulative_config_ok = cumulative_dataset['label'] == '累计现金流'
            test_suite.log_test_result("累计现金流数据集", cumulative_config_ok)
            
            if cumulative_config_ok:
                cumulative_data = cumulative_dataset['data']
                expected_cumulative = [-10000, -8000.0, -5000.0, -2500.0, -1000.0, 3000.0]
                calculation_ok = cumulative_data == expected_cumulative
                test_suite.log_test_result(
                    "累计现金流计算", 
                    calculation_ok,
                    f"期望: {expected_cumulative}，实际: {cumulative_data}"
                )
            
            # 验证现金流分派率数据
            distribution_rate_dataset = datasets[1]
            rate_config_ok = distribution_rate_dataset['label'] == '现金流分派率'
            test_suite.log_test_result("现金流分派率数据集", rate_config_ok)
            
            if rate_config_ok:
                distribution_rate_data = distribution_rate_dataset['data']
                expected_rates = [None, 20.0, 30.0, 25.0, 15.0, 40.0]
                rate_calculation_ok = distribution_rate_data == expected_rates
                test_suite.log_test_result(
                    "现金流分派率计算", 
                    rate_calculation_ok,
                    f"期望: {expected_rates}，实际: {distribution_rate_data}"
                )
        
        # 7. 验证图表标题
        print("\n📋 步骤7: 验证图表标题")
        title_config = cumulative_chart['options']['plugins']['title']
        title_ok = (
            title_config['display'] is True and
            title_config['text'] == '累计现金流分析'
        )
        test_suite.log_test_result(
            "图表标题", 
            title_ok,
            f"标题: {title_config['text']}"
        )
        
        print(f"\n📊 累计现金流图表API测试完成: {test_suite.get_summary()}")
        return test_suite.success_count == test_suite.total_tests
        
    except Exception as e:
        print(f"❌ 累计现金流图表API测试异常: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    print(f"{'='*80}")
    print("📊 综合图表功能测试套件")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    total_tests = 0
    passed_tests = 0
    
    # 测试1: 剩余本金分析图表
    print(f"\n{'🔸'*20} 测试套件1: 剩余本金分析图表 {'🔸'*20}")
    try:
        if test_capital_structure_chart():
            passed_tests += 1
            print("✅ 剩余本金分析图表测试通过")
        else:
            print("❌ 剩余本金分析图表测试失败")
        total_tests += 1
    except Exception as e:
        print(f"❌ 剩余本金分析图表测试异常: {e}")
        total_tests += 1
    
    # 测试2: 累计现金流分析图表（直接函数调用）
    print(f"\n{'🔸'*20} 测试套件2: 累计现金流分析图表 {'🔸'*20}")
    try:
        if test_cumulative_cash_flow_chart():
            passed_tests += 1
            print("✅ 累计现金流分析图表测试通过")
        else:
            print("❌ 累计现金流分析图表测试失败")
        total_tests += 1
    except Exception as e:
        print(f"❌ 累计现金流分析图表测试异常: {e}")
        total_tests += 1
    
    # 测试3: 累计现金流图表API
    print(f"\n{'🔸'*20} 测试套件3: 累计现金流图表API {'🔸'*20}")
    try:
        if test_api_cumulative_cash_flow_chart():
            passed_tests += 1
            print("✅ 累计现金流图表API测试通过")
        else:
            print("❌ 累计现金流图表API测试失败")
        total_tests += 1
    except Exception as e:
        print(f"❌ 累计现金流图表API测试异常: {e}")
        total_tests += 1
    
    # 输出总结
    print(f"\n{'='*80}")
    print(f"🎊 综合图表测试总结:")
    print(f"   总测试套件: {total_tests}")
    print(f"   通过套件: {passed_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("🌟 所有图表功能测试通过！")
        print("📍 图表系统运行正常，支持以下功能:")
        print("   • 剩余本金分析图表（双Y轴混合图表）")
        print("   • 累计现金流分析图表（柱状图+折线图）")
        print("   • 完整的API接口支持")
        print("   • 智能颜色配置和数据验证")
    else:
        print("⚠️  部分图表功能存在问题，请检查失败的测试套件")
    
    print(f"{'='*80}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 所有图表测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 存在测试失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生严重错误: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")
        sys.exit(1) 