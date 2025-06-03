# 累计现金流分析图表功能

## 📋 功能概述

在图表分析模块中，我们在"剩余本金分析"和"整体分配结构"之间新增了一张**累计现金流分析图表**，用于展示投资项目的累计现金流变化趋势和每年的现金流分派率情况。

## 🎯 功能特点

### 📊 双轴图表设计
- **主轴（左侧）**: 累计现金流柱状图，单位为万元
- **副轴（右侧）**: 现金流分派率折线图，单位为百分比

### 📈 数据展示
- **横轴**: 年份（第0年到第N年）
- **累计现金流**: 
  - 第0年为负的初始投资金额
  - 之后每年 = 上年累计现金流 + 当年净现金流
- **现金流分派率**: 
  - 每年的现金流分派率 = 当年净现金流 / 初始投资金额 × 100%
  - 第0年不展示（用null表示）

### 🎨 智能颜色配置
- **负值**: 红色（rgba(239, 68, 68)）- 表示尚未回本
- **正值**: 绿色（rgba(34, 197, 94)）- 表示已经回本

### 🖱️ 交互功能
- **鼠标悬停标签**: 详细显示数据值和状态图标
  - ❌ 负值累计现金流
  - ✅ 正值累计现金流
  - 📈 正值分派率
  - 📉 负值分派率

## 🔧 技术实现

### 后端实现

#### 1. 新增图表配置函数
```python
def get_cumulative_cash_flow_chart_config(result):
    """
    获取累计现金流分析图配置
    - 横轴：年份
    - 纵轴主轴：累计现金流柱状图
    - 纵轴副轴：现金流分派率折线图
    - 鼠标悬停展示标签数据
    """
```

#### 2. 核心计算逻辑
- **累计现金流计算**: 
  ```python
  cumulative_cash_flow = -initial_investment  # 第0年
  for each year:
      cumulative_cash_flow += current_net_cash_flow
  ```
- **分派率计算**: 
  ```python
  distribution_rate = (current_net_cash_flow / initial_investment) * 100
  ```

#### 3. API集成
在 `get_chart_data()` 函数中添加新图表配置：
```python
chart_configs = {
    'cash_flow_chart': get_cash_flow_chart_config(result),
    'distribution_chart': get_distribution_chart_config(result),
    'capital_structure_chart': get_capital_structure_chart_config(result),
    'cumulative_cash_flow_chart': get_cumulative_cash_flow_chart_config(result),  # 新增
    'pie_chart': get_pie_chart_config(result)
}
```

### 前端实现

#### 1. HTML结构
在图表网格中添加新的图表容器：
```html
<div class="chart-card">
    <div class="chart-card-header">
        <h4 class="chart-title">
            <i class="fas fa-chart-line me-2"></i>
            累计现金流分析
        </h4>
    </div>
    <div class="chart-card-body">
        <canvas id="cumulativeCashFlowChart"></canvas>
    </div>
</div>
```

#### 2. JavaScript渲染
在 `renderCharts()` 函数中添加新图表的渲染：
```javascript
await Promise.all([
    renderChart('cashFlowChart', chartConfigs.cash_flow_chart),
    renderChart('distributionChart', chartConfigs.distribution_chart),
    renderChart('capitalStructureChart', chartConfigs.capital_structure_chart),
    renderChart('cumulativeCashFlowChart', chartConfigs.cumulative_cash_flow_chart), // 新增
    renderChart('pieChart', chartConfigs.pie_chart)
]);
```

## 📊 图表配置详情

### Chart.js配置结构
```javascript
{
    "type": "bar",  // 主类型为柱状图
    "data": {
        "labels": ["第0年", "第1年", "第2年", ...],
        "datasets": [
            {
                "label": "累计现金流",
                "type": "bar",
                "data": [-10000, -8000, -5000, ...],
                "backgroundColor": [...], // 根据正负值动态设置颜色
                "yAxisID": "y"  // 主Y轴
            },
            {
                "label": "现金流分派率",
                "type": "line",
                "data": [null, 20.0, 30.0, ...],
                "yAxisID": "y1"  // 副Y轴
            }
        ]
    },
    "options": {
        "scales": {
            "y": {
                "title": { "text": "累计现金流 (万元)" },
                "position": "left"
            },
            "y1": {
                "title": { "text": "现金流分派率 (%)" },
                "position": "right"
            }
        }
    }
}
```

## 🧪 测试验证

### 1. 单元测试
- ✅ 图表配置生成测试
- ✅ 累计现金流计算逻辑验证
- ✅ 现金流分派率计算验证
- ✅ 颜色配置测试
- ✅ 异常情况处理测试

### 2. API测试
- ✅ 健康检查
- ✅ 基本参数设置
- ✅ 现金流数据设置
- ✅ 计算执行
- ✅ 图表数据获取
- ✅ 图表配置验证

### 3. 测试数据示例
```
投资金额: 10,000万元
投资期限: 5年
现金流: [2000, 3000, 2500, 1500, 4000]万元

预期结果:
- 累计现金流: [-10000, -8000, -5000, -2500, -1000, 3000]
- 分派率: [null, 20%, 30%, 25%, 15%, 40%]
```

## 📍 图表位置

新的累计现金流分析图表位于图表分析页面的第4个位置：

1. 现金流回收分析
2. 现金流分配结构  
3. 剩余本金分析
4. **累计现金流分析** ← 新增
5. 整体分配结构

## 🎯 业务价值

### 投资决策支持
- **回本时点识别**: 通过累计现金流从负转正的时点，清晰识别项目回本时间
- **现金流趋势分析**: 直观展示项目现金流的累计变化趋势
- **分派率监控**: 实时监控每年的现金流分派比例

### 风险管理
- **流动性分析**: 了解项目在不同时期的资金占用情况
- **收益预期管理**: 通过分派率变化趋势调整收益预期

### 投资者沟通
- **可视化报告**: 为投资者提供直观的现金流分析图表
- **透明度提升**: 清晰展示项目的现金流回收进度

## 🚀 使用方法

1. **完成基础计算**: 在系统中完成基本参数设置、现金流输入和收益分配计算
2. **进入图表分析**: 点击"图表分析"标签页
3. **查看累计现金流图表**: 在图表列表中找到"累计现金流分析"图表
4. **交互分析**: 
   - 鼠标悬停查看详细数据
   - 观察累计现金流的变化趋势
   - 分析各年度的分派率情况

## 📝 注意事项

1. **第0年处理**: 第0年累计现金流为负的初始投资金额，分派率不显示
2. **颜色含义**: 红色表示尚未回本，绿色表示已经回本
3. **数据精度**: 所有数值保留2位小数
4. **异常处理**: 当数据无效时，系统会返回基本的图表配置，避免页面崩溃

## 🔄 版本信息

- **功能版本**: v1.0.0
- **添加时间**: 2025-06-03
- **兼容性**: 支持所有现有的计算模式（平层结构、结构化等）
- **依赖**: Chart.js 4.0.1+

---

*该功能已通过完整的单元测试和API测试验证，可以安全部署到生产环境。* 