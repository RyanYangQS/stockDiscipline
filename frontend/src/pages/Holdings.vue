<template>
  <Card title="持仓操作建议表" icon="holdings" tone="primary">
    <template #actions>
      <button class="btn" @click="openAddModal">新增持仓</button>
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
          <tr v-for="row in advice" :key="row.position_id">
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
                <button class="btn-text danger" @click="confirmDelete(row)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!advice.length" class="text-muted">暂无持仓记录，点击"新增持仓"添加</p>
  </Card>

  <!-- 持仓弹窗（新增/编辑共用） -->
  <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isEditing ? '编辑持仓 - ' + form.name : '新增持仓' }}</h3>
        <button class="modal-close" @click="closeModal">×</button>
      </div>
      <form @submit.prevent="savePosition">
        <div class="form-grid">
          <label>股票代码<input v-model="form.symbol" placeholder="如: sh.600519" /></label>
          <label>股票名称<input v-model="form.name" required placeholder="必填" /></label>
          <label>持仓数量<input v-model.number="form.quantity" type="number" min="1" required /></label>
          <label>成本价<input v-model.number="form.cost_price" type="number" step="0.01" required /></label>
          <label>当前价
            <div class="price-input-group">
              <input v-model.number="form.current_price" type="number" step="0.01" required />
              <button class="btn-mini" @click.prevent="fetchCurrentPrice">获取实时价格</button>
            </div>
          </label>
          <label>分类<select v-model="form.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
          <label>行业<input v-model="form.sector" placeholder="如: 酒类" /></label>
          <label>备注<input v-model="form.note" placeholder="持仓说明" /></label>
        </div>
        <div class="modal-actions">
          <button class="btn" type="button" @click="closeModal">取消</button>
          <button class="btn primary" type="submit">{{ isEditing ? '保存修改' : '保存' }}</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 删除确认弹窗 -->
  <div v-if="showDeleteConfirm" class="modal-overlay confirm-overlay" @click.self="showDeleteConfirm = false">
    <div class="confirm-dialog">
      <div class="confirm-icon">⚠️</div>
      <div class="confirm-title">确认删除</div>
      <div class="confirm-message">确定要删除持仓 "<strong>{{ deleteTarget?.name }}</strong>" 吗？此操作不可恢复。</div>
      <div class="confirm-actions">
        <button class="btn" @click="showDeleteConfirm = false">取消</button>
        <button class="btn danger" @click="doDelete">确认删除</button>
      </div>
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
const categories = ["核心赛道", "观察仓", "弱势跟风", "高风险票", "恐慌释放观察"];
const rebuilding = ref(false);
const aiLoading = ref(false);

// Modal state
const showModal = ref(false);
const isEditing = ref(false);
const form = reactive({ id: 0, symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });

// Delete confirm state
const showDeleteConfirm = ref(false);
const deleteTarget = ref(null);

async function load() {
  advice.value = await apiGet("/api/advice");
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

function openAddModal() {
  isEditing.value = false;
  Object.assign(form, { id: 0, symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });
  showModal.value = true;
}

function openEditModal(row) {
  isEditing.value = true;
  Object.assign(form, {
    id: row.position_id,
    symbol: row.symbol || "",
    name: row.name,
    quantity: row.quantity,
    cost_price: row.cost_price,
    current_price: row.current_price,
    category: row.category,
    sector: row.sector || "",
    note: row.note || "",
  });
  showModal.value = true;
}

function closeModal() {
  showModal.value = false;
}

async function fetchCurrentPrice() {
  if (!form.name) {
    emit("toast", "请先填写股票名称");
    return;
  }
  try {
    const quote = await apiGet(`/api/quote?name=${form.name}&symbol=${form.symbol || ''}`);
    if (quote && quote.current_price) {
      form.current_price = quote.current_price;
      emit("toast", `现价已更新: ${quote.current_price}元`);
    } else {
      emit("toast", "无法获取实时价格");
    }
  } catch (err) {
    emit("toast", `获取价格失败: ${err.message}`);
  }
}

async function savePosition() {
  if (!form.name) {
    emit("toast", "请填写股票名称");
    return;
  }

  if (isEditing.value) {
    await apiPut(`/api/positions/${form.id}`, { ...form });
    emit("toast", "持仓已更新");
  } else {
    await apiPost("/api/positions", { ...form });
    emit("toast", "持仓已添加");
  }

  closeModal();
  await rebuild();
}

function confirmDelete(row) {
  deleteTarget.value = row;
  showDeleteConfirm.value = true;
}

async function doDelete() {
  if (!deleteTarget.value) return;
  await apiDelete(`/api/positions/${deleteTarget.value.position_id}`);
  showDeleteConfirm.value = false;
  deleteTarget.value = null;
  await rebuild();
  emit("toast", "持仓已删除");
}

onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>

<style scoped>
/* Table styles */
.table-wrap {
  max-height: 500px;
  overflow-x: auto;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--line);
}

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
.col-name { min-width: 100px; max-width: 120px; }
.col-qty { min-width: 70px; }
.col-cost, .col-price { min-width: 80px; }
.col-pnl { min-width: 70px; font-weight: 600; }
.col-cat { min-width: 90px; }
.col-scenario { min-width: 120px; }
.col-trigger { min-width: 140px; white-space: normal; line-height: 1.4; }
.col-add { min-width: 120px; white-space: normal; line-height: 1.4; }
.col-advice { min-width: 200px; max-width: 280px; white-space: normal; }
.col-action { min-width: 80px; width: 100px; text-align: center; }

/* PnL colors */
.pnl-positive { color: #dc2626; }
.pnl-negative { color: #16a34a; }

/* Risk tags */
.risk-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.risk-tag.is-high { background: #fee2e2; color: #dc2626; }
.risk-tag.is-medium-high { background: #fef3c7; color: #d97706; }
.risk-tag.is-medium { background: #e5e7eb; color: #6b7280; }
.risk-tag.is-low { background: #d1fae5; color: #059669; }

/* Advice content */
.advice-content { display: flex; flex-direction: column; gap: 4px; }
.advice-action { font-weight: 600; color: var(--ink); }
.advice-reason { font-size: 11px; line-height: 1.3; }

/* Action buttons */
.action-buttons { display: flex; gap: 12px; justify-content: center; }
.btn-text {
  padding: 2px 0;
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
  background: none;
  border: none;
  font-weight: 500;
}
.btn-text:hover { text-decoration: underline; }
.btn-text.danger { color: #dc2626; }

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

.modal-close:hover { color: var(--ink); }

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

.price-input-group input { flex: 1; }

.btn-mini {
  padding: 6px 12px;
  font-size: 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  cursor: pointer;
  color: var(--ink);
}

.btn-mini:hover { background: var(--table-header); }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

/* Confirm dialog styles */
.confirm-overlay {
  z-index: 200;
}

.confirm-dialog {
  background: var(--panel);
  border-radius: 16px;
  padding: 32px;
  width: 400px;
  max-width: 90%;
  text-align: center;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 12px;
}

.confirm-message {
  font-size: 14px;
  color: var(--muted);
  margin-bottom: 24px;
  line-height: 1.5;
}

.confirm-message strong {
  color: var(--ink);
}

.confirm-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.btn.danger {
  background: #dc2626;
  color: white;
  border-color: #dc2626;
}

.btn.danger:hover {
  background: #b91c1c;
}

.small { font-size: 11px; }

@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  .confirm-dialog { padding: 24px; }
}
</style>