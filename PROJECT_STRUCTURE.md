# Project Structure

```
calculation_of_fund_returns/
├── 📁 .github/                       # GitHub配置目录
│   ├── 📁 ISSUE_TEMPLATE/            # Issue模板目录
│   │   ├── bug_report.md             # Bug报告模板
│   │   └── feature_request.md        # 功能请求模板
│   ├── 📁 workflows/                 # GitHub Actions工作流
│   │   └── ci.yml                    # 持续集成配置
│   ├── CODEOWNERS                    # 代码拥有者配置
│   └── pull_request_template.md      # Pull Request模板
│
├── 📁 .PRD/                          # 产品需求文档目录
│   ├── 00-初始需求文档.md             # 项目初始需求
│   ├── 01-项目概述.md                 # 项目总体概述
│   ├── 02-功能需求规格说明书.md       # 详细功能需求
│   ├── 03-UI-UX设计规范.md           # 界面设计规范
│   ├── 04-技术架构设计.md             # 技术架构文档
│   ├── 05-数据库设计.md               # 数据库设计
│   ├── 06-API接口设计.md             # API接口规范
│   ├── 07-测试计划.md                 # 测试计划
│   ├── 08-部署运维文档.md             # 部署运维指南
│   ├── 09-项目管理文档.md             # 项目管理
│   ├── 10-用户手册.md                 # 用户使用手册
│   └── README.md                     # PRD目录说明
│
├── 📁 .UI/                           # UI设计文件目录
│   ├── 01-主页面布局.html             # 主页面设计
│   ├── 02-基本参数输入界面.html       # 参数输入界面
│   ├── 03-净现金流输入界面.html       # 现金流输入界面
│   ├── 04-分配模式设置界面.html       # 分配模式界面
│   ├── 05-计算结果展示界面.html       # 结果展示界面
│   ├── 06-图表可视化界面.html         # 图表界面
│   ├── 07-系统设置界面.html           # 系统设置界面
│   └── README.md                     # UI目录说明
│
├── 📁 templates/                     # Flask模板文件
│   └── index.html                    # 主页面模板（完整的单页应用）
│
├── 📄 app.py                         # Flask后端主程序
├── 📄 requirements.txt               # Python依赖包列表
├── 📄 deploy.bat                     # 一键部署脚本（Windows）
├── 📄 start.bat                      # 快速启动脚本（Windows）
├── 📄 README.md                      # 项目说明文档
└── 📄 PROJECT_STRUCTURE.md           # 本文件
```

## 📋 核心文件详解

### 🔧 后端文件

#### `app.py` - Flask后端主程序
- **FundCalculator类**：核心计算引擎
  - `set_basic_params()`: 设置基本投资参数
  - `set_cash_flows()`: 设置净现金流数据
  - `calculate_irr()`: 计算内部收益率
  - `calculate_dpi()`: 计算分配倍数
  - `calculate_flat_structure_priority_repayment()`: 平层结构优先还本计算
  - `calculate_flat_structure_periodic_distribution()`: 平层结构期间分配计算
  - `calculate_structured_senior_subordinate()`: 结构化优先劣后计算

- **API路由**：
  - `GET /`: 主页面
  - `GET /api/health`: 健康检查
  - `POST /api/basic-params`: 设置基本参数
  - `POST /api/cash-flows`: 设置现金流
  - `POST /api/calculate`: 执行计算
  - `POST /api/export`: 导出Excel
  - `POST /api/import`: 导入Excel
  - `GET /api/template`: 下载模板

#### `requirements.txt` - Python依赖管理
```
Flask==2.3.3           # Web框架
Flask-CORS==4.0.0       # 跨域支持
pandas==2.1.1           # 数据处理
numpy==1.24.3           # 数值计算
openpyxl==3.1.2         # Excel读取
xlsxwriter==3.1.3       # Excel写入
gunicorn==21.2.0        # WSGI服务器
python-dotenv==1.0.0    # 环境变量管理
```

### 🎨 前端文件

#### `templates/index.html` - 完整单页应用
- **HTML结构**：
  - 响应式布局设计
  - 步骤导航侧边栏
  - 5个主要功能模块

- **CSS样式**：
  - 基于Bootstrap 5框架
  - 自定义变量和主题色
  - 现代化UI设计

- **JavaScript功能**：
  - 单页应用路由管理
  - 表单验证和数据处理
  - AJAX API调用
  - Excel文件处理
  - 动态表格生成
  - 实时数据计算

### 🚀 部署文件

