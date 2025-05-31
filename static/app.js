/**
 * 基金收益分配计算系统 - 前端核心逻辑
 * @description 处理用户交互、API调用、数据验证和界面更新
 * @author 基金计算系统团队
 * @version 1.0.0
 */

/**
 * 全局变量定义
 */
let currentStep = 1; // 当前步骤
let calculationResult = null; // 计算结果存储
let chartInstance = null; // 图表实例

/**
 * 页面初始化函数
 */
$(document).ready(function() {
    console.log('基金计算系统初始化开始');
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化表单验证
    initializeFormValidation();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 初始化步骤导航
    updateStepNavigation();
    
    console.log('基金计算系统初始化完成');
});

/**
 * 初始化Bootstrap工具提示
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 初始化表单验证
 */
function initializeFormValidation() {
    // Bootstrap表单验证样式
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * 绑定事件监听器
 */
function bindEventListeners() {
    // 步骤导航点击事件
    $('.nav-link').click(function(e) {
        e.preventDefault();
        var targetStep = safeParseInt($(this).data('step'));
        if (targetStep <= currentStep) {
            showStep(targetStep);
        }
    });
    
    // 表单提交事件
    $('#basicForm').submit(handleBasicFormSubmit);
    $('#cashFlowForm').submit(handleCashFlowFormSubmit);
    
    // 分配模式选择事件
    $('input[name="distributionMode"]').change(handleDistributionModeChange);
    
    // Excel文件处理事件
    $('#excelFile').change(handleExcelFileChange);
    
    // 按钮点击事件
    $('#downloadTemplate').click(downloadTemplate);
    $('#exportExcel').click(exportToExcel);
    $('#resetAll').click(resetAllData);
}

/**
 * 处理基础参数表单提交
 * @param {Event} e - 表单提交事件
 */
function handleBasicFormSubmit(e) {
    e.preventDefault();
    
    showLoading('正在保存基础参数...');
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    // 数据验证
    if (!validateBasicParams(data)) {
        hideLoading();
        return;
    }
    
    // 发送API请求
    $.ajax({
        url: '/api/basic_params',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(response) {
            hideLoading();
            if (response.status === 'success') {
                showAlert('基础参数保存成功！', 'success');
                currentStep = Math.max(currentStep, 2);
                updateStepNavigation();
                showStep(2);
            } else {
                showAlert('保存失败：' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            showAlert('网络错误：' + error, 'danger');
        }
    });
}

/**
 * 处理现金流表单提交
 * @param {Event} e - 表单提交事件
 */
function handleCashFlowFormSubmit(e) {
    e.preventDefault();
    
    showLoading('正在保存现金流数据...');
    
    const cashFlows = collectCashFlowData();
    
    if (cashFlows.length === 0) {
        hideLoading();
        showAlert('请至少添加一条现金流记录', 'warning');
        return;
    }
    
    $.ajax({
        url: '/api/cash_flows',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({cash_flows: cashFlows}),
        success: function(response) {
            hideLoading();
            if (response.status === 'success') {
                showAlert('现金流数据保存成功！', 'success');
                currentStep = Math.max(currentStep, 3);
                updateStepNavigation();
                showStep(3);
            } else {
                showAlert('保存失败：' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            showAlert('网络错误：' + error, 'danger');
        }
    });
}

/**
 * 处理分配模式选择变更
 * @param {Event} e - 单选框变更事件
 */
function handleDistributionModeChange(e) {
    const selectedMode = $(this).val();
    
    // 显示对应的配置区域
    $('.distribution-config').hide();
    $('#' + selectedMode + 'Config').show();
    
    // 启用计算按钮
    $('#calculateBtn').prop('disabled', false);
}

/**
 * 处理Excel文件上传
 * @param {Event} e - 文件选择事件
 */
function handleExcelFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ];
    
    if (!allowedTypes.includes(file.type)) {
        showAlert('请选择Excel文件（.xlsx或.xls格式）', 'warning');
        $(this).val('');
        return;
    }
    
    // 验证文件大小（最大10MB）
    if (file.size > 10 * 1024 * 1024) {
        showAlert('文件大小不能超过10MB', 'warning');
        $(this).val('');
        return;
    }
    
    uploadExcelFile(file);
}

/**
 * 上传Excel文件
 * @param {File} file - 选择的文件
 */
function uploadExcelFile(file) {
    showLoading('正在解析Excel文件...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    $.ajax({
        url: '/api/import_excel',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            if (response.status === 'success') {
                showAlert('Excel文件导入成功！', 'success');
                
                // 更新基础参数
                if (response.data.basic_params) {
                    updateBasicParamsForm(response.data.basic_params);
                }
                
                // 更新现金流数据
                if (response.data.cash_flows) {
                    updateCashFlowTable(response.data.cash_flows);
                }
                
                currentStep = Math.max(currentStep, 2);
                updateStepNavigation();
            } else {
                showAlert('导入失败：' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            showAlert('导入错误：' + error, 'danger');
        }
    });
}

/**
 * 执行收益分配计算
 */
function performCalculation() {
    const distributionMode = $('input[name="distributionMode"]:checked').val();
    
    if (!distributionMode) {
        showAlert('请选择分配模式', 'warning');
        return;
    }
    
    showLoading('正在计算收益分配...');
    
    // 收集分配参数
    const distributionParams = collectDistributionParams(distributionMode);
    
    $.ajax({
        url: '/api/calculate',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            mode: distributionMode,
            params: distributionParams
        }),
        success: function(response) {
            hideLoading();
            if (response.status === 'success') {
                calculationResult = response.data;
                showAlert('计算完成！', 'success');
                currentStep = Math.max(currentStep, 4);
                updateStepNavigation();
                showStep(4);
                displayResults(response.data);
            } else {
                showAlert('计算失败：' + response.message, 'danger');
            }
        },
        error: function(xhr, status, error) {
            hideLoading();
            showAlert('计算错误：' + error, 'danger');
        }
    });
}

/**
 * 显示计算结果
 * @param {Object} results - 计算结果数据
 */
function displayResults(results) {
    // 显示基本指标
    displayBasicMetrics(results.metrics);
    
    // 显示分配明细
    displayDistributionDetails(results.distributions);
    
    // 显示图表
    createCharts(results);
    
    // 启用步骤5
    currentStep = Math.max(currentStep, 5);
    updateStepNavigation();
}

/**
 * 显示基本指标
 * @param {Object} metrics - 指标数据
 */
function displayBasicMetrics(metrics) {
    const metricsHtml = `
        <div class="row">
            <div class="col-md-6">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">总投资金额</h5>
                        <h3 class="text-primary">${formatCurrency(metrics.total_investment)}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">总回收金额</h5>
                        <h3 class="text-success">${formatCurrency(metrics.total_return)}</h3>
                    </div>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">IRR</h5>
                        <h3 class="text-info">${formatPercentage(metrics.irr)}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">DPI</h5>
                        <h3 class="text-warning">${formatNumber(metrics.dpi)}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">净收益</h5>
                        <h3 class="text-success">${formatCurrency(metrics.net_profit)}</h3>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('#metricsDisplay').html(metricsHtml);
}

/**
 * 显示分配明细表格
 * @param {Array} distributions - 分配明细数据
 */
function displayDistributionDetails(distributions) {
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>期间</th>
                        <th>可分配金额</th>
                        <th>GP分配</th>
                        <th>LP分配</th>
                        <th>分配比例</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    distributions.forEach(function(dist, index) {
        tableHtml += `
            <tr>
                <td>第${index + 1}期</td>
                <td>${formatCurrency(dist.distributable_amount)}</td>
                <td>${formatCurrency(dist.gp_distribution)}</td>
                <td>${formatCurrency(dist.lp_distribution)}</td>
                <td>GP:${formatPercentage(dist.gp_ratio)} / LP:${formatPercentage(dist.lp_ratio)}</td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    $('#distributionTable').html(tableHtml);
}

/**
 * 创建可视化图表
 * @param {Object} results - 计算结果数据
 */
function createCharts(results) {
    currentStep = Math.max(currentStep, 5);
    updateStepNavigation();
    showStep(5);
    
    // 创建现金流图表
    createCashFlowChart(results.cash_flows);
    
    // 创建分配比例饼图
    createDistributionPieChart(results.distributions);
}

/**
 * 工具函数：显示步骤
 * @param {number} step - 步骤编号
 */
function showStep(step) {
    // 隐藏所有步骤
    $('.step-content').hide();
    
    // 显示目标步骤
    $('#step' + step).show();
    
    // 更新导航状态
    $('.nav-link').removeClass('active');
    $('.nav-link[data-step="' + step + '"]').addClass('active');
}

/**
 * 工具函数：更新步骤导航状态
 */
function updateStepNavigation() {
    $('.nav-link').each(function() {
        const stepNum = safeParseInt($(this).data('step'));
        if (stepNum <= currentStep) {
            $(this).removeClass('disabled').prop('disabled', false);
        } else {
            $(this).addClass('disabled').prop('disabled', true);
        }
    });
}

/**
 * 工具函数：显示加载状态
 * @param {string} message - 加载消息
 */
function showLoading(message = '加载中...') {
    const loadingHtml = `
        <div class="text-center">
            <div class="loading"></div>
            <p class="mt-2">${message}</p>
        </div>
    `;
    
    // 可以在模态框或特定区域显示加载状态
    $('#loadingModal .modal-body').html(loadingHtml);
    $('#loadingModal').modal('show');
}

/**
 * 工具函数：隐藏加载状态
 */
function hideLoading() {
    $('#loadingModal').modal('hide');
}

/**
 * 工具函数：显示警告消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, warning, danger, info)
 */
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#alertContainer').html(alertHtml);
    
    // 自动隐藏成功消息
    if (type === 'success') {
        setTimeout(function() {
            $('.alert').alert('close');
        }, 3000);
    }
}

