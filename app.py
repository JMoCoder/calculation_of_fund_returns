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
    """
    计算各列的总计
    
    🔧 精度修复：在计算过程中保持原始精度，避免累积误差
    只在最终显示时进行四舍五入
    """
    totals = {
        'net_cash_flow': 0.0,
        'cash_flow_distribution_rate': 0.0
    }
    
    for row in cash_flow_table:
        # 🔧 关键修复：直接累加原始数值，不使用safe_round
        totals['net_cash_flow'] += float(row.get('net_cash_flow', 0))
        
        # 根据计算模式累计相应字段
        if calculation_mode == '平层结构-优先还本':
            if 'principal_repayment' not in totals:
                totals.update({
                    'principal_repayment': 0.0,
                    'accrued_hurdle_return': 0.0,
                    'distributed_hurdle_return': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                })
            # 🔧 修复：所有字段都直接累加原始数值
            totals['principal_repayment'] += float(row.get('principal_repayment', 0))
            totals['accrued_hurdle_return'] += float(row.get('accrued_hurdle_return', 0))
            totals['distributed_hurdle_return'] += float(row.get('distributed_hurdle_return', 0))
            totals['carry_lp'] += float(row.get('carry_lp', 0))
            totals['carry_gp'] += float(row.get('carry_gp', 0))
        elif calculation_mode == '平层结构-期间分配':
            # 添加平层结构-期间分配模式的总计计算
            if 'periodic_distribution' not in totals:
                totals.update({
                    'periodic_distribution': 0.0,
                    'accrued_hurdle_return': 0.0,
                    'principal_repayment': 0.0,
                    'distributed_hurdle_return': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                })
            totals['periodic_distribution'] += float(row.get('periodic_distribution', 0))
            totals['accrued_hurdle_return'] += float(row.get('accrued_hurdle_return', 0))
            totals['principal_repayment'] += float(row.get('principal_repayment', 0))
            totals['distributed_hurdle_return'] += float(row.get('distributed_hurdle_return', 0))
            totals['carry_lp'] += float(row.get('carry_lp', 0))
            totals['carry_gp'] += float(row.get('carry_gp', 0))
        elif calculation_mode == '结构化-优先劣后':
            if 'senior_principal_repayment' not in totals:
                totals.update({
                    'senior_principal_repayment': 0.0,
                    'senior_hurdle_accrual': 0.0,
                    'senior_periodic_return': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                })
            totals['senior_principal_repayment'] += float(row.get('senior_principal_repayment', 0))
            totals['senior_hurdle_accrual'] += float(row.get('senior_hurdle_accrual', 0))
            totals['senior_periodic_return'] += float(row.get('senior_periodic_return', 0))
            totals['subordinate_principal_repayment'] += float(row.get('subordinate_principal_repayment', 0))
            totals['carry_lp'] += float(row.get('carry_lp', 0))
            totals['carry_gp'] += float(row.get('carry_gp', 0))
        elif calculation_mode == '结构化-包含夹层':
            # 添加结构化-包含夹层模式的总计计算
            if 'senior_hurdle_distribution' not in totals:
                totals.update({
                    'senior_hurdle_distribution': 0.0,
                    'mezzanine_hurdle_distribution': 0.0,
                    'senior_principal_repayment': 0.0,
                    'mezzanine_principal_repayment': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                })
            totals['senior_hurdle_distribution'] += float(row.get('senior_hurdle_distribution', 0))
            totals['mezzanine_hurdle_distribution'] += float(row.get('mezzanine_hurdle_distribution', 0))
            totals['senior_principal_repayment'] += float(row.get('senior_principal_repayment', 0))
            totals['mezzanine_principal_repayment'] += float(row.get('mezzanine_principal_repayment', 0))
            totals['subordinate_principal_repayment'] += float(row.get('subordinate_principal_repayment', 0))
            totals['carry_lp'] += float(row.get('carry_lp', 0))
            totals['carry_gp'] += float(row.get('carry_gp', 0))
        elif calculation_mode == '结构化-息息本本':
            # 添加结构化-息息本本模式的总计计算
            if 'senior_periodic_return' not in totals:
                totals.update({
                    'senior_periodic_return': 0.0,
                    'subordinate_periodic_return': 0.0,
                    'senior_principal_repayment': 0.0,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                })
            totals['senior_periodic_return'] += float(row.get('senior_periodic_return', 0))
            totals['subordinate_periodic_return'] += float(row.get('subordinate_periodic_return', 0))
            totals['senior_principal_repayment'] += float(row.get('senior_principal_repayment', 0))
            totals['subordinate_principal_repayment'] += float(row.get('subordinate_principal_repayment', 0))
            totals['carry_lp'] += float(row.get('carry_lp', 0))
            totals['carry_gp'] += float(row.get('carry_gp', 0))
            
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
        self.last_calculation_result = None  # 添加这一行来存储最后的计算结果
    
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
        1. 优先级期间收益（基于期初本金）
        2. 劣后级期间收益（基于期初本金）
        3. 优先级还本
        4. 劣后级还本
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
            
            # 跟踪变量 - 用于跟踪剩余本金（用于还本计算）
            remaining_senior_principal = senior_amount
            remaining_subordinate_principal = subordinate_amount
            
            # 用于记录期初本金的变量 - 用于计算期间收益
            senior_beginning_balance = senior_amount  # 首年期初本金 = 优先级投资金额
            subordinate_beginning_balance = subordinate_amount  # 首年期初本金 = 劣后投资金额
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'senior_beginning_principal': senior_beginning_balance,  # 使用当年期初本金
                    'subordinate_beginning_principal': subordinate_beginning_balance,  # 使用当年期初本金
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
                
                # 步骤2：劣后级期间收益（基于期初本金）
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
                
                # 步骤4：劣后级还本 - 修复：优先级完全还完后才能劣后级还本
                if remaining_senior_principal == 0 and remaining_subordinate_principal > 0 and remaining_cash > 0:
                    subordinate_principal_payment = min(remaining_cash, remaining_subordinate_principal)
                    year_data['subordinate_principal_repayment'] = subordinate_principal_payment
                    remaining_subordinate_principal -= subordinate_principal_payment
                    remaining_cash -= subordinate_principal_payment
                
                # 步骤5：分配Carry - 只有优先级和劣后级本金都还完后才分配Carry
                if remaining_senior_principal == 0 and remaining_subordinate_principal == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
                
                # 🔧 关键修复：更新下一年的期初本金余额
                # 下年期初本金 = 本年期初本金 - 本年归还本金
                senior_beginning_balance = max(0, senior_beginning_balance - year_data['senior_principal_repayment'])
                subordinate_beginning_balance = max(0, subordinate_beginning_balance - year_data['subordinate_principal_repayment'])
            
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
            # 保存最后的计算结果供图表使用
            calculator.last_calculation_result = result
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

