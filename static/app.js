/**
 * 基金收益分配计算系统 - 主要应用逻辑（简化版）
 * 所有数据格式化现在由后端负责，前端只处理用户交互和数据传递
 */

// 全局变量
let currentStep = 1;

/**
 * 安全解析浮点数，防止NaN - 仅用于表单输入验证
 */
function safeParseFloat(value, defaultValue = 0) {
    if (value === null || value === undefined || value === '') {
        return defaultValue;
    }
    const parsed = parseFloat(value);
    return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * 安全解析整数，防止NaN - 仅用于表单输入验证
 */
function safeParseInt(value, defaultValue = 0) {
    if (value === null || value === undefined || value === '') {
        return defaultValue;
    }
    const parsed = parseInt(value);
    return isNaN(parsed) ? defaultValue : parsed;
}

$(document).ready(function() {
    console.log('应用初始化完成 - 简化版');
    
    // 基本的事件绑定
    $('.btn-primary').click(function(e) {
        e.preventDefault();
        const action = $(this).data('action');
        if (action) {
            window[action]();
        }
    });
    
    // 步骤导航
    $('.nav-link').click(function(e) {
        e.preventDefault();
        const targetStep = safeParseInt($(this).data('step'));
        if (targetStep <= currentStep) {
            showStep(targetStep);
        }
    });
});

/**
 * 显示指定步骤
 */
function showStep(stepNum) {
    currentStep = stepNum;
    $('.step-content').hide();
    $(`#step-${stepNum}`).show();
    
    // 更新导航状态
    $('.nav-link').each(function() {
        const stepNumber = safeParseInt($(this).data('step'));
        if (stepNumber <= currentStep) {
            $(this).removeClass('disabled').prop('disabled', false);
        } else {
            $(this).addClass('disabled').prop('disabled', true);
        }
    });
} 