/**
 * 工具函数：格式化货币
 * @param {number} amount - 金额
 * @returns {string} 格式化后的货币字符串
 */
function formatCurrency(amount) {
    // 安全检查：确保amount是有效数字
    if (typeof amount !== 'number' || isNaN(amount) || !isFinite(amount)) {
        return '￥0.00';
    }
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * 工具函数：格式化百分比
 * @param {number} value - 数值
 * @returns {string} 格式化后的百分比字符串
 */
function formatPercentage(value) {
    // 安全检查：确保value是有效数字
    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
        return '0.00%';
    }
    return new Intl.NumberFormat('zh-CN', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

/**
 * 工具函数：格式化数字
 * @param {number} value - 数值
 * @returns {string} 格式化后的数字字符串
 */
function formatNumber(value) {
    // 安全检查：确保value是有效数字
    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
        return '0.00';
    }
    return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * 安全解析浮点数，防止NaN
 */
function safeParseFloat(value, defaultValue = 0) {
    if (value === null || value === undefined || value === '') {
        return defaultValue;
    }
    const parsed = parseFloat(value);
    return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * 安全解析整数，防止NaN
 */
function safeParseInt(value, defaultValue = 0) {
    if (value === null || value === undefined || value === '') {
        return defaultValue;
    }
    const parsed = parseInt(value);
    return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * 数据验证：基础参数验证
 * @param {Object} data - 表单数据
 * @returns {boolean} 验证结果
 */
function validateBasicParams(data) {
    if (!data.fund_name || data.fund_name.trim() === '') {
        showAlert('请输入基金名称', 'warning');
        return false;
    }
    
    if (!data.fund_size || safeParseFloat(data.fund_size) <= 0) {
        showAlert('请输入有效的基金规模', 'warning');
        return false;
    }
    
    if (!data.management_fee_rate || safeParseFloat(data.management_fee_rate) < 0) {
        showAlert('请输入有效的管理费率', 'warning');
        return false;
    }
    
    return true;
}

/**
 * 数据收集：现金流数据
 * @returns {Array} 现金流数组
 */
function collectCashFlowData() {
    const cashFlows = [];
    
    $('#cashFlowTable tbody tr').each(function() {
        const row = $(this);
        const date = row.find('input[type="date"]').val();
        const type = row.find('select').val();
        const amount = safeParseFloat(row.find('input[type="number"]').val());
        
        if (date && type && amount) {
            cashFlows.push({
                date: date,
                type: type,
                amount: amount
            });
        }
    });
    
    return cashFlows;
}

/**
 * 数据收集：分配参数
 * @param {string} mode - 分配模式
 * @returns {Object} 分配参数对象
 */
function collectDistributionParams(mode) {
    const params = {};
    
    if (mode === 'flat') {
        params.hurdle_rate = safeParseFloat($('#hurdleRate').val());
        params.carry_rate = safeParseFloat($('#carryRate').val());
    } else if (mode === 'structured') {
        params.senior_rate = safeParseFloat($('#seniorRate').val());
        params.subordinate_rate = safeParseFloat($('#subordinateRate').val());
        params.catch_up_rate = safeParseFloat($('#catchUpRate').val());
    }
    
    return params;
}

// 导出函数供HTML模板使用
window.FundCalculator = {
    performCalculation: performCalculation,
    downloadTemplate: downloadTemplate,
    exportToExcel: exportToExcel,
    resetAllData: resetAllData,
    addCashFlowRow: addCashFlowRow,
    removeCashFlowRow: removeCashFlowRow
}; 