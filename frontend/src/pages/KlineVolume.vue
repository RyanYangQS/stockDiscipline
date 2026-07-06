<template>
  <Card title="专业 K线量能图" icon="kline" tone="primary">
    <template #subtitle>使用 KLineCharts 展示蜡烛图与成交量指标</template>
    <template #actions>
      <select v-model="selectedName" @change="loadKline"><option v-for="p in positions" :key="p.id" :value="p.name">{{ p.name }}</option></select>
      <button class="btn" @click="loadKline">刷新K线</button>
    </template>
    <KlineChart :bars="bars" />
  </Card>
  <div class="grid">
    <Card title="录入量能快照" icon="chart" tone="primary">
      <form @submit.prevent="saveVolume">
        <div class="form-grid">
          <label>标的<input v-model="volumeForm.name" /></label><label>交易日<input v-model="volumeForm.trade_date" type="date" /></label>
          <label>量能状态<select v-model="volumeForm.volume_state"><option>温和放量</option><option>异常放量</option><option>放量滞涨</option><option>缩量抗跌</option><option>缩量阴跌</option><option>天量换手</option></select></label>
          <label>量比<input v-model.number="volumeForm.volume_ratio" type="number" step="0.01" /></label>
          <label>换手率<input v-model.number="volumeForm.turnover_rate" type="number" step="0.01" /></label>
          <label>买入评分<input v-model.number="volumeForm.buy_watch_score" type="number" min="0" max="100" /></label>
          <label>卖出风险<input v-model.number="volumeForm.sell_risk_score" type="number" min="0" max="100" /></label>
          <label>建仓评分<input v-model.number="volumeForm.accumulation_score" type="number" min="0" max="100" /></label>
        </div>
        <button class="btn primary" type="submit">保存量能</button>
      </form>
    </Card>
    <Card title="录入日K" icon="kline" tone="default">
      <form @submit.prevent="saveBar">
        <div class="form-grid">
          <label>标的<input v-model="barForm.name" /></label><label>日期<input v-model="barForm.trade_date" type="date" /></label>
          <label>开盘<input v-model.number="barForm.open_price" type="number" step="0.01" /></label><label>最高<input v-model.number="barForm.high_price" type="number" step="0.01" /></label>
          <label>最低<input v-model.number="barForm.low_price" type="number" step="0.01" /></label><label>收盘<input v-model.number="barForm.close_price" type="number" step="0.01" /></label>
          <label>成交量<input v-model.number="barForm.volume" type="number" /></label><label>成交额<input v-model.number="barForm.amount" type="number" /></label>
        </div>
        <button class="btn primary" type="submit">保存日K</button>
      </form>
    </Card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import Card from "../components/Card.vue";
import KlineChart from "../components/KlineChart.vue";
import { apiGet, apiPost } from "../services/api";
import { today } from "../services/format";

const emit = defineEmits(["toast"]);
const positions = ref([]);
const selectedName = ref("");
const bars = ref([]);
const volumeForm = reactive({ name: "", trade_date: today(), volume_state: "温和放量", volume_ratio: 1, turnover_rate: 0, buy_watch_score: 50, sell_risk_score: 50, accumulation_score: 50 });
const barForm = reactive({ name: "", trade_date: today(), open_price: 0, high_price: 0, low_price: 0, close_price: 0, volume: 0, amount: 0, turnover_rate: 0 });

async function loadPositions() {
  positions.value = await apiGet("/api/positions");
  selectedName.value ||= positions.value[0]?.name || "";
  volumeForm.name ||= selectedName.value;
  barForm.name ||= selectedName.value;
}
async function loadKline() {
  if (!selectedName.value) return;
  bars.value = await apiGet(`/api/kline?name=${encodeURIComponent(selectedName.value)}&limit=160`);
}
async function saveVolume() {
  await apiPost("/api/volume", volumeForm);
  await apiPost("/api/advice/rebuild");
  emit("toast", "量能已保存");
}
async function saveBar() {
  await apiPost("/api/kline", barForm);
  await loadKline();
  emit("toast", "K线已保存");
}
onMounted(async () => {
  try { await loadPositions(); await loadKline(); } catch (err) { emit("toast", err.message); }
});
</script>