/**
 * 持仓状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getPositions, createPosition, deletePosition } from '@/api/position'

export const usePositionStore = defineStore('position', () => {
  // 状态
  const positions = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  // 计算属性
  const totalProfit = computed(() => {
    return positions.value.reduce((sum, p) => sum + (p.profit || 0), 0)
  })
  
  const positionCount = computed(() => {
    return positions.value.length
  })
  
  const hasPosition = computed(() => {
    return positions.value.length > 0
  })
  
  // 方法
  const fetchPositions = async () => {
    loading.value = true
    error.value = null
    
    try {
      const data = await getPositions()
      positions.value = data || []
      return positions.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }
  
  const addPosition = async (positionData) => {
    try {
      const data = await createPosition(positionData)
      positions.value.push(data)
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  const removePosition = async (id) => {
    try {
      await deletePosition(id)
      positions.value = positions.value.filter(p => p.id !== id)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  const updatePositionPrice = (code, currentPrice) => {
    const position = positions.value.find(p => p.stock_code === code)
    if (position) {
      position.current_price = currentPrice
      position.profit = (currentPrice - position.cost_price) * position.quantity
      position.profit_pct = ((currentPrice - position.cost_price) / position.cost_price) * 100
    }
  }
  
  return {
    // 状态
    positions,
    loading,
    error,
    
    // 计算属性
    totalProfit,
    positionCount,
    hasPosition,
    
    // 方法
    fetchPositions,
    addPosition,
    removePosition,
    updatePositionPrice
  }
})
