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

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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
            # 构建完整现金流序列：初始投资为负值，后续为正值
            full_cash_flows = [-initial_investment] + cash_flows
            
            # 使用牛顿法求解IRR
            def npv(rate, flows):
                """计算净现值"""
                return sum(cf / (1 + rate) ** i for i, cf in enumerate(flows))
            
            def npv_derivative(rate, flows):
                """计算NPV对利率的导数"""
                return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(flows))
            
            # 初始猜测值
            rate = 0.1
            tolerance = 1e-6
            max_iterations = 100
            
            for _ in range(max_iterations):
                npv_value = npv(rate, full_cash_flows)
                if abs(npv_value) < tolerance:
                    break
                
                derivative = npv_derivative(rate, full_cash_flows)
                if abs(derivative) < tolerance:
                    break
                
                rate = rate - npv_value / derivative
            
            return rate * 100  # 转换为百分比
            
        except Exception as e:
            logger.error(f"计算IRR时发生错误: {str(e)}")
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
            total_distributions = sum(cash_flows)
            return total_distributions / initial_investment if initial_investment > 0 else 0.0
        except Exception as e:
            logger.error(f"计算DPI时发生错误: {str(e)}")
            return 0.0
    
    def calculate_flat_structure_priority_repayment(self) -> Dict[str, Any]:
        """
        计算平层结构 - 优先还本模式
        
        分配顺序：
        1. 净现金流优先还本，并按期初本金余额计提门槛收益
        2. 本金还完当期，开始分配已计提的门槛收益
        3. 门槛收益还完当期，剩余净现金流开始分配Carry
        
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
                if remaining_principal == 0 and accumulated_hurdle > 0 and remaining_cash > 0:
                    hurdle_payment = min(remaining_cash, accumulated_hurdle)
                    year_data['distributed_hurdle_return'] = hurdle_payment
                    accumulated_hurdle -= hurdle_payment
                    remaining_cash -= hurdle_payment
                
                # 步骤4：分配Carry
                if remaining_principal == 0 and accumulated_hurdle == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '平层结构-优先还本',
                'core_metrics': {
                    'irr': round(irr, 2),
                    'dpi': round(dpi, 2)
                },
                'cash_flow_table': results,
                'summary': {
                    'total_principal_repaid': sum(row['principal_repayment'] for row in results),
                    'total_hurdle_distributed': sum(row['distributed_hurdle_return'] for row in results),
                    'total_carry_lp': sum(row['carry_lp'] for row in results),
                    'total_carry_gp': sum(row['carry_gp'] for row in results)
                }
            }
            
        except Exception as e:
            logger.error(f"计算平层结构-优先还本时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}
    
    def calculate_flat_structure_periodic_distribution(self, periodic_rate: float) -> Dict[str, Any]:
        """
        计算平层结构 - 期间分配模式
        
        Args:
            periodic_rate: 期间收益率（%）
        
        分配顺序：
        1. 净现金流优先按照期初本金余额分配期间收益
        2. 分配期间收益后，剩余现金流归还本金，并按期初本金余额计提门槛收益
        3. 本金还完当期，开始分配已计提的剩余门槛收益
        4. 门槛收益还完当期，剩余净现金流开始分配Carry
        
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
                
                # 步骤2：计提门槛收益（扣除期间收益率）
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
                
                # 步骤4：分配门槛收益
                if remaining_principal == 0 and accumulated_hurdle > 0 and remaining_cash > 0:
                    hurdle_payment = min(remaining_cash, accumulated_hurdle)
                    year_data['distributed_hurdle_return'] = hurdle_payment
                    accumulated_hurdle -= hurdle_payment
                    remaining_cash -= hurdle_payment
                
                # 步骤5：分配Carry
                if remaining_principal == 0 and accumulated_hurdle == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '平层结构-期间分配',
                'core_metrics': {
                    'irr': round(irr, 2),
                    'dpi': round(dpi, 2)
                },
                'cash_flow_table': results,
                'summary': {
                    'total_periodic_distribution': sum(row['periodic_distribution'] for row in results),
                    'total_principal_repaid': sum(row['principal_repayment'] for row in results),
                    'total_hurdle_distributed': sum(row['distributed_hurdle_return'] for row in results),
                    'total_carry_lp': sum(row['carry_lp'] for row in results),
                    'total_carry_gp': sum(row['carry_gp'] for row in results)
                }
            }
            
        except Exception as e:
            logger.error(f"计算平层结构-期间分配时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}
    
    def calculate_structured_senior_subordinate(self, senior_ratio: float) -> Dict[str, Any]:
        """
        计算结构化 - 优先劣后模式
        
        Args:
            senior_ratio: 优先级比例（%）
        
        分配顺序：
        1. 当期净现金流优先按期初优先级剩余本金*优先级收益率分配给优先级
        2. 剩余净现金流偿还优先级本金
        3. 优先级退出后，剩余净现金流开始偿还劣后本金
        4. 劣后本金退出后，剩余净现金流开始分配Carry
        
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
            
            for year in range(years):
                year_data = {
                    'year': year + 1,
                    'net_cash_flow': self.cash_flows[year],
                    'cash_flow_distribution_rate': self.cash_flows[year] / investment_amount * 100,
                    'senior_beginning_principal': remaining_senior_principal,
                    'senior_periodic_return': 0.0,
                    'senior_principal_repayment': 0.0,
                    'subordinate_principal_balance': remaining_subordinate_principal,
                    'subordinate_principal_repayment': 0.0,
                    'carry_lp': 0.0,
                    'carry_gp': 0.0
                }
                
                remaining_cash = self.cash_flows[year]
                
                # 步骤1：分配优先级收益
                if remaining_senior_principal > 0 and remaining_cash > 0:
                    senior_return = min(remaining_cash, remaining_senior_principal * senior_rate)
                    year_data['senior_periodic_return'] = senior_return
                    remaining_cash -= senior_return
                
                # 步骤2：偿还优先级本金
                if remaining_senior_principal > 0 and remaining_cash > 0:
                    senior_principal_payment = min(remaining_cash, remaining_senior_principal)
                    year_data['senior_principal_repayment'] = senior_principal_payment
                    remaining_senior_principal -= senior_principal_payment
                    remaining_cash -= senior_principal_payment
                
                # 步骤3：偿还劣后本金
                if remaining_senior_principal == 0 and remaining_subordinate_principal > 0 and remaining_cash > 0:
                    subordinate_principal_payment = min(remaining_cash, remaining_subordinate_principal)
                    year_data['subordinate_principal_repayment'] = subordinate_principal_payment
                    remaining_subordinate_principal -= subordinate_principal_payment
                    remaining_cash -= subordinate_principal_payment
                
                # 步骤4：分配Carry
                if remaining_senior_principal == 0 and remaining_subordinate_principal == 0 and remaining_cash > 0:
                    year_data['carry_lp'] = remaining_cash * (1 - carry_rate)
                    year_data['carry_gp'] = remaining_cash * carry_rate
                
                results.append(year_data)
            
            # 计算核心指标
            irr = self.calculate_irr(self.cash_flows, investment_amount)
            dpi = self.calculate_dpi(self.cash_flows, investment_amount)
            
            return {
                'success': True,
                'calculation_mode': '结构化-优先劣后',
                'structure_info': {
                    'senior_amount': round(senior_amount, 2),
                    'subordinate_amount': round(subordinate_amount, 2),
                    'senior_ratio': senior_ratio,
                    'subordinate_ratio': 100 - senior_ratio
                },
                'core_metrics': {
                    'irr': round(irr, 2),
                    'dpi': round(dpi, 2)
                },
                'cash_flow_table': results,
                'summary': {
                    'total_senior_return': sum(row['senior_periodic_return'] for row in results),
                    'total_senior_principal': sum(row['senior_principal_repayment'] for row in results),
                    'total_subordinate_principal': sum(row['subordinate_principal_repayment'] for row in results),
                    'total_carry_lp': sum(row['carry_lp'] for row in results),
                    'total_carry_gp': sum(row['carry_gp'] for row in results)
                }
            }
            
        except Exception as e:
            logger.error(f"计算结构化-优先劣后时发生错误: {str(e)}")
            return {'success': False, 'message': f'计算失败: {str(e)}'}

# 全局计算器实例
calculator = FundCalculator()

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
        cash_flows = data.get('cash_flows', [])
        result = calculator.set_cash_flows(cash_flows)
        return jsonify(result)
    except Exception as e:
        logger.error(f"设置现金流API错误: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """执行计算"""
    try:
        data = request.get_json()
        calculation_mode = data.get('mode')
        
        if calculation_mode == 'flat_priority_repayment':
            result = calculator.calculate_flat_structure_priority_repayment()
        elif calculation_mode == 'flat_periodic_distribution':
            periodic_rate = data.get('periodic_rate', 0)
            result = calculator.calculate_flat_structure_periodic_distribution(periodic_rate)
        elif calculation_mode == 'structured_senior_subordinate':
            senior_ratio = data.get('senior_ratio', 0)
            result = calculator.calculate_structured_senior_subordinate(senior_ratio)
        else:
            result = {'success': False, 'message': '不支持的计算模式'}
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"计算API错误: {str(e)}")
        return jsonify({'success': False, 'message': f'计算失败: {str(e)}'}), 500

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
        df = pd.read_excel(file)
        
        # 解析数据（根据模板格式）
        # 这里需要根据具体的Excel模板格式来实现解析逻辑
        
        return jsonify({
            'success': True,
            'message': '文件导入成功',
            'data': {
                'rows': len(df),
                'columns': list(df.columns)
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
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5000) 