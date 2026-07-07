<template>
  <Card title="智能市场分析" icon="ai" tone="primary">
    <template #subtitle>{{ statusText }}</template>
    <template #actions>
      <button class="btn" :disabled="scraping" @click="scrapeNews()">{{ scraping ? "抓取中..." : "自动抓取消息" }}</button>
      <button class="btn" @click="loadNews">刷新消息面</button>
      <button class="btn primary" :disabled="loading" @click="runAnalysis()">{{ loading ? "生成中..." : "生成 AI 分析" }}</button>
    </template>
    <div v-if="scraperStatus" class="scraper-status">
      <span :class="scraperStatus.available ? 'status-ok' : 'status-error'">
        {{ scraperStatus.available ? "爬虫已就绪" : `爬虫未安装: ${scraperStatus.error}` }}
      </span>
    </div>
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
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Card from "../components/Card.vue";
import MarkdownRender from "../components/MarkdownRender.vue";
import { apiGet, apiPost } from "../services/api";

const emit = defineEmits(["toast"]);
const status = ref({});
const scraperStatus = ref(null);
const news = ref([]);
const reports = ref([]);
const extraNote = ref("");
const loading = ref(false);
const scraping = ref(false);
const lastUpdatedAt = ref("");
let autoTimer = null;

const statusText = computed(() => {
  const base = `模型：${status.value.model || ""}；地址：${status.value.base_url || ""}`;
  return lastUpdatedAt.value ? `${base}；上次更新：${lastUpdatedAt.value}` : base;
});

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
      apiGet("/api/analysis/reports?report_type=market")
    ]);
    status.value = s;
    news.value = n;
    reports.value = r;
  } catch (err) {
    emit("toast", err.message);
  }
}

async function checkScraper() {
  try {
    scraperStatus.value = await apiGet("/api/scraper/status");
  } catch (err) {
    scraperStatus.value = { available: false, error: err.message };
  }
}

async function scrapeNews(options = {}) {
  scraping.value = true;
  try {
    const result = await apiPost("/api/news/scrape");
    if (!options.silent) {
      emit("toast", `抓取 ${result.scraped} 条消息，保存 ${result.saved} 条`);
    }
    await loadNews({ silent: true });
    return result;
  } catch (err) {
    if (!options.silent) emit("toast", err.message);
    throw err;
  } finally {
    scraping.value = false;
  }
}

async function loadNews(options = {}) {
  try {
    news.value = await apiGet("/api/news");
    if (!options.silent) emit("toast", "消息面已刷新");
  } catch (err) {
    if (!options.silent) emit("toast", err.message);
    throw err;
  }
}

async function loadReports(options = {}) {
  try {
    reports.value = await apiGet("/api/analysis/reports?report_type=market");
    if (!options.silent) emit("toast", "报告已刷新");
  } catch (err) {
    if (!options.silent) emit("toast", err.message);
    throw err;
  }
}

async function runAnalysis(options = {}) {
  loading.value = true;
  try {
    await apiPost("/api/analysis/market", { extra_note: extraNote.value });
    await loadReports({ silent: true });
    lastUpdatedAt.value = new Date().toLocaleString();
    if (!options.silent) emit("toast", "市场消息面AI分析已生成");
  } catch (err) {
    if (!options.silent) emit("toast", err.message);
    throw err;
  } finally {
    loading.value = false;
  }
}

async function refreshMarketIntelligence(options = {}) {
  if (scraping.value || loading.value) return;
  try {
    await scrapeNews({ silent: true });
    await runAnalysis({ silent: true });
    if (!options.silent) emit("toast", "市场消息面已更新");
  } catch (err) {
    if (!options.silent) emit("toast", err.message);
  }
}

function todayKey(slot) {
  const today = new Date().toISOString().slice(0, 10);
  return `stock-market-analysis-${today}-${slot}`;
}

function markSlot(slot) {
  localStorage.setItem(todayKey(slot), String(Date.now()));
}

function slotDone(slot) {
  return Boolean(localStorage.getItem(todayKey(slot)));
}

function shouldRunScheduledRefresh(now = new Date()) {
  const minutes = now.getHours() * 60 + now.getMinutes();
  if (minutes >= 8 * 60 + 45 && minutes < 9 * 60 + 30 && !slotDone("preopen")) {
    return "preopen";
  }
  if (minutes >= 15 * 60 && minutes < 16 * 60 + 30 && !slotDone("postclose")) {
    return "postclose";
  }
  if (minutes >= 9 * 60 + 30 && minutes <= 15 * 60) {
    const key = todayKey("hourly");
    const last = Number(localStorage.getItem(key) || 0);
    if (!last || Date.now() - last >= 60 * 60 * 1000) {
      return "hourly";
    }
  }
  return "";
}

async function runScheduledRefresh() {
  const slot = shouldRunScheduledRefresh();
  if (!slot) return;
  markSlot(slot);
  await refreshMarketIntelligence({ silent: true });
}

function startAutoRefresh() {
  stopAutoRefresh();
  autoTimer = setInterval(runScheduledRefresh, 60 * 1000);
}

function stopAutoRefresh() {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
}

onMounted(async () => {
  await Promise.all([load(), checkScraper()]);
  await refreshMarketIntelligence({ silent: true });
  const currentSlot = shouldRunScheduledRefresh();
  if (currentSlot) markSlot(currentSlot);
  startAutoRefresh();
});

onBeforeUnmount(stopAutoRefresh);
</script>

<style scoped>
.grid {
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  align-items: stretch;
}

.scraper-status {
  margin-bottom: 12px;
  padding: 8px;
  background: var(--table-header);
  border-radius: 4px;
}

.status-ok {
  color: var(--ok);
}

.status-error {
  color: var(--danger);
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
