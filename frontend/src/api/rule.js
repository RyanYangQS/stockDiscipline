/**
 * 规则相关API
 */
import api from './index'

/**
 * 获取系统规则
 * @returns {Promise}
 */
export function getSystemRules() {
  return api.get('/rule/system')
}

/**
 * 获取自定义规则
 * @returns {Promise}
 */
export function getCustomRules() {
  return api.get('/rule/custom')
}

/**
 * 创建规则
 * @param {Object} data - 规则数据
 * @returns {Promise}
 */
export function createRule(data) {
  return api.post('/rule/create', data)
}

/**
 * 切换规则状态
 * @param {number} id - 规则ID
 * @returns {Promise}
 */
export function toggleRule(id) {
  return api.put(`/rule/${id}/toggle`)
}

/**
 * 删除规则
 * @param {number} id - 规则ID
 * @returns {Promise}
 */
export function deleteRule(id) {
  return api.delete(`/rule/${id}`)
}
