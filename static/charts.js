/**
 * 基金收益分配计算系统 - 图表模块
 * 提供简化的图表初始化和管理功能
 */

// 确保Chart.js加载完成后再执行
document.addEventListener('DOMContentLoaded', function() {
    // 基本的图表初始化
    console.log('图表模块已加载');
    
    // 如果Chart.js存在，进行基本配置
    if (typeof Chart !== 'undefined') {
        // 设置Chart.js默认配置
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        
        console.log('Chart.js配置完成');
    } else {
        console.warn('Chart.js未加载，图表功能可能不可用');
    }
});

/**
 * 创建现金流图表
 * @param {Array} cashFlowData - 现金流数据（后端已格式化）
 */
function createCashFlowChart(cashFlowData) {
    const ctx = document.getElementById('cashFlowChart');
    if (!ctx || !cashFlowData) return;
    
    // 使用原始数值用于图表显示
    const years = cashFlowData.map(item => `第${item.year}年`);
    const values = cashFlowData.map(item => item.net_cash_flow || 0);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: '净现金流',
                data: values,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '现金流分布图'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '金额（万元）'
                    }
                }
            }
        }
    });
}

/**
 * 创建指标图表
 * @param {Object} metrics - 指标数据（后端已格式化）
 */
function createMetricsChart(metrics) {
    const ctx = document.getElementById('metricsChart');
    if (!ctx || !metrics) return;
    
    // 使用原始数值用于图表显示
    const data = [
        metrics.irr || 0,
        metrics.dpi || 0,
        (metrics.net_profit && metrics.total_investment) ? 
            (metrics.net_profit / metrics.total_investment) * 100 : 0
    ];
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['IRR (%)', 'DPI', '净收益率 (%)'],
            datasets: [{
                label: '投资收益指标',
                data: data,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '投资收益指标雷达图'
                }
            },
            scales: {
                r: {
                    beginAtZero: true
                }
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
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
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
                    backgroundColor: 'rgba(255, 206, 86, 0.6)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1
                },
                {
                    label: 'LP分配',
                    data: lpData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
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
    redrawAllCharts,
    getChart: function(canvasId) {
        return window.chartInstances ? window.chartInstances[canvasId] : null;
    }
}; 