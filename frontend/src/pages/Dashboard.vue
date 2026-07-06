<template>
  <div class="grid three">
    <div v-for="item in metrics" :key="item.label" class="metric-card" :class="item.tone">
      <div class="metric-icon-wrap" :class="item.tone"><Icon :name="item.icon" :size="20" /></div>
      <div class="metric-label">{{ item.label }}</div>
      <div class="metric-value" :class="item.tone">{{ item.value }}</div>
    </div>
  </div>
  <div class="grid">
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
      <div class="report">{{ latestReport || "还没有生成 AI 日报。" }}</div>
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Icon from "../components/Icons.vue";
import Card from "../components/Card.vue";
import { apiGet } from "../services/api";
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const summary = ref({});
const advice = ref([]);
const reports = ref([]);

const metrics = computed(() => [
  { label: "持仓数量", value: summary.value.position_count || 0, icon: "holdings", tone: "primary" },
  { label: "当前市值", value: `${money(summary.value.total_value)}元`, icon: "money", tone: "primary" },
  { label: "总盈亏", value: `${money(summary.value.total_pnl)}元`, icon: "chart", tone: summary.value.total_pnl < 0 ? "danger" : "success" },
  { label: "总盈亏率", value: pct(summary.value.total_pnl_ratio), icon: "chart", tone: summary.value.total_pnl_ratio < 0 ? "danger" : "success" },
  { label: "高风险", value: summary.value.high_risk_count || 0, icon: "warning", tone: "danger" },
  { label: "纪律拦截", value: summary.value.discipline_blocked_count || 0, icon: "warning", tone: "danger" }
]);

const latestReport = computed(() => reports.value[0]?.content || "");

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

onMounted(load);
</script>