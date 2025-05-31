/**
 * 基金收益分配计算系统 - 工具函数库
 * @description 提供通用的工具函数和辅助方法
 * @author 基金计算系统团队
 * @version 1.0.0
 */

/**
 * 数字格式化工具类
 */
class NumberFormatter {
    /**
     * 格式化货币
     * @param {number} amount - 金额
     * @param {string} currency - 货币类型，默认CNY
     * @returns {string} 格式化后的货币字符串
     */
    static formatCurrency(amount, currency = 'CNY') {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    /**
     * 格式化百分比
     * @param {number} value - 数值（以百分比形式，如15表示15%）
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的百分比字符串
     */
    static formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    }

    /**
     * 格式化普通数字
     * @param {number} value - 数值
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的数字字符串
     */
    static formatNumber(value, decimals = 2) {
        return new Intl.NumberFormat('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    /**
     * 解析货币字符串为数字
     * @param {string} currencyStr - 货币字符串
     * @returns {number} 数值
     */
    static parseCurrency(currencyStr) {
        // 移除货币符号和千位分隔符
        const cleaned = currencyStr.replace(/[￥¥$,\s]/g, '');
        return parseFloat(cleaned) || 0;
    }
}

/**
 * 日期处理工具类
 */
class DateUtils {
    /**
     * 格式化日期为字符串
     * @param {Date|string} date - 日期对象或字符串
     * @param {string} format - 格式类型 ('YYYY-MM-DD', 'YYYY/MM/DD', 'MM/DD/YYYY')
     * @returns {string} 格式化后的日期字符串
     */
    static formatDate(date, format = 'YYYY-MM-DD') {
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');

        switch (format) {
            case 'YYYY-MM-DD':
                return `${year}-${month}-${day}`;
            case 'YYYY/MM/DD':
                return `${year}/${month}/${day}`;
            case 'MM/DD/YYYY':
                return `${month}/${day}/${year}`;
            case 'DD/MM/YYYY':
                return `${day}/${month}/${year}`;
            default:
                return `${year}-${month}-${day}`;
        }
    }

    /**
     * 计算两个日期之间的天数差
     * @param {Date|string} startDate - 开始日期
     * @param {Date|string} endDate - 结束日期
     * @returns {number} 天数差
     */
    static daysBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end - start);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    /**
     * 计算年份差（用于IRR计算）
     * @param {Date|string} startDate - 开始日期
     * @param {Date|string} endDate - 结束日期
     * @returns {number} 年份差
     */
    static yearsBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        return (end - start) / (1000 * 60 * 60 * 24 * 365.25);
    }

    /**
     * 获取当前日期字符串
     * @param {string} format - 格式类型
     * @returns {string} 当前日期字符串
     */
    static now(format = 'YYYY-MM-DD') {
        return this.formatDate(new Date(), format);
    }
}

/**
 * 数据验证工具类
 */
class Validator {
    /**
     * 验证是否为有效的数字
     * @param {any} value - 待验证的值
     * @param {number} min - 最小值
     * @param {number} max - 最大值
     * @returns {boolean} 验证结果
     */
    static isValidNumber(value, min = -Infinity, max = Infinity) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    }

    /**
     * 验证是否为有效的日期
     * @param {any} value - 待验证的值
     * @returns {boolean} 验证结果
     */
    static isValidDate(value) {
        const date = new Date(value);
        return !isNaN(date.getTime());
    }

    /**
     * 验证是否为有效的百分比
     * @param {any} value - 待验证的值
     * @param {number} min - 最小百分比（如0表示0%）
     * @param {number} max - 最大百分比（如100表示100%）
     * @returns {boolean} 验证结果
     */
    static isValidPercentage(value, min = 0, max = 100) {
        return this.isValidNumber(value, min, max);
    }

    /**
     * 验证是否为非空字符串
     * @param {any} value - 待验证的值
     * @returns {boolean} 验证结果
     */
    static isNonEmptyString(value) {
        return typeof value === 'string' && value.trim().length > 0;
    }

    /**
     * 验证邮箱格式
     * @param {string} email - 邮箱地址
     * @returns {boolean} 验证结果
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
}

/**
 * 本地存储工具类
 */
class StorageUtils {
    /**
     * 保存数据到本地存储
     * @param {string} key - 键名
     * @param {any} value - 值
     */
    static save(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn('保存到本地存储失败:', error);
        }
    }

    /**
     * 从本地存储读取数据
     * @param {string} key - 键名
     * @param {any} defaultValue - 默认值
     * @returns {any} 读取的值
     */
    static load(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('从本地存储读取失败:', error);
            return defaultValue;
        }
    }

    /**
     * 删除本地存储中的数据
     * @param {string} key - 键名
     */
    static remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn('删除本地存储失败:', error);
        }
    }

    /**
     * 清空所有本地存储
     */
    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.warn('清空本地存储失败:', error);
        }
    }
}

/**
 * Excel处理工具类
 */
class ExcelUtils {
    /**
     * 下载数据为Excel文件
     * @param {Array} data - 数据数组
     * @param {string} filename - 文件名
     * @param {string} sheetName - 工作表名称
     */
    static downloadAsExcel(data, filename = 'data.xlsx', sheetName = 'Sheet1') {
        // 创建工作簿和工作表
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);
        
        // 添加工作表到工作簿
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
        
