<template>
  <!-- Auto-refresh indicator -->
  <div v-if="isRefreshing" class="refresh-indicator">
    <span class="refresh-spinner">●</span>
    <span>正在更新数据...</span>
  </div>
  <!-- AI report generation indicator -->
  <div v-if="isGeneratingReport" class="refresh-indicator ai">
    <span class="refresh-spinner">●</span>
    <span>正在生成AI日报...</span>
  </div>
  <div class="grid three">
    <div v-for="item in metrics" :key="item.label" class="metric-card" :class="getMetricClass(item)">
      <div class="metric-icon-wrap" :class="getMetricClass(item)"><Icon :name="item.icon" :size="20" /></div>
      <div class="metric-label">{{ item.label }}</div>
      <div class="metric-value" :class="getMetricClass(item)">{{ item.value }}</div>
    </div>
  </div>
  <div class="stack-layout">
    <Card title="风险优先级" icon="warning" tone="danger">
      <template #actions>
        <button class="btn" :disabled="isRefreshing" @click="load(false)">{{ isRefreshing ? '刷新中...' : '刷新' }}</button>
      </template>
      <div v-for="item in advice" :key="item.name" class="risk-item" :class="riskClass(item.risk_level)">
        <span class="risk-tag" :class="riskClass(item.risk_level)">{{ item.risk_level }}</span>
        <strong>{{ item.name }}</strong>：{{ item.scenario }}，{{ item.action_advice }}
      </div>
      <p v-if="!advice.length" class="text-muted">暂无风险项</p>
    </Card>
    <Card title="最新 AI 日报" icon="ai" tone="primary">
      <template #actions>
        <button class="btn" :disabled="isRefreshing" @click="load(false)">{{ isRefreshing ? '刷新中...' : '刷新' }}</button>
        <button class="btn primary" :disabled="isRefreshing" @click="generateDailyReport">生成日报</button>
      </template>
      <MarkdownRender v-if="latestReport" :content="latestReport" />
      <p v-else class="text-muted">还没有生成 AI 日报，点击"生成日报"按钮。</p>
    </Card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Icon from "../components/Icons.vue";
import Card from "../components/Card.vue";
import MarkdownRender from "../components/MarkdownRender.vue";
import { apiGet, apiPost } from "../services/api";
import { getCache, setCache } from "../services/cache";
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const summary = ref({});
const advice = ref([]);
const reports = ref([]);
const isRefreshing = ref(false);
const isGeneratingReport = ref(false);
let refreshTimer = null;
let reportTimer = null;
let refreshCounter = 0;

const metrics = computed(() => [
  { label: "持仓数量", value: summary.value.position_count || 0, icon: "holdings", tone: "primary", type: "neutral" },
  { label: "当前市值", value: `${money(summary.value.total_value)}元`, icon: "money", tone: "primary", type: "neutral" },
  { label: "总盈亏", value: `${money(summary.value.total_pnl)}元`, icon: "chart", type: "pnl", isProfit: summary.value.total_pnl >= 0 },
  { label: "总盈亏率", value: pct(summary.value.total_pnl_ratio), icon: "chart", type: "pnl", isProfit: summary.value.total_pnl_ratio >= 0 },
  { label: "高风险", value: summary.value.high_risk_count || 0, icon: "warning", tone: "danger", type: "neutral" },
  { label: "纪律拦截", value: summary.value.discipline_blocked_count || 0, icon: "warning", tone: "danger", type: "neutral" }
]);

function getMetricClass(item) {
  if (item.type === 'pnl') {
    return item.isProfit ? 'profit' : 'loss';
  }
  return item.tone;
}

const latestReport = computed(() => reports.value[0]?.content || "");

