<template>
  <Card title="专业 K线量能图" icon="kline" tone="primary">
    <template #subtitle>使用 KLineCharts 展示蜡烛图与成交量指标</template>
    <template #actions>
      <select v-model="selectedName" @change="onStockChange"><option v-for="p in positions" :key="p.id" :value="p.name">{{ p.name }}{{ p.symbol ? ` (${p.symbol})` : "" }}</option></select>
      <div class="mode-tabs">
        <button class="tab-btn" :class="{ active: chartMode === 'daily' }" @click="switchMode('daily')">日K</button>
        <button class="tab-btn" :class="{ active: chartMode === 'minute' }" @click="switchMode('minute')">分时K线</button>
      </div>
      <button class="btn" :disabled="loading" @click="refreshChart">{{ loading ? "获取中..." : "刷新K线" }}</button>
      <button class="btn primary" :disabled="aiLoading" @click="runAIAnalysis">{{ aiLoading ? "分析中..." : "AI量能分析" }}</button>
    </template>
    <div v-if="dataStatus" class="data-status">
      <span :class="dataStatus.available ? 'status-ok' : 'status-error'">
        {{ dataStatus.available ? (dataStatus.message || '数据源已连接') : `数据源未连接: ${dataStatus.error}` }}
      </span>
    </div>
    <div class="chart-meta">
      <span>{{ chartMode === "daily" ? `已加载 ${bars.length} 根日K，右侧锁定最后交易日` : `已加载 ${bars.length} 根${minutePeriod}分钟K，自动刷新中` }}</span>
      <span v-if="loadingMore">正在加载更多历史K线...</span>
    </div>
    <KlineChart :bars="bars" :mode="chartMode" @request-more-history="loadMoreHistory" />
    <p v-if="!bars.length" class="text-muted">暂无K线数据，请点击"刷新K线"</p>
  </Card>
  <Card v-if="aiReport" title="AI量能分析报告" icon="ai" tone="primary">
    <MarkdownRender :content="aiReport" />
  </Card>
  <Card title="实时行情" icon="chart" tone="default">
    <template #actions>
      <button class="btn" @click="refreshQuote">刷新行情</button>
    </template>
    <div v-if="quote" class="quote-info">
      <div class="quote-row">
        <span class="quote-label">当前价</span>
        <span class="quote-value" :class="quote.change_pct >= 0 ? 'pnl-positive' : 'pnl-negative'">{{ quote.current_price }}</span>
        <span :class="quote.change_pct >= 0 ? 'pnl-positive' : 'pnl-negative'">{{ quote.change_pct >= 0 ? '+' : '' }}{{ quote.change_pct }}%</span>
      </div>
      <div class="quote-row">
        <span class="quote-label">今开</span>
        <span class="quote-value">{{ quote.open_price }}</span>
        <span class="quote-label">最高</span>
        <span class="quote-value">{{ quote.high_price }}</span>
        <span class="quote-label">最低</span>
        <span class="quote-value">{{ quote.low_price }}</span>
      </div>
      <div class="quote-row">
        <span class="quote-label">成交量</span>
        <span class="quote-value">{{ formatVolume(quote.volume) }}</span>
        <span class="quote-label">成交额</span>
        <span class="quote-value">{{ formatAmount(quote.amount) }}</span>
      </div>
    </div>
    <p v-else class="text-muted">暂无实时行情数据</p>
  </Card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Card from "../components/Card.vue";
import KlineChart from "../components/KlineChart.vue";
import MarkdownRender from "../components/MarkdownRender.vue";
import { apiGet, apiPost } from "../services/api";

const emit = defineEmits(["toast"]);
const positions = ref([]);
const selectedName = ref("");
const bars = ref([]);
const quote = ref(null);
const dataStatus = ref(null);
const loading = ref(false);
const loadingMore = ref(false);
const aiLoading = ref(false);
const aiReport = ref("");
const chartMode = ref("daily");
const dailyDays = ref(260);
const minutePeriod = ref(5);
let minuteTimer = null;
const selectedPosition = computed(() => positions.value.find((item) => item.name === selectedName.value) || null);

function stockQuery(extra = {}) {
  const query = new URLSearchParams();
  if (selectedName.value) query.set("name", selectedName.value);
  if (selectedPosition.value?.symbol) query.set("symbol", selectedPosition.value.symbol);
  Object.entries(extra).forEach(([key, value]) => query.set(key, String(value)));
  return query.toString();
}

