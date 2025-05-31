/**
 * 基金收益分配计算系统 - 图表模块
 * @description 使用Chart.js处理数据可视化功能
 * @author 基金计算系统团队
 * @version 1.0.0
 */

/**
 * 安全的toFixed函数，防止NaN错误
 */
function safeToFixed(value, digits = 2) {
    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
        return '0.' + '0'.repeat(digits);
    }
    return value.toFixed(digits);
}

/**
 * 安全计算百分比，防止除零错误
 */
function safeCalculatePercentage(numerator, denominator) {
    if (typeof numerator !== 'number' || isNaN(numerator) || !isFinite(numerator)) {
        return 0;
    }
    if (typeof denominator !== 'number' || isNaN(denominator) || !isFinite(denominator) || denominator === 0) {
        return 0;
    }
    const result = (numerator / denominator) * 100;
    return isNaN(result) || !isFinite(result) ? 0 : result;
}

/**
 * 全局图表配置
 */
const CHART_CONFIG = {
    // 默认颜色主题
    colors: {
        primary: '#0d6efd',
        success: '#198754',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0',
        secondary: '#6c757d',
        light: '#f8f9fa',
        dark: '#212529'
    },
    
    // 字体配置
    font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 12
    },
    
    // 动画配置
    animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
    }
};

/**
 * 创建现金流趋势图
 * @param {Array} cashFlows - 现金流数据
 */
