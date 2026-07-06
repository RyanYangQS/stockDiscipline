<template>
  <section class="metrics">
    <div v-for="item in metrics" :key="item.label" class="metric" :class="item.tone">
      <span>{{ item.label }}</span><strong>{{ item.value }}</strong>
    </div>
  </section>
  <section class="grid">
    <div class="panel">
      <div class="panel-head"><h2>风险优先级</h2><button class="btn" @click="load">刷新</button></div>
      <p v-for="item in advice" :key="item.name">
        <span class="tag" :class="riskClass(item.risk_level)">{{ item.risk_level }}</span>
        <strong>{{ item.name }}</strong>：{{ item.scenario }}，{{ item.action_advice }}
      </p>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>最新 AI 日报</h2></div>
      <div class="report">{{ latestReport || "还没有生成 AI 日报。" }}</div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { apiGet } from "../services/api";
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const summary = ref({});
const advice = ref([]);
const reports = ref([]);

const metrics = computed(() => [
  { label: "持仓数量", value: summary.value.position_count || 0 },
  { label: "当前市值", value: `${money(summary.value.total_value)}元` },
  { label: "总盈亏", value: `${money(summary.value.total_pnl)}元`, tone: summary.value.total_pnl < 0 ? "danger" : "ok" },
  { label: "总盈亏率", value: pct(summary.value.total_pnl_ratio), tone: summary.value.total_pnl_ratio < 0 ? "danger" : "ok" },
  { label: "高风险", value: summary.value.high_risk_count || 0, tone: "danger" },
  { label: "纪律拦截", value: summary.value.discipline_blocked_count || 0, tone: "danger" }
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

