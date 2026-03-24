<template>
  <div class="screening-page">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">📈</span>
          <span class="logo-text">个人股票交易纪律系统</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-btn">📊 交易面板</router-link>
          <router-link to="/screening" class="nav-btn active">🎯 AI选股</router-link>
          <router-link to="/rules" class="nav-btn">📋 规则配置</router-link>
        </nav>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-content">
      <div class="screening-container">
        <!-- 选股条件 -->
        <div class="conditions-panel">
          <div class="panel-header">
            <h2>🔍 选股条件</h2>
          </div>
          
          <div class="condition-group">
            <h3>排除规则</h3>
            <div class="checkbox-group">
              <el-checkbox v-model="conditions.exclude_st">排除ST股</el-checkbox>
              <el-checkbox v-model="conditions.market_cap">市值过滤(20-500亿)</el-checkbox>
              <el-checkbox v-model="conditions.exclude_bad_news">排除利空股</el-checkbox>
              <el-checkbox v-model="conditions.exclude_zombie">排除僵尸股</el-checkbox>
            </div>
          </div>
          
          <div class="condition-group">
            <h3>核心标的</h3>
            <div class="checkbox-group">
              <el-checkbox v-model="conditions.long_shadow">放量长上影</el-checkbox>
              <el-checkbox v-model="conditions.one_to_two">一进二接力</el-checkbox>
              <el-checkbox v-model="conditions.resilient">抗跌强势股</el-checkbox>
            </div>
          </div>
          
          <div class="condition-group">
            <h3>市场筛选</h3>
            <el-radio-group v-model="market">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="sh">上海</el-radio-button>
              <el-radio-button label="sz">深圳</el-radio-button>
            </el-radio-group>
          </div>
          
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            @click="runScreening"
            class="screening-btn"
          >
            开始选股
          </el-button>
        </div>
        
        <!-- 选股结果 -->
        <div class="results-panel">
          <div class="panel-header">
            <h2>📊 选股结果</h2>
            <span v-if="results.length > 0" class="result-count">共 {{ results.length }} 只</span>
          </div>
          
          <el-table 
            v-if="results.length > 0"
            :data="results" 
            style="width: 100%"
            :max-height="500"
          >
            <el-table-column prop="code" label="代码" width="90" />
            <el-table-column prop="name" label="名称" width="100" />
            <el-table-column prop="signal_type" label="信号类型" width="120">
              <template #default="{ row }">
                <el-tag size="small" type="primary">{{ row.signal_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="匹配度" width="80">
              <template #default="{ row }">
                <span class="score">{{ row.score }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="90">
              <template #default="{ row }">
                ¥{{ row.price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="change_pct" label="涨跌幅" width="100">
              <template #default="{ row }">
                <span :class="row.change_pct >= 0 ? 'up' : 'down'">
                  {{ row.change_pct >= 0 ? '+' : '' }}{{ row.change_pct?.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="入选原因" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="viewDetail(row)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-else class="empty-state">
            <div class="empty-icon">🔍</div>
            <p>选择条件后点击"开始选股"</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
/**
 * AI选股视图
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { screenStocks } from '@/api/stock'
import { ElMessage } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const market = ref('all')
const conditions = reactive({
  exclude_st: true,
  market_cap: true,
  exclude_bad_news: true,
  exclude_zombie: true,
  long_shadow: true,
  one_to_two: true,
  resilient: true
})

const results = ref([])

const runScreening = async () => {
  loading.value = true
  
  try {
    const rules = []
    if (conditions.exclude_st) rules.push('exclude_st')
    if (conditions.market_cap) rules.push('market_cap')
    if (conditions.exclude_bad_news) rules.push('exclude_bad_news')
    if (conditions.exclude_zombie) rules.push('exclude_zombie')
    if (conditions.long_shadow) rules.push('long_shadow')
    if (conditions.one_to_two) rules.push('one_to_two')
    if (conditions.resilient) rules.push('resilient')
    
    const data = await screenStocks({
      rules,
      market: market.value,
      limit: 30
    })
    
    results.value = data.items || []
    ElMessage.success(`选股完成，找到${results.value.length}只符合条件的标的`)
  } catch (e) {
    console.error('选股失败', e)
    ElMessage.error('选股失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const viewDetail = (stock) => {
  // 跳转到交易面板并显示该股票
  router.push({ path: '/', query: { code: stock.code } })
}
</script>

<style lang="scss" scoped>
.screening-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0d0d1a 100%);
}

.header {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(20px);
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
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

.main-content {
  padding: 24px;
}

.screening-container {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.conditions-panel,
.results-panel {
  background: linear-gradient(145deg, rgba(22, 25, 40, 0.8), rgba(15, 18, 30, 0.9));
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }
  
  .result-count {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
  }
}

.condition-group {
  margin-bottom: 20px;
  
  h3 {
    font-size: 13px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 12px;
  }
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  
  :deep(.el-checkbox__label) {
    color: rgba(255, 255, 255, 0.7) !important;
  }
}

.screening-btn {
  width: 100%;
  margin-top: 24px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);
  
  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }
}

.score {
  color: #a78bfa;
  font-weight: 700;
}

.up {
  color: #ef4444;
}

.down {
  color: #22c55e;
}
</style>
