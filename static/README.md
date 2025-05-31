# 静态文件目录说明

本目录包含基金收益分配计算系统的前端静态资源文件。

## 目录结构

```
static/
├── README.md          # 本说明文件
├── style.css          # 主样式表
├── app.js             # 核心前端逻辑
├── charts.js          # 图表处理模块
└── utils.js           # 工具函数库
```

## 文件说明

### style.css
**主样式表文件**
- 包含全站的CSS样式定义
- 使用CSS变量管理主题色彩
- 提供响应式设计支持
- 包含组件样式：表单、表格、卡片、按钮等
- 支持打印样式优化

**主要功能：**
- 🎨 统一的设计语言
- 📱 移动端适配
- 🖨️ 打印友好
- 🎯 Bootstrap扩展样式

### app.js
**前端核心逻辑文件**
- 处理用户交互和事件绑定
- 管理表单提交和数据验证
- 执行API调用和错误处理
- 控制步骤导航和界面更新

**主要功能：**
- 📝 表单处理与验证
- 🔄 Ajax API交互
- 🧭 多步骤流程管理
- 📊 数据展示和格式化
- 📤 Excel导入导出

### charts.js
**数据可视化模块**
- 基于Chart.js库的图表处理
- 提供多种图表类型支持
- 支持图表交互和动画效果
- 可导出图表为图片

**支持的图表类型：**
- 📈 现金流趋势线图
- 🥧 收益分配饼图
- 📊 业绩指标柱状图
- 📉 时间序列分配图

### utils.js
**工具函数库**
- 提供通用的工具类和函数
- 包含数据格式化、验证、计算等功能
- 支持本地存储和文件处理
- 提供财务计算工具

**主要工具类：**
- 💰 `NumberFormatter` - 数字格式化
- 📅 `DateUtils` - 日期处理
- ✅ `Validator` - 数据验证
- 💾 `StorageUtils` - 本地存储
- 📑 `ExcelUtils` - Excel处理
- 🔗 `UrlUtils` - URL操作
- 🛠️ `Utils` - 通用工具
- 📈 `FinanceUtils` - 财务计算

## 使用方式

### 在HTML中引入
```html
<!-- 样式文件 -->
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">

<!-- JavaScript文件 -->
<script src="{{ url_for('static', filename='utils.js') }}"></script>
<script src="{{ url_for('static', filename='charts.js') }}"></script>
<script src="{{ url_for('static', filename='app.js') }}"></script>
```

### JavaScript API使用示例

#### 数字格式化
```javascript
// 格式化货币
const formatted = NumberFormatter.formatCurrency(1234567.89);
// 输出: ¥1,234,567.89

// 格式化百分比
const percent = NumberFormatter.formatPercentage(15.5);
// 输出: 15.50%
```

#### 日期处理
```javascript
// 格式化日期
const dateStr = DateUtils.formatDate('2024-01-15', 'YYYY/MM/DD');
// 输出: 2024/01/15

// 计算日期差
const days = DateUtils.daysBetween('2024-01-01', '2024-01-15');
// 输出: 14
```

#### 数据验证
```javascript
// 验证数字
const isValid = Validator.isValidNumber('123.45', 0, 1000);
// 输出: true

// 验证日期
const isValidDate = Validator.isValidDate('2024-01-15');
// 输出: true
```

#### 图表创建
```javascript
// 创建现金流图表
ChartUtils.createCashFlowChart(cashFlowData);

// 创建分配饼图
ChartUtils.createDistributionPieChart(distributionData);
```

## 技术特性

### 兼容性
- ✅ 现代浏览器支持 (Chrome 80+, Firefox 75+, Safari 13+, Edge 80+)
- ✅ 移动端浏览器支持
- ✅ 响应式设计

### 依赖关系
- **Bootstrap 5.3** - UI框架
- **jQuery 3.6** - DOM操作
- **Chart.js 4.0** - 图表库
- **SheetJS** - Excel处理

### 性能优化
- 🚀 代码分模块管理
- 🎯 按需加载功能
- 💾 本地缓存支持
- ⚡ 防抖节流优化

## 开发说明

### 代码规范
- 使用ES6+语法
- 遵循JSDoc注释规范
- 采用驼峰命名法
- 使用严格模式

### 调试建议
```javascript
// 开启控制台调试
console.log('基金计算系统初始化完成');

// 检查全局对象
window.FundCalculator
window.ChartUtils
window.NumberFormatter
```

### 自定义扩展
可以通过扩展现有工具类来添加新功能：

```javascript
// 扩展NumberFormatter
NumberFormatter.formatLargeNumber = function(value) {
    if (value >= 1000000000) {
        return (value / 1000000000).toFixed(1) + 'B';
    } else if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
    }
    return value.toString();
};
```

## 更新日志

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- 🎨 完整的样式系统
- 📊 图表功能完善
- 🛠️ 工具函数库建立
- 📱 响应式设计实现

---

如有问题或建议，请参考项目主文档或联系开发团队。 