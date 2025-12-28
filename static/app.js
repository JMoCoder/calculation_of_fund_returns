/**
 * 基金收益分配计算系统 - 主要应用逻辑
 * 无状态版本：前端负责管理所有数据，最后一次性提交给后端计算
 */

// 全局应用状态
const AppState = {
    currentStep: 1,
    basicParams: {},
    cashFlows: [],
    mode: '',
    modeParams: {},
    calculationResult: null
};

$(document).ready(function() {
    console.log('应用初始化完成 - 完整版');
    
    // 初始化页面加载器
    if (window.PageLoader) {
        window.PageLoader.finishLoading();
    }
    
    // 绑定事件
    bindEvents();
    
    // 初始化快速调整开关
    initQuickAdjustment();
});

/**
 * 绑定页面事件
 */
function bindEvents() {
    // 导航点击事件
    $('.nav-link, .step-item').click(function(e) {
        // 如果是禁用状态，不处理
        if ($(this).hasClass('disabled') || $(this).prop('disabled')) {
            return;
        }
        
        // 如果是侧边栏点击
        if ($(this).hasClass('step-item')) {
            // 获取步骤索引
            const index = $(this).index() + 1;
            // 只有已完成或当前步骤之前的步骤可点击
            if (index < AppState.currentStep) {
                // 根据索引找到对应的ID
                const ids = ['basic-params', 'cash-flows', 'distribution-mode', 'results', 'visualization'];
                if (ids[index-1]) {
                    showTab(ids[index-1]);
                }
            }
        }
    });
}

/**
 * 显示指定标签页
 */
function showTab(tabId) {
    // 隐藏所有内容区域
    $('.content-area').removeClass('active').hide();
    // 显示目标区域
    $(`#${tabId}`).addClass('active').fadeIn();
    
    // 更新侧边栏状态
    updateSidebar(tabId);
    
    // 如果是返回结果页，且有结果，则不需要重新计算
    if (tabId === 'results' && AppState.calculationResult) {
        renderResults(AppState.calculationResult);
    }
    
    // 如果是图表页，且有结果，渲染图表
    if (tabId === 'visualization' && AppState.calculationResult) {
        if (window.renderCharts && AppState.calculationResult.chart_data) {
            window.renderCharts(AppState.calculationResult.chart_data);
        }
    }
}

/**
 * 更新侧边栏状态
 */
function updateSidebar(activeTabId) {
    const tabMap = {
        'basic-params': 1,
        'cash-flows': 2,
        'distribution-mode': 3,
        'results': 4,
        'visualization': 5
    };
    
    const activeStep = tabMap[activeTabId] || 1;
    AppState.currentStep = Math.max(AppState.currentStep, activeStep);
    
    $('.step-item').each(function(index) {
        const stepNum = index + 1;
        $(this).removeClass('active completed');
        
        if (stepNum === activeStep) {
            $(this).addClass('active');
        } else if (stepNum < activeStep) {
            $(this).addClass('completed');
        }
    });
}

/**
 * 步骤1：保存基本参数
 */
function saveBasicParams() {
    // 获取表单数据
    const params = {
        investment_target: $('#investmentTarget').val(),
        investment_amount: parseFloat($('#investmentAmount').val()),
        investment_period: parseInt($('#investmentPeriod').val()),
        hurdle_rate: parseFloat($('#hurdleRate').val()),
        management_carry: parseFloat($('#managementCarry').val())
    };
    
    // 验证数据
    if (!params.investment_target) {
        showAlert('请输入投资标的名称', 'error');
        return;
    }
    if (isNaN(params.investment_amount) || params.investment_amount <= 0) {
        showAlert('请输入有效的投资金额', 'error');
        return;
    }
    if (isNaN(params.investment_period) || params.investment_period <= 0 || params.investment_period > 30) {
        showAlert('请输入有效的投资期限（1-30年）', 'error');
        return;
    }
    if (isNaN(params.hurdle_rate) || params.hurdle_rate < 0 || params.hurdle_rate > 100) {
        showAlert('请输入有效的门槛收益率（0-100%）', 'error');
        return;
    }
    if (isNaN(params.management_carry) || params.management_carry < 0 || params.management_carry > 100) {
        showAlert('请输入有效的管理人Carry（0-100%）', 'error');
        return;
    }
    
    // 保存到全局状态
    AppState.basicParams = params;
    
    // 调用后端校验（可选，这里为了保持兼容性可以调一下，或者直接跳过）
    // 为了无状态化，我们这里只做前端校验，直接进入下一步
    
    // 生成现金流输入框
    generateCashFlowInputs(params.investment_period);
    
    // 切换到下一步
    showTab('cash-flows');
    showAlert('基本参数设置成功', 'success');
}

/**
 * 生成现金流输入框
 */
