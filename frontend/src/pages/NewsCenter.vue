<template>
  <Card title="智能市场分析" icon="ai" tone="primary">
    <template #subtitle>{{ statusText }}</template>
    <template #actions>
      <button class="btn" @click="loadNews">刷新消息面</button>
      <button class="btn primary" :disabled="loading" @click="runAnalysis">{{ loading ? "生成中..." : "生成 AI 分析" }}</button>
    </template>
    <form @submit.prevent>
      <label>补充说明<textarea v-model="extraNote" placeholder="补充今日盘面、重点板块或个人观察"></textarea></label>
    </form>
  </Card>
  <div class="grid">
    <Card title="持仓相关消息" icon="news" tone="primary">
      <div class="table-wrap">
        <table>
          <thead><tr><th>时间</th><th>标的</th><th>来源</th><th>情绪</th><th>标题</th></tr></thead>
          <tbody>
            <tr v-for="n in holdingsNews" :key="n.id">
              <td>{{ n.published_at }}</td><td>{{ n.name }}</td><td>{{ n.source }}</td>
              <td><span class="risk-tag" :class="sentimentClass(n.sentiment)">{{ n.sentiment }}</span></td>
              <td>{{ n.title }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!holdingsNews.length" class="text-muted">暂无持仓相关消息</p>
    </Card>
    <Card title="市场热点" icon="chart" tone="default">
      <div class="table-wrap">
        <table>
          <thead><tr><th>时间</th><th>来源</th><th>情绪</th><th>标题</th></tr></thead>
          <tbody>
            <tr v-for="n in marketNews" :key="n.id">
              <td>{{ n.published_at }}</td><td>{{ n.source }}</td>
              <td><span class="risk-tag" :class="sentimentClass(n.sentiment)">{{ n.sentiment }}</span></td>
              <td>{{ n.title }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!marketNews.length" class="text-muted">暂无市场热点消息</p>
    </Card>
  </div>
  <Card title="AI 分析报告" icon="ai" tone="default">
    <template #actions>
      <button class="btn" @click="loadReports">刷新报告</button>
    </template>
    <article v-for="r in reports" :key="r.id" class="report-card">
      <div class="report-header">
        <h3>{{ r.report_date }}</h3>
        <span class="model-tag">{{ r.model }}</span>
      </div>
      <MarkdownRender :content="r.content" />
    </article>
    <p v-if="!reports.length" class="text-muted">还没有生成 AI 分析报告</p>
  </Card>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import Card from "../components/Card.vue";
import MarkdownRender from "../components/MarkdownRender.vue";
import { apiGet, apiPost } from "../services/api";

const emit = defineEmits(["toast"]);
const status = ref({});
const news = ref([]);
const reports = ref([]);
const extraNote = ref("");
const loading = ref(false);

const statusText = computed(() => `模型：${status.value.model || ""}；地址：${status.value.base_url || ""}`);

// Separate news: holdings-related vs market-wide
const holdingsNews = computed(() => news.value.filter(n => n.name && n.name.trim()));
const marketNews = computed(() => news.value.filter(n => !n.name || !n.name.trim()));

function sentimentClass(sentiment) {
  if (sentiment.includes('利空') || sentiment.includes('恐慌') || sentiment.includes('风险')) return 'danger';
  if (sentiment.includes('利好')) return 'success';
  return 'default';
}

async function load() {
  try {
    const [s, n, r] = await Promise.all([
      apiGet("/api/settings/deepseek"),
      apiGet("/api/news"),
      apiGet("/api/analysis/reports")
    ]);
    status.value = s;
    news.value = n;
    reports.value = r;
  } catch (err) {
    emit("toast", err.message);
  }
}

async function loadNews() {
  try {
    news.value = await apiGet("/api/news");
    emit("toast", "消息面已刷新");
  } catch (err) {
    emit("toast", err.message);
  }
}

async function loadReports() {
  try {
    reports.value = await apiGet("/api/analysis/reports");
    emit("toast", "报告已刷新");
  } catch (err) {
    emit("toast", err.message);
  }
}

async function runAnalysis() {
  loading.value = true;
  try {
    await apiPost("/api/analysis/daily", { extra_note: extraNote.value });
    await loadReports();
    emit("toast", "AI分析已生成");
  } catch (err) {
    emit("toast", err.message);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.grid {
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  align-items: stretch;
}

.report-card {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--table-header);
  border-radius: 8px;
}

.report-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.report-header h3 {
  margin: 0;
  font-size: 16px;
}

.model-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--primary);
  color: #fff;
}

textarea {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}
</style>