/**
 * 持仓相关API
 */
import api from './index'

/**
 * 获取持仓列表
 * @returns {Promise}
 */
export function getPositions() {
  return api.get('/position/list')
}

/**
 * 创建持仓
 * @param {Object} data - 持仓数据
 * @returns {Promise}
 */
export function createPosition(data) {
  return api.post('/position/create', data)
}

/**
 * 删除持仓
 * @param {number} id - 持仓ID
 * @returns {Promise}
 */
export function deletePosition(id) {
  return api.delete(`/position/${id}`)
}
