<template>
  <div class="trade-panel">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">📈</span>
          <span class="logo-text">股票交易纪律系统</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-btn" :class="{ active: $route.path === '/' }">
            📊 交易面板
          </router-link>
          <router-link to="/screening" class="nav-btn">
            🎯 AI选股
          </router-link>
          <router-link to="/rules" class="nav-btn">
            📋 规则配置
          </router-link>
        </nav>
      </div>
      <div class="header-right">
        <div class="market-status">
          <span>市场</span>
          <span class="up">↑ {{ marketOverview.up_count }}</span>
          <span class="down">↓ {{ marketOverview.down_count }}</span>
        </div>
        <div class="time">{{ currentTime }}</div>
        <div :class="['open-status', canOpen ? 'can' : 'cannot']">
          {{ canOpen ? '可开仓' : '禁止开仓' }}
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- K线图区域 -->
      <section class="kline-section">
        <div class="stock-header">
          <div class="stock-info">
            <span class="stock-name">{{ currentStock.name }}</span>
            <span class="stock-code">{{ currentStock.code }}</span>
            <span :class="['stock-price', priceClass]">{{ currentStock.price?.toFixed(2) }}</span>
            <span :class="['stock-change', priceClass]">
              {{ changeText }}
            </span>
          </div>
          <el-button type="primary" size="small">切换股票</el-button>
        </div>
        
        <div class="kline-tabs">
          <el-radio-group v-model="period" size="small" @change="loadKline">
            <el-radio-button label="daily">日K</el-radio-button>
            <el-radio-button label="weekly">周K</el-radio-button>
            <el-radio-button label="minute">分时</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="kline-container">
          <div ref="chartRef" class="chart"></div>
        </div>
      </section>

      <!-- 右侧面板 -->
      <aside class="right-panel">
        <!-- 功能入口 -->
        <div class="entry-cards">
          <router-link to="/screening" class="entry-card">
            <div class="entry-icon">🎯</div>
            <div class="entry-title">AI选股</div>
            <div class="entry-sub">智能筛选标的</div>
          </router-link>
          <router-link to="/rules" class="entry-card">
            <div class="entry-icon">📋</div>
            <div class="entry-title">规则配置</div>
            <div class="entry-sub">自定义规则</div>
          </router-link>
        </div>

        <!-- 买卖信号 -->
        <div class="panel">
          <div class="panel-title">📋 买卖信号</div>
          <div v-for="signal in buySignals" :key="signal.id" class="signal-item buy" @click="showSignalDetail(signal)">
            <div class="signal-type">🟢 {{ signal.signal_name }}</div>
            <div class="signal-detail">{{ signal.reason }}</div>
            <div class="signal-price">建议价: ¥{{ signal.price?.toFixed(2) }}</div>
          </div>
          <div v-for="signal in sellSignals" :key="signal.id" class="signal-item sell" @click="showSignalDetail(signal)">
            <div class="signal-type">⚠️ {{ signal.signal_name }}</div>
            <div class="signal-detail">{{ signal.reason }}</div>
            <div class="signal-price">触发价: ¥{{ signal.price?.toFixed(2) }}</div>
          </div>
          <div v-if="buySignals.length === 0 && sellSignals.length === 0" class="empty">
            <div class="empty-icon">📊</div>
            <div>暂无信号</div>
          </div>
        </div>

        <!-- 选股池 -->
        <div class="panel">
          <div class="panel-title">🎯 今日选股池</div>
          <div class="pool-tags">
            <el-tag 
              v-for="tag in poolTags" 
              :key="tag" 
              :type="activeTag === tag ? 'primary' : 'info'" 
              size="small"
              @click="activeTag = tag"
            >
              {{ tag }}
            </el-tag>
          </div>
          <div 
            v-for="stock in filteredPool" 
            :key="stock.code" 
            class="pool-item"
            @click="selectStock(stock)"
          >
            <div class="pool-info">
              <div class="pool-name">{{ stock.name }}</div>
              <div class="pool-code">{{ stock.code }}</div>
            </div>
            <div class="pool-right">
              <span class="pool-signal">{{ stock.signal_type }}</span>
              <div class="pool-score">
                <div class="score-val">{{ stock.score }}</div>
                <div class="score-lab">匹配度</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 持仓管理 -->
        <div class="panel">
          <div class="panel-title">💼 持仓管理</div>
          <div v-for="pos in positions" :key="pos.id" class="position-item">
            <div class="pos-info">
              <div class="pos-name">{{ pos.stock_name }}</div>
              <div class="pos-cost">成本: ¥{{ pos.cost_price?.toFixed(2) }} | {{ pos.quantity }}股</div>
            </div>
            <div class="pos-profit">
              <div :class="['profit-val', pos.profit >= 0 ? 'up' : 'down']">
                {{ pos.profit >= 0 ? '+' : '' }}¥{{ Math.abs(pos.profit || 0).toFixed(0) }}
              </div>
              <div :class="['profit-pct', pos.profit >= 0 ? 'up' : 'down']">
                {{ pos.profit >= 0 ? '+' : '' }}{{ (pos.profit_pct || 0).toFixed(2) }}%
              </div>
            </div>
          </div>
          <div v-if="positions.length === 0" class="empty">
            <div class="empty-icon">📭</div>
            <div>暂无持仓</div>
          </div>
          <el-button type="primary" size="small" style="width: 100%; margin-top: 8px;" @click="showPositionDialog = true">
            + 录入持仓
          </el-button>
        </div>
      </aside>
    </main>

    <!-- 状态栏 -->
    <footer class="status-bar">
      <div class="status-left">
        <span class="status-item"><span class="dot ok"></span>数据连接正常</span>
        <span class="status-item">🕐 {{ currentTime }}</span>
      </div>
      <div class="status-right">
        <span class="status-item">📊 今日选股: {{ stockPool.length }} 只</span>
        <span class="status-item">⚠️ 违规监控: 0 次</span>
      </div>
    </footer>

    <!-- 录入持仓弹窗 -->
    <el-dialog v-model="showPositionDialog" title="💼 录入持仓" width="450px">
      <el-form :model="positionForm" label-width="80px" size="small">
        <el-form-item label="股票代码">
          <el-input v-model="positionForm.stock_code" placeholder="如: 000001" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="positionForm.stock_name" placeholder="如: 平安银行" />
        </el-form-item>
        <el-form-item label="买入成本">
          <el-input-number v-model="positionForm.cost_price" :precision="2" :min="0" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="持仓数量">
          <el-input-number v-model="positionForm.quantity" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="买入日期">
          <el-date-picker v-model="positionForm.buy_date" type="date" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showPositionDialog = false">取消</el-button>
        <el-button type="primary" size="small" @click="savePosition">保存持仓</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 交易面板视图
 */
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { init, dispose } from 'klinecharts'
import { getMarketOverview, getKlineData, screenStocks } from '@/api/stock'
import { getPositions, createPosition } from '@/api/position'

