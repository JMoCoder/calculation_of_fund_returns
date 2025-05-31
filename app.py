#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收益分配测算系统 - 后端应用程序
提供基金收益分配的计算逻辑和API接口

主要功能：
- 平层结构分配计算（优先还本、期间分配）
- 结构化分配计算（优先劣后、包含夹层、息息本本）
- IRR/DPI等核心指标计算
- Excel文件导入导出
- 数据验证和安全处理
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import io
import os
from datetime import datetime
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
import math
import traceback

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局计算器实例
calculator = None

# ==================== 数据格式化工具函数 ====================

def safe_round(value, decimals=2):
    """安全的数值舍入，防止NaN和Infinity"""
    if value is None or math.isnan(value) or math.isinf(value):
        return 0.0
    return round(float(value), decimals)

def safe_format_currency(value):
    """安全格式化货币，返回格式化字符串"""
    safe_value = safe_round(value, 0)
    try:
        return f"{safe_value:,.0f}"
    except (ValueError, TypeError):
        return "0"

def safe_format_percentage(value, decimals=2):
    """安全格式化百分比，返回格式化字符串"""
    safe_value = safe_round(value, decimals)
    try:
        return f"{safe_value:.{decimals}f}%"
    except (ValueError, TypeError):
        return f"0.{'0' * decimals}%"

def safe_format_decimal(value, decimals=2):
    """安全格式化小数，返回格式化字符串"""
    safe_value = safe_round(value, decimals)
    try:
        return f"{safe_value:.{decimals}f}"
    except (ValueError, TypeError):
        return f"0.{'0' * decimals}"

def safe_format_years(value):
    """安全格式化年份，特殊处理无法回本的情况"""
    # 如果已经是字符串（比如"无法回本"），直接返回
    if isinstance(value, str):
        return value
    
    # 如果是None、NaN、Infinity或负数，返回"无法回本"
    if value is None or (isinstance(value, (int, float)) and (math.isnan(value) or math.isinf(value) or value <= 0)):
        return "无法回本"
    
    # 否则格式化为带年份单位的字符串
    return f"{safe_round(value, 2):.2f} 年"

def format_calculation_results(raw_data):
    """格式化计算结果，返回直接的格式化字符串"""
    try:
        # 格式化核心指标 - 直接返回格式化字符串
        core_metrics = raw_data.get('core_metrics', {})
        formatted_metrics = {
            'irr': safe_format_percentage(core_metrics.get('irr', 0)),
            'dpi': safe_format_decimal(core_metrics.get('dpi', 0)),
            'static_payback_period': safe_format_years(core_metrics.get('static_payback_period')),
            'dynamic_payback_period': safe_format_years(core_metrics.get('dynamic_payback_period'))
        }
        
        # 格式化现金流表格 - 直接返回格式化字符串
        cash_flow_table = raw_data.get('cash_flow_table', [])
        formatted_table = []
        
        for row in cash_flow_table:
            # 格式化输出时的字段映射 - 统一字段名称
            if raw_data.get('calculation_mode') == '平层结构-优先还本':
                formatted_row = {
                    'year': str(int(row.get('year', 0))),
                    'net_cash_flow': safe_format_currency(row.get('net_cash_flow', 0)),
                    'cash_flow_distribution_rate': safe_format_percentage(row.get('cash_flow_distribution_rate', 0)),
                    'beginning_principal_balance': safe_format_currency(row.get('beginning_principal_balance', 0)),
                    'principal_repayment': safe_format_currency(row.get('principal_repayment', 0)),
                    'accrued_hurdle_return': safe_format_currency(row.get('accrued_hurdle_return', 0)),
                    'distributed_hurdle_return': safe_format_currency(row.get('distributed_hurdle_return', 0)),
                    'carry_lp': safe_format_currency(row.get('carry_lp', 0)),
                    'carry_gp': safe_format_currency(row.get('carry_gp', 0))
                }
            elif raw_data.get('calculation_mode') == '平层结构-期间分配':
                formatted_row = {
                    'year': str(int(row.get('year', 0))),
                    'net_cash_flow': safe_format_currency(row.get('net_cash_flow', 0)),
                    'cash_flow_distribution_rate': safe_format_percentage(row.get('cash_flow_distribution_rate', 0)),
                    'beginning_principal_balance': safe_format_currency(row.get('beginning_principal_balance', 0)),
                    'periodic_distribution': safe_format_currency(row.get('periodic_distribution', 0)),
                    'accrued_hurdle_return': safe_format_currency(row.get('accrued_hurdle_return', 0)),
                    'principal_repayment': safe_format_currency(row.get('principal_repayment', 0)),
                    'distributed_hurdle_return': safe_format_currency(row.get('distributed_hurdle_return', 0)),
                    'carry_lp': safe_format_currency(row.get('carry_lp', 0)),
                    'carry_gp': safe_format_currency(row.get('carry_gp', 0))
                }
            elif raw_data.get('calculation_mode') == '结构化-优先劣后':
                formatted_row = {
                    'year': str(int(row.get('year', 0))),
                    'net_cash_flow': safe_format_currency(row.get('net_cash_flow', 0)),
                    'cash_flow_distribution_rate': safe_format_percentage(row.get('cash_flow_distribution_rate', 0)),
                    'senior_beginning_principal': safe_format_currency(row.get('senior_beginning_principal', 0)),
                    'senior_principal_repayment': safe_format_currency(row.get('senior_principal_repayment', 0)),
                    'senior_hurdle_accrual': safe_format_currency(row.get('senior_hurdle_accrual', 0)),
                    'senior_periodic_return': safe_format_currency(row.get('senior_periodic_return', 0)),
                    'subordinate_principal_balance': safe_format_currency(row.get('subordinate_principal_balance', 0)),
                    'subordinate_principal_repayment': safe_format_currency(row.get('subordinate_principal_repayment', 0)),
                    'carry_lp': safe_format_currency(row.get('carry_lp', 0)),
                    'carry_gp': safe_format_currency(row.get('carry_gp', 0))
                }
            elif raw_data.get('calculation_mode') == '结构化-包含夹层':
                formatted_row = {
                    'year': str(int(row.get('year', 0))),
                    'net_cash_flow': safe_format_currency(row.get('net_cash_flow', 0)),
                    'cash_flow_distribution_rate': safe_format_percentage(row.get('cash_flow_distribution_rate', 0)),
                    'senior_beginning_principal': safe_format_currency(row.get('senior_beginning_principal', 0)),
                    'mezzanine_beginning_principal': safe_format_currency(row.get('mezzanine_beginning_principal', 0)),
                    'subordinate_beginning_principal': safe_format_currency(row.get('subordinate_beginning_principal', 0)),
                    'senior_hurdle_distribution': safe_format_currency(row.get('senior_hurdle_distribution', 0)),
                    'mezzanine_hurdle_distribution': safe_format_currency(row.get('mezzanine_hurdle_distribution', 0)),
                    'senior_principal_repayment': safe_format_currency(row.get('senior_principal_repayment', 0)),
                    'mezzanine_principal_repayment': safe_format_currency(row.get('mezzanine_principal_repayment', 0)),
                    'subordinate_principal_repayment': safe_format_currency(row.get('subordinate_principal_repayment', 0)),
                    'carry_lp': safe_format_currency(row.get('carry_lp', 0)),
                    'carry_gp': safe_format_currency(row.get('carry_gp', 0))
                }
            elif raw_data.get('calculation_mode') == '结构化-息息本本':
                formatted_row = {
                    'year': str(int(row.get('year', 0))),
                    'net_cash_flow': safe_format_currency(row.get('net_cash_flow', 0)),
                    'cash_flow_distribution_rate': safe_format_percentage(row.get('cash_flow_distribution_rate', 0)),
                    'senior_beginning_principal': safe_format_currency(row.get('senior_beginning_principal', 0)),
                    'senior_periodic_return': safe_format_currency(row.get('senior_periodic_return', 0)),
                    'subordinate_beginning_principal': safe_format_currency(row.get('subordinate_beginning_principal', 0)),
                    'subordinate_periodic_return': safe_format_currency(row.get('subordinate_periodic_return', 0)),
                    'senior_principal_repayment': safe_format_currency(row.get('senior_principal_repayment', 0)),
                    'subordinate_principal_repayment': safe_format_currency(row.get('subordinate_principal_repayment', 0)),
                    'carry_lp': safe_format_currency(row.get('carry_lp', 0)),
                    'carry_gp': safe_format_currency(row.get('carry_gp', 0))
                }
            
            formatted_table.append(formatted_row)
        
        # 计算并格式化总计 - 直接返回格式化字符串
        totals = calculate_totals(cash_flow_table, raw_data.get('calculation_mode'))
        formatted_totals = {}
        for key, value in totals.items():
            if key == 'cash_flow_distribution_rate':
                # 分派率不做总计，用特殊处理
                continue
            formatted_totals[key] = safe_format_currency(value)
        
        return {
            'success': True,
            'calculation_mode': raw_data.get('calculation_mode'),
            'core_metrics': formatted_metrics,
            'cash_flow_table': formatted_table,
            'totals': formatted_totals,
            'raw_data': raw_data  # 保留原始数据供图表使用
        }
        
    except Exception as e:
        logger.error(f"格式化计算结果时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': f'数据格式化失败: {str(e)}'
        }