        // 下载文件
        XLSX.writeFile(wb, filename);
    }

    /**
     * 读取Excel文件
     * @param {File} file - Excel文件
     * @returns {Promise<Object>} 解析结果
     */
    static readExcelFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                try {
                    const data = e.target.result;
                    const workbook = XLSX.read(data, { type: 'binary' });
                    
                    const result = {};
                    workbook.SheetNames.forEach(sheetName => {
                        result[sheetName] = XLSX.utils.sheet_to_json(
                            workbook.Sheets[sheetName],
                            { header: 1 }
                        );
                    });
                    
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = function(error) {
                reject(error);
            };
            
            reader.readAsBinaryString(file);
        });
    }
}

/**
 * URL工具类
 */
class UrlUtils {
    /**
     * 获取URL参数
     * @param {string} name - 参数名
     * @returns {string|null} 参数值
     */
    static getParam(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    /**
     * 设置URL参数
     * @param {string} name - 参数名
     * @param {string} value - 参数值
     */
    static setParam(name, value) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        window.history.replaceState({}, '', url);
    }

    /**
     * 删除URL参数
     * @param {string} name - 参数名
     */
    static removeParam(name) {
        const url = new URL(window.location);
        url.searchParams.delete(name);
        window.history.replaceState({}, '', url);
    }
}

/**
 * 通用工具函数
 */
class Utils {
    /**
     * 深拷贝对象
     * @param {any} obj - 待拷贝的对象
     * @returns {any} 拷贝后的对象
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} 防抖后的函数
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 限制时间（毫秒）
     * @returns {Function} 节流后的函数
     */
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 生成UUID
     * @returns {string} UUID字符串
     */
    static generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 下载文件
     * @param {string} content - 文件内容
     * @param {string} filename - 文件名
     * @param {string} mimeType - MIME类型
     */
    static downloadFile(content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise<boolean>} 复制结果
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            // 降级方案
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                return true;
            } catch (fallbackError) {
                console.error('复制到剪贴板失败:', fallbackError);
                return false;
            }
        }
    }
}

/**
 * 财务计算工具类
 */
class FinanceUtils {
    /**
     * 计算IRR（内部收益率）- 牛顿法
     * @param {Array} cashFlows - 现金流数组 [{date, amount}]
     * @param {number} guess - 初始猜测值
     * @param {number} tolerance - 容错范围
     * @param {number} maxIterations - 最大迭代次数
     * @returns {number} IRR值（百分比）
     */
    static calculateIRR(cashFlows, guess = 0.1, tolerance = 0.0001, maxIterations = 100) {
        if (cashFlows.length < 2) return 0;

        // 按日期排序
        const sortedFlows = cashFlows.sort((a, b) => new Date(a.date) - new Date(b.date));
        const startDate = new Date(sortedFlows[0].date);

        // 计算每个现金流的时间差（年）
        const flows = sortedFlows.map(flow => ({
            amount: flow.amount,
            years: DateUtils.yearsBetween(startDate, flow.date)
        }));

        let rate = guess;
        
        for (let i = 0; i < maxIterations; i++) {
            const npv = this.calculateNPV(flows, rate);
            const dnpv = this.calculateDerivativeNPV(flows, rate);
            
            if (Math.abs(npv) < tolerance) {
                return rate * 100; // 转换为百分比
            }
            
            if (dnpv === 0) break;
            
            rate = rate - npv / dnpv;
        }
        
        return rate * 100; // 转换为百分比
    }

    /**
     * 计算NPV（净现值）
     * @param {Array} flows - 现金流数组
     * @param {number} rate - 折现率
     * @returns {number} NPV值
     */
    static calculateNPV(flows, rate) {
        return flows.reduce((npv, flow) => {
            return npv + flow.amount / Math.pow(1 + rate, flow.years);
        }, 0);
    }

    /**
     * 计算NPV的导数
     * @param {Array} flows - 现金流数组
     * @param {number} rate - 折现率
     * @returns {number} 导数值
     */
    static calculateDerivativeNPV(flows, rate) {
        return flows.reduce((derivative, flow) => {
            return derivative - flow.years * flow.amount / Math.pow(1 + rate, flow.years + 1);
        }, 0);
    }

    /**
     * 计算DPI（投资分配倍数）
     * @param {number} totalDistributions - 总分配金额
     * @param {number} totalInvestments - 总投资金额
     * @returns {number} DPI值
     */
    static calculateDPI(totalDistributions, totalInvestments) {
        if (totalInvestments === 0) return 0;
        return totalDistributions / totalInvestments;
    }

    /**
     * 计算年化收益率
     * @param {number} startValue - 初始值
     * @param {number} endValue - 结束值
     * @param {number} years - 年数
     * @returns {number} 年化收益率（百分比）
     */
    static calculateAnnualizedReturn(startValue, endValue, years) {
        if (startValue === 0 || years === 0) return 0;
        return (Math.pow(endValue / startValue, 1 / years) - 1) * 100;
    }
}

// 全局暴露工具类
window.NumberFormatter = NumberFormatter;
window.DateUtils = DateUtils;
window.Validator = Validator;
window.StorageUtils = StorageUtils;
window.ExcelUtils = ExcelUtils;
window.UrlUtils = UrlUtils;
window.Utils = Utils;
window.FinanceUtils = FinanceUtils;

// 向后兼容：全局函数
window.formatCurrency = NumberFormatter.formatCurrency;
window.formatPercentage = NumberFormatter.formatPercentage;
window.formatNumber = NumberFormatter.formatNumber; 