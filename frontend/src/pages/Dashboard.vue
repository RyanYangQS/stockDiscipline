<template>
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
        <button class="btn" @click="load">刷新</button>
      </template>
      <div v-for="item in advice" :key="item.name" class="risk-item" :class="riskClass(item.risk_level)">
        <span class="risk-tag" :class="riskClass(item.risk_level)">{{ item.risk_level }}</span>
        <strong>{{ item.name }}</strong>：{{ item.scenario }}，{{ item.action_advice }}
      </div>
      <p v-if="!advice.length" class="text-muted">暂无风险项</p>
    </Card>
    <Card title="最新 AI 日报" icon="ai" tone="primary">
      <template #actions>
        <button class="btn" @click="load">刷新</button>
        <button class="btn primary" @click="generateDailyReport">生成日报</button>
      </template>
      <div v-if="keyHighlights.length" class="key-highlights">
        <div v-for="h in keyHighlights" :key="h.label" class="highlight-card" :class="h.tone">
          <span class="highlight-label">{{ h.label }}</span>
          <span class="highlight-value">{{ h.value }}</span>
        </div>
      </div>
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
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const summary = ref({});
const advice = ref([]);
const reports = ref([]);
let refreshTimer = null;

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

// Extract key highlights from AI report
const keyHighlights = computed(() => {
  const report = latestReport.value;
  if (!report) return [];

  const highlights = [];
  // Extract 盈亏 section
  const pnlMatch = report.match(/盈亏[^：:]*[：:]\s*([^\n]+)/);
  if (pnlMatch) {
    highlights.push({ label: '盈亏', value: pnlMatch[1].slice(0, 50), tone: 'primary' });
  }
  // Extract 建议 section
  const adviceMatch = report.match(/建议[^：:]*[：:]\s*([^\n]+)/);
  if (adviceMatch) {
    highlights.push({ label: '建议', value: adviceMatch[1].slice(0, 50), tone: 'success' });
  }
  // Extract 风险 section
  const riskMatch = report.match(/风险[^：:]*[：:]\s*([^\n]+)/);
  if (riskMatch) {
    highlights.push({ label: '风险', value: riskMatch[1].slice(0, 50), tone: 'danger' });
  }

  return highlights;
});

async function load() {
  try {
    const [s, a, r] = await Promise.all([apiGet("/api/summary"), apiGet("/api/advice"), apiGet("/api/analysis/reports")]);
    summary.value = s;
    advice.value = a;
    reports.value = r;
  } catch (err) {
    emit("toast", err.message);
  }
}

async function generateDailyReport() {
  try {
    await apiPost("/api/analysis/daily");
    await load();
    emit("toast", "AI日报已生成");
  } catch (err) {
    emit("toast", err.message);
  }
}

function startRefreshTimer() {
  stopRefreshTimer();
  // Refresh every minute (same as price updates)
  refreshTimer = setInterval(load, 60000);
}

function stopRefreshTimer() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

onMounted(load);
onMounted(startRefreshTimer);
onBeforeUnmount(stopRefreshTimer);
</script>

<style scoped>
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

/* Key highlights section */
.key-highlights {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.highlight-card {
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  border-radius: 6px;
  background: var(--table-header);
  min-width: 120px;
}

.highlight-card.primary {
  border-left: 3px solid var(--primary);
}

.highlight-card.success {
  border-left: 3px solid var(--ok);
}

.highlight-card.danger {
  border-left: 3px solid var(--danger);
}

.highlight-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 4px;
}

.highlight-value {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.4;
}
</style>