def calculate_totals(cash_flow_table, calculation_mode):
    """计算各列的总计"""
    totals = {
        'net_cash_flow': 0,
        'cash_flow_distribution_rate': 0
    }
    
    for row in cash_flow_table:
        totals['net_cash_flow'] += safe_round(row.get('net_cash_flow', 0))
        
        # 根据计算模式累计相应字段
        if calculation_mode == '平层结构-优先还本':
            if 'principal_repayment' not in totals:
                totals.update({
                    'principal_repayment': 0,
                    'accrued_hurdle_return': 0,
                    'distributed_hurdle_return': 0,
                    'carry_lp': 0,
                    'carry_gp': 0
                })
            totals['principal_repayment'] += safe_round(row.get('principal_repayment', 0))
            totals['accrued_hurdle_return'] += safe_round(row.get('accrued_hurdle_return', 0))
            totals['distributed_hurdle_return'] += safe_round(row.get('distributed_hurdle_return', 0))
            totals['carry_lp'] += safe_round(row.get('carry_lp', 0))
            totals['carry_gp'] += safe_round(row.get('carry_gp', 0))
        elif calculation_mode == '结构化-优先劣后':
            if 'senior_principal_repayment' not in totals:
                totals.update({
                    'senior_principal_repayment': 0,
                    'senior_hurdle_accrual': 0,
                    'senior_periodic_return': 0,
                    'subordinate_principal_repayment': 0,
                    'carry_lp': 0,
                    'carry_gp': 0
                })
            totals['senior_principal_repayment'] += safe_round(row.get('senior_principal_repayment', 0))
            totals['senior_hurdle_accrual'] += safe_round(row.get('senior_hurdle_accrual', 0))
            totals['senior_periodic_return'] += safe_round(row.get('senior_periodic_return', 0))
            totals['subordinate_principal_repayment'] += safe_round(row.get('subordinate_principal_repayment', 0))
            totals['carry_lp'] += safe_round(row.get('carry_lp', 0))
            totals['carry_gp'] += safe_round(row.get('carry_gp', 0))
            
    return totals

