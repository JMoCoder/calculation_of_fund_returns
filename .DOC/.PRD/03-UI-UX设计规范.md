# 收益分配测算系统 - UI/UX设计规范

## 1. 设计理念

### 1.1 设计原则
- **专业性**：体现金融行业的专业性和严谨性
- **简洁性**：界面简洁明了，突出核心功能
- **易用性**：操作流程清晰，降低学习成本
- **一致性**：保持整体设计风格的统一性
- **可靠性**：确保数据展示的准确性和可信度

### 1.2 设计目标
- 提供直观的用户操作体验
- 确保复杂金融计算的可理解性
- 支持高效的数据输入和结果查看
- 适应不同设备和屏幕尺寸

## 2. 视觉设计规范

### 2.1 色彩规范

#### 主色调
```css
/* 主品牌色 */
--primary-color: #1890ff;        /* 蓝色 - 专业、可信 */
--primary-light: #40a9ff;        /* 浅蓝色 */
--primary-dark: #096dd9;         /* 深蓝色 */

/* 辅助色 */
--secondary-color: #52c41a;      /* 绿色 - 成功、收益 */
--warning-color: #faad14;        /* 橙色 - 警告 */
--error-color: #ff4d4f;          /* 红色 - 错误、风险 */
--info-color: #13c2c2;           /* 青色 - 信息 */
```

#### 中性色
```css
/* 文字颜色 */
--text-primary: #262626;         /* 主要文字 */
--text-secondary: #595959;       /* 次要文字 */
--text-disabled: #bfbfbf;        /* 禁用文字 */
--text-inverse: #ffffff;         /* 反色文字 */

/* 背景颜色 */
--bg-primary: #ffffff;           /* 主背景 */
--bg-secondary: #fafafa;         /* 次背景 */
--bg-tertiary: #f5f5f5;          /* 三级背景 */
--bg-disabled: #f5f5f5;          /* 禁用背景 */

/* 边框颜色 */
--border-primary: #d9d9d9;       /* 主边框 */
--border-secondary: #f0f0f0;     /* 次边框 */
--border-focus: #40a9ff;         /* 焦点边框 */
```

#### 数据可视化色彩
```css
/* 图表配色方案 */
--chart-color-1: #1890ff;        /* 蓝色 */
--chart-color-2: #52c41a;        /* 绿色 */
--chart-color-3: #faad14;        /* 橙色 */
--chart-color-4: #722ed1;        /* 紫色 */
--chart-color-5: #13c2c2;        /* 青色 */
--chart-color-6: #eb2f96;        /* 粉色 */
--chart-color-7: #f5222d;        /* 红色 */
--chart-color-8: #fa8c16;        /* 橙红色 */
```

### 2.2 字体规范

#### 字体族
```css
/* 主字体 */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
             'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 
             'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 
             'Noto Color Emoji';

/* 数字字体 */
font-family: 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', 
             'Source Code Pro', Menlo, Consolas, 'Courier New', monospace;
```

#### 字体大小
```css
/* 标题字体 */
--font-size-h1: 32px;            /* 主标题 */
--font-size-h2: 24px;            /* 二级标题 */
--font-size-h3: 20px;            /* 三级标题 */
--font-size-h4: 16px;            /* 四级标题 */

/* 正文字体 */
--font-size-base: 14px;          /* 基础字体 */
--font-size-large: 16px;         /* 大字体 */
--font-size-small: 12px;         /* 小字体 */
--font-size-mini: 10px;          /* 迷你字体 */

/* 数字字体 */
--font-size-number-large: 24px;  /* 大数字 */
--font-size-number-base: 16px;   /* 基础数字 */
--font-size-number-small: 14px;  /* 小数字 */
```

#### 字重
```css
--font-weight-light: 300;        /* 细体 */
--font-weight-normal: 400;       /* 正常 */
--font-weight-medium: 500;       /* 中等 */
--font-weight-semibold: 600;     /* 半粗 */
--font-weight-bold: 700;         /* 粗体 */
```

### 2.3 间距规范

#### 基础间距
```css
/* 间距单位 */
--spacing-xs: 4px;               /* 极小间距 */
--spacing-sm: 8px;               /* 小间距 */
--spacing-md: 16px;              /* 中等间距 */
--spacing-lg: 24px;              /* 大间距 */
--spacing-xl: 32px;              /* 极大间距 */
--spacing-xxl: 48px;             /* 超大间距 */
```

#### 组件间距
```css
/* 组件内边距 */
--padding-xs: 4px 8px;           /* 极小内边距 */
--padding-sm: 8px 12px;          /* 小内边距 */
--padding-md: 12px 16px;         /* 中等内边距 */
--padding-lg: 16px 24px;         /* 大内边距 */

/* 组件外边距 */
--margin-xs: 4px;                /* 极小外边距 */
--margin-sm: 8px;                /* 小外边距 */
--margin-md: 16px;               /* 中等外边距 */
--margin-lg: 24px;               /* 大外边距 */
```