async function load(showNotification = false, useCache = true) {
  // Load cached data first if available (for immediate display)
  if (useCache && !showNotification) {
    const cachedSummary = getCache('dashboard_summary');
    const cachedAdvice = getCache('dashboard_advice');
    const cachedReports = getCache('dashboard_reports');

    if (cachedSummary) summary.value = cachedSummary;
    if (cachedAdvice) advice.value = cachedAdvice;
    if (cachedReports) reports.value = cachedReports;
  }

  if (showNotification) {
    isRefreshing.value = true;
  }

  try {
    // Fetch fresh data
    const [s, a, r] = await Promise.all([
      apiGet("/api/summary"),
      apiGet("/api/advice"),
      apiGet("/api/analysis/reports?report_type=daily")
    ]);

    // Update state and cache
    summary.value = s;
    advice.value = a;
    reports.value = r;

    setCache('dashboard_summary', s);
    setCache('dashboard_advice', a);
    setCache('dashboard_reports', r);

    if (showNotification) {
      emit("toast", "数据已自动更新");
    }
  } catch (err) {
    emit("toast", err.message);
  } finally {
    isRefreshing.value = false;
  }
}

async function generateDailyReport() {
  isGeneratingReport.value = true;
  try {
    await apiPost("/api/analysis/daily");
    await load();
    emit("toast", "AI日报已生成");
  } catch (err) {
    emit("toast", err.message);
  } finally {
    isGeneratingReport.value = false;
  }
}

function startRefreshTimer() {
  stopRefreshTimer();
  // Quick data refresh every minute
  refreshTimer = setInterval(() => {
    refreshCounter++;
    load(true);
    // Generate AI report every 10 minutes (after 10 quick refreshes)
    if (refreshCounter >= 10) {
      refreshCounter = 0;
      generateDailyReport();
    }
  }, 60000);
}

function stopRefreshTimer() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  if (reportTimer) {
    clearInterval(reportTimer);
    reportTimer = null;
  }
}

onMounted(load);
onMounted(startRefreshTimer);
onBeforeUnmount(stopRefreshTimer);
</script>

<style scoped>
/* Refresh indicator */
.refresh-indicator {
  position: fixed;
  top: 16px;
  right: 16px;
  background: var(--primary);
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: fadeIn 0.3s ease;
}

.refresh-spinner {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Balanced grid - equal height cards */
.grid.three {
  grid-template-columns: repeat(3, minmax(180px, 1fr));
}

/* Stack layout for risk and AI report */
.stack-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stack-layout > * {
  width: 100%;
}

/* Metric card profit/loss styling */
.metric-card.profit {
  border-color: #dc2626;
}

.metric-card.profit .metric-icon-wrap {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
}

.metric-card.profit .metric-value {
  color: #dc2626;
}

.metric-card.loss {
  border-color: #16a34a;
}

.metric-card.loss .metric-icon-wrap {
  background: rgba(22, 163, 74, 0.1);
  color: #16a34a;
}

.metric-card.loss .metric-value {
  color: #16a34a;
}

/* Risk items - improved dark mode visibility */
.risk-item {
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: var(--table-header);
  color: var(--ink);
  line-height: 1.5;
  text-align: left;
}

.risk-item.is-high {
  background: rgba(220, 38, 38, 0.1);
  border-left: 3px solid #dc2626;
}

.risk-item.is-medium-high {
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid #f59e0b;
}

.risk-item.is-medium {
  background: rgba(107, 114, 128, 0.1);
  border-left: 3px solid #6b7280;
}

.risk-item.is-low {
  background: rgba(22, 163, 74, 0.1);
  border-left: 3px solid #16a34a;
}

/* Risk tag in Dashboard */
.risk-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
}
.risk-tag.is-high { background: #dc2626; color: white; }
.risk-tag.is-medium-high { background: #f59e0b; color: white; }
.risk-tag.is-medium { background: #6b7280; color: white; }
.risk-tag.is-low { background: #16a34a; color: white; }

/* Dark mode fixes */
@media (prefers-color-scheme: dark) {
  .risk-item {
    background: rgba(0, 0, 0, 0.2);
    color: #f3f4f6;
  }

  .risk-item strong {
    color: #f3f4f6;
  }

  .metric-card.profit .metric-icon-wrap {
    background: rgba(220, 38, 38, 0.2);
  }

  .metric-card.loss .metric-icon-wrap {
    background: rgba(22, 163, 74, 0.2);
  }
}
</style>
