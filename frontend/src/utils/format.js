/**
 * 格式化工具函数
 */
import dayjs from 'dayjs'

/**
 * 格式化价格
 * @param {number} price - 价格
 * @param {number} decimals - 小数位数
 * @returns {string}
 */
export function formatPrice(price, decimals = 2) {
  if (price === null || price === undefined) return '--'
  return price.toFixed(decimals)
}

/**
 * 格式化涨跌幅
 * @param {number} change - 涨跌幅
 * @returns {string}
 */
export function formatChange(change) {
  if (change === null || change === undefined) return '--'
  const prefix = change >= 0 ? '+' : ''
  return `${prefix}${change.toFixed(2)}%`
}

/**
 * 格式化成交量
 * @param {number} volume - 成交量
 * @returns {string}
 */
export function formatVolume(volume) {
  if (volume === null || volume === undefined) return '--'
  
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`
  }
  return volume.toString()
}

/**
 * 格式化金额
 * @param {number} amount - 金额
 * @returns {string}
 */
export function formatAmount(amount) {
  if (amount === null || amount === undefined) return '--'
  
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`
  }
  return amount.toFixed(2)
}

/**
 * 格式化日期
 * @param {Date|string|number} date - 日期
 * @param {string} format - 格式
 * @returns {string}
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '--'
  return dayjs(date).format(format)
}

/**
 * 格式化时间
 * @param {Date|string|number} date - 日期
 * @returns {string}
 */
export function formatTime(date) {
  if (!date) return '--'
  return dayjs(date).format('HH:mm:ss')
}

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期
 * @returns {string}
 */
export function formatDateTime(date) {
  if (!date) return '--'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 获取价格样式类
 * @param {number} change - 涨跌幅
 * @returns {string}
 */
export function getPriceClass(change) {
  if (change > 0) return 'up'
  if (change < 0) return 'down'
  return 'flat'
}

/**
 * 获取信号优先级样式类
 * @param {string} priority - 优先级
 * @returns {string}
 */
export function getPriorityClass(priority) {
  const map = {
    'HIGH': 'danger',
    'MEDIUM': 'warning',
    'LOW': 'info'
  }
  return map[priority] || 'info'
}

/**
 * 获取信号优先级文本
 * @param {string} priority - 优先级
 * @returns {string}
 */
export function getPriorityText(priority) {
  const map = {
    'HIGH': '高优先级',
    'MEDIUM': '建议',
    'LOW': '参考'
  }
  return map[priority] || priority
}
