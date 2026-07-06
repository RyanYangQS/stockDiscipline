<template>
  <Card title="专业 K线量能图" icon="kline" tone="primary">
    <template #subtitle>使用 KLineCharts 展示蜡烛图与成交量指标</template>
    <template #actions>
      <select v-model="selectedName" @change="onStockChange"><option v-for="p in positions" :key="p.id" :value="p.name">{{ p.name }}</option></select>
      <button class="btn" :disabled="loading" @click="fetchRealtime">{{ loading ? "获取中..." : "自动获取K线" }}</button>
      <button class="btn primary" :disabled="aiLoading" @click="runAIAnalysis">{{ aiLoading ? "分析中..." : "AI量能分析" }}</button>
    </template>
    <div v-if="dataStatus" class="data-status">
      <span :class="dataStatus.available ? 'status-ok' : 'status-error'">
        {{ dataStatus.available ? `AKShare 已连接 (${dataStatus.stocks_count} 只股票)` : `数据源未连接: ${dataStatus.error}` }}
      </span>
    </div>
    <KlineChart :bars="bars" />
    <p v-if="!bars.length" class="text-muted">暂无K线数据，请点击"自动获取K线"</p>
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
import { onMounted, ref } from "vue";
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
const aiLoading = ref(false);
const aiReport = ref("");

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
  bars.value = await apiGet(`/api/kline?name=${encodeURIComponent(selectedName.value)}&limit=160`);
}

async function onStockChange() {
  bars.value = [];
  quote.value = null;
  aiReport.value = "";
  await loadKline();
}

async function fetchRealtime() {
  if (!selectedName.value) return;
  loading.value = true;
  try {
    const result = await apiGet(`/api/kline/realtime?name=${encodeURIComponent(selectedName.value)}&days=60`);
    if (result.bars && result.bars.length) {
      bars.value = result.bars;
      emit("toast", `获取 ${result.bars.length} 条K线数据`);
    } else {
      emit("toast", "未获取到K线数据，请检查股票名称或安装AKShare");
    }
  } catch (err) {
    emit("toast", err.message);
  } finally {
    loading.value = false;
  }
}

async function refreshQuote() {
  if (!selectedName.value) return;
  try {
    quote.value = await apiGet(`/api/quote/?name=${encodeURIComponent(selectedName.value)}`);
  } catch (err) {
    emit("toast", err.message);
  }
}

async function runAIAnalysis() {
  if (!bars.value.length) {
    emit("toast", "请先获取K线数据");
    return;
  }
  aiLoading.value = true;
  try {
    const context = {
      stock: selectedName.value,
      bars: bars.value.slice(-30),
      quote: quote.value,
    };
    await apiPost("/api/analysis/daily", { extra_note: `请分析 ${selectedName.value} 的量能特征和K线结构` });
    const reports = await apiGet("/api/analysis/reports");
    aiReport.value = reports[0]?.content || "";
    emit("toast", "AI分析已生成");
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