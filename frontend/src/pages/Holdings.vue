<template>
  <Card title="持仓操作建议表" icon="holdings" tone="primary">
    <template #actions>
      <button class="btn" @click="showAddModal = true">新增持仓</button>
      <button class="btn" :disabled="rebuilding" @click="rebuild">{{ rebuilding ? '生成中...' : '本地规则建议' }}</button>
      <button class="btn primary" :disabled="aiLoading" @click="generateAiAdvice">{{ aiLoading ? '分析中...' : 'AI生成建议' }}</button>
      <a class="btn" href="/api/advice.csv">导出 CSV</a>
    </template>
    <div class="table-wrap">
      <table class="holdings-table">
        <thead>
          <tr>
            <th class="col-name">标的</th>
            <th class="col-qty">持仓</th>
            <th class="col-cost">成本</th>
            <th class="col-price">现价</th>
            <th class="col-pnl">盈亏</th>
            <th class="col-cat">分类</th>
            <th class="col-scenario">情景判断</th>
            <th class="col-trigger">减仓触发</th>
            <th class="col-trigger">止损触发</th>
            <th class="col-add">加仓参考</th>
            <th class="col-advice">操作建议</th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in advice" :key="row.name">
            <td class="col-name">
              <strong>{{ row.name }}</strong>
              <br><span class="text-muted small">{{ row.symbol || '-' }}</span>
            </td>
            <td class="col-qty">{{ row.quantity }}股</td>
            <td class="col-cost">{{ money(row.cost_price) }}元</td>
            <td class="col-price">{{ money(row.current_price) }}元</td>
            <td class="col-pnl" :class="pnlClass(row.pnl_ratio)">{{ row.pnl_ratio_text || pct(row.pnl_ratio) }}</td>
            <td class="col-cat">{{ row.category }}</td>
            <td class="col-scenario"><span class="risk-tag" :class="riskClass(row.risk_level)">{{ row.scenario }}</span></td>
            <td class="col-trigger">{{ row.trim_trigger }}</td>
            <td class="col-trigger">{{ row.stop_trigger }}</td>
            <td class="col-add">{{ row.add_reference }}</td>
            <td class="col-advice">
              <div class="advice-content">
                <span class="advice-action">{{ row.action_advice }}</span>
                <span class="advice-reason text-muted">{{ row.reason }}</span>
              </div>
            </td>
            <td class="col-action">
              <div class="action-buttons">
                <button class="btn-text" @click="openEditModal(row)">编辑</button>
                <button class="btn-text danger" @click="remove(row)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!advice.length" class="text-muted">暂无持仓记录，点击"新增持仓"添加</p>
  </Card>

  <!-- 新增持仓弹窗 -->
  <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>新增持仓</h3>
        <button class="modal-close" @click="showAddModal = false">×</button>
      </div>
      <form @submit.prevent="saveNewPosition">
        <div class="form-grid">
          <label>股票代码<input v-model="newForm.symbol" placeholder="如: sh.600519" /></label>
          <label>股票名称<input v-model="newForm.name" required placeholder="必填" /></label>
          <label>持仓数量<input v-model.number="newForm.quantity" type="number" min="1" required /></label>
          <label>成本价<input v-model.number="newForm.cost_price" type="number" step="0.01" required /></label>
          <label>当前价
            <div class="price-input-group">
              <input v-model.number="newForm.current_price" type="number" step="0.01" required />
              <button class="btn-mini" @click="fetchPriceForNew" type="button">获取实时价格</button>
            </div>
          </label>
          <label>分类<select v-model="newForm.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
          <label>行业<input v-model="newForm.sector" placeholder="如: 酒类" /></label>
          <label>备注<input v-model="newForm.note" placeholder="持仓说明" /></label>
        </div>
        <div class="modal-actions">
          <button class="btn" type="button" @click="showAddModal = false">取消</button>
          <button class="btn primary" type="submit">保存</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 编辑持仓弹窗 -->
  <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>编辑持仓 - {{ editForm.name }}</h3>
        <button class="modal-close" @click="showEditModal = false">×</button>
      </div>
      <form @submit.prevent="saveEditPosition">
        <div class="form-grid">
          <label>股票代码<input v-model="editForm.symbol" placeholder="如: sh.600519" /></label>
          <label>股票名称<input v-model="editForm.name" required /></label>
          <label>持仓数量<input v-model.number="editForm.quantity" type="number" min="1" required /></label>
          <label>成本价<input v-model.number="editForm.cost_price" type="number" step="0.01" required /></label>
          <label>当前价
            <div class="price-input-group">
              <input v-model.number="editForm.current_price" type="number" step="0.01" required />
              <button class="btn-mini" @click="fetchPriceForEdit" type="button">获取实时价格</button>
            </div>
          </label>
          <label>分类<select v-model="editForm.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
          <label>行业<input v-model="editForm.sector" /></label>
          <label>备注<input v-model="editForm.note" /></label>
        </div>
        <div class="modal-actions">
          <button class="btn" type="button" @click="showEditModal = false">取消</button>
          <button class="btn primary" type="submit">保存</button>
        </div>
      </form>
    </div>
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
const rebuilding = ref(false);
const aiLoading = ref(false);
const showAddModal = ref(false);
const showEditModal = ref(false);
const newForm = reactive({ symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });
const editForm = reactive({ id: 0, symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });

async function load() {
  [advice.value, positions.value] = await Promise.all([apiGet("/api/advice"), apiGet("/api/positions")]);
}

