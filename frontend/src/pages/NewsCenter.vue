<template>
  <Card title="市场分析" icon="ai" tone="primary">
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
  <div class="stack-layout">
    <Card title="持仓相关消息" icon="news" tone="primary">
      <template #subtitle>每只持仓显示今日最热门5条消息</template>
      <div v-for="(items, stockName) in groupedHoldingsNews" :key="stockName" class="news-group">
        <div class="stock-name-header">{{ stockName }}</div>
        <div class="table-wrap compact">
          <table>
            <thead><tr><th>时间</th><th>来源</th><th>情绪</th><th>标题</th></tr></thead>
            <tbody>
              <tr v-for="n in items" :key="n.id">
                <td class="time-col">{{ n.published_at?.slice(0, 16) || '-' }}</td>
                <td class="source-col">{{ n.source }}</td>
                <td><span class="sentiment-tag" :class="sentimentClass(n.sentiment)">{{ n.sentiment }}</span></td>
                <td class="title-col">{{ n.title }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p v-if="!Object.keys(groupedHoldingsNews).length" class="text-muted">暂无持仓相关消息</p>
    </Card>
    <Card title="市场热点" icon="chart" tone="default">
      <template #subtitle>显示最热门10条消息</template>
      <div class="table-wrap">
        <table>
          <thead><tr><th>时间</th><th>来源</th><th>情绪</th><th>标题</th></tr></thead>
          <tbody>
            <tr v-for="n in topMarketNews" :key="n.id">
              <td class="time-col">{{ n.published_at?.slice(0, 16) || '-' }}</td>
              <td class="source-col">{{ n.source }}</td>
              <td><span class="sentiment-tag" :class="sentimentClass(n.sentiment)">{{ n.sentiment }}</span></td>
              <td class="title-col">{{ n.title }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="!topMarketNews.length" class="text-muted">暂无市场热点消息</p>
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
import { getCache, setCache } from "../services/cache";

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

// Group holdings news by stock, show top 5 per stock (ranked by importance)
const groupedHoldingsNews = computed(() => {
  const grouped = {};
  for (const n of news.value) {
    if (n.name && n.name.trim()) {
      if (!grouped[n.name]) grouped[n.name] = [];
      grouped[n.name].push(n);
    }
  }
  // Sort each group by importance (descending) and limit to 5
  for (const name in grouped) {
    grouped[name].sort((a, b) => (b.importance || 50) - (a.importance || 50));
    grouped[name] = grouped[name].slice(0, 5);
  }
  return grouped;
});

// Market news: show top 10 most important
const topMarketNews = computed(() => {
  const market = news.value.filter(n => !n.name || !n.name.trim());
  market.sort((a, b) => (b.importance || 50) - (a.importance || 50));
  return market.slice(0, 10);
});

function sentimentClass(sentiment) {
  // 利空用绿色(下跌色), 利好用红色(上涨色), 与A股涨跌色一致
  if (sentiment.includes('利空') || sentiment.includes('恐慌') || sentiment.includes('风险')) return 'negative';
  if (sentiment.includes('利好')) return 'positive';
  return 'default';
}

async function load() {
  // Load cached data first for immediate display
  const cachedStatus = getCache('newscenter_status');
  const cachedNews = getCache('newscenter_news');
  const cachedReports = getCache('newscenter_reports');

  if (cachedStatus) status.value = cachedStatus;
  if (cachedNews) news.value = cachedNews;
  if (cachedReports) reports.value = cachedReports;

  // Fetch fresh data in background
  try {
    const [s, n, r] = await Promise.all([
      apiGet("/api/settings/deepseek"),
      apiGet("/api/news"),
      apiGet("/api/analysis/reports?report_type=market")
    ]);
    status.value = s;
    news.value = n;
    reports.value = r;

    setCache('newscenter_status', s);
    setCache('newscenter_news', n);
    setCache('newscenter_reports', r);
  } catch (err) {
    // If fetch fails, keep using cached data
    if (!cachedNews && !cachedReports) {
      emit("toast", err.message);
    }
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
/* Vertical stack layout for news cards */
.stack-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stack-layout > * {
  width: 100%;
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

/* News grouping styles */
.news-group {
  margin-bottom: 16px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 12px;
}

.news-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.stock-name-header {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 8px;
  padding: 4px 8px;
  background: var(--primary);
  color: white;
  border-radius: 4px;
  display: inline-block;
}

/* Sentiment tags: 利空=green(下跌), 利好=red(上涨) */
.sentiment-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.sentiment-tag.positive {
  background: #dc2626;
  color: white;
}

.sentiment-tag.negative {
  background: #16a34a;
  color: white;
}

.sentiment-tag.default {
  background: #6b7280;
  color: white;
}

/* Compact table */
.table-wrap.compact {
  max-height: 200px;
}

.table-wrap.compact table {
  font-size: 12px;
}

.table-wrap.compact th,
.table-wrap.compact td {
  padding: 6px 8px;
}

.time-col {
  width: 100px;
}

.source-col {
  width: 80px;
}

.title-col {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
