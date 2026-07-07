<template>
  <Card title="大模型配置管理" icon="ai" tone="primary">
    <template #actions>
      <button class="btn primary" @click="showAddForm = true">添加配置</button>
    </template>
    <div v-if="configs.length" class="config-list">
      <div v-for="c in configs" :key="c.id" class="config-card" :class="{ active: c.is_active }">
        <div class="config-header">
          <strong>{{ c.display_name }}</strong>
          <span class="provider-tag">{{ c.provider }}</span>
          <span v-if="c.is_active" class="active-badge">当前激活</span>
        </div>
        <div class="config-details">
          <span>模型: {{ c.model }}</span>
          <span>地址: {{ c.base_url || '默认' }}</span>
        </div>
        <div class="config-actions">
          <button class="btn" @click="testConfig(c.id)">测试连接</button>
          <button v-if="!c.is_active" class="btn primary" @click="activateConfig(c.id)">激活</button>
          <button class="btn" @click="editConfig(c)">编辑</button>
          <button class="btn danger" @click="deleteConfig(c.id)">删除</button>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">暂无大模型配置，请添加或使用环境变量</p>
  </Card>
  <Card title="环境变量配置 (备用)" icon="settings" tone="default">
    <div class="env-info">
      <div class="env-row">
        <span class="env-label">DEEPSEEK_API_KEY</span>
        <span class="env-value">{{ envStatus.key_hint }}</span>
      </div>
      <div class="env-row">
        <span class="env-label">DEEPSEEK_MODEL</span>
        <span class="env-value">{{ envStatus.model }}</span>
      </div>
      <div class="env-row">
        <span class="env-label">DEEPSEEK_BASE_URL</span>
        <span class="env-value">{{ envStatus.base_url }}</span>
      </div>
    </div>
  </Card>
  <div v-if="showAddForm || editing" class="modal-overlay" @click.self="closeForm">
    <div class="modal">
      <h3>{{ editing ? '编辑配置' : '添加配置' }}</h3>
      <form @submit.prevent="saveConfig">
        <div class="form-grid">
          <label>提供商
            <select v-model="form.provider" @change="onProviderChange">
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="custom">自定义</option>
            </select>
          </label>
          <label>显示名称<input v-model="form.display_name" required /></label>
          <label>API Key<input v-model="form.api_key" type="password" placeholder="sk-..." /></label>
          <label>Base URL<input v-model="form.base_url" :placeholder="defaultBaseUrl" /></label>
          <label>模型
            <select v-model="form.model">
              <option v-for="m in modelOptions" :key="m" :value="m">{{ m }}</option>
            </select>
          </label>
          <label v-if="editing">激活状态
            <select v-model.number="form.is_active">
              <option :value="0">未激活</option>
              <option :value="1">激活</option>
            </select>
          </label>
        </div>
        <div class="form-actions">
          <button class="btn primary" type="submit">保存</button>
          <button class="btn" type="button" @click="closeForm">取消</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import Card from "../components/Card.vue";
import { apiDelete, apiGet, apiPost, apiPut } from "../services/api";
import { getCache, setCache } from "../services/cache";

const emit = defineEmits(["toast"]);
const configs = ref([]);
const envStatus = ref({});
const showAddForm = ref(false);
const editing = ref(null);
const form = reactive({ provider: "deepseek", display_name: "", api_key: "", base_url: "", model: "deepseek-chat", is_active: 0 });

const providerDefaults = {
  deepseek: { base_url: "https://api.deepseek.com", models: ["deepseek-chat", "deepseek-coder"] },
  openai: { base_url: "https://api.openai.com/v1", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] },
  anthropic: { base_url: "https://api.anthropic.com", models: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"] },
  custom: { base_url: "", models: ["custom-model"] }
};

const defaultBaseUrl = computed(() => providerDefaults[form.provider]?.base_url || "");
const modelOptions = computed(() => providerDefaults[form.provider]?.models || []);

function onProviderChange() {
  form.base_url = providerDefaults[form.provider]?.base_url || "";
  form.model = providerDefaults[form.provider]?.models[0] || "";
}

async function load() {
  // Load cached data first for immediate display
  const cachedConfigs = getCache('settings_configs');
  const cachedStatus = getCache('settings_status');

  if (cachedConfigs) configs.value = cachedConfigs;
  if (cachedStatus) envStatus.value = cachedStatus;

  // Fetch fresh data
  try {
    const [c, s] = await Promise.all([apiGet("/api/llm/configs"), apiGet("/api/settings/deepseek")]);
    configs.value = c;
    envStatus.value = s;
    setCache('settings_configs', c);
    setCache('settings_status', s);
  } catch (err) {
    // If fetch fails and no cache, show error
    if (!cachedConfigs && !cachedStatus) {
      emit("toast", err.message);
    }
  }
}

async function saveConfig() {
  try {
    if (editing.value) {
      await apiPut(`/api/llm/config/${editing.value.id}`, form);
      emit("toast", "配置已更新");
    } else {
      await apiPost("/api/llm/configs", form);
      emit("toast", "配置已添加");
    }
    closeForm();
    await load();
  } catch (err) {
    emit("toast", err.message);
  }
}

function editConfig(c) {
  editing.value = c;
  Object.assign(form, { provider: c.provider, display_name: c.display_name, api_key: c.api_key, base_url: c.base_url, model: c.model, is_active: c.is_active });
}

function closeForm() {
  showAddForm.value = false;
  editing.value = null;
  Object.assign(form, { provider: "deepseek", display_name: "", api_key: "", base_url: "", model: "deepseek-chat", is_active: 0 });
}

async function testConfig(id) {
  try {
    const result = await apiPost(`/api/llm/config/${id}/test`);
    if (result.success) {
      emit("toast", `连接成功: ${result.response_preview}`);
    } else {
      emit("toast", `连接失败: ${result.error}`);
    }
  } catch (err) {
    emit("toast", err.message);
  }
}

async function activateConfig(id) {
  try {
    await apiPost(`/api/llm/config/${id}/activate`);
    emit("toast", "配置已激活");
    await load();
  } catch (err) {
    emit("toast", err.message);
  }
}

async function deleteConfig(id) {
  try {
    await apiDelete(`/api/llm/config/${id}`);
    emit("toast", "配置已删除");
    await load();
  } catch (err) {
    emit("toast", err.message);
  }
}

onMounted(load);
</script>

<style scoped>
.config-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-card {
  padding: 16px;
  background: var(--table-header);
  border-radius: 8px;
  border-left: 3px solid var(--muted);
}

.config-card.active {
  border-left-color: var(--primary);
  background: rgba(23, 107, 135, 0.1);
}

.config-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.provider-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--line);
  color: var(--muted);
}

.active-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--primary);
  color: #fff;
}

.config-details {
  display: flex;
  gap: 16px;
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 12px;
}

.config-actions {
  display: flex;
  gap: 8px;
}

.env-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.env-row {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: var(--table-header);
  border-radius: 4px;
}

.env-label {
  font-weight: 600;
  color: var(--ink);
}

.env-value {
  color: var(--muted);
}

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

.modal {
  background: var(--panel);
  padding: 24px;
  border-radius: 12px;
  max-width: 480px;
  width: 100%;
}

.modal h3 {
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
</style>