async function rebuild() {
  rebuilding.value = true;
  try {
    await apiPost("/api/advice/rebuild");
    await load();
    emit("toast", "本地规则建议已生成");
  } finally {
    rebuilding.value = false;
  }
}

async function generateAiAdvice() {
  aiLoading.value = true;
  try {
    const result = await apiPost("/api/advice/ai");
    await load();
    emit("toast", `AI持仓建议已生成 (${result.advice?.length || 0}只持仓)`);
  } finally {
    aiLoading.value = false;
  }
}

function openEditModal(row) {
  const position = positions.value.find(p => p.id === row.position_id);
  if (!position) return;
  Object.assign(editForm, {
    id: position.id,
    symbol: position.symbol || "",
    name: position.name,
    quantity: position.quantity,
    cost_price: position.cost_price,
    current_price: position.current_price,
    category: position.category,
    sector: position.sector || "",
    note: position.note || "",
  });
  showEditModal.value = true;
}

async function fetchPriceForNew() {
  if (!newForm.name) {
    emit("toast", "请先填写股票名称");
    return;
  }
  try {
    const quote = await apiGet(`/api/quote?name=${newForm.name}&symbol=${newForm.symbol || ''}`);
    if (quote && quote.current_price) {
      newForm.current_price = quote.current_price;
      emit("toast", `现价已更新: ${quote.current_price}元`);
    } else {
      emit("toast", "无法获取实时价格");
    }
  } catch (err) {
    emit("toast", `获取价格失败: ${err.message}`);
  }
}

async function fetchPriceForEdit() {
  if (!editForm.name) {
    emit("toast", "请先填写股票名称");
    return;
  }
  try {
    const quote = await apiGet(`/api/quote?name=${editForm.name}&symbol=${editForm.symbol || ''}`);
    if (quote && quote.current_price) {
      editForm.current_price = quote.current_price;
      emit("toast", `现价已更新: ${quote.current_price}元`);
    } else {
      emit("toast", "无法获取实时价格");
    }
  } catch (err) {
    emit("toast", `获取价格失败: ${err.message}`);
  }
}

async function saveNewPosition() {
  if (!newForm.name) {
    emit("toast", "请填写股票名称");
    return;
  }
  await apiPost("/api/positions", { ...newForm });
  showAddModal.value = false;
  Object.assign(newForm, { symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });
  await rebuild();
  emit("toast", "持仓已添加");
}

async function saveEditPosition() {
  await apiPut(`/api/positions/${editForm.id}`, { ...editForm });
  showEditModal.value = false;
  await rebuild();
  emit("toast", "持仓已更新");
}

async function remove(row) {
  if (!confirm(`确认删除持仓 "${row.name}"?`)) return;
  await apiDelete(`/api/positions/${row.position_id}`);
  await rebuild();
  emit("toast", "持仓已删除");
}

onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>

<style scoped>
/* Scrollable container */
.table-wrap {
  max-height: 500px;
  overflow-x: auto;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--line);
}

/* Table base */
.holdings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.holdings-table th,
.holdings-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}

.holdings-table th {
  background: var(--table-header);
  font-weight: 600;
  font-size: 12px;
  color: var(--muted);
  position: sticky;
  top: 0;
  z-index: 1;
  white-space: nowrap;
}

.holdings-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.03);
}

/* Column widths */
.col-name {
  min-width: 100px;
  max-width: 120px;
}

.col-qty {
  min-width: 70px;
}

.col-cost, .col-price {
  min-width: 80px;
}

.col-pnl {
  min-width: 70px;
  font-weight: 600;
}

.col-cat {
  min-width: 90px;
}

.col-scenario {
  min-width: 120px;
}

.col-trigger {
  min-width: 140px;
  white-space: normal;
  line-height: 1.4;
}

.col-add {
  min-width: 120px;
  white-space: normal;
  line-height: 1.4;
}

.col-advice {
  min-width: 200px;
  max-width: 280px;
  white-space: normal;
}

.col-action {
  min-width: 80px;
  width: 100px;
  text-align: center;
}

/* PnL colors */
.pnl-positive {
  color: #dc2626;
}

.pnl-negative {
  color: #16a34a;
}

/* Risk/Scenario tags */
.risk-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.risk-tag.is-high {
  background: #fee2e2;
  color: #dc2626;
}

.risk-tag.is-medium-high {
  background: #fef3c7;
  color: #d97706;
}

.risk-tag.is-medium {
  background: #e5e7eb;
  color: #6b7280;
}

.risk-tag.is-low {
  background: #d1fae5;
  color: #059669;
}

/* Advice content */
.advice-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.advice-action {
  font-weight: 600;
  color: var(--ink);
}

.advice-reason {
  font-size: 11px;
  line-height: 1.3;
}

/* Action buttons - text style */
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-text {
  padding: 2px 0;
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
  background: none;
  border: none;
  font-weight: 500;
}

.btn-text:hover {
  text-decoration: underline;
}

.btn-text.danger {
  color: #dc2626;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: var(--panel);
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--muted);
  line-height: 1;
}

.modal-close:hover {
  color: var(--ink);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.form-grid input,
.form-grid select {
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font-size: 14px;
}

.price-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.price-input-group input {
  flex: 1;
}

.btn-mini {
  padding: 6px 12px;
  font-size: 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  cursor: pointer;
  color: var(--ink);
}

.btn-mini:hover {
  background: var(--table-header);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.small {
  font-size: 11px;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>