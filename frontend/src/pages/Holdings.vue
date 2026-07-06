<template>
  <Card title="持仓操作建议表" icon="holdings" tone="primary">
    <template #actions>
      <button class="btn primary" @click="rebuild">重新生成建议</button>
    </template>
    <div class="table-wrap">
      <table>
        <thead><tr><th>标的</th><th>持仓</th><th>成本</th><th>现价</th><th>盈亏</th><th>分类</th><th>情景</th><th>减仓触发</th><th>止损触发</th><th>加仓参考</th><th>操作建议</th></tr></thead>
        <tbody>
          <tr v-for="row in advice" :key="row.name">
            <td><strong>{{ row.name }}</strong></td><td>{{ row.quantity }}股</td><td>{{ money(row.cost_price) }}元</td><td>{{ money(row.current_price) }}元</td>
            <td>{{ row.pnl_ratio_text || pct(row.pnl_ratio) }}</td><td>{{ row.category }}</td><td><span class="risk-tag" :class="riskClass(row.risk_level)">{{ row.scenario }}</span></td>
            <td>{{ row.trim_trigger }}</td><td>{{ row.stop_trigger }}</td><td>{{ row.add_reference }}</td><td>{{ row.action_advice }}<br><span class="text-muted">{{ row.reason }}</span></td>
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