function formatVolume(vol) {
  if (vol >= 1e8) return `${(vol / 1e8).toFixed(2)}亿`;
  if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}万`;
  return vol.toString();
}

function formatAmount(amt) {
  if (amt >= 1e8) return `${(amt / 1e8).toFixed(2)}亿`;
  if (amt >= 1e6) return `${(amt / 1e6).toFixed(2)}万`;
  return amt.toString();
}

async function loadPositions() {
  positions.value = await apiGet("/api/positions");
  selectedName.value ||= positions.value[0]?.name || "";
}

async function checkDataStatus() {
  try {
    dataStatus.value = await apiGet("/api/data/status");
  } catch (err) {
    dataStatus.value = { available: false, error: err.message };
  }
}

async function loadKline() {
  if (!selectedName.value) return;
  await fetchDailyKline(false);
}

async function onStockChange() {
  bars.value = [];
  quote.value = null;
  aiReport.value = "";
  dailyDays.value = 260;
  await refreshChart();
}

async function fetchDailyKline(appendHistory = false) {
  if (!selectedName.value) return;
  if (!appendHistory) loading.value = true;
  try {
    const result = await apiGet(`/api/kline/realtime?${stockQuery({ days: dailyDays.value })}`);
    if (result.bars && result.bars.length) {
      bars.value = result.bars;
      const sourceText = result.source === "baostock" ? "实时源" : "本地缓存";
      emit("toast", `${sourceText}加载 ${result.bars.length} 条K线数据`);
    } else {
      emit("toast", result.message || "未获取到K线数据，请检查股票代码或Baostock连接");
    }
  } catch (err) {
    emit("toast", err.message);
  } finally {
    if (!appendHistory) loading.value = false;
  }
}

async function fetchMinuteKline() {
  if (!selectedName.value) return;
  loading.value = true;
  try {
    const result = await apiGet(`/api/kline/intraday?${stockQuery({ period: minutePeriod.value, limit: 240 })}`);
    if (result.bars && result.bars.length) {
      bars.value = result.bars;
      emit("toast", `分时K线刷新 ${result.bars.length} 根`);
    } else {
      emit("toast", result.message || "未获取到分时K线数据");
    }
  } catch (err) {
    emit("toast", err.message);
  } finally {
    loading.value = false;
  }
}

async function refreshChart() {
  if (chartMode.value === "daily") {
    stopMinuteTimer();
    await fetchDailyKline(false);
    return;
  }
  await fetchMinuteKline();
  startMinuteTimer();
}

async function switchMode(mode) {
  if (chartMode.value === mode) return;
  chartMode.value = mode;
  bars.value = [];
  if (mode === "minute") {
    await fetchMinuteKline();
    startMinuteTimer();
  } else {
    stopMinuteTimer();
    await fetchDailyKline(false);
  }
}

async function loadMoreHistory() {
  if (chartMode.value !== "daily" || loadingMore.value || loading.value) return;
  loadingMore.value = true;
  dailyDays.value = Math.min(dailyDays.value + 180, 1000);
  try {
    await fetchDailyKline(true);
  } finally {
    loadingMore.value = false;
  }
}

function startMinuteTimer() {
  stopMinuteTimer();
  minuteTimer = setInterval(() => {
    if (chartMode.value === "minute" && selectedName.value) {
      fetchMinuteKline();
    }
  }, 30000);
}

function stopMinuteTimer() {
  if (minuteTimer) {
    clearInterval(minuteTimer);
    minuteTimer = null;
  }
}

async function refreshQuote() {
  if (!selectedName.value) return;
  try {
    quote.value = await apiGet(`/api/quote?${stockQuery()}`);
  } catch (err) {
    emit("toast", err.message);
  }
}

async function runAIAnalysis() {
  if (!bars.value.length) {
    emit("toast", "请先获取K线数据");
    return;
  }
  if (bars.value.length < 5) {
    emit("toast", "K线数据不足，需要至少5根");
    return;
  }
  aiLoading.value = true;
  try {
    const context = {
      stock: selectedName.value,
      bars: bars.value,
      quote: quote.value,
    };
    const result = await apiPost("/api/analysis/volume", context);
    aiReport.value = result.content || "";
    emit("toast", `AI量能分析完成 (${result.provider})`);
  } catch (err) {
    emit("toast", err.message);
  } finally {
    aiLoading.value = false;
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadPositions(), checkDataStatus()]);
    await loadKline();
  } catch (err) {
    emit("toast", err.message);
  }
});

onBeforeUnmount(stopMinuteTimer);
</script>

<style scoped>
.data-status {
  margin-bottom: 12px;
  padding: 8px;
  background: var(--table-header);
  border-radius: 4px;
}

.status-ok {
  color: var(--ok);
}

.status-error {
  color: var(--danger);
}

.mode-tabs {
  display: inline-flex;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background: var(--panel);
}

.tab-btn {
  min-height: 38px;
  border: 0;
  border-right: 1px solid var(--line);
  padding: 0 14px;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  font-weight: 700;
}

.tab-btn:last-child {
  border-right: 0;
}

.tab-btn.active {
  color: #fff;
  background: var(--primary);
}

.chart-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 13px;
}

.quote-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quote-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--table-header);
  border-radius: 4px;
}

.quote-label {
  color: var(--muted);
  font-size: 14px;
}

.quote-value {
  color: var(--ink);
  font-weight: 600;
}

.pnl-positive {
  color: var(--ok);
}

.pnl-negative {
  color: var(--danger);
}
</style>
