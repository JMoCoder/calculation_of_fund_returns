#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金收益计算器测试套件

该包包含以下测试模块：
- test_api.py: API接口测试
- test_calculations.py: 计算逻辑测试
- test_charts.py: 图表功能综合测试

使用方法：
python -m tests.test_api          # 运行API测试
python -m tests.test_calculations # 运行计算逻辑测试  
python -m tests.test_charts       # 运行图表功能测试
"""

__version__ = "1.0.0"
__author__ = "Fund Calculator Team"

# 导出主要测试模块
__all__ = ['test_api', 'test_calculations', 'test_charts'] 