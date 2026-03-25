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
        <!-- 紧凑的股票信息栏 -->
        <div class="stock-header">
          <div class="stock-main-info">
            <span class="stock-name">{{ currentStock.name }}</span>
            <span class="stock-code">{{ currentStock.code }}</span>
            <span :class="['stock-price', priceClass]">{{ currentStock.price?.toFixed(2) }}</span>
            <span :class="['stock-change', priceClass]">{{ changeText }}</span>
          </div>
          <div class="stock-detail-compact">
            <div class="detail-cell">
              <span class="label">昨收</span>
              <span class="value">{{ minuteData.preClose.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">今开</span>
              <span :class="['value', minuteData.open >= minuteData.preClose ? 'up' : 'down']">{{ minuteData.open.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">最高</span>
              <span class="value up">{{ minuteData.high.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">最低</span>
              <span class="value down">{{ minuteData.low.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">振幅</span>
              <span class="value">{{ minuteData.amplitude.toFixed(2) }}%</span>
            </div>
            <div class="detail-cell">
              <span class="label">成交量</span>
              <span class="value">{{ (minuteData.volume / 10000).toFixed(0) }}万</span>
            </div>
            <div class="detail-cell">
              <span class="label">成交额</span>
              <span class="value">{{ (minuteData.amount / 100000000).toFixed(2) }}亿</span>
            </div>
            <div class="detail-cell">
              <span class="label">换手</span>
              <span class="value">{{ minuteData.turnoverRate.toFixed(2) }}%</span>
            </div>
            <div class="detail-cell">
              <span class="label">市盈</span>
              <span class="value">{{ minuteData.peRatio.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">市净</span>
              <span class="value">{{ minuteData.pbRatio.toFixed(2) }}</span>
            </div>
            <div class="detail-cell">
              <span class="label">市值</span>
              <span class="value">{{ minuteData.marketCap.toFixed(0) }}亿</span>
            </div>
          </div>
        </div>
        
        <div class="kline-tabs">
          <el-radio-group v-model="period" size="small" @change="handlePeriodChange">
            <el-radio-button label="daily">日K</el-radio-button>
            <el-radio-button label="weekly">周K</el-radio-button>
            <el-radio-button label="minute">分时</el-radio-button>
          </el-radio-group>
        </div>
        
        <!-- 分时图布局 -->
        <div v-if="period === 'minute'" class="minute-layout">
          <!-- 分时图 -->
          <div class="minute-chart-container">
            <div class="minute-chart">
              <div ref="minuteChartRef" class="chart"></div>
            </div>
          </div>
          
          <!-- 成交明细 -->
          <div class="trade-details">
            <div class="detail-title">成交明细</div>
            <div class="detail-header">
              <span>时间</span>
              <span>价格</span>
              <span>成交量</span>
            </div>
            <div class="detail-list">
              <div 
                v-for="(item, i) in tradeDetails" 
                :key="i" 
                :class="['detail-row', item.type]"
              >
                <span class="time">{{ item.time }}</span>
                <span :class="['price', item.type]">{{ item.price.toFixed(2) }}</span>
                <span class="volume">{{ item.volume }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- K线图布局 -->
        <div v-else class="kline-container">
          <div class="kline-chart-wrapper">
            <div ref="chartRef" class="chart"></div>
          </div>
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
import { init, dispose, registerIndicator } from 'klinecharts'
import { getMarketOverview, getKlineData, screenStocks } from '@/api/stock'
import { getPositions, createPosition } from '@/api/position'

/**
 * 注册自定义均价指标（用于分时图）
 */
registerIndicator({
  name: 'AVG',
  shortName: '均价',
  precision: 2,
  calcParams: [],
  figures: [
    { 
      key: 'avg', 
      title: '均价: ', 
      type: 'line',
      styles: () => ({
        style: 'solid',
        color: '#FF9800',
        size: 1.5
      })
    }
  ],
  calc: (dataList) => {
    return dataList.map(item => ({ avg: item.vwap || item.close }))
  }
})

// 响应式数据
const currentTime = ref('')
const period = ref('minute')  // 默认显示分时图
const chartRef = ref(null)
const minuteChartRef = ref(null)
let chart = null
let minuteChart = null
let refreshTimer = null

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
  price: 14.25,      // 当前价格
  change_pct: 14.00  // 涨幅14%
})

// 分时图数据
const minuteData = ref({
  preClose: 12.50,   // 昨收
  open: 12.55,       // 今开
  high: 14.95,       // 最高（约+20%）
  low: 10.50,        // 最低（约-16%）
  volume: 125634,    // 成交量（手）
  amount: 15862345,  // 成交额（元）
  turnoverRate: 2.5, // 换手率
  amplitude: 35.6,   // 振幅（%）
  marketCap: 2450,   // 总市值（亿）
  totalShares: 194.06, // 总股本（亿）
  circulationCap: 2450, // 流通值（亿）
  peRatio: 4.97,     // 市盈率
  pbRatio: 0.85      // 市净率
})

// 成交明细
const tradeDetails = ref([
  { time: '14:30:05', price: 12.85, volume: 100, type: 'buy' },
  { time: '14:30:03', price: 12.84, volume: 200, type: 'sell' },
  { time: '14:29:58', price: 12.85, volume: 150, type: 'buy' }
])

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

/**
 * 加载K线数据
 */
const loadKline = async () => {
  try {
    const data = await getKlineData(currentStock.value.code, period.value, 60)
    if (chart && data.data) {
      const klineData = data.data.map(item => ({
        timestamp: new Date(item.timestamp).getTime(),
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume
      }))
      
      // 应用数据
      chart.applyNewData(klineData)
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
      // 创建新图表，自定义样式
      chart = init(chartRef.value, {
        theme: 'dark',
        styles: {
          grid: {
            show: true,
            horizontal: {
              show: true,
              size: 1,
              color: 'rgba(255, 255, 255, 0.1)',
              style: 'dashed'
            },
            vertical: {
              show: true,
              size: 1,
              color: 'rgba(255, 255, 255, 0.1)',
              style: 'dashed'
            }
          },
          candle: {
            priceMark: {
              show: true,
              high: {
                show: true,
                color: '#EF5350'  // 高点红色
              },
              low: {
                show: true,
                color: '#26A69A'  // 低点绿色
              },
              last: {
                show: true,
                upColor: '#EF5350',     // 涨红
                downColor: '#26A69A',    // 跌绿
                noChangeColor: '#888888'
              }
            },
            bar: {
              upColor: '#EF5350',        // 涨红
              downColor: '#26A69A',      // 跌绿
              noChangeColor: '#888888',
              upBorderColor: '#EF5350',
              downBorderColor: '#26A69A',
              noChangeBorderColor: '#888888',
              upWickColor: '#EF5350',
              downWickColor: '#26A69A',
              noChangeWickColor: '#888888'
            }
          },
          indicator: {
            lastValueMark: {
              show: true
            },
            tooltip: {
              showRule: 'follow_cross',
              showType: 'standard'
            }
          },
          xAxis: {
            axisLine: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            tickText: {
              color: 'rgba(255, 255, 255, 0.5)'
            }
          },
          yAxis: {
            type: 'normal',
            axisLine: {
              color: 'rgba(255, 255, 255, 0.2)'
            },
            tickText: {
              color: 'rgba(255, 255, 255, 0.5)'
            },
            show: true
          },
          crosshair: {
            show: true,
            horizontal: {
              line: {
                color: 'rgba(255, 255, 255, 0.3)',
                style: 'dashed'
              }
            },
            vertical: {
              line: {
                color: 'rgba(255, 255, 255, 0.3)',
                style: 'dashed'
              }
            }
          }
        }
      })
      
      // 先在主图（candle_pane）上叠加MA指标
      chart.createIndicator('MA', true, { id: 'candle_pane' })
      
      // 创建成交量指标（新pane）
      chart.createIndicator('VOL', false, { height: 100 })
      
      // 创建MACD指标（新pane）
      chart.createIndicator('MACD', false, { height: 100 })
      
      // 加载K线数据
      loadKline()
    }
  })
}

/**
 * 初始化分时图
 */
const initMinuteChart = () => {
  nextTick(() => {
    if (minuteChartRef.value) {
      if (minuteChart) {
        dispose(minuteChartRef.value)
      }
      
      // 判断涨跌
      const isUp = currentStock.value.change_pct >= 0
      const lineColor = isUp ? '#EF5350' : '#26A69A'
      const fillColor = isUp ? 'rgba(239, 83, 80, 0.15)' : 'rgba(38, 166, 154, 0.15)'
      const preClose = minuteData.value.preClose
      
      // 创建分时图（使用面积图样式）
      minuteChart = init(minuteChartRef.value, {
        theme: 'dark',
        styles: {
          grid: {
            show: true,
            horizontal: {
              show: true,
              size: 1,
              color: 'rgba(255, 255, 255, 0.06)',
              style: 'solid'
            },
            vertical: {
              show: true,
              size: 1,
              color: 'rgba(255, 255, 255, 0.06)',
              style: 'solid'
            }
          },
          candle: {
            type: 'area',
            priceMark: {
              high: { show: false },
              low: { show: false },
              last: {
                show: true,
                upColor: '#EF5350',    // 涨红
                downColor: '#26A69A',   // 跌绿
                noChangeColor: '#888888'
              }
            },
            bar: {
              upColor: 'rgba(239, 83, 80, 0.5)',     // 涨红
              downColor: 'rgba(38, 166, 154, 0.5)',  // 跌绿
              noChangeColor: 'rgba(136, 136, 136, 0.3)'
            },
            area: {
              lineSize: 2,
              lineColor: lineColor,
              fillColor: fillColor
            }
          },
          xAxis: {
            axisLine: { color: 'rgba(255, 255, 255, 0.15)' },
            tickText: { color: 'rgba(255, 255, 255, 0.5)', size: 11 }
          },
          yAxis: {
            type: 'normal',
            axisLine: { color: 'rgba(255, 255, 255, 0.15)' },
            tickText: { color: 'rgba(255, 255, 255, 0.5)', size: 11 },
            show: true
          },
          crosshair: {
            show: true,
            horizontal: {
              line: { color: 'rgba(255, 255, 255, 0.4)', style: 'dashed' }
            },
            vertical: {
              line: { color: 'rgba(255, 255, 255, 0.4)', style: 'dashed' }
            }
          },
          overlay: {
            show: true
          },
          indicator: {
            lastValueMark: {
              show: true
            },
            tooltip: {
              showRule: 'follow_cross',
              showType: 'standard'
            }
          }
        }
      })
      
      // 添加昨收基准线（水平线）
      minuteChart.createOverlay({
        name: 'horizontalStraightLine',
        extendData: '昨收',
        styles: {
          line: {
            color: '#FFD700',
            size: 1,
            style: 'dashed'
          }
        },
        points: [{ value: preClose }]
      })
      
      // 加载分时数据
      const minuteDataResult = generateMinuteData()
      
      // 计算VWAP均价并添加到数据中
      let totalAmount = 0
      let totalVolume = 0
      const dataWithVWAP = minuteDataResult.map((item) => {
        const close = item.close || 0
        const volume = item.volume || 0
        totalAmount += close * volume
        totalVolume += volume
        const vwap = totalVolume > 0 ? totalAmount / totalVolume : close
        return {
          ...item,
          vwap: vwap
        }
      })
      
      minuteChart.applyNewData(dataWithVWAP)
      
      // 创建成交量面板
      minuteChart.createIndicator('VOL', false, { height: 80 })
      
      // 在主图上叠加均价线指标（已全局注册）
      minuteChart.createIndicator('AVG', true, { id: 'candle_pane' })
    }
  })
}

/**
 * 生成模拟分时数据
 */
const generateMinuteData = () => {
  const data = []
  const preClose = minuteData.value.preClose
  const high = minuteData.value.high
  const low = minuteData.value.low
  const now = new Date()
  
  // 计算价格范围
  const priceRange = high - low
  
  let prevPrice = minuteData.value.open
  
  // 生成上午9:30-11:30的数据（120分钟）
  for (let i = 0; i < 120; i++) {
    const hour = Math.floor(i / 60) + 9
    const minute = (i % 60) + 30
    const adjustedMinute = minute >= 60 ? minute - 60 : minute
    const adjustedHour = minute >= 60 ? hour + 1 : hour
    
    if (adjustedHour > 11 || (adjustedHour === 11 && adjustedMinute > 30)) break
    
    const time = new Date(now)
    time.setHours(adjustedHour, adjustedMinute, 0, 0)
    
    // 模拟价格波动：逐步攀升或下跌
    const progress = i / 120  // 上午进度
    const baseTrend = Math.sin(progress * Math.PI) * priceRange * 0.3
    const noise = (Math.random() - 0.5) * priceRange * 0.08
    
    // 价格在最高价和最低价之间波动
    const currentPrice = Math.max(low, Math.min(high, preClose + baseTrend + noise))
    
    data.push({
      timestamp: time.getTime(),
      open: prevPrice,
      high: Math.max(prevPrice, currentPrice) + Math.random() * 0.02,
      low: Math.min(prevPrice, currentPrice) - Math.random() * 0.02,
      close: currentPrice,
      volume: Math.floor(Math.random() * 8000 + 2000)
    })
    
    prevPrice = currentPrice
  }
  
  // 生成下午13:00-15:00的数据（120分钟）
  for (let i = 0; i < 120; i++) {
    const hour = Math.floor(i / 60) + 13
    const minute = i % 60
    
    if (hour >= 15) break
    
    const time = new Date(now)
    time.setHours(hour, minute, 0, 0)
    
    // 下午走势：延续或反转
    const progress = i / 120  // 下午进度
    const baseTrend = Math.sin((progress + 0.5) * Math.PI) * priceRange * 0.25
    const noise = (Math.random() - 0.5) * priceRange * 0.08
    
    const currentPrice = Math.max(low, Math.min(high, preClose + baseTrend + noise))
    
    data.push({
      timestamp: time.getTime(),
      open: prevPrice,
      high: Math.max(prevPrice, currentPrice) + Math.random() * 0.02,
      low: Math.min(prevPrice, currentPrice) - Math.random() * 0.02,
      close: currentPrice,
      volume: Math.floor(Math.random() * 8000 + 2000)
    })
    
    prevPrice = currentPrice
  }
  
  return data
}

/**
 * 刷新成交明细
 */
const refreshOrderBook = () => {
  // 模拟新增成交记录
  const basePrice = currentStock.value.price
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  
  tradeDetails.value.unshift({
    time,
    price: basePrice + (Math.random() - 0.5) * 0.1,
    volume: Math.floor(Math.random() * 500 + 100),
    type: Math.random() > 0.5 ? 'buy' : 'sell'
  })
  
  // 只保留最近20条
  if (tradeDetails.value.length > 20) {
    tradeDetails.value = tradeDetails.value.slice(0, 20)
  }
}

/**
 * 处理周期切换
 */
const handlePeriodChange = (val) => {
  if (val === 'minute') {
    // 切换到分时图
    nextTick(() => {
      initMinuteChart()
      // 启动实时刷新
      if (refreshTimer) clearInterval(refreshTimer)
      refreshTimer = setInterval(refreshOrderBook, 3000)
      refreshOrderBook()
    })
  } else {
    // 切换到K线图
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    nextTick(() => {
      initChart()
    })
  }
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
  
  // 根据默认周期初始化图表
  if (period.value === 'minute') {
    initMinuteChart()
    // 启动实时刷新
    refreshTimer = setInterval(refreshOrderBook, 3000)
  } else {
    initChart()
  }
  
  // 定时刷新市场数据
  setInterval(loadMarketOverview, 30000)
})

// 组件卸载前清理
onBeforeUnmount(() => {
  // 清理K线图
  if (chart && chartRef.value) {
    dispose(chartRef.value)
    chart = null
  }
  // 清理分时图
  if (minuteChart && minuteChartRef.value) {
    dispose(minuteChartRef.value)
    minuteChart = null
  }
  // 清理定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
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
  flex: 1;
  background: linear-gradient(145deg, rgba(22, 25, 40, 0.8), rgba(15, 18, 30, 0.9));
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  min-height: 0;
  overflow: hidden;
}

// 紧凑的股票信息栏
.stock-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.stock-main-info {
  display: flex;
  align-items: baseline;
  gap: 14px;
  
  .stock-name {
    font-size: 24px;
    font-weight: 700;
  }
  
  .stock-code {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.4);
    padding: 2px 10px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  .stock-price {
    font-size: 32px;
    font-weight: 800;
    margin-left: 12px;
    
    &.up {
      color: #ef4444;
      text-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
    }
    
    &.down {
      color: #22c55e;
      text-shadow: 0 0 15px rgba(34, 197, 94, 0.5);
    }
  }
  
  .stock-change {
    font-size: 15px;
    padding: 4px 10px;
    border-radius: 5px;
    font-weight: 600;
    
    &.up {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
    }
    
    &.down {
      background: rgba(34, 197, 94, 0.15);
      color: #22c55e;
    }
  }
}

.stock-detail-compact {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: center;
  
  .detail-cell {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    
    .label {
      color: rgba(255, 255, 255, 0.4);
    }
    
    .value {
      color: rgba(255, 255, 255, 0.85);
      font-weight: 600;
      font-family: 'Courier New', monospace;
      
      &.up { color: #EF5350; }
      &.down { color: #26A69A; }
    }
  }
}

.kline-tabs {
  margin-bottom: 10px;
}

.kline-container {
  flex: 1;
  min-height: 0;
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  
  .kline-chart-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    
    .chart {
      width: 100%;
      flex: 1;
      min-height: 450px;
    }
  }
}

// 分时图布局
.minute-layout {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 0;
  
  .minute-chart-container {
    flex: 1;
    display: flex;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    overflow: hidden;
    
    .minute-chart {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      .chart {
        width: 100%;
        flex: 1;
        min-height: 400px;
      }
    }
  }
  
  .trade-details {
    width: 220px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    
    .detail-title {
      text-align: center;
      font-size: 14px;
      font-weight: 600;
      color: #fff;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .detail-header {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      span {
        flex: 1;
        text-align: center;
      }
    }
    
    .detail-list {
      flex: 1;
      overflow-y: auto;
      
      &::-webkit-scrollbar {
        width: 4px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 2px;
      }
    }
    
    .detail-row {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      font-size: 12px;
      font-family: 'Courier New', monospace;
      
      .time {
        flex: 1;
        text-align: center;
        color: rgba(255, 255, 255, 0.5);
      }
      
      .price {
        flex: 1;
        text-align: center;
        font-weight: 600;
        
        &.buy { color: #26A69A; }
        &.sell { color: #EF5350; }
      }
      
      .volume {
        flex: 1;
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
      }
    }
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
