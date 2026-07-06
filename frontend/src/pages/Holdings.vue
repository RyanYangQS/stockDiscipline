<template>
  <Card title="持仓操作建议表" icon="holdings" tone="primary">
    <template #actions>
      <button class="btn primary" @click="rebuild">重新生成建议</button>
    </template>
    <div class="table-wrap">
      <table class="holdings-table">
        <thead><tr><th>标的</th><th>持仓</th><th>成本</th><th>现价</th><th class="col-pnl">盈亏</th><th>分类</th><th>情景</th><th>减仓触发</th><th>止损触发</th><th>加仓参考</th><th class="col-action">操作建议</th></tr></thead>
        <tbody>
          <tr v-for="row in advice" :key="row.name">
            <td><strong>{{ row.name }}</strong></td><td>{{ row.quantity }}股</td><td>{{ money(row.cost_price) }}元</td><td>{{ money(row.current_price) }}元</td>
            <td class="col-pnl" :class="pnlClass(row.pnl_ratio)">{{ row.pnl_ratio_text || pct(row.pnl_ratio) }}</td>
            <td>{{ row.category }}</td><td><span class="risk-tag" :class="riskClass(row.risk_level)">{{ row.scenario }}</span></td>
            <td>{{ row.trim_trigger }}</td><td>{{ row.stop_trigger }}</td><td>{{ row.add_reference }}</td>
            <td class="col-action">{{ row.action_advice }}<br><span class="text-muted">{{ row.reason }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </Card>
  <div class="grid">
    <Card title="新增持仓" icon="holdings" tone="primary">
      <form @submit.prevent="savePosition">
        <div class="form-grid">
          <label>代码<input v-model="form.symbol" /></label><label>标的<input v-model="form.name" required /></label>
          <label>数量<input v-model.number="form.quantity" type="number" min="1" required /></label><label>成本价<input v-model.number="form.cost_price" type="number" step="0.01" required /></label>
          <label>当前价<input v-model.number="form.current_price" type="number" step="0.01" required /></label>
          <label>分类<select v-model="form.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
          <label>行业<input v-model="form.sector" /></label><label>备注<input v-model="form.note" /></label>
        </div>
        <button class="btn primary" type="submit">保存持仓</button>
      </form>
    </Card>
    <Card title="持仓维护" icon="holdings" tone="default">
      <div v-for="p in positions" :key="p.id" class="card" style="margin-bottom: 15px; padding: 15px;">
        <h3>{{ p.name }}</h3>
        <div class="form-grid">
          <label>数量<input v-model.number="p.quantity" type="number" /></label>
          <label>成本<input v-model.number="p.cost_price" type="number" step="0.01" /></label>
          <label>现价<input v-model.number="p.current_price" type="number" step="0.01" /></label>
          <label>分类<select v-model="p.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
        </div>
        <div class="head-actions"><button class="btn primary" @click="update(p)">保存</button><button class="btn danger" @click="remove(p)">删除</button></div>
      </div>
      <p v-if="!positions.length" class="text-muted">暂无持仓记录</p>
    </Card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import Card from "../components/Card.vue";
import { apiDelete, apiGet, apiPost, apiPut } from "../services/api";
import { money, pct, riskClass } from "../services/format";

function pnlClass(ratio) {
  if (ratio > 0) return 'pnl-positive';
  if (ratio < 0) return 'pnl-negative';
  return '';
}

const emit = defineEmits(["toast"]);
const advice = ref([]);
const positions = ref([]);
const categories = ["核心赛道", "观察仓", "弱势跟风", "高风险票", "恐慌释放观察"];
const form = reactive({ symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });

async function load() {
  [advice.value, positions.value] = await Promise.all([apiGet("/api/advice"), apiGet("/api/positions")]);
}
async function rebuild() { await apiPost("/api/advice/rebuild"); await load(); emit("toast", "建议已重新生成"); }
async function savePosition() { await apiPost("/api/positions", form); await rebuild(); Object.assign(form, { symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" }); }
async function update(p) { await apiPut(`/api/positions/${p.id}`, p); await rebuild(); }
async function remove(p) { await apiDelete(`/api/positions/${p.id}`); await rebuild(); }

onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>

<style scoped>
/* Responsive table with auto-fit columns */
.holdings-table {
  width: 100%;
  table-layout: auto;
  border-collapse: collapse;
}

.holdings-table th,
.holdings-table td {
  min-width: 60px;
  padding: 8px 12px;
  white-space: nowrap;
}

/* Sticky header for long tables */
.holdings-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.holdings-table thead th {
  background: var(--table-header);
  border-bottom: 2px solid var(--line);
}

/* Highlight 盈亏 column - red/green */
.col-pnl {
  font-weight: 600;
}

.pnl-positive {
  color: var(--ok);
}

.pnl-negative {
  color: var(--danger);
}

/* Highlight 操作建议 column - wider for content */
.col-action {
  min-width: 180px;
  white-space: normal;
}

/* Symmetrical cards - same height grid */
.grid {
  grid-template-columns: repeat(2, 1fr);
  align-items: stretch;
}

.grid > .card {
  height: 100%;
}

/* Aligned forms */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
</style>