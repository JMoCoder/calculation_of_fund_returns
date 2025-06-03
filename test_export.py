#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导出功能的脚本
验证不同计算模式下导出的Excel结构是否与页面展示一致
"""

import json
import io
import pandas as pd
from datetime import datetime

# 测试数据：平层结构-优先还本
test_data_flat_priority = {
    "success": True,
    "calculation_mode": "平层结构-优先还本",
    "core_metrics": {
        "irr": "12.50%",
        "dpi": "1.85",
        "static_payback_period": "3.20 年",
        "dynamic_payback_period": "4.10 年"
    },
    "cash_flow_table": [
        {
            "year": 1,
            "net_cash_flow": "100",
            "cash_flow_distribution_rate": "10.00%",
            "beginning_principal_balance": "1,000",
            "principal_repayment": "0",
            "accrued_hurdle_return": "80",
            "distributed_hurdle_return": "80",
            "carry_lp": "16",
            "carry_gp": "4"
        },
        {
            "year": 2,
            "net_cash_flow": "200",
            "cash_flow_distribution_rate": "20.00%",
            "beginning_principal_balance": "1,000",
            "principal_repayment": "120",
            "accrued_hurdle_return": "80",
            "distributed_hurdle_return": "80",
            "carry_lp": "0",
            "carry_gp": "0"
        },
        {
            "year": 3,
            "net_cash_flow": "300",
            "cash_flow_distribution_rate": "30.00%",
            "beginning_principal_balance": "880",
            "principal_repayment": "300",
            "accrued_hurdle_return": "70.4",
            "distributed_hurdle_return": "0",
            "carry_lp": "0",
            "carry_gp": "0"
        }
    ],
    "totals": {
        "net_cash_flow": "600",
        "principal_repayment": "420",
        "accrued_hurdle_return": "230.4",
        "distributed_hurdle_return": "160",
        "carry_lp": "16",
        "carry_gp": "4"
    }
}

# 测试数据：结构化-优先劣后
test_data_structured = {
    "success": True,
    "calculation_mode": "结构化-优先劣后",
    "core_metrics": {
        "irr": "15.30%",
        "dpi": "2.10",
        "static_payback_period": "2.80 年",
        "dynamic_payback_period": "3.50 年"
    },
    "cash_flow_table": [
        {
            "year": 1,
            "net_cash_flow": "150",
            "cash_flow_distribution_rate": "15.00%",
            "senior_beginning_principal": "700",
            "senior_principal_repayment": "0",
            "senior_hurdle_accrual": "56",
            "senior_periodic_return": "56",
            "subordinate_principal_balance": "300",
            "subordinate_principal_repayment": "0",
            "carry_lp": "75.2",
            "carry_gp": "18.8"
        },
        {
            "year": 2,
            "net_cash_flow": "250",
            "cash_flow_distribution_rate": "25.00%",
            "senior_beginning_principal": "700",
            "senior_principal_repayment": "194",
            "senior_hurdle_accrual": "56",
            "senior_periodic_return": "56",
            "subordinate_principal_balance": "300",
            "subordinate_principal_repayment": "0",
            "carry_lp": "0",
            "carry_gp": "0"
        }
    ],
    "totals": {
        "net_cash_flow": "400",
        "senior_principal_repayment": "194",
        "senior_hurdle_accrual": "112",
        "senior_periodic_return": "112",
        "subordinate_principal_repayment": "0",
        "carry_lp": "75.2",
        "carry_gp": "18.8"
    }
}

def test_export_function():
    """测试导出功能"""
    print("🧪 开始测试导出功能...")
    
    # 模拟基本参数
    basic_params = {
        'investment_target': '测试基金项目',
        'investment_amount': 1000,
        'investment_period': 3,
        'hurdle_rate': 8,
        'management_carry': 20
    }
    
    # 测试不同计算模式
    test_cases = [
        ("平层结构-优先还本", test_data_flat_priority),
        ("结构化-优先劣后", test_data_structured)
    ]
    
    for mode_name, test_data in test_cases:
        print(f"\n📊 测试计算模式: {mode_name}")
        
        try:
            # 模拟导出逻辑
            results = test_data
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 投资收益分析工作表
                core_metrics = results.get('core_metrics', {})
                
                # 计算分派率范围
                cash_flow_table = results.get('cash_flow_table', [])
                rates = []
                for row in cash_flow_table:
                    rate_str = row.get('cash_flow_distribution_rate', '0.00%')
                    rate_value = float(rate_str.replace('%', '')) if rate_str != '0.00%' else 0
                    if rate_value > 0:
                        rates.append(rate_value)
                
                if rates:
                    min_rate = min(rates)
                    max_rate = max(rates)
                    distribution_rate = f"{min_rate:.2f}%" if min_rate == max_rate else f"{min_rate:.2f}%-{max_rate:.2f}%"
                else:
                    distribution_rate = "0.00%"
                
                # 投资收益分析数据
                investment_analysis = pd.DataFrame([
                    ['内部收益率', core_metrics.get('irr', '0.00%')],
                    ['分配倍数', core_metrics.get('dpi', '0.00')],
                    ['分派率', distribution_rate],
                    ['静态回本周期', core_metrics.get('static_payback_period', '无法回本')],
                    ['计算模式', results.get('calculation_mode', '')],
                    ['投资金额', f"{basic_params.get('investment_amount', 0)} 万元"],
                    ['投资期限', f"{basic_params.get('investment_period', 0)} 年"],
                    ['门槛收益率', f"{basic_params.get('hurdle_rate', 0)}%"]
                ], columns=['指标名称', '指标值'])
                
                investment_analysis.to_excel(writer, sheet_name='投资收益分析', index=False)
                
                # 计算详情工作表
                calculation_mode = results.get('calculation_mode', '')
                
                if calculation_mode == '平层结构-优先还本':
                    columns = [
                        '年份', '净现金流(万元)', '分派率(%)', '期初本金余额(万元)', 
                        '归还本金(万元)', '计提门槛收益(万元)', '分配门槛收益(万元)', 
                        'CarryLP(万元)', 'CarryGP(万元)'
                    ]
                    data_rows = []
                    for row in cash_flow_table:
                        data_rows.append([
                            row.get('year', '0'),
                            row.get('net_cash_flow', '0'),
                            row.get('cash_flow_distribution_rate', '0.00%'),
                            row.get('beginning_principal_balance', '0'),
                            row.get('principal_repayment', '0'),
                            row.get('accrued_hurdle_return', '0'),
                            row.get('distributed_hurdle_return', '0'),
                            row.get('carry_lp', '0'),
                            row.get('carry_gp', '0')
                        ])
                    
                    # 添加总计行
                    totals = results.get('totals', {})
                    if totals:
                        data_rows.append([
                            '总计',
                            totals.get('net_cash_flow', '0'),
                            '-',
                            '-',
                            totals.get('principal_repayment', '0'),
                            totals.get('accrued_hurdle_return', '0'),
                            totals.get('distributed_hurdle_return', '0'),
                            totals.get('carry_lp', '0'),
                            totals.get('carry_gp', '0')
                        ])
                        
                elif calculation_mode == '结构化-优先劣后':
                    columns = [
                        '年份', '净现金流(万元)', '分派率(%)', '优先级期初本金(万元)',
                        '优先级本金归还(万元)', '优先级收益计提(万元)', '优先级收益分配(万元)',
                        '劣后级本金余额(万元)', '劣后级本金归还(万元)', 'CarryLP(万元)', 'CarryGP(万元)'
                    ]
                    data_rows = []
                    for row in cash_flow_table:
                        data_rows.append([
                            row.get('year', '0'),
                            row.get('net_cash_flow', '0'),
                            row.get('cash_flow_distribution_rate', '0.00%'),
                            row.get('senior_beginning_principal', '0'),
                            row.get('senior_principal_repayment', '0'),
                            row.get('senior_hurdle_accrual', '0'),
                            row.get('senior_periodic_return', '0'),
                            row.get('subordinate_principal_balance', '0'),
                            row.get('subordinate_principal_repayment', '0'),
                            row.get('carry_lp', '0'),
                            row.get('carry_gp', '0')
                        ])
                    
                    # 添加总计行
                    totals = results.get('totals', {})
                    if totals:
                        data_rows.append([
                            '总计',
                            totals.get('net_cash_flow', '0'),
                            '-',
                            '-',
                            totals.get('senior_principal_repayment', '0'),
                            totals.get('senior_hurdle_accrual', '0'),
                            totals.get('senior_periodic_return', '0'),
                            '-',
                            totals.get('subordinate_principal_repayment', '0'),
                            totals.get('carry_lp', '0'),
                            totals.get('carry_gp', '0')
                        ])
                
                # 创建计算详情DataFrame
                calculation_details_df = pd.DataFrame(data_rows, columns=columns)
                calculation_details_df.to_excel(writer, sheet_name='计算详情', index=False)
                
                # 基本参数工作表
                basic_info = pd.DataFrame([
                    ['投资标的', basic_params.get('investment_target', '')],
                    ['投资金额(万元)', basic_params.get('investment_amount', 0)],
                    ['投资期限(年)', basic_params.get('investment_period', 0)],
                    ['门槛收益率(%)', basic_params.get('hurdle_rate', 0)],
                    ['管理人Carry(%)', basic_params.get('management_carry', 0)],
                    ['计算模式', calculation_mode]
                ], columns=['参数名称', '参数值'])
                basic_info.to_excel(writer, sheet_name='基本参数', index=False)
            
            output.seek(0)
            
            # 生成测试文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'测试导出_{mode_name}_{timestamp}.xlsx'
            
            # 保存测试文件
            with open(filename, 'wb') as f:
                f.write(output.getvalue())
            
            print(f"✅ {mode_name} 导出测试成功，文件保存为: {filename}")
            
            # 验证文件内容
            verify_excel_content(filename, mode_name)
            
        except Exception as e:
            print(f"❌ {mode_name} 导出测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

def verify_excel_content(filename, mode_name):
    """验证Excel文件内容"""
    try:
        # 读取投资收益分析工作表
        investment_df = pd.read_excel(filename, sheet_name='投资收益分析')
        print(f"   📋 投资收益分析工作表包含 {len(investment_df)} 个指标")
        
        # 读取计算详情工作表
        details_df = pd.read_excel(filename, sheet_name='计算详情')
        print(f"   📊 计算详情工作表包含 {len(details_df)} 行数据，{len(details_df.columns)} 列")
        
        # 读取基本参数工作表
        params_df = pd.read_excel(filename, sheet_name='基本参数')
        print(f"   ⚙️ 基本参数工作表包含 {len(params_df)} 个参数")
        
        # 验证列名是否正确
        expected_metrics_cols = ['指标名称', '指标值']
        expected_params_cols = ['参数名称', '参数值']
        
        if list(investment_df.columns) == expected_metrics_cols:
            print(f"   ✅ 投资收益分析列名正确")
        else:
            print(f"   ❌ 投资收益分析列名不匹配: {investment_df.columns}")
            
        if list(params_df.columns) == expected_params_cols:
            print(f"   ✅ 基本参数列名正确")
        else:
            print(f"   ❌ 基本参数列名不匹配: {params_df.columns}")
        
        # 验证关键指标是否存在
        metrics_names = investment_df['指标名称'].tolist()
        expected_metrics = ['内部收益率', '分配倍数', '分派率', '静态回本周期', '计算模式', '投资金额', '投资期限', '门槛收益率']
        
        missing_metrics = [m for m in expected_metrics if m not in metrics_names]
        if not missing_metrics:
            print(f"   ✅ 所有核心指标都存在")
        else:
            print(f"   ❌ 缺少指标: {missing_metrics}")
        
        print(f"   📝 验证完成")
        
    except Exception as e:
        print(f"   ❌ 文件验证失败: {str(e)}")

if __name__ == '__main__':
    test_export_function()
    print("\n🎉 测试完成！") 