function generateCashFlowInputs(years) {
    const container = $('#cashFlowInputs');
    container.empty();
    
    // 创建表单结构
    let html = '<div class="form-group">';
    
    // 每行显示3个输入框
    for (let i = 1; i <= years; i++) {
        if ((i - 1) % 3 === 0) {
            html += '<div class="form-row triple">';
        }
        
        // 尝试获取已有的值
        const existingValue = AppState.cashFlows[i-1] !== undefined ? AppState.cashFlows[i-1] : '';
        
        html += `
            <div class="field-wrapper">
                <label class="label">第 ${i} 年净现金流</label>
                <div class="input-group">
                    <input type="number" class="input cash-flow-input" 
                           data-year="${i}" 
                           id="cashFlow_${i}" 
                           value="${existingValue}" 
                           placeholder="输入金额" step="0.01">
                    <span class="input-addon">万元</span>
                </div>
            </div>
        `;
        
        if (i % 3 === 0 || i === years) {
            html += '</div>';
        }
    }
    
    html += '</div>';
    container.html(html);
}

/**
 * 步骤2：保存现金流
 */
function saveCashFlows() {
    const cashFlows = [];
    let isValid = true;
    
    $('.cash-flow-input').each(function() {
        const val = parseFloat($(this).val());
        if (isNaN(val)) {
            isValid = false;
            $(this).addClass('error');
        } else {
            $(this).removeClass('error');
            cashFlows.push(val);
        }
    });
    
    if (!isValid) {
        showAlert('请填写所有年份的有效现金流数据', 'error');
        return;
    }
    
    // 保存到全局状态
    AppState.cashFlows = cashFlows;
    
    // 切换到下一步
    showTab('distribution-mode');
    showAlert('现金流数据保存成功', 'success');
}

/**
 * 步骤3：选择分配模式
 */
function selectMode(element, mode) {
    // 更新UI
    $('.mode-option').removeClass('selected');
    $('.mode-card').removeClass('selected');
    $(element).addClass('selected');
    $(element).closest('.mode-card').addClass('selected');
    $(element).find('input[type="radio"]').prop('checked', true);
    
    // 保存模式
    AppState.mode = mode;
    
    // 显示/隐藏特定参数输入框
    $('#periodicRateInput').hide();
    $('#structuredParams').hide();
    $('#mezzanineParams').hide();
    $('#interestPrincipalParams').hide();
    
    if (mode === 'flat_periodic_distribution') {
        $('#periodicRateInput').fadeIn();
    } else if (mode === 'structured_senior_subordinate') {
        $('#structuredParams').fadeIn();
    } else if (mode === 'structured_mezzanine') {
        $('#mezzanineParams').fadeIn();
    } else if (mode === 'structured_interest_principal') {
        $('#interestPrincipalParams').fadeIn();
    }
}

/**
 * 步骤3：执行计算
 */
function calculate() {
    if (!AppState.mode) {
        showAlert('请选择分配模式', 'warning');
        return;
    }
    
    // 收集模式特定参数
    const modeParams = {};
    let isValid = true;
    
    if (AppState.mode === 'flat_periodic_distribution') {
        const rate = parseFloat($('#periodicRate').val());
        if (isNaN(rate) || rate < 0 || rate > 100) {
            isValid = false;
            showAlert('请输入有效的期间收益率', 'error');
        }
        modeParams.periodic_rate = rate;
    } 
    else if (AppState.mode === 'structured_senior_subordinate') {
        const ratio = parseFloat($('#seniorRatio').val());
        if (isNaN(ratio) || ratio <= 0 || ratio >= 100) {
            isValid = false;
            showAlert('请输入有效的优先级比例', 'error');
        }
        modeParams.senior_ratio = ratio;
    }
    else if (AppState.mode === 'structured_mezzanine') {
        const sRatio = parseFloat($('#mezzSeniorRatio').val());
        const mRatio = parseFloat($('#mezzRatio').val());
        const mRate = parseFloat($('#mezzRate').val());
        
        if (isNaN(sRatio) || isNaN(mRatio) || isNaN(mRate)) {
            isValid = false;
            showAlert('请填写完整的参数', 'error');
        } else if (sRatio + mRatio >= 100) {
            isValid = false;
            showAlert('优先级和夹层比例之和必须小于100%', 'error');
        }
        modeParams.senior_ratio = sRatio;
        modeParams.mezzanine_ratio = mRatio;
        modeParams.mezzanine_rate = mRate;
    }
    else if (AppState.mode === 'structured_interest_principal') {
        const sRatio = parseFloat($('#ipSeniorRatio').val());
        const subRate = parseFloat($('#ipSubordinateRate').val());
        
        if (isNaN(sRatio) || isNaN(subRate)) {
            isValid = false;
            showAlert('请填写完整的参数', 'error');
        }
        modeParams.senior_ratio = sRatio;
        modeParams.subordinate_rate = subRate;
    }
    
    if (!isValid) return;
    
    AppState.modeParams = modeParams;
    
    // 构建完整请求数据
    const payload = {
        basic_params: AppState.basicParams,
        cash_flows: AppState.cashFlows,
        mode: AppState.mode,
        ...modeParams
    };
    
    // 显示加载中
    disableInterface('正在计算收益分配...');
    
    // 发送请求
    $.ajax({
        url: '/api/calculate',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        success: function(response) {
            enableInterface();
            if (response.success) {
                // 保存结果
                AppState.calculationResult = response;
                // 渲染结果
                renderResults(response);
                // 切换到结果页
                showTab('results');
                showAlert('计算完成', 'success');
            } else {
                showAlert(response.message || '计算失败', 'error');
            }
        },
        error: function(xhr, status, error) {
            enableInterface();
            showAlert('服务器请求失败: ' + error, 'error');
        }
    });
}