### 2.4 圆角和阴影

#### 圆角
```css
--border-radius-sm: 2px;         /* 小圆角 */
--border-radius-md: 4px;         /* 中等圆角 */
--border-radius-lg: 8px;         /* 大圆角 */
--border-radius-xl: 12px;        /* 极大圆角 */
```

#### 阴影
```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);           /* 小阴影 */
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);            /* 中等阴影 */
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);          /* 大阴影 */
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);         /* 极大阴影 */
```

## 3. 组件设计规范

### 3.1 按钮组件

#### 主要按钮
```css
.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: var(--text-inverse);
  padding: var(--padding-md);
  border-radius: var(--border-radius-md);
  font-weight: var(--font-weight-medium);
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
}
```

#### 次要按钮
```css
.btn-secondary {
  background-color: transparent;
  border-color: var(--border-primary);
  color: var(--text-primary);
  padding: var(--padding-md);
  border-radius: var(--border-radius-md);
}

.btn-secondary:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}
```

#### 按钮尺寸
- **大按钮**: 高度48px，用于主要操作
- **中等按钮**: 高度40px，用于常规操作
- **小按钮**: 高度32px，用于次要操作

### 3.2 表单组件

#### 输入框
```css
.input {
  width: 100%;
  padding: var(--padding-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-base);
  transition: border-color 0.3s ease;
}

.input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.input.error {
  border-color: var(--error-color);
}
```

#### 标签
```css
.label {
  display: block;
  margin-bottom: var(--margin-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.label.required::after {
  content: ' *';
  color: var(--error-color);
}
```

#### 表单布局
- 标签在输入框上方
- 必填项标注红色星号
- 错误信息在输入框下方显示
- 表单项之间间距16px

### 3.3 表格组件

#### 表格样式
```css
.table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.table th {
  background-color: var(--bg-tertiary);
  padding: var(--padding-md);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  border-bottom: 1px solid var(--border-secondary);
}

.table td {
  padding: var(--padding-md);
  border-bottom: 1px solid var(--border-secondary);
}

.table tr:hover {
  background-color: var(--bg-secondary);
}
```

#### 数字对齐
- 数字列右对齐
- 金额显示千分位分隔符
- 百分比保留2位小数
- 负数用红色显示

### 3.4 卡片组件

#### 基础卡片
```css
.card {
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--padding-lg);
  margin-bottom: var(--margin-lg);
}

.card-header {
  border-bottom: 1px solid var(--border-secondary);
  padding-bottom: var(--padding-md);
  margin-bottom: var(--margin-md);
}

.card-title {
  font-size: var(--font-size-h4);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}
```

### 3.5 选项卡组件

#### 选项卡样式
```css
.tabs {
  border-bottom: 1px solid var(--border-secondary);
  margin-bottom: var(--margin-lg);
}

.tab-item {
  display: inline-block;
  padding: var(--padding-md) var(--padding-lg);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
}

.tab-item.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.tab-item:hover {
  color: var(--primary-light);
}
```

## 4. 布局设计规范

### 4.1 页面布局

#### 整体布局
```
┌─────────────────────────────────────┐
│              Header                 │
├─────────────────────────────────────┤
│  Sidebar  │      Main Content      │
│           │                        │
│           │                        │
│           │                        │
├─────────────────────────────────────┤
│              Footer                 │
└─────────────────────────────────────┘
```

#### 响应式断点
```css
/* 移动设备 */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  .main-content {
    width: 100%;
  }
}

/* 平板设备 */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 200px;
  }
  .main-content {
    width: calc(100% - 200px);
  }
}

/* 桌面设备 */
@media (min-width: 1025px) {
  .sidebar {
    width: 240px;
  }
  .main-content {
    width: calc(100% - 240px);
  }
}
```

### 4.2 网格系统

#### 12列网格
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-md);
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 calc(-1 * var(--spacing-md) / 2);
}

.col {
  padding: 0 calc(var(--spacing-md) / 2);
}

/* 列宽度 */
.col-1 { flex: 0 0 8.333333%; }
.col-2 { flex: 0 0 16.666667%; }
.col-3 { flex: 0 0 25%; }
.col-4 { flex: 0 0 33.333333%; }
.col-6 { flex: 0 0 50%; }
.col-8 { flex: 0 0 66.666667%; }
.col-12 { flex: 0 0 100%; }
```

### 4.3 内容区域

#### 主要内容区
- 最大宽度: 1200px
- 左右边距: 24px
- 内容区域圆角: 8px
- 背景色: 白色

#### 侧边栏
- 宽度: 240px (桌面), 200px (平板)
- 背景色: #fafafa
- 导航项高度: 48px

## 5. 交互设计规范

### 5.1 状态反馈

#### 加载状态
```css
.loading {
  position: relative;
  pointer-events: none;
}

