# 📦 项目依赖管理说明

## 🎯 依赖文件位置

- **主依赖文件**: `/requirements.txt` (项目根目录)
- **原因**: 遵循Python标准约定，便于pip和CI/CD工具自动识别

## 📋 当前依赖列表

### 🌐 Web框架
- **Flask>=2.3.0**: 主Web框架
- **Flask-CORS>=4.0.0**: 跨域资源共享支持

### 📊 数据处理
- **pandas>=2.0.0**: 数据分析和处理
- **numpy>=1.24.0**: 高性能数值计算
- **openpyxl>=3.1.0**: Excel文件读写
- **xlsxwriter>=3.1.0**: Excel文件生成

### 🚀 部署相关
- **gunicorn>=21.0.0**: WSGI HTTP服务器
- **python-dotenv>=1.0.0**: 环境变量管理

## 🔧 安装方法

### 标准安装
```bash
pip install -r requirements.txt
```

### 国内镜像安装 (推荐)
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 开发环境安装
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 📈 版本管理策略

### 🔒 版本锁定
- 使用 `>=` 指定最低版本要求
- 确保兼容性的同时获得安全更新
- 避免过度锁定导致的依赖冲突

### 🔄 更新策略
1. **安全更新**: 及时更新有安全漏洞的包
2. **功能更新**: 谨慎评估新功能的必要性
3. **兼容性测试**: 更新后运行完整测试套件

## 🧪 测试依赖

当前项目的测试依赖已集成在主要求文件中：
- **requests**: API测试
- **unittest**: 内置测试框架

## 🐳 容器化部署

Docker环境下的依赖安装：
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

## ⚠️ 注意事项

1. **位置固定**: `requirements.txt` 必须位于项目根目录
2. **自动化**: 多个脚本和CI/CD流程依赖此文件
3. **标准约定**: 符合Python社区标准实践
4. **工具支持**: IDE和开发工具自动识别根目录的requirements.txt

## 🔍 依赖安全

### 安全检查
```bash
# 安装安全检查工具
pip install safety

# 检查已知漏洞
safety check -r requirements.txt
```

### 许可证检查
```bash
# 安装许可证检查工具
pip install pip-licenses

# 查看所有依赖的许可证
pip-licenses
```

---

**维护说明**: 此文档与 `/requirements.txt` 保持同步，任何依赖变更都应同时更新此说明。 