function createCashFlowChart(cashFlows) {
    const ctx = document.getElementById('cashFlowChart').getContext('2d');
    
    // 处理数据
    const processedData = processCashFlowData(cashFlows);
    
    // 销毁之前的图表实例
    if (window.cashFlowChartInstance) {
        window.cashFlowChartInstance.destroy();
    }
    
    // 创建新图表
    window.cashFlowChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: processedData.labels,
            datasets: [
                {
                    label: '累计投资',
                    data: processedData.cumulativeInvestment,
                    borderColor: CHART_CONFIG.colors.danger,
                    backgroundColor: CHART_CONFIG.colors.danger + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4
                },
                {
                    label: '累计回收',
                    data: processedData.cumulativeReturn,
                    borderColor: CHART_CONFIG.colors.success,
                    backgroundColor: CHART_CONFIG.colors.success + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4
                },
                {
                    label: '净现金流',
                    data: processedData.netCashFlow,
                    borderColor: CHART_CONFIG.colors.primary,
                    backgroundColor: CHART_CONFIG.colors.primary + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: CHART_CONFIG.animation,
            plugins: {
                title: {
                    display: true,
                    text: '现金流趋势分析',
                    font: {
                        size: 16,
                        weight: 'bold',
                        family: CHART_CONFIG.font.family
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: CHART_CONFIG.colors.dark,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: CHART_CONFIG.colors.primary,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const value = formatCurrency(context.parsed.y);
                            return `${context.dataset.label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '时间',
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: CHART_CONFIG.colors.light
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '金额 (万元)',
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: CHART_CONFIG.colors.light
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * 创建分配比例饼图
 * @param {Array} distributions - 分配数据
 */
function createDistributionPieChart(distributions) {
    const ctx = document.getElementById('distributionPieChart').getContext('2d');
    
    // 计算总分配金额
    const totalGP = distributions.reduce((sum, dist) => sum + dist.gp_distribution, 0);
    const totalLP = distributions.reduce((sum, dist) => sum + dist.lp_distribution, 0);
    
    // 销毁之前的图表实例
    if (window.distributionPieChartInstance) {
        window.distributionPieChartInstance.destroy();
    }
    
    // 创建新图表
    window.distributionPieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['GP分配', 'LP分配'],
            datasets: [{
                data: [totalGP, totalLP],
                backgroundColor: [
                    CHART_CONFIG.colors.warning,
                    CHART_CONFIG.colors.success
                ],
                borderColor: [
                    CHART_CONFIG.colors.warning,
                    CHART_CONFIG.colors.success
                ],
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: CHART_CONFIG.animation,
            plugins: {
                title: {
                    display: true,
                    text: '收益分配比例',
                    font: {
                        size: 16,
                        weight: 'bold',
                        family: CHART_CONFIG.font.family
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size
                        }
                    }
                },
                tooltip: {
                    backgroundColor: CHART_CONFIG.colors.dark,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: CHART_CONFIG.colors.primary,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const value = formatCurrency(context.parsed);
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = safeToFixed(safeCalculatePercentage(context.parsed, total), 1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * 创建收益率对比柱状图
 * @param {Object} metrics - 计算指标
 */
function createMetricsChart(metrics) {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    
    // 销毁之前的图表实例
    if (window.metricsChartInstance) {
        window.metricsChartInstance.destroy();
    }
    
    // 创建新图表
    window.metricsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['IRR (%)', 'DPI', '净收益率 (%)'],
            datasets: [{
                label: '投资指标',
                data: [
                    metrics.irr || 0,
                    metrics.dpi || 0,
                    safeCalculatePercentage(metrics.net_profit, metrics.total_investment)
                ],
                backgroundColor: [
                    CHART_CONFIG.colors.primary + '80',
                    CHART_CONFIG.colors.success + '80',
                    CHART_CONFIG.colors.info + '80'
                ],
                borderColor: [
                    CHART_CONFIG.colors.primary,
                    CHART_CONFIG.colors.success,
                    CHART_CONFIG.colors.info
                ],
                borderWidth: 2,
                borderRadius: 5,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: CHART_CONFIG.animation,
            plugins: {
                title: {
                    display: true,
                    text: '投资业绩指标',
                    font: {
                        size: 16,
                        weight: 'bold',
                        family: CHART_CONFIG.font.family
                    },
                    padding: 20
                },
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: CHART_CONFIG.colors.dark,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: CHART_CONFIG.colors.primary,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let value = context.parsed.y;
                            if (context.dataIndex === 0 || context.dataIndex === 2) {
                                // IRR和净收益率显示为百分比
                                return `${context.label}: ${safeToFixed(value, 2)}%`;
                            } else {
                                // DPI显示为倍数
                                return `${context.label}: ${safeToFixed(value, 2)}x`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: CHART_CONFIG.colors.light
                    },
                    ticks: {
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size
                        }
                    }
                }
            }
        }
    });
}

/**
 * 创建时间序列分配图
 * @param {Array} distributions - 分配明细数据
 */
function createTimeSeriesDistributionChart(distributions) {
    const ctx = document.getElementById('timeSeriesChart').getContext('2d');
    
    // 销毁之前的图表实例
    if (window.timeSeriesChartInstance) {
        window.timeSeriesChartInstance.destroy();
    }
    
    // 处理数据
    const labels = distributions.map((_, index) => `第${index + 1}期`);
    const gpData = distributions.map(dist => dist.gp_distribution);
    const lpData = distributions.map(dist => dist.lp_distribution);
    
    // 创建新图表
    window.timeSeriesChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'GP分配',
                    data: gpData,
                    backgroundColor: CHART_CONFIG.colors.warning + '80',
                    borderColor: CHART_CONFIG.colors.warning,
                    borderWidth: 2
                },
                {
                    label: 'LP分配',
                    data: lpData,
                    backgroundColor: CHART_CONFIG.colors.success + '80',
                    borderColor: CHART_CONFIG.colors.success,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: CHART_CONFIG.animation,
            plugins: {
                title: {
                    display: true,
                    text: '分期收益分配明细',
                    font: {
                        size: 16,
                        weight: 'bold',
                        family: CHART_CONFIG.font.family
                    },
                    padding: 20
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size
                        }
                    }
                },
                tooltip: {
                    backgroundColor: CHART_CONFIG.colors.dark,
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: CHART_CONFIG.colors.primary,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const value = formatCurrency(context.parsed.y);
                            return `${context.dataset.label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '分配期间',
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '分配金额 (万元)',
                        font: {
                            family: CHART_CONFIG.font.family,
                            size: CHART_CONFIG.font.size,
                            weight: 'bold'
                        }
                    },
                    beginAtZero: true,
                    grid: {
                        color: CHART_CONFIG.colors.light
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

/**
 * 处理现金流数据用于图表显示
 * @param {Array} cashFlows - 原始现金流数据
 * @returns {Object} 处理后的图表数据
 */
function processCashFlowData(cashFlows) {
    // 按日期排序
    const sortedFlows = cashFlows.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const labels = [];
    const cumulativeInvestment = [];
    const cumulativeReturn = [];
    const netCashFlow = [];
    
    let totalInvestment = 0;
    let totalReturn = 0;
    
    sortedFlows.forEach(flow => {
        // 格式化日期标签
        const date = new Date(flow.date);
        const formattedDate = date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
        labels.push(formattedDate);
        
        // 累计投资和回收
        if (flow.type === 'investment' || flow.type === 'capital_call') {
            totalInvestment += flow.amount;
        } else if (flow.type === 'distribution' || flow.type === 'exit') {
            totalReturn += flow.amount;
        }
        
        cumulativeInvestment.push(totalInvestment);
        cumulativeReturn.push(totalReturn);
        netCashFlow.push(totalReturn - totalInvestment);
    });
    
    return {
        labels,
        cumulativeInvestment,
        cumulativeReturn,
        netCashFlow
    };
}

/**
 * 销毁所有图表实例
 */
function destroyAllCharts() {
    const chartInstances = [
        'cashFlowChartInstance',
        'distributionPieChartInstance',
        'metricsChartInstance',
        'timeSeriesChartInstance'
    ];
    
    chartInstances.forEach(instanceName => {
        if (window[instanceName]) {
            window[instanceName].destroy();
            window[instanceName] = null;
        }
    });
}

/**
 * 导出图表为图片
 * @param {string} chartId - 图表ID
 * @param {string} filename - 文件名
 */
function exportChartAsImage(chartId, filename = 'chart.png') {
    const canvas = document.getElementById(chartId);
    if (canvas) {
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        link.click();
    }
}

/**
 * 更新图表主题
 * @param {string} theme - 主题名称 ('light' 或 'dark')
 */
function updateChartTheme(theme) {
    if (theme === 'dark') {
        CHART_CONFIG.colors.light = '#495057';
        CHART_CONFIG.colors.dark = '#212529';
    } else {
        CHART_CONFIG.colors.light = '#f8f9fa';
        CHART_CONFIG.colors.dark = '#212529';
    }
    
    // 重新绘制所有图表
    redrawAllCharts();
}

/**
 * 重新绘制所有图表
 */
function redrawAllCharts() {
    if (calculationResult) {
        if (calculationResult.cash_flows) {
            createCashFlowChart(calculationResult.cash_flows);
        }
        if (calculationResult.distributions) {
            createDistributionPieChart(calculationResult.distributions);
            createTimeSeriesDistributionChart(calculationResult.distributions);
        }
        if (calculationResult.metrics) {
            createMetricsChart(calculationResult.metrics);
        }
    }
}

// 全局暴露图表函数
window.ChartUtils = {
    createCashFlowChart,
    createDistributionPieChart,
    createMetricsChart,
    createTimeSeriesDistributionChart,
    destroyAllCharts,
    exportChartAsImage,
    updateChartTheme,
    redrawAllCharts
}; 