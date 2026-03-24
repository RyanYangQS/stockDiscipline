/**
 * 股票状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { screenStocks, getKlineData, getRealtimeQuote, getMarketOverview } from '@/api/stock'

export const useStockStore = defineStore('stock', () => {
  // 状态
  const currentStock = ref({
    code: '000001',
    name: '平安银行',
    price: 12.85,
    change_pct: 5.23
  })
  
  const stockPool = ref([])
  const klineData = ref([])
  const marketOverview = ref({
    up_count: 0,
    down_count: 0,
    total_count: 0
  })
  
  const loading = ref(false)
  const error = ref(null)
  
  // 计算属性
  const priceClass = computed(() => {
    return currentStock.value.change_pct >= 0 ? 'up' : 'down'
  })
  
  const changeText = computed(() => {
    const change = currentStock.value.change_pct || 0
    return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`
  })
  
  // 方法
  const setCurrentStock = (stock) => {
    currentStock.value = { ...currentStock.value, ...stock }
  }
  
  const fetchStockPool = async (params) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await screenStocks(params)
      stockPool.value = data.items || []
      return stockPool.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }
  
  const fetchKlineData = async (code, period = 'daily', count = 60) => {
    try {
      const data = await getKlineData(code, period, count)
      klineData.value = data.data || []
      return klineData.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  const fetchRealtimeQuote = async (code) => {
    try {
      const data = await getRealtimeQuote(code)
      if (data) {
        currentStock.value = {
          code: data.code,
          name: data.name,
          price: data.price,
          change_pct: data.change_pct
        }
      }
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  const fetchMarketOverview = async () => {
    try {
      const data = await getMarketOverview()
      marketOverview.value = data
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }
  
  return {
    // 状态
    currentStock,
    stockPool,
    klineData,
    marketOverview,
    loading,
    error,
    
    // 计算属性
    priceClass,
    changeText,
    
    // 方法
    setCurrentStock,
    fetchStockPool,
    fetchKlineData,
    fetchRealtimeQuote,
    fetchMarketOverview
  }
})