/**
 * 渲染计算结果
 */
function renderResults(data) {
    // 渲染核心指标
    const metrics = data.core_metrics;
    let metricsHtml = '';
    
    // 定义指标显示顺序和样式
    const metricConfigs = [
        { key: 'irr', label: '内部收益率', icon: 'fa-chart-line' },
        { key: 'dpi', label: '分配倍数', icon: 'fa-percentage' },
        { key: 'static_payback_period', label: '静态回本周期', icon: 'fa-history' },
        { key: 'dynamic_payback_period', label: '动态回本周期', icon: 'fa-clock' }
    ];
    
    metricConfigs.forEach(conf => {
        const value = metrics[conf.key] || '-';
        metricsHtml += `
            <div class="metric-card">
                <div class="metric-label">${conf.label}</div>
                <div class="metric-value">${value}</div>
            </div>
        `;
    });
    
    $('#coreMetrics').html(metricsHtml);
    
    // 渲染现金流表格
    const tableData = data.cash_flow_table;
    const totals = data.totals;
    const tableContainer = $('#resultTableContainer');
    
    if (!tableData || tableData.length === 0) {
        tableContainer.html('<p class="text-center">无数据</p>');
        return;
    }
    
    // 获取表头（根据第一行数据推断，或后端返回）
    // 这里我们简单处理，直接使用数据中的键，或者硬编码映射
    // 实际上后端返回的数据已经是格式化好的字典列表
    
    // 定义列名映射
    const colMap = {
        'year': '年份',
        'net_cash_flow': '净现金流',
        'cash_flow_distribution_rate': '分派率',
        'beginning_principal_balance': '期初本金',
        'principal_repayment': '归还本金',
        'accrued_hurdle_return': '计提门槛收益',
        'distributed_hurdle_return': '分配门槛收益',
        'periodic_distribution': '期间分配',
        'senior_principal_repayment': '优先级还本',
        'subordinate_principal_repayment': '劣后级还本',
        'senior_periodic_return': '优先级收益',
        'subordinate_periodic_return': '劣后级收益',
        'senior_hurdle_distribution': '优先级收益',
        'mezzanine_hurdle_distribution': '夹层收益',
        'mezzanine_principal_repayment': '夹层还本',
        'carry_lp': 'Carry LP',
        'carry_gp': 'Carry GP'
    };
    
    // 获取所有存在的键（除了year）
    const keys = Object.keys(tableData[0]).filter(k => k !== 'year');
    
    let tableHtml = '<table class="result-table"><thead><tr>';
    tableHtml += '<th class="year-header">年份</th>';
    
    keys.forEach(key => {
        const label = colMap[key] || key;
        tableHtml += `<th>${label}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';
    
    // 数据行
    tableData.forEach(row => {
        tableHtml += '<tr>';
        tableHtml += `<td class="year-cell">${row.year}</td>`;
        keys.forEach(key => {
            tableHtml += `<td>${row[key]}</td>`;
        });
        tableHtml += '</tr>';
    });
    
    // 总计行
    if (totals) {
        tableHtml += '<tr class="total-row"><td class="total-label">总计</td>';
        keys.forEach(key => {
            const val = totals[key];
            if (val) {
                tableHtml += `<td class="total-value">${val}</td>`;
            } else {
                tableHtml += '<td class="total-dash">-</td>';
            }
        });
        tableHtml += '</tr>';
    }
    
    tableHtml += '</tbody></table>';
    tableContainer.html(tableHtml);
}

/**
 * 导出Excel
 */
function exportResults() {
    if (!AppState.calculationResult) {
        showAlert('没有可导出的结果', 'warning');
        return;
    }
    
    disableInterface('正在生成Excel...');
    
    $.ajax({
        url: '/api/export',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ results: AppState.calculationResult }),
        xhrFields: {
            responseType: 'blob'
        },
        success: function(blob) {
            enableInterface();
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = `收益分配测算结果_${new Date().getTime()}.xlsx`;
            link.click();
        },
        error: function() {
            enableInterface();
            showAlert('导出失败', 'error');
        }
    });
}

/**
 * 显示提示消息
 */
function showAlert(message, type = 'info') {
    const alertId = 'alert-' + Date.now();
    const iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const html = `
        <div id="${alertId}" class="alert ${type}">
            <i class="fas ${iconMap[type]}"></i>
            <span>${message}</span>
        </div>
    `;
    
    $('body').append(html);
    
    // 3秒后自动消失
    setTimeout(() => {
        $(`#${alertId}`).fadeOut(function() {
            $(this).remove();
        });
    }, 3000);
}