// 响应式数据
const currentTime = ref('')
const period = ref('daily')
const chartRef = ref(null)
let chart = null

// 市场数据
const marketOverview = ref({
  up_count: 0,
  down_count: 0,
  total_count: 0
})

// 当前股票
const currentStock = ref({
  code: '000001',
  name: '平安银行',
  price: 12.85,
  change_pct: 5.23
})

// 选股池
const stockPool = ref([])
const activeTag = ref('全部')
const poolTags = ['全部', '放量长上影', '一进二', '抗跌强势']

const filteredPool = computed(() => {
  if (activeTag.value === '全部') return stockPool.value
  return stockPool.value.filter(s => s.signal_type === activeTag.value)
})

// 持仓
const positions = ref([])
const showPositionDialog = ref(false)
const positionForm = ref({
  stock_code: '',
  stock_name: '',
  cost_price: 0,
  quantity: 100,
  buy_date: new Date()
})

// 信号
const buySignals = ref([])
const sellSignals = ref([])

// 计算属性
const canOpen = computed(() => {
  // 根据持仓和风控规则判断
  return positions.value.length < 3
})

const priceClass = computed(() => {
  return currentStock.value.change_pct >= 0 ? 'up' : 'down'
})

const changeText = computed(() => {
  const change = currentStock.value.change_pct || 0
  return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`
})

// 方法
const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

const loadMarketOverview = async () => {
  try {
    const data = await getMarketOverview()
    marketOverview.value = data
  } catch (e) {
    console.error('加载市场概览失败', e)
  }
}

const loadStockPool = async () => {
  try {
    const data = await screenStocks({
      rules: ['exclude_st', 'market_cap', 'long_shadow', 'one_to_two', 'resilient'],
      market: 'all',
      limit: 10
    })
    stockPool.value = data.items || []
  } catch (e) {
    console.error('加载选股池失败', e)
  }
}

const loadPositions = async () => {
  try {
    const data = await getPositions()
    positions.value = data || []
  } catch (e) {
    console.error('加载持仓失败', e)
  }
}

const loadKline = async () => {
  try {
    const data = await getKlineData(currentStock.value.code, period.value, 60)
    if (chart && data.data) {
      chart.applyData(data.data.map(item => ({
        timestamp: new Date(item.timestamp).getTime(),
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume
      })))
    }
  } catch (e) {
    console.error('加载K线失败', e)
  }
}

const initChart = () => {
  nextTick(() => {
    if (chartRef.value) {
      // 销毁旧图表
      if (chart) {
        dispose(chartRef.value)
      }
      // 创建新图表
      chart = init(chartRef.value, {
        theme: 'dark'
      })
      chart.createIndicator('MA', true, { calcParams: [5, 10, 20, 60] })
      chart.createIndicator('VOL', true, { height: 60 })
      loadKline()
    }
  })
}

const selectStock = (stock) => {
  currentStock.value = {
    code: stock.code,
    name: stock.name,
    price: stock.price,
    change_pct: stock.change_pct
  }
  loadKline()
}

const savePosition = async () => {
  try {
    await createPosition(positionForm.value)
    showPositionDialog.value = false
    loadPositions()
  } catch (e) {
    console.error('保存持仓失败', e)
  }
}

const showSignalDetail = (signal) => {
  // TODO: 显示信号详情
  console.log('信号详情', signal)
}

// 生命周期
onMounted(() => {
  updateTime()
  setInterval(updateTime, 5000)
  
  loadMarketOverview()
  loadStockPool()
  loadPositions()
  initChart()
  
  // 定时刷新市场数据
  setInterval(loadMarketOverview, 30000)
})

// 组件卸载前清理
onBeforeUnmount(() => {
  if (chart && chartRef.value) {
    dispose(chartRef.value)
    chart = null
  }
})
</script>

<style lang="scss" scoped>
.trade-panel {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

// 头部样式
.header {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(20px);
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  flex-shrink: 0;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .logo-icon {
    font-size: 26px;
    filter: drop-shadow(0 0 8px rgba(102, 126, 234, 0.5));
  }
  
  .logo-text {
    font-size: 17px;
    font-weight: 700;
    background: linear-gradient(135deg, #7c83fd, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}

.header-nav {
  display: flex;
  gap: 4px;
  margin-left: 32px;
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
  border-radius: 10px;
  
  .nav-btn {
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    transition: all 0.25s;
    
    &:hover {
      color: rgba(255, 255, 255, 0.85);
      background: rgba(255, 255, 255, 0.05);
    }
    
    &.active {
      background: linear-gradient(135deg, rgba(124, 131, 253, 0.2), rgba(168, 85, 247, 0.15));
      color: #fff;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.market-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  font-size: 12px;
  
  .up { color: #ef4444; }
  .down { color: #22c55e; }
}

.time {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  font-size: 12px;
}

.open-status {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  
  &.can {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }
  
  &.cannot {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
}

// 主内容区
.main-content {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
  padding: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// K线图区域
.kline-section {
  background: linear-gradient(145deg, rgba(22, 25, 40, 0.8), rgba(15, 18, 30, 0.9));
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.stock-info {
  display: flex;
  align-items: baseline;
  gap: 12px;
  
  .stock-name {
    font-size: 18px;
    font-weight: 700;
  }
  
  .stock-code {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  .stock-price {
    font-size: 24px;
    font-weight: 800;
    
    &.up {
      color: #ef4444;
      text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
    }
    
    &.down {
      color: #22c55e;
      text-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
    }
  }
  
  .stock-change {
    font-size: 12px;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    
    &.up {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1));
      color: #ef4444;
    }
    
    &.down {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1));
      color: #22c55e;
    }
  }
}

.kline-tabs {
  margin-bottom: 10px;
}

.kline-container {
  flex: 1;
  min-height: 0;
  
  .chart {
    width: 100%;
    height: 100%;
    border-radius: 12px;
  }
}

// 右侧面板
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

// 入口卡片
.entry-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.entry-card {
  background: linear-gradient(145deg, rgba(124, 131, 253, 0.08), rgba(168, 85, 247, 0.05));
  border: 1px solid rgba(124, 131, 253, 0.15);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-3px);
    border-color: rgba(124, 131, 253, 0.3);
    box-shadow: 0 8px 25px rgba(124, 131, 253, 0.15);
  }
  
  .entry-icon {
    font-size: 28px;
    margin-bottom: 8px;
  }
  
  .entry-title {
    font-weight: 600;
    font-size: 13px;
  }
  
  .entry-sub {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.4);
    margin-top: 4px;
  }
}

// 面板
.panel {
  background: linear-gradient(145deg, rgba(22, 25, 40, 0.7), rgba(15, 18, 30, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 14px;
  
  .panel-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
  }
}

// 信号项
.signal-item {
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.25s;
  
  &.buy {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(34, 197, 94, 0.04));
    border-left: 3px solid #22c55e;
    
    &:hover {
      background: linear-gradient(135deg, rgba(34, 197, 94, 0.18), rgba(34, 197, 94, 0.06));
    }
  }
  
  &.sell {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.04));
    border-left: 3px solid #ef4444;
    
    &:hover {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.18), rgba(239, 68, 68, 0.06));
    }
  }
  
  .signal-type {
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 6px;
  }
  
  .signal-detail {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 6px;
  }
  
  .signal-price {
    font-size: 15px;
    font-weight: 700;
  }
}

// 选股池
.pool-tags {
  margin-bottom: 10px;
  display: flex;
  gap: 6px;
}

.pool-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: rgba(124, 131, 253, 0.08);
    border-color: rgba(124, 131, 253, 0.2);
    transform: translateX(3px);
  }
  
  .pool-name {
    font-weight: 600;
    font-size: 13px;
  }
  
  .pool-code {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.35);
    margin-top: 2px;
  }
  
  .pool-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .pool-signal {
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 6px;
    background: linear-gradient(135deg, rgba(124, 131, 253, 0.2), rgba(168, 85, 247, 0.15));
    color: #a78bfa;
    font-weight: 600;
  }
  
  .pool-score {
    text-align: right;
    
    .score-val {
      font-size: 16px;
      font-weight: 800;
      background: linear-gradient(135deg, #7c83fd, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .score-lab {
      font-size: 10px;
      color: rgba(255, 255, 255, 0.35);
    }
  }
}

// 持仓
.position-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  margin-bottom: 8px;
  
  .pos-name {
    font-weight: 600;
    font-size: 13px;
  }
  
  .pos-cost {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.4);
    margin-top: 3px;
  }
  
  .pos-profit {
    text-align: right;
    
    .profit-val {
      font-size: 15px;
      font-weight: 700;
    }
    
    .profit-pct {
      font-size: 12px;
      font-weight: 600;
    }
    
    .up {
      color: #ef4444;
    }
    
    .down {
      color: #22c55e;
    }
  }
}

// 空状态
.empty {
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.3);
  
  .empty-icon {
    font-size: 36px;
    margin-bottom: 10px;
    opacity: 0.6;
  }
}

// 状态栏
.status-bar {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(10px);
  padding: 8px 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  height: 38px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: pulse 2s infinite;
  
  &.ok {
    background: #22c55e;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