@app.route('/api/chart-data', methods=['GET'])
def get_chart_data():
    """获取图表数据"""
    try:
        # 检查是否有计算结果
        if not hasattr(calculator, 'last_calculation_result') or not calculator.last_calculation_result:
            return jsonify({'success': False, 'message': '请先完成计算'}), 400
        
        result = calculator.last_calculation_result
        
        # 格式化核心指标数据
        core_metrics = result.get('core_metrics', {})
        basic_params = calculator.basic_params
        
        # 8个核心指标
        metrics_data = {
            'irr': {
                'title': '内部收益率',
                'value': core_metrics.get('irr', 0),
                'subtitle': 'IRR',
                'unit': '%'
            },
            'dpi': {
                'title': '分配倍数', 
                'value': core_metrics.get('dpi', 0),
                'subtitle': 'DPI',
                'unit': ''
            },
            'distribution_rate': {
                'title': '分派率',
                'value': get_distribution_rate_range(result.get('cash_flow_table', [])),
                'subtitle': '年度分派率范围',
                'unit': ''
            },
            'static_payback': {
                'title': '静态回本周期',
                'value': core_metrics.get('static_payback_period', '无法回本'),
                'subtitle': '不含时间价值',
                'unit': ''
            },
            'calculation_mode': {
                'title': '计算模式',
                'value': format_mode_display(result.get('calculation_mode', '')),
                'subtitle': get_mode_subtitle(result.get('calculation_mode', '')),
                'unit': ''
            },
            'investment_amount': {
                'title': '投资金额',
                'value': f"{basic_params.get('investment_amount', 0):,.0f}",
                'subtitle': '总投资',
                'unit': '万元'
            },
            'investment_period': {
                'title': '投资期限',
                'value': f"{basic_params.get('investment_period', 0)}",
                'subtitle': '投资周期',
                'unit': '年'
            },
            'hurdle_rate': {
                'title': '门槛收益率',
                'value': f"{basic_params.get('hurdle_rate', 0)}",
                'subtitle': '最低预期收益',
                'unit': '%'
            }
        }
        
        # 获取原始数据的totals用于图表计算
        raw_totals = calculate_totals(result.get('cash_flow_table', []), result.get('calculation_mode', ''))
        
        # 分配情况概览
        try:
            distribution_summary = get_distribution_summary(
                result.get('calculation_mode', ''),
                result.get('cash_flow_table', []),
                raw_totals  # 使用原始数据totals
            )
        except Exception as e:
            logger.error(f"获取分配概览错误: {str(e)}")
            return jsonify({'success': False, 'message': f'获取分配概览失败: {str(e)}'}), 500
        
        # 构建图表配置
        chart_configs = {
            'cash_flow_chart': get_cash_flow_chart_config(result),
            'distribution_chart': get_distribution_chart_config(result),
            'capital_structure_chart': get_capital_structure_chart_config(result),
            'cumulative_cash_flow_chart': get_cumulative_cash_flow_chart_config(result),
            'pie_chart': get_pie_chart_config(result)
        }
        
        return jsonify({
            'success': True,
            'data': {
                'core_metrics': metrics_data,
                'distribution_summary': distribution_summary,
                'chart_configs': chart_configs
            }
        })
        
    except Exception as e:
        logger.error(f"获取图表数据错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取图表数据失败: {str(e)}'}), 500

def get_distribution_rate_range(cash_flow_table):
    """计算分派率范围"""
    try:
        rates = []
        for row in cash_flow_table:
            rate = row.get('cash_flow_distribution_rate', 0)
            if isinstance(rate, (int, float)) and rate > 0:
                rates.append(rate)
        
        if not rates:
            return '0.00%'
        
        min_rate = min(rates)
        max_rate = max(rates)
        
        if min_rate == max_rate:
            return f'{min_rate:.2f}%'
        else:
            return f'{min_rate:.2f}%-{max_rate:.2f}%'
    except:
        return '0.00%'

def format_mode_display(mode):
    """格式化计算模式显示"""
    mode_map = {
        '平层结构-优先还本': '平层结构',
        '平层结构-期间分配': '平层结构',
        '结构化-优先劣后': '结构化',
        '结构化-包含夹层': '结构化',
        '结构化-息息本本': '结构化'
    }
    return mode_map.get(mode, mode)

def get_mode_subtitle(mode):
    """获取计算模式副标题"""
    subtitle_map = {
        '平层结构-优先还本': '优先还本',
        '平层结构-期间分配': '期间分配',
        '结构化-优先劣后': '优先劣后',
        '结构化-包含夹层': '包含夹层',
        '结构化-息息本本': '息息本本'
    }
    return subtitle_map.get(mode, '')

def get_distribution_summary(calculation_mode, cash_flow_table, totals):
    """获取分配情况概览"""
    try:
        # 根据不同计算模式定义分配类型和顺序
        mode_configs = {
            '平层结构-优先还本': {
                'order': ['本金归还', '门槛收益', 'Carry分配'],
                'fields': {
                    '本金归还': 'principal_repayment',
                    '门槛收益': 'distributed_hurdle_return',
                    'Carry分配': ['carry_lp', 'carry_gp']
                }
            },
            '平层结构-期间分配': {
                'order': ['期间分配', '本金归还', '门槛收益', 'Carry分配'],
                'fields': {
                    '期间分配': 'periodic_distribution',
                    '本金归还': 'principal_repayment',
                    '门槛收益': 'distributed_hurdle_return',
                    'Carry分配': ['carry_lp', 'carry_gp']
                }
            },
            '结构化-优先劣后': {
                'order': ['优先级还本', '优先级收益', '劣后级还本', 'Carry分配'],
                'fields': {
                    '优先级还本': 'senior_principal_repayment',
                    '优先级收益': 'senior_periodic_return',
                    '劣后级还本': 'subordinate_principal_repayment',
                    'Carry分配': ['carry_lp', 'carry_gp']
                }
            },
            '结构化-包含夹层': {
                'order': ['优先级收益', '夹层收益', '优先级还本', '夹层还本', '劣后级还本', 'Carry分配'],
                'fields': {
                    '优先级收益': 'senior_hurdle_distribution',
                    '夹层收益': 'mezzanine_hurdle_distribution',
                    '优先级还本': 'senior_principal_repayment',
                    '夹层还本': 'mezzanine_principal_repayment',
                    '劣后级还本': 'subordinate_principal_repayment',
                    'Carry分配': ['carry_lp', 'carry_gp']
                }
            },
            '结构化-息息本本': {
                'order': ['优先级收益', '劣后级收益', '优先级还本', '劣后级还本', 'Carry分配'],
                'fields': {
                    '优先级收益': 'senior_periodic_return',
                    '劣后级收益': 'subordinate_periodic_return',
                    '优先级还本': 'senior_principal_repayment',
                    '劣后级还本': 'subordinate_principal_repayment',
                    'Carry分配': ['carry_lp', 'carry_gp']
                }
            }
        }
        
        config = mode_configs.get(calculation_mode, mode_configs['平层结构-优先还本'])
        
        # 计算各项金额和比例
        total_amount = totals.get('net_cash_flow', 0)
        items = []
        
        for name in config['order']:
            field = config['fields'].get(name)
            if isinstance(field, list):
                # Carry分配需要合并LP和GP
                amount = 0
                for f in field:
                    amount += totals.get(f, 0)
            else:
                amount = totals.get(field, 0)
            
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            
            items.append({
                'name': name,
                'amount': f'{amount:,.0f}万元',
                'percentage': f'{percentage:.1f}%',
                'class': get_distribution_class(name)
            })
        
        return {
            'mode': calculation_mode,
            'order': config['order'],
            'items': items
        }
        
    except Exception as e:
        logger.error(f"获取分配概览错误: {str(e)}")
        return {
            'mode': calculation_mode,
            'order': ['本金归还', '门槛收益', 'Carry分配'],
            'items': []
        }

def get_distribution_class(name):
    """获取分配类型的CSS类名"""
    if '本金' in name or '还本' in name:
        return 'principal'
    elif '收益' in name or '门槛' in name or '期间' in name:
        return 'hurdle'  
    elif 'Carry' in name:
        return 'carry'
    else:
        return 'other'

def get_cash_flow_chart_config(result):
    """
    生成现金流回收分析图表配置 - 显示分配结构
    """
    try:
        cash_flow_table = result.get('cash_flow_table', [])
        calculation_mode = result.get('calculation_mode', '')
        
        # 使用与第二张图相同的颜色配置
        field_configs = {
            '平层结构-优先还本': [
                {'field': 'principal_repayment', 'label': '本金归还', 'color': '#3b82f6'},
                {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#10b981'},
                {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#8b5cf6'},
                {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#f59e0b'}
            ],
            '平层结构-期间分配': [
                {'field': 'periodic_distribution', 'label': '期间分配', 'color': '#3b82f6'},
                {'field': 'principal_repayment', 'label': '本金归还', 'color': '#10b981'},
                {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#8b5cf6'},
                {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
                {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
            ],
            '结构化-优先劣后': [
                {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#3b82f6'},
                {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#10b981'},
                {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#8b5cf6'},
                {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
                {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
            ],
            '结构化-包含夹层': [
                {'field': 'senior_hurdle_distribution', 'label': '优先级收益', 'color': '#3b82f6'},
                {'field': 'mezzanine_hurdle_distribution', 'label': '夹层收益', 'color': '#10b981'},
                {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
                {'field': 'mezzanine_principal_repayment', 'label': '夹层还本', 'color': '#f59e0b'},
                {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#ef4444'},
                {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#a855f7'},
                {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ec4899'}
            ],
            '结构化-息息本本': [
                {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#3b82f6'},
                {'field': 'subordinate_periodic_return', 'label': '劣后级收益', 'color': '#10b981'},
                {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
                {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#f59e0b'},
                {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#ef4444'},
                {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#a855f7'}
            ]
        }
        
        fields = field_configs.get(calculation_mode, field_configs['平层结构-优先还本'])
        
        # 准备年份标签
        years = [f"第{row.get('year', i+1)}年" for i, row in enumerate(cash_flow_table)]
        
        # 准备分配数据集
        datasets = []
        
        for field_config in fields:
            field = field_config['field']
            label = field_config['label']
            color = field_config['color']
            
            data = []
            for row in cash_flow_table:
                # 解析字段值 - 移除格式化字符并转换为浮点数
                value_str = str(row.get(field, '0'))
                value_str = value_str.replace(',', '').replace('万元', '').strip()
                try:
                    value = float(value_str)
                    if math.isnan(value) or math.isinf(value):
                        value = 0
                except (ValueError, TypeError):
                    value = 0
                data.append(value)
            
            datasets.append({
                'label': label,
                'data': data,
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1
            })

        # 图表配置
        config = {
            "type": "bar",
            "data": {
                "labels": years,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "现金流回收分析"
                    },
                    "legend": {
                        "position": "top"
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": """function(context) {
                                let label = context.dataset.label || '';
                                let value = context.parsed.y;
                                return label + ': ' + new Intl.NumberFormat('zh-CN').format(value) + ' 万元';
                            }"""
                        }
                    }
                },
                "scales": {
                    "x": {
                        "stacked": True
                    },
                    "y": {
                        "stacked": True,
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "现金流量(万元)"
                        }
                    }
                }
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"生成现金流图表配置时出错: {e}")
        return {
            "type": "bar",
            "data": {"labels": [], "datasets": []},
            "options": {"responsive": True}
        }

def get_pie_chart_config(result):
    """获取分配结构饼图配置"""
    # 使用原始数据计算totals
    raw_totals = calculate_totals(result.get('cash_flow_table', []), result.get('calculation_mode', ''))
    calculation_mode = result.get('calculation_mode', '')
    
    # 计算净现金流总额
    cash_flow_table = result.get('cash_flow_table', [])
    total_net_cash_flow = 0
    try:
        for row in cash_flow_table:
            net_flow_str = str(row.get('net_cash_flow', '0'))
            # 移除格式化字符
            net_flow_str = net_flow_str.replace(',', '').replace('万元', '').strip()
            try:
                net_flow = float(net_flow_str)
                total_net_cash_flow += net_flow
            except (ValueError, TypeError):
                continue
    except Exception as e:
        logger.warning(f"计算净现金流总额时出错: {e}")
        total_net_cash_flow = 0
    
    # 根据计算模式获取分配数据
    distribution_summary = get_distribution_summary(calculation_mode, [], raw_totals)
    
    labels = []
    data = []
    colors = []
    
    # 使用与前两张图一致的颜色映射
    field_configs = {
        '平层结构-优先还本': [
            {'field': 'principal_repayment', 'label': '本金归还', 'color': '#3b82f6'},
            {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#10b981'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#8b5cf6'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#f59e0b'}
        ],
        '平层结构-期间分配': [
            {'field': 'periodic_distribution', 'label': '期间分配', 'color': '#3b82f6'},
            {'field': 'principal_repayment', 'label': '本金归还', 'color': '#10b981'},
            {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#8b5cf6'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
        ],
        '结构化-优先劣后': [
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#3b82f6'},
            {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#10b981'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#8b5cf6'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
        ],
        '结构化-包含夹层': [
            {'field': 'senior_hurdle_distribution', 'label': '优先级收益', 'color': '#3b82f6'},
            {'field': 'mezzanine_hurdle_distribution', 'label': '夹层收益', 'color': '#10b981'},
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
            {'field': 'mezzanine_principal_repayment', 'label': '夹层还本', 'color': '#f59e0b'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#ef4444'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#a855f7'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ec4899'}
        ],
        '结构化-息息本本': [
            {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#3b82f6'},
            {'field': 'subordinate_periodic_return', 'label': '劣后级收益', 'color': '#10b981'},
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#f59e0b'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#ef4444'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#a855f7'}
        ]
    }
    
    # 创建颜色映射
    color_map = {}
    fields = field_configs.get(calculation_mode, field_configs['平层结构-优先还本'])
    for field_config in fields:
        color_map[field_config['label']] = field_config['color']
    
    for item in distribution_summary['items']:
        # 安全处理amount字段
        amount_str = str(item['amount'])
        try:
            amount = float(amount_str.replace('万元', '').replace(',', ''))
            if amount > 0:
                labels.append(item['name'])
                data.append(amount)
                # 使用一致的颜色映射
                color = color_map.get(item['name'], '#6b7280')
                colors.append(color)
        except:
            continue
    
    # 构建图表配置
    config = {
        'type': 'pie',
        'data': {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors,
                'borderColor': '#ffffff',
                'borderWidth': 2
            }]
        },
        'options': {
            'responsive': True,
            'plugins': {
                'title': {
                    'display': True,
                    'text': '整体分配结构'
                },
                'subtitle': {
                    'display': True,
                    'text': f'投资期间回收净现金流总额：{total_net_cash_flow:,.0f} 万元',
                    'color': '#6b7280',
                    'font': {
                        'size': 12,
                        'style': 'italic'
                    },
                    'padding': {
                        'top': 10,
                        'bottom': 15
                    }
                },
                'legend': {
                    'position': 'bottom',
                    'labels': {
                        'padding': 20,
                        'usePointStyle': True
                    }
                },
                'tooltip': {
                    'callbacks': {
                        'label': """function(context) {
                            let label = context.label || '';
                            let value = context.parsed;
                            let total = context.dataset.data.reduce((a, b) => a + b, 0);
                            let percentage = ((value / total) * 100).toFixed(1);
                            return label + ': ' + new Intl.NumberFormat('zh-CN').format(value) + ' 万元 (' + percentage + '%)';
                        }"""
                    }
                }
            }
        }
    }
    
    return config

def get_trend_chart_config(result):
    """删除收益趋势分析图表函数"""
    pass

def get_distribution_chart_config(result):
    """获取现金流分配图配置"""
    cash_flow_table = result.get('cash_flow_table', [])
    calculation_mode = result.get('calculation_mode', '')
    
    labels = []
    datasets = []
    
    # 根据计算模式确定数据字段 - 与第一张图保持一致的配色
    field_configs = {
        '平层结构-优先还本': [
            {'field': 'principal_repayment', 'label': '本金归还', 'color': '#3b82f6'},
            {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#10b981'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#8b5cf6'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#f59e0b'}
        ],
        '平层结构-期间分配': [
            {'field': 'periodic_distribution', 'label': '期间分配', 'color': '#3b82f6'},
            {'field': 'principal_repayment', 'label': '本金归还', 'color': '#10b981'},
            {'field': 'distributed_hurdle_return', 'label': '门槛收益', 'color': '#8b5cf6'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
        ],
        '结构化-优先劣后': [
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#3b82f6'},
            {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#10b981'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#8b5cf6'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#f59e0b'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ef4444'}
        ],
        '结构化-包含夹层': [
            {'field': 'senior_hurdle_distribution', 'label': '优先级收益', 'color': '#3b82f6'},
            {'field': 'mezzanine_hurdle_distribution', 'label': '夹层收益', 'color': '#10b981'},
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
            {'field': 'mezzanine_principal_repayment', 'label': '夹层还本', 'color': '#f59e0b'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#ef4444'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#a855f7'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#ec4899'}
        ],
        '结构化-息息本本': [
            {'field': 'senior_periodic_return', 'label': '优先级收益', 'color': '#3b82f6'},
            {'field': 'subordinate_periodic_return', 'label': '劣后级收益', 'color': '#10b981'},
            {'field': 'senior_principal_repayment', 'label': '优先级还本', 'color': '#8b5cf6'},
            {'field': 'subordinate_principal_repayment', 'label': '劣后级还本', 'color': '#f59e0b'},
            {'field': 'carry_lp', 'label': 'Carry LP', 'color': '#ef4444'},
            {'field': 'carry_gp', 'label': 'Carry GP', 'color': '#a855f7'}
        ]
    }
    
    fields = field_configs.get(calculation_mode, field_configs['平层结构-优先还本'])
    
    # 准备数据
    for row in cash_flow_table:
        year = row.get('year', 0)
        labels.append(f'第{year}年')
    
    for field_config in fields:
        field = field_config['field']
        label = field_config['label']
        color = field_config['color']
        
        data = []
        for row in cash_flow_table:
            # 解析字段值
            value_str = str(row.get(field, '0'))
            value_str = value_str.replace(',', '').replace('万元', '').strip()
            try:
                value = float(value_str)
                if math.isnan(value) or math.isinf(value):
                    value = 0
            except (ValueError, TypeError):
                value = 0
            
            # 解析净现金流
            net_flow_str = str(row.get('net_cash_flow', '0'))
            net_flow_str = net_flow_str.replace(',', '').replace('万元', '').strip()
            try:
                net_flow = float(net_flow_str)
                if math.isnan(net_flow) or math.isinf(net_flow):
                    net_flow = 0
            except (ValueError, TypeError):
                net_flow = 0
            
            percentage = (value / net_flow * 100) if net_flow > 0 else 0
            data.append(percentage)
        
        datasets.append({
            'label': label,
            'data': data,
            'backgroundColor': color,
            'borderColor': color,
            'borderWidth': 1
        })
    
    return {
        'type': 'bar',
        'data': {
            'labels': labels,
            'datasets': datasets
        },
        'options': {
            'responsive': True,
            'plugins': {
                'title': {
                    'display': True,
                    'text': '现金流分配结构'
                },
                'legend': {
                    'position': 'top'
                },
                'tooltip': {
                    'callbacks': {
                        'label': """function(context) {
                            let label = context.dataset.label || '';
                            let value = context.parsed.y;
                            return label + ': ' + value.toFixed(1) + '%';
                        }"""
                    }
                }
            },
            'scales': {
                'x': {
                    'stacked': True
                },
                'y': {
                    'stacked': True,
                    'beginAtZero': True,
                    'max': 100,
                    'title': {
                        'display': True,
                        'text': '分配比例(%)'
                    }
                }
            }
        }
    }

def get_capital_structure_chart_config(result):
    """
    获取剩余本金分析图配置
    
    🔧 重要修复：剩余本金分析现在与静态回本周期使用相同的计算逻辑
    - 基于累计净现金流计算剩余本金，而非仅基于本金归还
    - 这确保了剩余本金归零的时间与静态回本周期一致
    
    图表配置：
    - 横轴：年份（第0年-第N年）
    - 纵轴主轴：剩余本金比例柱状图（基于净现金流累计回收计算）
    - 纵轴副轴：年累计分派率折线图（年累计已回收净现金流/初始投资金额）
    
    计算逻辑：
    - 剩余本金 = 初始投资金额 - 累计净现金流回收
    - 剩余本金比例 = 剩余本金 / 初始投资金额 × 100%
    - 年累计分派率 = 累计净现金流 / 初始投资金额 × 100%
    """
    try:
        cash_flow_table = result.get('cash_flow_table', [])
        calculation_mode = result.get('calculation_mode', '')
        basic_params = calculator.basic_params if hasattr(calculator, 'basic_params') else {}
        initial_investment = basic_params.get('investment_amount', 0)
        
        if not cash_flow_table or initial_investment <= 0:
            return {
                "type": "bar",
                "data": {"labels": [], "datasets": []},
                "options": {"responsive": True}
            }
        
        # 准备年份标签（包含第0年）
        years = [f"第{i}年" for i in range(len(cash_flow_table) + 1)]
        
        # 剩余本金比例数据
        remaining_principal_ratio_data = []
        # 年累计分派率数据
        cumulative_distribution_rate_data = []
        
        # 第0年初始状态
        remaining_principal_ratio_data.append(100.0)  # 初始时剩余本金比例为100%
        cumulative_distribution_rate_data.append(0.0)  # 初始时累计分派率为0%
        
        # 累计变量
        cumulative_distributed_cash = 0  # 累计已回收净现金流
        # 🔧 关键修复：使用净现金流而非本金归还来计算剩余本金
        # 这与静态回本周期的计算逻辑保持一致
        
        for i, row in enumerate(cash_flow_table):
            # 解析数值的通用函数
            def parse_value(field_name):
                """解析字段值为数值"""
                value_str = str(row.get(field_name, '0'))
                value_str = value_str.replace(',', '').replace('万元', '').strip()
                try:
                    value = float(value_str)
                    return value if not (math.isnan(value) or math.isinf(value)) else 0
                except (ValueError, TypeError):
                    return 0
            
            # 🔧 修复：直接使用净现金流计算累计回收金额，与静态回本周期逻辑一致
            period_net_cash_flow = parse_value('net_cash_flow')
            cumulative_distributed_cash += period_net_cash_flow
            
            # 计算年末剩余本金比例 = (初始投资金额 - 累计已回收净现金流) / 初始投资金额
            remaining_principal = initial_investment - cumulative_distributed_cash
            remaining_principal_ratio = (remaining_principal / initial_investment) * 100 if initial_investment > 0 else 0
            
            # 确保剩余本金比例不为负
            if remaining_principal_ratio < 0:
                remaining_principal_ratio = 0
            
            # 计算年累计分派率
            cumulative_distribution_rate = (cumulative_distributed_cash / initial_investment) * 100 if initial_investment > 0 else 0
            
            # 添加到数据数组
            remaining_principal_ratio_data.append(round(remaining_principal_ratio, 2))
            cumulative_distribution_rate_data.append(round(cumulative_distribution_rate, 2))
        
        # 构建数据集
        datasets = [
            {
                'label': '剩余本金比例',
                'type': 'bar',
                'data': remaining_principal_ratio_data,
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',  # 蓝色柱状图
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'yAxisID': 'y'  # 使用主Y轴
            },
            {
                'label': '年累计分派率',
                'type': 'line',
                'data': cumulative_distribution_rate_data,
                'borderColor': 'rgba(34, 197, 94, 1)',  # 绿色折线图
                'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                'borderWidth': 2,
                'fill': False,
                'tension': 0.1,
                'yAxisID': 'y1'  # 使用副Y轴
            }
        ]
        
        # 图表配置
        config = {
            "type": "bar",  # 主类型为柱状图
            "data": {
                "labels": years,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "interaction": {
                    "mode": "index",
                    "intersect": False
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "剩余本金分析"
                    },
                    "legend": {
                        "position": "top"
                    },
                    "tooltip": {
                        "mode": "index",
                        "intersect": False,
                        "callbacks": {
                            "label": "function(context) { if(context.datasetIndex === 0) { return '剩余本金比例: ' + context.parsed.y.toFixed(2) + '%'; } else { return '年累计分派率: ' + context.parsed.y.toFixed(2) + '%'; } }"
                        }
                    }
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": False
                        }
                    },
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "剩余本金比例 (%)"
                        },
                        "ticks": {
                            "callback": "function(value) { return value + '%'; }"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "年累计分派率 (%)"
                        },
                        "grid": {
                            "drawOnChartArea": False  # 避免网格线重叠
                        },
                        "ticks": {
                            "callback": "function(value) { return value + '%'; }"
                        }
                    }
                }
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"生成剩余本金分析图表配置时出错: {e}")
        return {
            "type": "bar",
            "data": {"labels": [], "datasets": []},
            "options": {"responsive": True}
        }

def get_cumulative_cash_flow_chart_config(result):
    """
    获取累计现金流分析图配置
    - 横轴：年份
    - 纵轴主轴：累计现金流柱状图（第0年为负的初始投资金额，之后每年累计现金流=上年累计现金流+当年净现金流）
    - 纵轴副轴：现金流分派率折线图（每年的现金流分派率=当年净现金流/初始投资金额，第0年不展示）
    - 鼠标悬停展示标签数据
    """
    try:
        cash_flow_table = result.get('cash_flow_table', [])
        calculation_mode = result.get('calculation_mode', '')
        basic_params = calculator.basic_params if hasattr(calculator, 'basic_params') else {}
        initial_investment = basic_params.get('investment_amount', 0)
        
        if not cash_flow_table or initial_investment <= 0:
            return {
                "type": "bar",
                "data": {"labels": [], "datasets": []},
                "options": {"responsive": True}
            }
        
        # 准备年份标签（包含第0年）
        years = [f"第{i}年" for i in range(len(cash_flow_table) + 1)]
        
        # 累计现金流数据
        cumulative_cash_flow_data = []
        # 现金流分派率数据
        cash_flow_distribution_rate_data = []
        
        # 第0年初始状态 - 负的初始投资金额
        cumulative_cash_flow_data.append(-initial_investment)
        # 第0年不展示分派率（用null表示）
        cash_flow_distribution_rate_data.append(None)
        
        # 累计现金流变量
        cumulative_cash_flow = -initial_investment  # 第0年为负的初始投资
        
        for i, row in enumerate(cash_flow_table):
            # 解析净现金流的通用函数
            def parse_net_cash_flow():
                """解析当年净现金流"""
                net_flow_str = str(row.get('net_cash_flow', '0'))
                net_flow_str = net_flow_str.replace(',', '').replace('万元', '').strip()
                try:
                    net_flow = float(net_flow_str)
                    return net_flow if not (math.isnan(net_flow) or math.isinf(net_flow)) else 0
                except (ValueError, TypeError):
                    return 0
            
            # 获取当年净现金流
            current_net_cash_flow = parse_net_cash_flow()
            
            # 计算累计现金流 = 上年累计现金流 + 当年净现金流
            cumulative_cash_flow += current_net_cash_flow
            
            # 计算现金流分派率 = 当年净现金流 / 初始投资金额
            distribution_rate = (current_net_cash_flow / initial_investment) * 100 if initial_investment > 0 else 0
            
            # 添加到数据数组
            cumulative_cash_flow_data.append(round(cumulative_cash_flow, 2))
            cash_flow_distribution_rate_data.append(round(distribution_rate, 2))
        
        # 构建数据集
        datasets = [
            {
                'label': '累计现金流',
                'type': 'bar',
                'data': cumulative_cash_flow_data,
                'backgroundColor': [
                    # 根据数值正负设置不同颜色
                    'rgba(239, 68, 68, 0.6)' if val < 0 else 'rgba(34, 197, 94, 0.6)' 
                    for val in cumulative_cash_flow_data
                ],
                'borderColor': [
                    'rgba(239, 68, 68, 1)' if val < 0 else 'rgba(34, 197, 94, 1)' 
                    for val in cumulative_cash_flow_data
                ],
                'borderWidth': 1,
                'yAxisID': 'y'  # 使用主Y轴
            },
            {
                'label': '现金流分派率',
                'type': 'line',
                'data': cash_flow_distribution_rate_data,
                'borderColor': 'rgba(59, 130, 246, 1)',  # 蓝色折线图
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'borderWidth': 2,
                'fill': False,
                'tension': 0.1,
                'pointBackgroundColor': [
                    'transparent' if val is None else 'rgba(59, 130, 246, 1)' 
                    for val in cash_flow_distribution_rate_data
                ],
                'pointBorderColor': [
                    'transparent' if val is None else 'rgba(59, 130, 246, 1)' 
                    for val in cash_flow_distribution_rate_data
                ],
                'yAxisID': 'y1'  # 使用副Y轴
            }
        ]
        
        # 图表配置
        config = {
            "type": "bar",  # 主类型为柱状图
            "data": {
                "labels": years,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "interaction": {
                    "mode": "index",
                    "intersect": False
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "累计现金流分析"
                    },
                    "legend": {
                        "position": "top"
                    },
                    "tooltip": {
                        "mode": "index",
                        "intersect": False,
                        "filter": "function(tooltipItem) { return tooltipItem.datasetIndex === 0 || (tooltipItem.datasetIndex === 1 && tooltipItem.parsed.y !== null); }",
                        "callbacks": {
                            "label": "function(context) { if(context.datasetIndex === 0) { let value = context.parsed.y; let color = value >= 0 ? '✅' : '❌'; return color + ' 累计现金流: ' + new Intl.NumberFormat('zh-CN').format(value) + ' 万元'; } else if(context.parsed.y !== null) { let value = context.parsed.y; let color = value >= 0 ? '📈' : '📉'; return color + ' 现金流分派率: ' + value.toFixed(2) + '%'; } }"
                        }
                    }
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": False
                        }
                    },
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "累计现金流 (万元)"
                        },
                        "grid": {
                            "drawOnChartArea": True
                        },
                        "ticks": {
                            "callback": "function(value) { return new Intl.NumberFormat('zh-CN').format(value); }"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "现金流分派率 (%)"
                        },
                        "grid": {
                            "drawOnChartArea": False  # 避免网格线重叠
                        },
                        "ticks": {
                            "callback": "function(value) { return value + '%'; }"
                        }
                    }
                }
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"生成累计现金流分析图表配置时出错: {e}")
        return {
            "type": "bar",
            "data": {"labels": [], "datasets": []},
            "options": {"responsive": True}
        }

if __name__ == '__main__':
    # 初始化全局计算器
    calculator = FundCalculator()
    # 添加最后计算结果属性
    calculator.last_calculation_result = None
    logger.info("后端服务启动，计算器已初始化")
    
    # 启动开发服务器
    app.run(host='0.0.0.0', port=5000, debug=True) 