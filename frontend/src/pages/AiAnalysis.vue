<template>
  <Card title="DeepSeek 每日分析" icon="ai" tone="primary">
    <template #subtitle>{{ statusText }}</template>
    <template #actions>
      <button class="btn primary" :disabled="loading" @click="runAnalysis">{{ loading ? "生成中..." : "生成今日 AI 日报" }}</button>
    </template>
    <form @submit.prevent>
      <label>补充说明<textarea v-model="extraNote" placeholder="补充今日盘面、重点板块或个人观察"></textarea></label>
    </form>
  </Card>
  <Card title="分析报告历史" icon="ai" tone="default">
    <article v-for="r in reports" :key="r.id" class="card" style="margin-bottom: 15px; padding: 15px;">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        <h3 style="margin: 0;">{{ r.report_date }} · {{ r.provider }} · {{ r.status }}</h3>
        <span class="risk-tag" style="background: var(--primary);">{{ r.model }}</span>
      </div>
      <div class="report">{{ r.content }}</div>
    </article>
    <p v-if="!reports.length" class="text-muted">还没有报告。</p>
  </Card>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Card from "../components/Card.vue";
import { apiGet, apiPost } from "../services/api";

const emit = defineEmits(["toast"]);
const status = ref({});
const reports = ref([]);
const extraNote = ref("");
const loading = ref(false);
const statusText = computed(() => `${status.value.key_hint || ""}；模型：${status.value.model || ""}；地址：${status.value.base_url || ""}`);

async function load() {
  [status.value, reports.value] = await Promise.all([apiGet("/api/settings/deepseek"), apiGet("/api/analysis/reports")]);
}
async function runAnalysis() {
  loading.value = true;
  try {
    await apiPost("/api/analysis/daily", { extra_note: extraNote.value });
    await load();
    emit("toast", "AI日报已生成");
  } catch (err) {
    emit("toast", err.message);
  } finally {
    loading.value = false;
  }
}
onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>