<template>
  <Card title="专业 K线量能图" icon="kline" tone="primary">
    <template #subtitle>使用 KLineCharts 展示蜡烛图与成交量指标</template>
    <template #actions>
      <div class="actions-row">
        <select v-model="selectedName" @change="onStockChange" class="stock-select">
          <option v-for="p in positions" :key="p.id" :value="p.name">{{ p.name }}{{ p.symbol ? ` (${p.symbol})` : "" }}</option>
        </select>
        <div class="mode-tabs compact">
          <button class="tab-btn compact" :class="{ active: chartMode === 'daily' }" @click="switchMode('daily')">日K</button>
          <button class="tab-btn compact" :class="{ active: chartMode === 'minute' }" @click="switchMode('minute')">分时</button>
        </div>
        <button class="btn compact" :disabled="loading" @click="refreshChart">{{ loading ? "获取中..." : "刷新" }}</button>
        <button class="btn compact primary" :disabled="aiLoading" @click="runAIAnalysis">{{ aiLoading ? "分析中..." : "AI分析" }}</button>
      </div>
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
  <Card v-if="aiMetrics || aiReport" title="AI量能分析报告" icon="ai" tone="primary">
    <!-- 关键指标速览 -->
    <div v-if="aiMetrics && aiSignals" class="analysis-summary">
      <div class="summary-header">
        <span class="stock-name">{{ selectedName }}</span>
        <span class="analysis-date">{{ aiMetrics.trade_date }}</span>
      </div>
      <div class="metrics-grid">
        <!-- 核心价格指标 -->
        <div class="metric-item">
          <span class="metric-label">最新收盘</span>
          <span class="metric-value">{{ aiMetrics.price_metrics?.last_close?.toFixed(2) }}元</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">今日涨跌</span>
          <span :class="['metric-value', getChangeClass(aiMetrics.price_metrics?.change_pct)]">
            {{ formatChange(aiMetrics.price_metrics?.change_pct) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">量比(5日)</span>
          <span :class="['metric-value', getVolumeRatioClass(aiMetrics.volume_metrics?.volume_ratio_5)]">
            {{ aiMetrics.volume_metrics?.volume_ratio_5?.toFixed(2) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">换手率</span>
          <span :class="['metric-value', getTurnoverClass(aiMetrics.volume_metrics?.last_turnover_rate)]">
            {{ aiMetrics.volume_metrics?.last_turnover_rate?.toFixed(2) }}%
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">均线状态</span>
          <span :class="['metric-value', getMaTrendClass(aiMetrics.ma_metrics?.ma_trend)]">
            {{ aiMetrics.ma_metrics?.ma_trend }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">距20日高点</span>
          <span :class="['metric-value', getDistanceClass(aiMetrics.position_metrics?.distance_from_high)]">
            {{ aiMetrics.position_metrics?.distance_from_high?.toFixed(2) }}%
          </span>
        </div>
      </div>
      <!-- 识别形态 -->
      <div v-if="aiMetrics.patterns?.volume_price_patterns?.length" class="patterns-section">
        <span class="patterns-label">量价形态:</span>
        <span v-for="p in aiMetrics.patterns.volume_price_patterns" :key="p" class="pattern-tag">{{ p }}</span>
      </div>
      <div v-if="aiMetrics.patterns?.kline_patterns?.length" class="patterns-section">
        <span class="patterns-label">K线形态:</span>
        <span v-for="p in aiMetrics.patterns.kline_patterns" :key="p" class="pattern-tag">{{ p }}</span>
      </div>
      <!-- 风险与建议 - 重点标红 -->
      <div class="risk-action-box">
        <div class="risk-item">
          <span class="risk-label">风险等级</span>
          <span :class="['risk-value', getRiskClass(aiSignals.risk_level)]">{{ aiSignals.risk_level }}</span>
        </div>
        <div class="action-item">
          <span class="action-label">操作建议</span>
          <span class="action-value">{{ aiSignals.action_suggestion }}</span>
        </div>
      </div>
      <!-- 风险信号 -->
      <div v-if="aiSignals.risk_signals?.length" class="signals-box risk-signals">
        <div class="signals-title">⚠️ 风险信号</div>
        <div v-for="s in aiSignals.risk_signals" :key="s.type" class="signal-item">
          <span :class="['signal-severity', s.severity === '高' ? 'high' : s.severity === '中高' ? 'medium-high' : 'medium']">{{ s.severity }}</span>
          <span class="signal-type">{{ s.type }}</span>
          <span class="signal-desc">{{ s.description }}</span>
        </div>
      </div>
      <!-- 机会信号 -->
      <div v-if="aiSignals.opportunity_signals?.length" class="signals-box opportunity-signals">
        <div class="signals-title">💡 机会信号</div>
        <div v-for="s in aiSignals.opportunity_signals" :key="s.type" class="signal-item">
          <span class="signal-severity opportunity">{{ s.severity }}</span>
          <span class="signal-type">{{ s.type }}</span>
          <span class="signal-desc">{{ s.description }}</span>
        </div>
      </div>
    </div>
    <!-- 详细分析报告(可折叠) -->
    <details v-if="aiReport" class="analysis-details">
      <summary>查看完整分析报告</summary>
      <MarkdownRender :content="aiReport" />
    </details>
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
import { getCache, setCache } from "../services/cache";

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
const aiMetrics = ref(null);
const aiSignals = ref(null);
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

function formatChange(pct) {
  if (!pct) return "0.00%";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

function getChangeClass(pct) {
  if (!pct) return "";
  if (pct > 0) return "is-up";
  if (pct < 0) return "is-down";
  return "";
}

function getVolumeRatioClass(ratio) {
  if (!ratio) return "";
  if (ratio > 2) return "is-high-volume";
  if (ratio > 1.5) return "is-moderate-volume";
  if (ratio < 0.7) return "is-low-volume";
  return "";
}

function getTurnoverClass(rate) {
  if (!rate) return "";
  if (rate > 10) return "is-high-turnover";
  if (rate > 5) return "is-moderate-turnover";
  return "";
}

function getMaTrendClass(trend) {
  if (!trend) return "";
  if (trend === "多头排列") return "is-bullish";
  if (trend === "空头排列") return "is-bearish";
  return "";
}

function getDistanceClass(distance) {
  if (!distance) return "";
  if (distance > 5) return "is-near-high";
  if (distance < -10) return "is-far-from-high";
  return "";
}

function getRiskClass(level) {
  if (!level) return "";
  if (level === "高") return "is-high-risk";
  if (level === "中高") return "is-medium-high-risk";
  if (level === "中") return "is-medium-risk";
  return "is-low-risk";
}

async function loadPositions() {
  // Load cached positions first for immediate display
  const cachedPositions = getCache('kline_positions');
  if (cachedPositions) {
    positions.value = cachedPositions;
    selectedName.value = cachedPositions[0]?.name || "";
  }

  // Fetch fresh data
  try {
    const data = await apiGet("/api/positions");
    positions.value = data;
    setCache('kline_positions', data);
    if (!selectedName.value) {
      selectedName.value = data[0]?.name || "";
    }
  } catch (err) {
    // If fetch fails and no cache, set empty
    if (!cachedPositions) {
      positions.value = [];
    }
  }
}

async function checkDataStatus() {
  const cachedStatus = getCache('data_status', 60000); // 1 minute cache for status
  if (cachedStatus) {
    dataStatus.value = cachedStatus;
  }

  try {
    const status = await apiGet("/api/data/status");
    dataStatus.value = status;
    setCache('data_status', status);
  } catch (err) {
    if (!cachedStatus) {
      dataStatus.value = { available: false, error: err.message };
    }
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
  aiMetrics.value = null;
  aiSignals.value = null;
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
  aiMetrics.value = null;
  aiSignals.value = null;
  aiReport.value = "";
  try {
    const context = {
      stock: selectedName.value,
      bars: bars.value,
      quote: quote.value,
    };
    const result = await apiPost("/api/analysis/volume", context);
    aiMetrics.value = result.metrics || null;
    aiSignals.value = result.signals || null;
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
    // Auto load first position's data
    if (positions.value.length && selectedName.value) {
      await loadKline();
      await refreshQuote();
      // Trigger AI analysis for the first stock
      if (bars.value.length >= 5) {
        await runAIAnalysis();
      }
    }
  } catch (err) {
    emit("toast", err.message);
  }
});

onBeforeUnmount(stopMinuteTimer);
</script>

<style scoped>
/* Actions row - compact and responsive */
.actions-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stock-select {
  padding: 4px 8px;
  font-size: 13px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  min-width: 120px;
}

.mode-tabs.compact {
  display: inline-flex;
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  background: var(--panel);
}

.tab-btn.compact {
  min-height: 28px;
  border: 0;
  border-right: 1px solid var(--line);
  padding: 4px 10px;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
}

.tab-btn.compact:last-child {
  border-right: 0;
}

.tab-btn.compact.active {
  color: #fff;
  background: var(--primary);
}

.btn.compact {
  padding: 4px 10px;
  font-size: 12px;
  min-height: 28px;
}

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

/* AI Analysis Summary Styles */
.analysis-summary {
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

.stock-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
}

.analysis-date {
  font-size: 13px;
  color: var(--muted);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  background: var(--table-header);
  border-radius: 6px;
}

.metric-label {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
}

/* Price changes */
.is-up {
  color: #dc2626;
}

.is-down {
  color: #16a34a;
}

/* Volume ratio highlighting */
.is-high-volume {
  color: #dc2626;
  font-weight: 700;
}

.is-moderate-volume {
  color: #f59e0b;
}

.is-low-volume {
  color: #6b7280;
}

/* Turnover highlighting */
.is-high-turnover {
  color: #dc2626;
  font-weight: 700;
}

.is-moderate-turnover {
  color: #f59e0b;
}

/* MA trend */
.is-bullish {
  color: #16a34a;
}

.is-bearish {
  color: #dc2626;
}

/* Distance from high */
.is-near-high {
  color: #16a34a;
}

.is-far-from-high {
  color: #dc2626;
}

/* Patterns section */
.patterns-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.patterns-label {
  font-size: 13px;
  color: var(--muted);
  font-weight: 600;
}

.pattern-tag {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--primary);
  color: white;
  border-radius: 4px;
}

/* Risk action box - 重点标红 */
.risk-action-box {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 12px 0;
  padding: 12px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
}

.risk-item, .action-item {
  display: flex;
  flex-direction: column;
}

.risk-label, .action-label {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 4px;
}

.risk-value {
  font-size: 18px;
  font-weight: 700;
}

.is-high-risk {
  color: #dc2626;
}

.is-medium-high-risk {
  color: #f59e0b;
}

.is-medium-risk {
  color: #6b7280;
}

.is-low-risk {
  color: #16a34a;
}

.action-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
}

/* Signals box */
.signals-box {
  margin: 12px 0;
  padding: 10px 12px;
  border-radius: 8px;
}

.risk-signals {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.opportunity-signals {
  background: rgba(22, 163, 74, 0.08);
  border: 1px solid rgba(22, 163, 74, 0.15);
}

.signals-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
}

.risk-signals .signals-title {
  color: #dc2626;
}

.opportunity-signals .signals-title {
  color: #16a34a;
}

.signal-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
}

.signal-severity {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.signal-severity.high {
  background: #dc2626;
  color: white;
}

.signal-severity.medium-high {
  background: #f59e0b;
  color: white;
}

.signal-severity.medium {
  background: #6b7280;
  color: white;
}

.signal-severity.opportunity {
  background: #16a34a;
  color: white;
}

.signal-type {
  font-weight: 600;
  color: var(--ink);
}

.signal-desc {
  color: var(--muted);
}

/* Details section */
.analysis-details {
  margin-top: 16px;
  border-top: 1px solid var(--line);
  padding-top: 12px;
}

.analysis-details summary {
  cursor: pointer;
  font-size: 14px;
  color: var(--muted);
  font-weight: 600;
  padding: 4px 0;
}

.analysis-details summary:hover {
  color: var(--primary);
}

.analysis-details[open] summary {
  margin-bottom: 12px;
}
</style>
