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
            <th>标的</th>
            <th>持仓</th>
            <th>成本</th>
            <th>现价</th>
            <th class="col-pnl">盈亏</th>
            <th>分类</th>
            <th class="col-risk">情景</th>
            <th>减仓触发</th>
            <th>止损触发</th>
            <th>加仓参考</th>
            <th class="col-action">操作建议</th>
            <th class="col-edit">编辑</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in advice" :key="row.name">
            <td><strong>{{ row.name }}</strong><br><span class="text-muted">{{ row.symbol || '-' }}</span></td>
            <td :class="{ 'editing': editingId === row.position_id }">
              <span v-if="editingId !== row.position_id">{{ row.quantity }}股</span>
              <input v-else v-model.number="editForm.quantity" type="number" min="1" class="edit-input" />
            </td>
            <td :class="{ 'editing': editingId === row.position_id }">
              <span v-if="editingId !== row.position_id">{{ money(row.cost_price) }}元</span>
              <input v-else v-model.number="editForm.cost_price" type="number" step="0.01" class="edit-input" />
            </td>
            <td :class="{ 'editing': editingId === row.position_id }">
              <span v-if="editingId !== row.position_id">{{ money(row.current_price) }}元</span>
              <div v-else class="price-edit">
                <input v-model.number="editForm.current_price" type="number" step="0.01" class="edit-input" />
                <button class="btn-sm" @click="fetchCurrentPrice(row)" title="自动获取现价">🔄</button>
              </div>
            </td>
            <td class="col-pnl" :class="pnlClass(row.pnl_ratio)">{{ row.pnl_ratio_text || pct(row.pnl_ratio) }}</td>
            <td :class="{ 'editing': editingId === row.position_id }">
              <span v-if="editingId !== row.position_id">{{ row.category }}</span>
              <select v-else v-model="editForm.category" class="edit-select">
                <option v-for="c in categories" :key="c">{{ c }}</option>
              </select>
            </td>
            <td class="col-risk"><span class="risk-tag" :class="riskClass(row.risk_level)">{{ row.scenario }}</span></td>
            <td>{{ row.trim_trigger }}</td>
            <td>{{ row.stop_trigger }}</td>
            <td>{{ row.add_reference }}</td>
            <td class="col-action">
              <span class="action-text">{{ row.action_advice }}</span>
              <br><span class="text-muted">{{ row.reason }}</span>
            </td>
            <td class="col-edit">
              <div v-if="editingId === row.position_id" class="edit-actions">
                <button class="btn-sm primary" @click="saveEdit(row)">保存</button>
                <button class="btn-sm" @click="cancelEdit">取消</button>
              </div>
              <div v-else class="edit-actions">
                <button class="btn-sm" @click="startEdit(row)">编辑</button>
                <button class="btn-sm danger" @click="remove(row)">删除</button>
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
          <label>当前价<input v-model.number="newForm.current_price" type="number" step="0.01" required /></label>
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
const editingId = ref(null);
const editForm = reactive({ quantity: 0, cost_price: 0, current_price: 0, category: "" });
const newForm = reactive({ symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });

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

function startEdit(row) {
  editingId.value = row.position_id;
  Object.assign(editForm, {
    quantity: row.quantity,
    cost_price: row.cost_price,
    current_price: row.current_price,
    category: row.category,
  });
}

function cancelEdit() {
  editingId.value = null;
}

async function saveEdit(row) {
  const position = positions.value.find(p => p.id === row.position_id);
  if (!position) return;

  Object.assign(position, editForm);
  await apiPut(`/api/positions/${row.position_id}`, position);
  editingId.value = null;
  await rebuild();
  emit("toast", "持仓已更新");
}

async function fetchCurrentPrice(row) {
  try {
    const quote = await apiGet(`/api/quote?name=${row.name}&symbol=${row.symbol || ''}`);
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

async function remove(row) {
  if (!confirm(`确认删除持仓 "${row.name}"?`)) return;
  await apiDelete(`/api/positions/${row.position_id}`);
  await rebuild();
  emit("toast", "持仓已删除");
}

async function saveNewPosition() {
  if (!newForm.name) {
    emit("toast", "请填写股票名称");
    return;
  }
  await apiPost("/api/positions", newForm);
  showAddModal.value = false;
  Object.assign(newForm, { symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });
  await rebuild();
  emit("toast", "持仓已添加");
}

onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>

<style scoped>
/* Scrollable container */
.table-wrap {
  max-height: 500px;
  overflow: auto;
  border-radius: 8px;
}

/* Responsive table */
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

.holdings-table th {
  background: var(--table-header);
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}

.holdings-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

/* Column highlighting */
.col-pnl {
  min-width: 80px;
}

.pnl-positive {
  color: #dc2626;
  font-weight: 600;
}

.pnl-negative {
  color: #16a34a;
  font-weight: 600;
}

.col-risk {
  min-width: 120px;
}

.risk-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.risk-tag.is-high {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
}

.risk-tag.is-medium-high {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.risk-tag.is-medium {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.risk-tag.is-low {
  background: rgba(22, 163, 74, 0.1);
  color: #16a34a;
}

.col-action {
  min-width: 180px;
  max-width: 250px;
}

.action-text {
  font-weight: 600;
}

.col-edit {
  min-width: 100px;
}

/* Editing state */
.editing {
  background: rgba(59, 130, 246, 0.05);
}

.edit-input {
  width: 80px;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 4px;
  font-size: 13px;
}

.edit-select {
  width: 100px;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 4px;
  font-size: 13px;
}

.price-edit {
  display: flex;
  gap: 4px;
  align-items: center;
}

.edit-actions {
  display: flex;
  gap: 4px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel);
  cursor: pointer;
}

.btn-sm:hover {
  background: var(--table-header);
}

.btn-sm.primary {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.btn-sm.danger {
  background: rgba(220, 38, 38, 0.1);
  color: #dc2626;
  border-color: #dc2626;
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
  gap: 4px;
}

.form-grid input,
.form-grid select {
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>