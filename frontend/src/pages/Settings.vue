<template>
  <Card title="DeepSeek 配置" icon="settings" tone="primary">
    <div class="report">{{ JSON.stringify(status, null, 2) }}</div>
  </Card>
  <Card title="运行环境" icon="settings" tone="default">
    <div class="report">DEEPSEEK_API_KEY=你的Key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

启动示例：
DEEPSEEK_API_KEY=sk-xxx PORT=8080 ./start.sh</div>
  </Card>
</template>

<script setup>
import { onMounted, ref } from "vue";
import Card from "../components/Card.vue";
import { apiGet } from "../services/api";

const emit = defineEmits(["toast"]);
const status = ref({});

onMounted(async () => {
  try { status.value = await apiGet("/api/settings/deepseek"); } catch (err) { emit("toast", err.message); }
});
</script>