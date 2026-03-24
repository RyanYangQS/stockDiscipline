/**
 * 股票相关API
 */
import api from './index'

/**
 * 执行选股
 * @param {Object} params - 选股参数
 * @returns {Promise}
 */
export function screenStocks(params) {
  return api.post('/stock/screening', params)
}

/**
 * 获取K线数据
 * @param {string} code - 股票代码
 * @param {string} period - 周期
 * @param {number} count - 数据条数
 * @returns {Promise}
 */
export function getKlineData(code, period = 'daily', count = 60) {
  return api.get(`/stock/kline/${code}`, {
    params: { period, count }
  })
}

/**
 * 获取实时行情
 * @param {string} code - 股票代码
 * @returns {Promise}
 */
export function getRealtimeQuote(code) {
  return api.get(`/stock/realtime/${code}`)
}

/**
 * 获取市场概览
 * @returns {Promise}
 */
export function getMarketOverview() {
  return api.get('/stock/market/overview')
}