.loading::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  margin: -10px 0 0 -10px;
  border: 2px solid var(--border-primary);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

#### 成功状态
- 使用绿色 (#52c41a)
- 显示成功图标
- 3秒后自动消失

#### 错误状态
- 使用红色 (#ff4d4f)
- 显示错误图标
- 需要用户手动关闭

#### 警告状态
- 使用橙色 (#faad14)
- 显示警告图标
- 5秒后自动消失

### 5.2 动画效果

#### 过渡动画
```css
/* 通用过渡 */
.transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 淡入淡出 */
.fade-enter {
  opacity: 0;
}
.fade-enter-active {
  opacity: 1;
  transition: opacity 0.3s ease;
}

/* 滑动效果 */
.slide-enter {
  transform: translateX(-100%);
}
.slide-enter-active {
  transform: translateX(0);
  transition: transform 0.3s ease;
}
```

#### 微交互
- 按钮悬停: 0.3s缓动
- 表单焦点: 0.2s缓动
- 页面切换: 0.5s缓动
- 数据加载: 脉冲动画

### 5.3 用户引导

#### 步骤指示器
```css
.steps {
  display: flex;
  align-items: center;
  margin-bottom: var(--margin-xl);
}

.step {
  display: flex;
  align-items: center;
  flex: 1;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-semibold);
}

.step.active .step-number {
  background-color: var(--primary-color);
  color: var(--text-inverse);
}

.step.completed .step-number {
  background-color: var(--secondary-color);
  color: var(--text-inverse);
}
```

#### 提示信息
- 工具提示: 悬停显示
- 帮助文本: 输入框下方
- 验证信息: 实时显示
- 操作确认: 模态对话框

## 6. 数据可视化规范

### 6.1 图表设计

#### 图表配色
- 主色调: 蓝色系
- 对比色: 绿色、橙色
- 中性色: 灰色系
- 强调色: 红色（负值）

#### 图表类型
- **折线图**: 趋势展示
- **柱状图**: 数值对比
- **饼图**: 比例展示
- **面积图**: 累积展示

### 6.2 数据展示

#### 数值格式
```javascript
// 金额格式化
function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

// 百分比格式化
function formatPercentage(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value / 100);
}

// 数字格式化
function formatNumber(value) {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}
```

#### 表格数据
- 数字右对齐
- 金额显示货币符号
- 百分比显示%符号
- 负数红色显示
- 零值灰色显示

## 7. 可访问性规范

### 7.1 键盘导航
- Tab键顺序合理
- 焦点状态明显
- 快捷键支持
- 跳过链接提供

### 7.2 屏幕阅读器
- 语义化HTML标签
- ARIA标签支持
- 图片alt属性
- 表格标题关联

### 7.3 色彩对比
- 文字对比度 ≥ 4.5:1
- 大文字对比度 ≥ 3:1
- 非文字对比度 ≥ 3:1
- 色盲友好设计

## 8. 移动端适配

### 8.1 响应式设计
- 移动优先策略
- 弹性布局
- 图片自适应
- 字体缩放

### 8.2 触摸交互
- 最小触摸目标: 44px
- 手势支持
- 触摸反馈
- 滑动操作

### 8.3 性能优化
- 图片压缩
- 代码分割
- 懒加载
- 缓存策略

## 9. 设计检查清单

### 9.1 视觉检查
- [ ] 色彩使用符合规范
- [ ] 字体大小和层级正确
- [ ] 间距使用一致
- [ ] 组件状态完整
- [ ] 图标使用统一

### 9.2 交互检查
- [ ] 操作反馈及时
- [ ] 错误处理完善
- [ ] 加载状态明确
- [ ] 导航逻辑清晰
- [ ] 表单验证友好

### 9.3 兼容性检查
- [ ] 浏览器兼容性
- [ ] 设备适配性
- [ ] 网络环境适应
- [ ] 可访问性支持
- [ ] 性能表现良好

## 10. 设计资源

### 10.1 图标库
- 使用Ant Design Icons或Feather Icons
- 统一图标风格
- 合适的图标大小
- 语义化图标选择

### 10.2 插图和图片
- 专业金融风格
- 高质量矢量图
- 统一视觉风格
- 适当的文件大小

### 10.3 设计工具
- Figma设计稿
- Sketch组件库
- Adobe XD原型
- 设计规范文档