/**
 * 下载模板
 */
function downloadTemplate() {
    window.location.href = '/api/template';
}

/**
 * 导入Excel
 */
function importExcel() {
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    disableInterface('正在导入数据...');
    
    $.ajax({
        url: '/api/import',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            enableInterface();
            if (response.success) {
                const data = response.data;
                // 填充基本参数
                $('#investmentTarget').val(data.basic_params.investment_target);
                $('#investmentAmount').val(data.basic_params.investment_amount);
                $('#investmentPeriod').val(data.basic_params.investment_period);
                $('#hurdleRate').val(data.basic_params.hurdle_rate);
                $('#managementCarry').val(data.basic_params.management_carry);
                
                // 保存基本参数
                AppState.basicParams = data.basic_params;
                
                // 生成并填充现金流
                generateCashFlowInputs(data.basic_params.investment_period);
                data.cash_flows.forEach((val, idx) => {
                    $(`#cashFlow_${idx+1}`).val(val);
                });
                
                showAlert('数据导入成功', 'success');
            } else {
                showAlert(response.message, 'error');
            }
            // 清空文件输入，允许再次选择同一文件
            fileInput.value = '';
        },
        error: function(xhr) {
            enableInterface();
            showAlert('导入失败: ' + (xhr.responseJSON?.message || '服务器错误'), 'error');
            fileInput.value = '';
        }
    });
}

/**
 * 重置所有数据
 */
function resetAllData() {
    if (confirm('确定要重置所有数据吗？')) {
        // 重置前端状态
        AppState.basicParams = {};
        AppState.cashFlows = [];
        AppState.mode = '';
        AppState.modeParams = {};
        AppState.calculationResult = null;
        AppState.currentStep = 1;
        
        // 重置表单
        $('#basicParamsForm')[0].reset();
        $('#cashFlowInputs').empty();
        
        // 切换回第一步
        showTab('basic-params');
        
        // 调用后端重置（可选）
        $.post('/api/reset');
        
        showAlert('数据已重置', 'info');
    }
}

/**
 * 快速调整模块初始化
 */
function initQuickAdjustment() {
    $('#quickAdjustmentSwitch').change(function() {
        if ($(this).is(':checked')) {
            $('#quickAdjustmentPanel').slideDown();
        } else {
            $('#quickAdjustmentPanel').slideUp();
        }
    });
}

/**
 * 增加数值
 */
function incrementValue(id, step) {
    const input = $(`#${id}`);
    const currentVal = parseFloat(input.val()) || 0;
    input.val((currentVal + step).toFixed(2));
    updatePreview();
}

/**
 * 减少数值
 */
function decrementValue(id, step) {
    const input = $(`#${id}`);
    const currentVal = parseFloat(input.val()) || 0;
    const newVal = Math.max(0, currentVal - step);
    input.val(newVal.toFixed(2));
    updatePreview();
}

/**
 * 应用快速调整
 */
function applyQuickAdjustment() {
    const firstYear = parseFloat($('#firstYearCashFlow').val());
    const freq = parseInt($('#growthFrequency').val());
    const rate = parseFloat($('#growthRate').val());
    const years = parseInt($('#investmentPeriod').val());
    
    if (isNaN(firstYear) || isNaN(freq) || isNaN(rate) || isNaN(years)) {
        showAlert('请先设置有效的基本参数和调整参数', 'warning');
        return;
    }
    
    // 生成现金流输入框（如果还没生成）
    if ($('#cashFlowInputs').is(':empty')) {
        generateCashFlowInputs(years);
    }
    
    // 计算并填充
    let currentFlow = firstYear;
    for (let i = 1; i <= years; i++) {
        $(`#cashFlow_${i}`).val(currentFlow.toFixed(2));
        
        if (i % freq === 0) {
            currentFlow = currentFlow * (1 + rate / 100);
        }
    }
    
    // 关闭面板
    $('#quickAdjustmentSwitch').prop('checked', false).trigger('change');
    showAlert('现金流已自动生成', 'success');
}

/**
 * 更新预览（占位）
 */
function updatePreview() {
    // 实际实现略，视需求而定
}