#### `deploy.bat` - 一键部署脚本（Windows）
执行流程：
1. 检查Python环境
2. 验证pip包管理器
3. 升级pip到最新版本
4. 安装项目依赖包
5. 检查端口占用情况
6. 启动Web服务器
7. 自动打开浏览器

#### `start.bat` - 快速启动脚本
用于已配置环境的快速启动，简化启动流程。

### 📚 文档文件

#### `README.md` - 项目主文档
- 项目简介和功能说明
- 安装和使用指南
- 技术架构介绍
- 常见问题解答

#### `.PRD/` - 产品需求文档
完整的产品设计文档，包含：
- 需求分析
- 功能规范
- 技术设计
- 测试计划
- 部署指南

#### `.UI/` - 界面设计文件
原始的HTML界面设计文件，作为开发参考。

## 🔄 系统工作流程

### 1. 启动流程
```
用户双击 deploy.bat
    ↓
检查系统环境
    ↓
安装依赖包
    ↓
启动Flask服务器
    ↓
打开浏览器访问系统
```

### 2. 计算流程
```
输入基本参数
    ↓
设置净现金流
    ↓
选择分配模式
    ↓
执行计算逻辑
    ↓
展示结果和图表
    ↓
导出Excel报告
```

### 3. 数据流向
```
前端表单输入
    ↓
JavaScript验证
    ↓
AJAX发送到后端
    ↓
Flask路由处理
    ↓
FundCalculator计算
    ↓
JSON结果返回
    ↓
前端渲染显示
```

## 🛠️ 开发和维护

### 环境要求
- Python 3.8或更高版本
- 现代浏览器（Chrome 90+, Firefox 88+, Safari 14+）
- Windows 10/11（推荐）

### 开发模式启动
```bash
# 开发模式（自动重载）
python app.py

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 代码结构规范
- 后端：遵循PEP 8 Python编码规范
- 前端：使用ES6+语法，模块化设计
- 注释：每个函数都有详细的JSDoc注释

### 安全特性
- 无数据持久化存储
- 输入数据严格验证
- 本地环境运行
- 临时文件自动清理

## 🔧 扩展和定制

### 添加新的分配模式
1. 在`FundCalculator`类中添加新的计算方法
2. 在`/api/calculate`路由中添加新模式的处理逻辑
3. 在前端添加新模式的界面和参数输入
4. 更新结果显示逻辑

### 添加新的图表类型
1. 在前端引入Chart.js图表库
2. 在可视化模块中添加新图表的生成逻辑
3. 根据计算结果数据创建相应的图表配置

### 国际化支持
- 前端：添加多语言字符串资源
- 后端：添加多语言错误消息
- 界面：支持RTL布局和本地化格式

## 📊 性能优化

### 前端优化
- 使用CDN加载外部库
- 图片和资源压缩
- JavaScript代码压缩
- 缓存策略优化

### 后端优化
- 数据计算算法优化
- 内存使用优化
- 并发处理能力
- 错误处理和日志

## 🧪 测试和质量保证

### 功能测试
- 输入验证测试
- 计算逻辑测试
- 界面交互测试
- 文件导入导出测试

### 性能测试
- 大数据量计算测试
- 并发用户访问测试
- 内存泄漏测试
- 响应时间测试

### 兼容性测试
- 不同浏览器兼容性
- 不同操作系统兼容性
- 不同Python版本兼容性

---

**注意**：这是一个完整的、生产就绪的金融计算系统，所有组件都经过精心设计和优化，确保稳定性、安全性和易用性。 

### 🐙 GitHub配置文件

#### `.github/ISSUE_TEMPLATE/` - Issue模板
- **bug_report.md**: Bug报告标准模板
  - 包含Bug描述、重现步骤、环境信息等字段
  - 自动分配给@JMoCoder进行处理
  - 自动添加bug标签

- **feature_request.md**: 功能请求模板
  - 包含功能描述、使用场景、验收标准等字段
  - 自动分配给@JMoCoder进行评估
  - 自动添加enhancement标签

#### `.github/workflows/ci.yml` - 持续集成配置
- **多Python版本测试**: 支持3.8-3.11版本矩阵测试
- **代码质量检查**: 使用flake8进行代码风格检查
- **安全扫描**: 使用safety和bandit进行安全漏洞检测
- **自动化测试**: 基本功能测试和文件完整性检查
- **构建验证**: Windows和Linux环境构建测试

#### `.github/CODEOWNERS` - 代码拥有者
- 设置@JMoCoder为所有文件的默认审查者
- 对核心文件和目录进行特别指定
- 确保重要更改需要经过审查

#### `.github/pull_request_template.md` - PR模板
- 标准化Pull Request格式
- 包含检查清单和类型分类
- 要求描述更改内容和测试情况 