class FundCalculator:
    """
    基金收益分配计算引擎
    
    提供多种分配模式的计算功能：
    1. 平层结构：优先还本、期间分配
    2. 结构化：优先劣后、包含夹层、息息本本
    """
    
    def __init__(self):
        """初始化计算器"""
        self.reset_data()
    
    def reset_data(self):
        """重置所有数据"""
        self.basic_params = {}
        self.cash_flows = []
        self.distribution_params = {}
        self.results = {}
    
    def set_basic_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        设置基本投资参数
        
        Args:
            params: 包含以下字段的字典
                - investment_target: 投资标的
                - investment_amount: 拟投资金额（万元）
                - investment_period: 投资期限（年）
                - hurdle_rate: 门槛收益率（%）
                - management_carry: 管理人Carry（%）
        
        Returns:
            验证结果和处理后的参数
        """
        try:
            # 数据验证
            required_fields = [
                'investment_target', 'investment_amount', 
                'investment_period', 'hurdle_rate', 'management_carry'
            ]
            
            for field in required_fields:
                if field not in params:
                    return {'success': False, 'message': f'缺少必需字段: {field}'}
            
            # 数值验证
            if params['investment_amount'] <= 0:
                return {'success': False, 'message': '投资金额必须大于0'}
            
            if params['investment_period'] <= 0 or params['investment_period'] > 30:
                return {'success': False, 'message': '投资期限必须在1-30年之间'}
            
            if params['hurdle_rate'] < 0 or params['hurdle_rate'] > 100:
                return {'success': False, 'message': '门槛收益率必须在0-100%之间'}
            
            if params['management_carry'] < 0 or params['management_carry'] > 100:
                return {'success': False, 'message': '管理人Carry必须在0-100%之间'}
            
            # 保存参数
            self.basic_params = params.copy()
            
            # 初始化现金流数组
            self.cash_flows = [0.0] * (int(params['investment_period']) + 1)
            
            return {
                'success': True, 
                'message': '基本参数设置成功',
                'data': self.basic_params
            }
            
        except Exception as e:
            logger.error(f"设置基本参数时发生错误: {str(e)}")
            return {'success': False, 'message': f'参数设置失败: {str(e)}'}
    
    def set_cash_flows(self, cash_flows: List[float]) -> Dict[str, Any]:
        """
        设置净现金流数据
        
        Args:
            cash_flows: 各年度净现金流列表
        
        Returns:
            处理结果
        """
        try:
            if not self.basic_params:
                return {'success': False, 'message': '请先设置基本参数'}
            
            expected_length = int(self.basic_params['investment_period'])
            if len(cash_flows) != expected_length:
                return {'success': False, 'message': f'现金流数据长度应为{expected_length}年'}
            
            # 验证现金流数据
            for i, cf in enumerate(cash_flows):
                if not isinstance(cf, (int, float)):
                    return {'success': False, 'message': f'第{i+1}年现金流数据格式错误'}
                if cf < 0:
                    return {'success': False, 'message': f'第{i+1}年现金流不能为负数'}
            
            self.cash_flows = cash_flows.copy()
            
            return {
                'success': True,
                'message': '现金流数据设置成功',
                'data': self.cash_flows
            }
            
        except Exception as e:
            logger.error(f"设置现金流数据时发生错误: {str(e)}")
            return {'success': False, 'message': f'现金流设置失败: {str(e)}'}
    
    def calculate_irr(self, cash_flows: List[float], initial_investment: float) -> float:
        """
        计算内部收益率（IRR）
        
        Args:
            cash_flows: 现金流列表
            initial_investment: 初始投资金额
        
        Returns:
            IRR值（百分比）
        """
        try:
            # 输入验证
            if not cash_flows or initial_investment <= 0:
                logger.warning("IRR计算输入无效：现金流为空或初始投资金额无效")
                return 0.0
            
            # 检查现金流是否全为零或负数
            total_cash_flow = sum(cash_flows)
            if total_cash_flow <= 0:
                logger.warning("IRR计算：现金流总和小于等于零，无法计算有效IRR")
                return 0.0
            
            # 构建完整现金流序列：初始投资为负值，后续为正值
            full_cash_flows = [-initial_investment] + cash_flows
            
            # 使用牛顿法求解IRR
            def npv(rate, flows):
                """计算净现值"""
                try:
                    if rate <= -1:  # 避免除零错误
                        return float('inf')
                    return sum(cf / (1 + rate) ** i for i, cf in enumerate(flows))
                except (ZeroDivisionError, OverflowError):
                    return float('inf')
            
            def npv_derivative(rate, flows):
                """计算NPV对利率的导数"""
                try:
                    if rate <= -1:  # 避免除零错误
                        return 0.0
                    return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(flows))
                except (ZeroDivisionError, OverflowError):
                    return 0.0
            
            # 初始猜测值
            rate = 0.1
            tolerance = 1e-6
            max_iterations = 100
            
            for iteration in range(max_iterations):
                # 检查rate是否有效
                if not isinstance(rate, (int, float)) or math.isnan(rate) or math.isinf(rate):
                    logger.warning(f"IRR计算：第{iteration}次迭代时rate无效: {rate}")
                    rate = 0.1  # 重置为初始猜测值
                    continue
                
                npv_value = npv(rate, full_cash_flows)
                if abs(npv_value) < tolerance:
                    break
                
                derivative = npv_derivative(rate, full_cash_flows)
                if abs(derivative) < tolerance:
                    logger.warning("IRR计算：导数太小，停止迭代")
                    break
                
                # 计算新的rate值
                new_rate = rate - npv_value / derivative
                
                # 检查new_rate是否有效
                if not isinstance(new_rate, (int, float)) or math.isnan(new_rate) or math.isinf(new_rate):
                    logger.warning(f"IRR计算：新rate值无效: {new_rate}，使用备用方法")
                    # 使用简单的近似方法
                    return (total_cash_flow / initial_investment - 1) * 100 / len(cash_flows) * 100
                
                # 限制rate的范围，避免极端值
                if new_rate < -0.99:
                    new_rate = -0.99
                elif new_rate > 10:  # 限制最大1000%收益率
                    new_rate = 10
                
                rate = new_rate
            
            # 最终检查返回值
            final_result = rate * 100
            if not isinstance(final_result, (int, float)) or math.isnan(final_result) or math.isinf(final_result):
                logger.warning(f"IRR计算：最终结果无效: {final_result}，使用备用计算")
                # 使用简单的平均收益率作为备用
                return (total_cash_flow / initial_investment - 1) * 100 / len(cash_flows) * 100
            
            return final_result  # 转换为百分比
            
        except Exception as e:
            logger.error(f"计算IRR时发生错误: {str(e)}")
            # 返回安全的默认值
            try:
                # 计算简单的平均收益率
                total_cash_flow = sum(cash_flows)
                simple_return = (total_cash_flow / initial_investment - 1) * 100 / len(cash_flows) * 100
                if isinstance(simple_return, (int, float)) and not math.isnan(simple_return) and not math.isinf(simple_return):
                    return simple_return
            except:
                pass
            return 0.0
    
    def calculate_dpi(self, cash_flows: List[float], initial_investment: float) -> float:
        """
        计算DPI（分配倍数）
        
        Args:
            cash_flows: 现金流列表
            initial_investment: 初始投资金额
        
        Returns:
            DPI值
        """
        try:
            # 输入验证
            if not cash_flows or initial_investment <= 0:
                logger.warning("DPI计算输入无效：现金流为空或初始投资金额无效")
                return 0.0
            
            total_distributions = sum(cash_flows)
            
            # 安全除法
            if initial_investment > 0:
                result = total_distributions / initial_investment
                # 检查结果是否有效
                if isinstance(result, (int, float)) and not math.isnan(result) and not math.isinf(result):
                    return result
                else:
                    logger.warning(f"DPI计算结果无效: {result}")
                    return 0.0
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算DPI时发生错误: {str(e)}")
            return 0.0
    
    def calculate_static_payback_period(self, cash_flows: List[float], initial_investment: float) -> float:
        """
        计算静态回本周期
        
        Args:
            cash_flows: 现金流列表
            initial_investment: 初始投资金额
        
        Returns:
            静态回本周期（年）
        """
        try:
            # 输入验证
            if not cash_flows or initial_investment <= 0:
                logger.warning("静态回本周期计算输入无效")
                return float('inf')
            
            cumulative_cash_flow = 0.0
            for i, cf in enumerate(cash_flows):
                # 检查现金流值是否有效
                if not isinstance(cf, (int, float)) or math.isnan(cf) or math.isinf(cf):
                    logger.warning(f"第{i+1}年现金流无效: {cf}")
                    continue
                    
                cumulative_cash_flow += cf
                if cumulative_cash_flow >= initial_investment:
                    # 线性插值计算精确的回本时间
                    if i == 0:
                        result = cf / initial_investment if cf > 0 else float('inf')
                    else:
                        prev_cumulative = cumulative_cash_flow - cf
                        remaining = initial_investment - prev_cumulative
                        result = i + (remaining / cf) if cf > 0 else i + 1
                    
                    # 检查结果是否有效
                    if isinstance(result, (int, float)) and not math.isnan(result):
                        return result
                        
            return float('inf')  # 如果现金流总和不足以回本
        except Exception as e:
            logger.error(f"计算静态回本周期时发生错误: {str(e)}")
            return float('inf')
    
    def calculate_dynamic_payback_period(self, cash_flows: List[float], initial_investment: float, discount_rate: float = 0.1) -> float:
        """
        计算动态回本周期（考虑时间价值）
        
        Args:
            cash_flows: 现金流列表
            initial_investment: 初始投资金额
            discount_rate: 折现率（默认10%）
        
        Returns:
            动态回本周期（年）
        """
        try:
            # 输入验证
            if not cash_flows or initial_investment <= 0:
                logger.warning("动态回本周期计算输入无效")
                return float('inf')
            
            # 使用门槛收益率作为折现率
            if hasattr(self, 'basic_params') and 'hurdle_rate' in self.basic_params:
                discount_rate = self.basic_params['hurdle_rate'] / 100
            
            # 验证折现率
            if not isinstance(discount_rate, (int, float)) or math.isnan(discount_rate) or discount_rate < 0:
                discount_rate = 0.1  # 使用默认值
            
            cumulative_pv = 0.0
            for i, cf in enumerate(cash_flows):
                # 检查现金流值是否有效
                if not isinstance(cf, (int, float)) or math.isnan(cf) or math.isinf(cf):
                    logger.warning(f"第{i+1}年现金流无效: {cf}")
                    continue
                
                try:
                    pv = cf / ((1 + discount_rate) ** (i + 1))
                    # 检查现值是否有效
                    if not isinstance(pv, (int, float)) or math.isnan(pv) or math.isinf(pv):
                        continue
                        
                    cumulative_pv += pv
                    if cumulative_pv >= initial_investment:
                        # 线性插值计算精确的动态回本时间
                        if i == 0:
                            result = 1.0 if pv >= initial_investment else float('inf')
                        else:
                            prev_pv = cumulative_pv - pv
                            remaining = initial_investment - prev_pv
                            year_fraction = remaining / pv if pv > 0 else 0
                            result = i + 1 + year_fraction
                        
                        # 检查结果是否有效
                        if isinstance(result, (int, float)) and not math.isnan(result):
                            return result
                            
                except (ZeroDivisionError, OverflowError):
                    continue
                    
            return float('inf')  # 如果折现后现金流总和不足以回本
        except Exception as e:
            logger.error(f"计算动态回本周期时发生错误: {str(e)}")
            return float('inf')
    
    def safe_round(self, value, digits=2):
        """
        安全的round函数，确保不会因为NaN而崩溃
        
        Args:
            value: 要四舍五入的值
            digits: 小数位数
        
        Returns:
            四舍五入后的值，如果输入无效则返回0
        """
        try:
            if not isinstance(value, (int, float)):
                return 0.0
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return round(value, digits)
        except:
            return 0.0
    
    def calculate_flat_structure_priority_repayment(self) -> Dict[str, Any]:
        """
        计算平层结构 - 优先还本模式（分配方式1.1）
        
        分配顺序：
        1. 还本
        2. 门槛收益
        3. Carry分配
        
        Returns:
            计算结果详细表格
        """
        try:
            investment_amount = self.basic_params['investment_amount']
            hurdle_rate = self.basic_params['hurdle_rate'] / 100
            carry_rate = self.basic_params['management_carry'] / 100
            
            years = len(self.cash_flows)
            
            # 初始化结果表格
            results = []
            
            # 跟踪变量
            remaining_principal = investment_amount  # 剩余本金
            accumulated_hurdle = 0.0  # 累计计提门槛收益
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'beginning_principal_balance': remaining_principal,
                    'principal_repayment': 0.0,
                    'accrued_hurdle_return': 0.0,
                    'distributed_hurdle_return': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：计提门槛收益
                if remaining_principal > 0:
                    hurdle_accrual = remaining_principal * hurdle_rate
                    year_data['accrued_hurdle_return'] = hurdle_accrual
                    accumulated_hurdle += hurdle_accrual
                
                # 步骤2：优先还本
                if remaining_principal > 0 and remaining_cash > 0:
                    principal_payment = min(remaining_cash, remaining_principal)
                    year_data['principal_repayment'] = principal_payment
                    remaining_principal -= principal_payment
                    remaining_cash -= principal_payment
                
                # 步骤3：分配门槛收益
                if accumulated_hurdle > 0 and remaining_cash > 0:
                    hurdle_payment = min(remaining_cash, accumulated_hurdle)
                    year_data['distributed_hurdle_return'] = hurdle_payment
                    accumulated_hurdle -= hurdle_payment
                    remaining_cash -= hurdle_payment
                
                # 步骤4：分配Carry
                if accumulated_hurdle == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            static_payback = self.calculate_static_payback_period(self.cash_flows, investment_amount)
            dynamic_payback = self.calculate_dynamic_payback_period(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '平层结构-优先还本',
                'core_metrics': {
                    'irr': self.safe_round(irr),
                    'dpi': self.safe_round(dpi),
                    'static_payback_period': self.safe_round(static_payback) if static_payback != float('inf') else '无法回本',
                    'dynamic_payback_period': self.safe_round(dynamic_payback) if dynamic_payback != float('inf') else '无法回本'
                },
                'cash_flow_table': results,
                'summary': {
                    'total_principal_repaid': self.safe_round(sum(row['principal_repayment'] for row in results)),
                    'total_hurdle_distributed': self.safe_round(sum(row['distributed_hurdle_return'] for row in results)),
                    'total_carry_lp': self.safe_round(sum(row['carry_lp'] for row in results)),
                    'total_carry_gp': self.safe_round(sum(row['carry_gp'] for row in results))
                }
            }
            
        except Exception as e:
            logger.error(f"计算平层结构-优先还本时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}
    
    def calculate_flat_structure_periodic_distribution(self, periodic_rate: float) -> Dict[str, Any]:
        """
        计算平层结构 - 期间分配模式（分配方式1.2）
        
        Args:
            periodic_rate: 期间收益率（%）
        
        分配顺序：
        1. 期间收益
        2. 还本
        3. 剩余门槛收益
        4. Carry分配
        
        Returns:
            计算结果详细表格
        """
        try:
            investment_amount = self.basic_params['investment_amount']
            hurdle_rate = self.basic_params['hurdle_rate'] / 100
            carry_rate = self.basic_params['management_carry'] / 100
            periodic_rate_decimal = periodic_rate / 100
            
            years = len(self.cash_flows)
            
            # 初始化结果表格
            results = []
            
            # 跟踪变量
            remaining_principal = investment_amount  # 剩余本金
            accumulated_hurdle = 0.0  # 累计计提门槛收益
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'beginning_principal_balance': remaining_principal,
                    'periodic_distribution': 0.0,
                    'accrued_hurdle_return': 0.0,
                    'principal_repayment': 0.0,
                    'distributed_hurdle_return': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：分配期间收益
                if remaining_principal > 0 and remaining_cash > 0:
                    periodic_payment = min(remaining_cash, remaining_principal * periodic_rate_decimal)
                    year_data['periodic_distribution'] = periodic_payment
                    remaining_cash -= periodic_payment
                
                # 步骤2：计提剩余门槛收益（扣除期间收益率）
                if remaining_principal > 0:
                    net_hurdle_rate = hurdle_rate - periodic_rate_decimal
                    if net_hurdle_rate > 0:
                        hurdle_accrual = remaining_principal * net_hurdle_rate
                        year_data['accrued_hurdle_return'] = hurdle_accrual
                        accumulated_hurdle += hurdle_accrual
                
                # 步骤3：归还本金
                if remaining_principal > 0 and remaining_cash > 0:
                    principal_payment = min(remaining_cash, remaining_principal)
                    year_data['principal_repayment'] = principal_payment
                    remaining_principal -= principal_payment
                    remaining_cash -= principal_payment
                
                # 步骤4：分配剩余门槛收益
                if accumulated_hurdle > 0 and remaining_cash > 0:
                    hurdle_payment = min(remaining_cash, accumulated_hurdle)
                    year_data['distributed_hurdle_return'] = hurdle_payment
                    accumulated_hurdle -= hurdle_payment
                    remaining_cash -= hurdle_payment
                
                # 步骤5：分配Carry
                if accumulated_hurdle == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            static_payback = self.calculate_static_payback_period(self.cash_flows, investment_amount)
            dynamic_payback = self.calculate_dynamic_payback_period(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '平层结构-期间分配',
                'core_metrics': {
                    'irr': self.safe_round(irr),
                    'dpi': self.safe_round(dpi),
                    'static_payback_period': self.safe_round(static_payback) if static_payback != float('inf') else '无法回本',
                    'dynamic_payback_period': self.safe_round(dynamic_payback) if dynamic_payback != float('inf') else '无法回本'
                },
                'cash_flow_table': results,
                'summary': {
                    'total_periodic_distribution': self.safe_round(sum(row['periodic_distribution'] for row in results)),
                    'total_principal_repaid': self.safe_round(sum(row['principal_repayment'] for row in results)),
                    'total_hurdle_distributed': self.safe_round(sum(row['distributed_hurdle_return'] for row in results)),
                    'total_carry_lp': self.safe_round(sum(row['carry_lp'] for row in results)),
                    'total_carry_gp': self.safe_round(sum(row['carry_gp'] for row in results))
                }
            }
            
        except Exception as e:
            logger.error(f"计算平层结构-期间分配时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}
    
    def calculate_structured_senior_subordinate(self, senior_ratio: float) -> Dict[str, Any]:
        """
        计算结构化 - 优先劣后模式（分配方式2.1）
        
        Args:
            senior_ratio: 优先级比例（%）
        
        分配顺序：
        1. 优先级还本
        2. 优先级门槛收益
        3. 劣后还本
        4. Carry分配
        
        Returns:
            计算结果详细表格
        """
        try:
            investment_amount = self.basic_params['investment_amount']
            senior_rate = self.basic_params['hurdle_rate'] / 100  # 优先级收益率等于门槛收益率
            carry_rate = self.basic_params['management_carry'] / 100
            senior_ratio_decimal = senior_ratio / 100
            subordinate_ratio_decimal = 1 - senior_ratio_decimal
            
            senior_amount = investment_amount * senior_ratio_decimal
            subordinate_amount = investment_amount * subordinate_ratio_decimal
            
            years = len(self.cash_flows)
            
            # 初始化结果表格
            results = []
            
            # 跟踪变量
            remaining_senior_principal = senior_amount
            remaining_subordinate_principal = subordinate_amount
            accumulated_senior_hurdle = 0.0
            
            # 用于记录期初本金的变量
            senior_beginning_balance = senior_amount  # 首年期初本金 = 优先级投资金额
            subordinate_beginning_balance = subordinate_amount  # 首年期初本金 = 劣后投资金额
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'senior_beginning_principal': senior_beginning_balance,  # 使用正确的期初本金
                    'subordinate_beginning_principal': subordinate_beginning_balance,  # 使用正确的期初本金
                    'subordinate_principal_balance': remaining_subordinate_principal,  # 劣后本金余额
                    'senior_hurdle_accrual': 0.0,
                    'senior_periodic_return': 0.0,
                    'senior_principal_repayment': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：计提优先级门槛收益（基于期初本金）
                if senior_beginning_balance > 0:
                    senior_hurdle_accrual = senior_beginning_balance * senior_rate
                    year_data['senior_hurdle_accrual'] = senior_hurdle_accrual
                    accumulated_senior_hurdle += senior_hurdle_accrual
                
                # 步骤2：偿还优先级本金
                if remaining_senior_principal > 0 and remaining_cash > 0:
                    senior_principal_payment = min(remaining_cash, remaining_senior_principal)
                    year_data['senior_principal_repayment'] = senior_principal_payment
                    remaining_senior_principal -= senior_principal_payment
                    remaining_cash -= senior_principal_payment
                
                # 步骤3：分配优先级门槛收益
                if accumulated_senior_hurdle > 0 and remaining_cash > 0:
                    senior_hurdle_payment = min(remaining_cash, accumulated_senior_hurdle)
                    year_data['senior_periodic_return'] = senior_hurdle_payment
                    accumulated_senior_hurdle -= senior_hurdle_payment
                    remaining_cash -= senior_hurdle_payment
                
                # 步骤4：偿还劣后本金
                if remaining_senior_principal == 0 and accumulated_senior_hurdle == 0 and remaining_subordinate_principal > 0 and remaining_cash > 0:
                    subordinate_principal_payment = min(remaining_cash, remaining_subordinate_principal)
                    year_data['subordinate_principal_repayment'] = subordinate_principal_payment
                    remaining_subordinate_principal -= subordinate_principal_payment
                    remaining_cash -= subordinate_principal_payment
                
                # 步骤5：分配Carry
                if remaining_senior_principal == 0 and accumulated_senior_hurdle == 0 and remaining_subordinate_principal == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
                
                # 更新下一年的期初本金：本年期初本金 - 本年摊还本金
                senior_beginning_balance = senior_beginning_balance - year_data['senior_principal_repayment']
                subordinate_beginning_balance = subordinate_beginning_balance - year_data['subordinate_principal_repayment']
                
                # 确保期初本金不为负数
                if senior_beginning_balance < 0:
                    senior_beginning_balance = 0
                if subordinate_beginning_balance < 0:
                    subordinate_beginning_balance = 0
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            static_payback = self.calculate_static_payback_period(self.cash_flows, investment_amount)
            dynamic_payback = self.calculate_dynamic_payback_period(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '结构化-优先劣后',
                'structure_info': {
                    'senior_amount': self.safe_round(senior_amount),
                    'subordinate_amount': self.safe_round(subordinate_amount),
                    'senior_ratio': senior_ratio,
                    'subordinate_ratio': self.safe_round(100 - senior_ratio)
                },
                'core_metrics': {
                    'irr': self.safe_round(irr),
                    'dpi': self.safe_round(dpi),
                    'static_payback_period': self.safe_round(static_payback) if static_payback != float('inf') else '无法回本',
                    'dynamic_payback_period': self.safe_round(dynamic_payback) if dynamic_payback != float('inf') else '无法回本'
                },
                'cash_flow_table': results,
                'summary': {
                    'total_senior_return': self.safe_round(sum(row['senior_periodic_return'] for row in results)),
                    'total_senior_principal': self.safe_round(sum(row['senior_principal_repayment'] for row in results)),
                    'total_subordinate_principal': self.safe_round(sum(row['subordinate_principal_repayment'] for row in results)),
                    'total_carry_lp': self.safe_round(sum(row['carry_lp'] for row in results)),
                    'total_carry_gp': self.safe_round(sum(row['carry_gp'] for row in results))
                }
            }
            
        except Exception as e:
            logger.error(f"计算结构化-优先劣后时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}

    def calculate_structured_mezzanine(self, senior_ratio: float, mezzanine_ratio: float, mezzanine_rate: float) -> Dict[str, Any]:
        """
        计算结构化 - 包含夹层模式（分配方式2.2）
        
        Args:
            senior_ratio: 优先级比例（%）
            mezzanine_ratio: 夹层比例（%）
            mezzanine_rate: 夹层收益率（%）
        
        分配顺序：
        1. 优先级门槛收益
        2. 夹层门槛收益  
        3. 优先级还本
        4. 夹层还本
        5. 劣后还本
        6. Carry分配
        
        Returns:
            计算结果详细表格
        """
        try:
            investment_amount = self.basic_params['investment_amount']
            senior_rate = self.basic_params['hurdle_rate'] / 100  # 优先级收益率等于门槛收益率
            mezzanine_rate_decimal = mezzanine_rate / 100
            carry_rate = self.basic_params['management_carry'] / 100
            
            senior_ratio_decimal = senior_ratio / 100
            mezzanine_ratio_decimal = mezzanine_ratio / 100
            subordinate_ratio_decimal = 1 - senior_ratio_decimal - mezzanine_ratio_decimal
            
            senior_amount = investment_amount * senior_ratio_decimal
            mezzanine_amount = investment_amount * mezzanine_ratio_decimal
            subordinate_amount = investment_amount * subordinate_ratio_decimal
            
            years = len(self.cash_flows)
            
            # 初始化结果表格
            results = []
            
            # 跟踪变量
            remaining_senior_principal = senior_amount
            remaining_mezzanine_principal = mezzanine_amount
            remaining_subordinate_principal = subordinate_amount
            accumulated_senior_hurdle = 0.0
            accumulated_mezzanine_hurdle = 0.0
            
            # 用于记录期初本金的变量
            senior_beginning_balance = senior_amount  # 首年期初本金 = 优先级投资金额
            mezzanine_beginning_balance = mezzanine_amount  # 首年期初本金 = 夹层投资金额
            subordinate_beginning_balance = subordinate_amount  # 首年期初本金 = 劣后投资金额
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'senior_beginning_principal': senior_beginning_balance,  # 使用正确的期初本金
                    'mezzanine_beginning_principal': mezzanine_beginning_balance,  # 使用正确的期初本金
                    'subordinate_beginning_principal': subordinate_beginning_balance,  # 使用正确的期初本金
                    'senior_hurdle_accrual': 0.0,
                    'mezzanine_hurdle_accrual': 0.0,
                    'senior_hurdle_distribution': 0.0,
                    'mezzanine_hurdle_distribution': 0.0,
                    'senior_principal_repayment': 0.0,
                    'mezzanine_principal_repayment': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：计提门槛收益（基于期初本金）
                if senior_beginning_balance > 0:
                    senior_hurdle_accrual = senior_beginning_balance * senior_rate
                    year_data['senior_hurdle_accrual'] = senior_hurdle_accrual
                    accumulated_senior_hurdle += senior_hurdle_accrual
                    
                if mezzanine_beginning_balance > 0:
                    mezzanine_hurdle_accrual = mezzanine_beginning_balance * mezzanine_rate_decimal
                    year_data['mezzanine_hurdle_accrual'] = mezzanine_hurdle_accrual
                    accumulated_mezzanine_hurdle += mezzanine_hurdle_accrual
                
                # 步骤2：分配优先级门槛收益
                if accumulated_senior_hurdle > 0 and remaining_cash > 0:
                    senior_hurdle_payment = min(remaining_cash, accumulated_senior_hurdle)
                    year_data['senior_hurdle_distribution'] = senior_hurdle_payment
                    accumulated_senior_hurdle -= senior_hurdle_payment
                    remaining_cash -= senior_hurdle_payment
                
                # 步骤3：分配夹层门槛收益
                if accumulated_mezzanine_hurdle > 0 and remaining_cash > 0:
                    mezzanine_hurdle_payment = min(remaining_cash, accumulated_mezzanine_hurdle)
                    year_data['mezzanine_hurdle_distribution'] = mezzanine_hurdle_payment
                    accumulated_mezzanine_hurdle -= mezzanine_hurdle_payment
                    remaining_cash -= mezzanine_hurdle_payment
                
                # 步骤4：优先级还本
                if accumulated_senior_hurdle == 0 and remaining_senior_principal > 0 and remaining_cash > 0:
                    senior_principal_payment = min(remaining_cash, remaining_senior_principal)
                    year_data['senior_principal_repayment'] = senior_principal_payment
                    remaining_senior_principal -= senior_principal_payment
                    remaining_cash -= senior_principal_payment
                
                # 步骤5：夹层还本
                if accumulated_mezzanine_hurdle == 0 and remaining_senior_principal == 0 and remaining_mezzanine_principal > 0 and remaining_cash > 0:
                    mezzanine_principal_payment = min(remaining_cash, remaining_mezzanine_principal)
                    year_data['mezzanine_principal_repayment'] = mezzanine_principal_payment
                    remaining_mezzanine_principal -= mezzanine_principal_payment
                    remaining_cash -= mezzanine_principal_payment
                
                # 步骤6：劣后还本
                if remaining_senior_principal == 0 and remaining_mezzanine_principal == 0 and remaining_subordinate_principal > 0 and remaining_cash > 0:
                    subordinate_principal_payment = min(remaining_cash, remaining_subordinate_principal)
                    year_data['subordinate_principal_repayment'] = subordinate_principal_payment
                    remaining_subordinate_principal -= subordinate_principal_payment
                    remaining_cash -= subordinate_principal_payment
                
                # 步骤7：分配Carry
                if (remaining_senior_principal == 0 and remaining_mezzanine_principal == 0 and 
                    remaining_subordinate_principal == 0 and remaining_cash > 0):
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
                
                # 更新下一年的期初本金：本年期初本金 - 本年摊还本金
                senior_beginning_balance = senior_beginning_balance - year_data['senior_principal_repayment']
                mezzanine_beginning_balance = mezzanine_beginning_balance - year_data['mezzanine_principal_repayment']
                subordinate_beginning_balance = subordinate_beginning_balance - year_data['subordinate_principal_repayment']
                
                # 确保期初本金不为负数
                if senior_beginning_balance < 0:
                    senior_beginning_balance = 0
                if mezzanine_beginning_balance < 0:
                    mezzanine_beginning_balance = 0
                if subordinate_beginning_balance < 0:
                    subordinate_beginning_balance = 0
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            static_payback = self.calculate_static_payback_period(self.cash_flows, investment_amount)
            dynamic_payback = self.calculate_dynamic_payback_period(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '结构化-包含夹层',
                'structure_info': {
                    'senior_amount': self.safe_round(senior_amount),
                    'mezzanine_amount': self.safe_round(mezzanine_amount),
                    'subordinate_amount': self.safe_round(subordinate_amount),
                    'senior_ratio': senior_ratio,
                    'mezzanine_ratio': mezzanine_ratio,
                    'subordinate_ratio': self.safe_round(subordinate_ratio_decimal * 100),
                    'senior_rate': senior_rate,
                    'mezzanine_rate': mezzanine_rate
                },
                'core_metrics': {
                    'irr': self.safe_round(irr),
                    'dpi': self.safe_round(dpi),
                    'static_payback_period': self.safe_round(static_payback) if static_payback != float('inf') else '无法回本',
                    'dynamic_payback_period': self.safe_round(dynamic_payback) if dynamic_payback != float('inf') else '无法回本'
                },
                'cash_flow_table': results,
                'summary': {
                    'total_senior_hurdle': self.safe_round(sum(row['senior_hurdle_distribution'] for row in results)),
                    'total_mezzanine_hurdle': self.safe_round(sum(row['mezzanine_hurdle_distribution'] for row in results)),
                    'total_senior_principal': self.safe_round(sum(row['senior_principal_repayment'] for row in results)),
                    'total_mezzanine_principal': self.safe_round(sum(row['mezzanine_principal_repayment'] for row in results)),
                    'total_subordinate_principal': self.safe_round(sum(row['subordinate_principal_repayment'] for row in results)),
                    'total_carry_lp': self.safe_round(sum(row['carry_lp'] for row in results)),
                    'total_carry_gp': self.safe_round(sum(row['carry_gp'] for row in results))
                }
            }
            
        except Exception as e:
            logger.error(f"计算结构化-包含夹层时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}

    def calculate_structured_interest_principal(self, senior_ratio: float, subordinate_rate: float) -> Dict[str, Any]:
        """
        计算结构化 - 息息本本模式（分配方式2.3）
        
        Args:
            senior_ratio: 优先级比例（%）
            subordinate_rate: 劣后级收益率（%）
        
        分配顺序：
        1. 优先级期间收益
        2. 劣后期间收益
        3. 优先级还本
        4. 劣后还本
        5. Carry分配
        
        Returns:
            计算结果详细表格
        """
        try:
            investment_amount = self.basic_params['investment_amount']
            senior_rate = self.basic_params['hurdle_rate'] / 100  # 优先级收益率等于门槛收益率
            subordinate_rate_decimal = subordinate_rate / 100
            carry_rate = self.basic_params['management_carry'] / 100
            
            senior_ratio_decimal = senior_ratio / 100
            subordinate_ratio_decimal = 1 - senior_ratio_decimal
            
            senior_amount = investment_amount * senior_ratio_decimal
            subordinate_amount = investment_amount * subordinate_ratio_decimal
            
            years = len(self.cash_flows)
            
            # 初始化结果表格
            results = []
            
            # 跟踪变量
            remaining_senior_principal = senior_amount
            remaining_subordinate_principal = subordinate_amount
            
            # 用于记录期初本金的变量
            senior_beginning_balance = senior_amount  # 首年期初本金 = 优先级投资金额
            subordinate_beginning_balance = subordinate_amount  # 首年期初本金 = 劣后投资金额
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'senior_beginning_principal': senior_beginning_balance,  # 使用正确的期初本金
                    'subordinate_beginning_principal': subordinate_beginning_balance,  # 使用正确的期初本金
                    'senior_periodic_return': 0.0,
                    'subordinate_periodic_return': 0.0,
                    'senior_principal_repayment': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：优先级期间收益（基于期初本金）
                if senior_beginning_balance > 0 and remaining_cash > 0:
                    senior_return = min(remaining_cash, senior_beginning_balance * senior_rate)
                    year_data['senior_periodic_return'] = senior_return
                    remaining_cash -= senior_return
                
                # 步骤2：劣后期间收益（基于期初本金）
                if subordinate_beginning_balance > 0 and remaining_cash > 0:
                    subordinate_return = min(remaining_cash, subordinate_beginning_balance * subordinate_rate_decimal)
                    year_data['subordinate_periodic_return'] = subordinate_return
                    remaining_cash -= subordinate_return
                
                # 步骤3：优先级还本
                if remaining_senior_principal > 0 and remaining_cash > 0:
                    senior_principal_payment = min(remaining_cash, remaining_senior_principal)
                    year_data['senior_principal_repayment'] = senior_principal_payment
                    remaining_senior_principal -= senior_principal_payment
                    remaining_cash -= senior_principal_payment
                
                # 步骤4：劣后还本
                if remaining_senior_principal == 0 and remaining_subordinate_principal > 0 and remaining_cash > 0:
                    subordinate_principal_payment = min(remaining_cash, remaining_subordinate_principal)
                    year_data['subordinate_principal_repayment'] = subordinate_principal_payment
                    remaining_subordinate_principal -= subordinate_principal_payment
                    remaining_cash -= subordinate_principal_payment
                
                # 步骤5：分配Carry
                if remaining_senior_principal == 0 and remaining_subordinate_principal == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            static_payback = self.calculate_static_payback_period(self.cash_flows, investment_amount)
            dynamic_payback = self.calculate_dynamic_payback_period(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '结构化-息息本本',
                'structure_info': {
                    'senior_amount': self.safe_round(senior_amount),
                    'subordinate_amount': self.safe_round(subordinate_amount),
                    'senior_ratio': senior_ratio,
                    'subordinate_ratio': self.safe_round(subordinate_ratio_decimal * 100),
                    'senior_rate': senior_rate,
                    'subordinate_rate': subordinate_rate
                },
                'core_metrics': {
                    'irr': self.safe_round(irr),
                    'dpi': self.safe_round(dpi),
                    'static_payback_period': self.safe_round(static_payback) if static_payback != float('inf') else '无法回本',
                    'dynamic_payback_period': self.safe_round(dynamic_payback) if dynamic_payback != float('inf') else '无法回本'
                },
                'cash_flow_table': results,
                'summary': {
                    'total_senior_return': self.safe_round(sum(row['senior_periodic_return'] for row in results)),
                    'total_subordinate_return': self.safe_round(sum(row['subordinate_periodic_return'] for row in results)),
                    'total_senior_principal': self.safe_round(sum(row['senior_principal_repayment'] for row in results)),
                    'total_subordinate_principal': self.safe_round(sum(row['subordinate_principal_repayment'] for row in results)),
                    'total_carry_lp': self.safe_round(sum(row['carry_lp'] for row in results)),
                    'total_carry_gp': self.safe_round(sum(row['carry_gp'] for row in results))
                }
            }
            
        except Exception as e:
            logger.error(f"计算结构化-息息本本时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}

# 新增：重置API端点
@app.route('/api/reset', methods=['POST'])
def reset_calculator():
    """重置计算器状态"""
    try:
        global calculator
        calculator.reset_data()
        logger.info("计算器状态已重置")
        return jsonify({
            'success': True,
            'message': '系统状态已重置'
        })
    except Exception as e:
        logger.error(f"重置计算器错误: {str(e)}")
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'}), 500

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/basic-params', methods=['POST'])
def set_basic_params():
    """设置基本投资参数"""
    try:
        data = request.get_json()
        
        # 增强数据验证和清理
        if not data:
            return jsonify({'success': False, 'message': '请提供有效的参数数据'}), 400
        
        # 验证和清理数值类型数据
        for key in ['investment_amount', 'investment_period', 'hurdle_rate', 'management_carry']:
            if key in data:
                try:
                    value = float(data[key])
                    if math.isnan(value) or math.isinf(value):
                        return jsonify({'success': False, 'message': f'{key}包含无效数值'}), 400
                    data[key] = value
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': f'{key}数据格式错误'}), 400
        
        result = calculator.set_basic_params(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"设置基本参数API错误: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/api/cash-flows', methods=['POST'])
def set_cash_flows():
    """设置净现金流数据"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请提供有效的现金流数据'}), 400
        
        cash_flows = data.get('cash_flows', [])
        
        # 增强现金流数据验证和清理
        cleaned_cash_flows = []
        for i, cf in enumerate(cash_flows):
            try:
                value = float(cf)
                if math.isnan(value) or math.isinf(value):
                    return jsonify({'success': False, 'message': f'第{i+1}年现金流包含无效数值'}), 400
                cleaned_cash_flows.append(value)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': f'第{i+1}年现金流数据格式错误'}), 400
        
        result = calculator.set_cash_flows(cleaned_cash_flows)
        return jsonify(result)
    except Exception as e:
        logger.error(f"设置现金流API错误: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """
    执行收益分配计算
    """
    global calculator
    
    try:
        data = request.get_json()
        logger.info(f"收到计算请求: {data}")
        
        if not calculator:
            calculator = FundCalculator()
        
        # 验证计算模式
        mode = data.get('mode')
        if not mode:
            return jsonify({'success': False, 'message': '缺少计算模式参数'})
        
        # 验证所有数值参数，防止NaN
        def validate_numeric_param(param_name, value, min_val=0, max_val=100):
            if value is None:
                return True  # 允许None值，由各模式自行处理
            if isinstance(value, (int, float)) and not (math.isnan(value) or math.isinf(value)):
                if min_val <= value <= max_val:
                    return True
            logger.error(f"参数 {param_name} 值无效: {value}")
            return False
        
        # 根据模式验证参数
        if mode == 'flat_periodic_distribution':
            periodic_rate = data.get('periodic_rate')
            if not validate_numeric_param('periodic_rate', periodic_rate, 0, 100):
                return jsonify({'success': False, 'message': '期间收益率参数无效'})
            result = calculator.calculate_flat_structure_periodic_distribution(periodic_rate)
            
        elif mode == 'flat_priority_repayment':
            result = calculator.calculate_flat_structure_priority_repayment()
            
        elif mode == 'structured_senior_subordinate':
            senior_ratio = data.get('senior_ratio')
            if not validate_numeric_param('senior_ratio', senior_ratio, 1, 99):
                return jsonify({'success': False, 'message': '优先级比例参数无效'})
            result = calculator.calculate_structured_senior_subordinate(senior_ratio)
            
        elif mode == 'structured_mezzanine':
            senior_ratio = data.get('senior_ratio')
            mezzanine_ratio = data.get('mezzanine_ratio')
            mezzanine_rate = data.get('mezzanine_rate')
            
            if not validate_numeric_param('senior_ratio', senior_ratio, 1, 97):
                return jsonify({'success': False, 'message': '优先级比例参数无效'})
            if not validate_numeric_param('mezzanine_ratio', mezzanine_ratio, 1, 97):
                return jsonify({'success': False, 'message': '夹层比例参数无效'})
            if not validate_numeric_param('mezzanine_rate', mezzanine_rate, 0, 100):
                return jsonify({'success': False, 'message': '夹层收益率参数无效'})
                
            # 验证比例总和
            if senior_ratio + mezzanine_ratio >= 100:
                return jsonify({'success': False, 'message': '优先级和夹层比例总和必须小于100%'})
                
            result = calculator.calculate_structured_mezzanine(senior_ratio, mezzanine_ratio, mezzanine_rate)
            
        elif mode == 'structured_interest_principal':
            senior_ratio = data.get('senior_ratio')
            subordinate_rate = data.get('subordinate_rate')
            
            if not validate_numeric_param('senior_ratio', senior_ratio, 1, 99):
                return jsonify({'success': False, 'message': '优先级比例参数无效'})
            if not validate_numeric_param('subordinate_rate', subordinate_rate, 0, 100):
                return jsonify({'success': False, 'message': '劣后级收益率参数无效'})
                
            result = calculator.calculate_structured_interest_principal(senior_ratio, subordinate_rate)
            
        else:
            return jsonify({'success': False, 'message': f'不支持的计算模式: {mode}'})
        
        logger.info(f"计算完成，模式: {mode}")
        
        # 格式化结果并返回
        if result.get('success'):
            formatted_result = format_calculation_results(result)
            logger.info("结果格式化完成")
            return jsonify(formatted_result)
        else:
            logger.error(f"计算失败: {result.get('message')}")
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"计算请求处理异常: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'计算请求处理失败: {str(e)}'})

@app.route('/api/export', methods=['POST'])
def export_results():
    """导出计算结果到Excel"""
    try:
        data = request.get_json()
        results = data.get('results')
        
        if not results:
            return jsonify({'success': False, 'message': '没有可导出的数据'}), 400
        
        # 创建Excel文件
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 基本信息表
            basic_info = pd.DataFrame([
                ['投资标的', calculator.basic_params.get('investment_target', '')],
                ['投资金额(万元)', calculator.basic_params.get('investment_amount', 0)],
                ['投资期限(年)', calculator.basic_params.get('investment_period', 0)],
                ['门槛收益率(%)', calculator.basic_params.get('hurdle_rate', 0)],
                ['管理人Carry(%)', calculator.basic_params.get('management_carry', 0)],
                ['计算模式', results.get('calculation_mode', '')],
                ['IRR(%)', results.get('core_metrics', {}).get('irr', 0)],
                ['DPI', results.get('core_metrics', {}).get('dpi', 0)]
            ], columns=['项目', '数值'])
            basic_info.to_excel(writer, sheet_name='基本信息', index=False)
            
            # 现金流分配表
            if 'cash_flow_table' in results:
                df = pd.DataFrame(results['cash_flow_table'])
                df.to_excel(writer, sheet_name='现金流分配表', index=False)
        
        output.seek(0)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'收益分配测算结果_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"导出Excel错误: {str(e)}")
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500

@app.route('/api/import', methods=['POST'])
def import_excel():
    """从Excel导入数据"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': '文件格式不支持，请上传Excel文件'}), 400
        
        # 读取Excel文件
        try:
            # 读取基本参数表
            basic_df = pd.read_excel(file, sheet_name='基本参数')
            # 读取现金流表
            cashflow_df = pd.read_excel(file, sheet_name='净现金流')
        except Exception as e:
            return jsonify({'success': False, 'message': f'Excel文件格式错误，请使用标准模板：{str(e)}'}), 400
        
        # 解析基本参数
        basic_params = {}
        try:
            for _, row in basic_df.iterrows():
                param_name = str(row['参数名称']).strip()
                param_value = row['参数值']
                
                if '投资标的' in param_name:
                    basic_params['investment_target'] = str(param_value).strip()
                elif '投资金额' in param_name:
                    value = float(param_value)
                    if math.isnan(value) or math.isinf(value) or value <= 0:
                        return jsonify({'success': False, 'message': '投资金额数据无效'}), 400
                    basic_params['investment_amount'] = value
                elif '投资期限' in param_name:
                    value = int(param_value)
                    if value <= 0 or value > 30:
                        return jsonify({'success': False, 'message': '投资期限数据无效'}), 400
                    basic_params['investment_period'] = value
                elif '门槛收益率' in param_name:
                    value = float(param_value)
                    if math.isnan(value) or math.isinf(value) or value < 0 or value > 100:
                        return jsonify({'success': False, 'message': '门槛收益率数据无效'}), 400
                    basic_params['hurdle_rate'] = value
                elif 'Carry' in param_name or 'carry' in param_name:
                    value = float(param_value)
                    if math.isnan(value) or math.isinf(value) or value < 0 or value > 100:
                        return jsonify({'success': False, 'message': '管理人Carry数据无效'}), 400
                    basic_params['management_carry'] = value
        except Exception as e:
            return jsonify({'success': False, 'message': f'基本参数解析失败：{str(e)}'}), 400
        
        # 解析现金流数据
        cash_flows = []
        try:
            for index, row in cashflow_df.iterrows():
                value = float(row['净现金流(万元)'])
                if math.isnan(value) or math.isinf(value) or value < 0:
                    return jsonify({'success': False, 'message': f'第{index+1}年现金流数据无效'}), 400
                cash_flows.append(value)
        except Exception as e:
            return jsonify({'success': False, 'message': f'现金流数据解析失败：{str(e)}'}), 400
        
        # 验证数据完整性
        required_params = ['investment_target', 'investment_amount', 'investment_period', 'hurdle_rate', 'management_carry']
        for param in required_params:
            if param not in basic_params:
                return jsonify({'success': False, 'message': f'缺少必要参数：{param}'}), 400
        
        if len(cash_flows) != basic_params['investment_period']:
            return jsonify({'success': False, 'message': f'现金流年数({len(cash_flows)})与投资期限({basic_params["investment_period"]})不匹配'}), 400
        
        return jsonify({
            'success': True,
            'message': '文件导入成功',
            'data': {
                'basic_params': basic_params,
                'cash_flows': cash_flows,
                'rows': len(cashflow_df),
                'columns': list(cashflow_df.columns)
            }
        })
        
    except Exception as e:
        logger.error(f"导入Excel错误: {str(e)}")
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'}), 500

@app.route('/api/template')
def download_template():
    """下载Excel模板"""
    try:
        # 创建模板Excel文件
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 基本参数模板
            basic_template = pd.DataFrame([
                ['投资标的', '请输入投资标的名称'],
                ['投资金额(万元)', 1000],
                ['投资期限(年)', 5],
                ['门槛收益率(%)', 8],
                ['管理人Carry(%)', 20]
            ], columns=['参数名称', '参数值'])
            basic_template.to_excel(writer, sheet_name='基本参数', index=False)
            
            # 现金流模板
            cash_flow_template = pd.DataFrame({
                '年份': [1, 2, 3, 4, 5],
                '净现金流(万元)': [100, 200, 300, 400, 500]
            })
            cash_flow_template.to_excel(writer, sheet_name='净现金流', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='收益分配测算模板.xlsx'
        )
        
    except Exception as e:
        logger.error(f"下载模板错误: {str(e)}")
        return jsonify({'success': False, 'message': f'下载模板失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 初始化全局计算器
    calculator = FundCalculator()
    logger.info("后端服务启动，计算器已初始化")
    
    # 启动开发服务器
    app.run(host='0.0.0.0', port=5000, debug=True) 