<template>
  <div class="grid">
    <Card title="录入消息面" icon="news" tone="primary">
      <form @submit.prevent="saveNews">
        <div class="form-grid">
          <label>标的<input v-model="newsForm.name" /></label><label>来源<input v-model="newsForm.source" /></label>
          <label class="wide">标题<input v-model="newsForm.title" required /></label>
          <label>情绪<select v-model="newsForm.sentiment"><option>中性</option><option>重大利好</option><option>重大利空</option><option>利好兑现</option><option>监管风险</option><option>舆情过热</option><option>舆情恐慌</option></select></label>
          <label>情景<select v-model="newsForm.scenario"><option></option><option>恐慌性下跌观察</option><option>主力出货风险</option><option>主力洗盘观察</option><option>利好兑现风险</option><option>利空释放观察</option></select></label>
          <label>重要性<input v-model.number="newsForm.importance" type="number" min="0" max="100" /></label>
          <label>链接<input v-model="newsForm.url" /></label>
        </div>
        <button class="btn primary" type="submit">保存消息</button>
      </form>
    </Card>
    <Card title="市场快照" icon="chart" tone="default">
      <form @submit.prevent="saveMarket">
        <div class="form-grid">
          <label>日期<input v-model="marketForm.snapshot_date" type="date" /></label><label>指数状态<input v-model="marketForm.index_state" /></label>
          <label>市场量能<input v-model="marketForm.market_volume_state" /></label><label>涨停家数<input v-model.number="marketForm.limit_up_count" type="number" /></label>
          <label>跌停家数<input v-model.number="marketForm.limit_down_count" type="number" /></label>
          <label class="wide">热点板块<input v-model="marketForm.hot_sectors" /></label>
          <label class="wide">风险事件<input v-model="marketForm.risk_events" /></label>
        </div>
        <button class="btn primary" type="submit">保存快照</button>
      </form>
    </Card>
  </div>
  <Card title="消息列表" icon="news" tone="primary">
    <div class="table-wrap"><table><thead><tr><th>时间</th><th>标的</th><th>来源</th><th>情绪</th><th>情景</th><th>标题</th></tr></thead>
      <tbody><tr v-for="n in news" :key="n.id"><td>{{ n.published_at }}</td><td>{{ n.name }}</td><td>{{ n.source }}</td><td>{{ n.sentiment }}</td><td>{{ n.scenario }}</td><td>{{ n.title }}</td></tr></tbody>
    </table></div>
    <p v-if="!news.length" class="text-muted">暂无消息记录</p>
  </Card>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import Card from "../components/Card.vue";
import { apiGet, apiPost } from "../services/api";
import { today } from "../services/format";

const emit = defineEmits(["toast"]);
const news = ref([]);
const newsForm = reactive({ name: "", source: "", title: "", sentiment: "中性", importance: 50, scenario: "", url: "", published_at: today() });
const marketForm = reactive({ snapshot_date: today(), index_state: "", market_volume_state: "", limit_up_count: 0, limit_down_count: 0, hot_sectors: "", risk_events: "" });

async function load() { news.value = await apiGet("/api/news"); }
async function saveNews() { await apiPost("/api/news", newsForm); await apiPost("/api/advice/rebuild"); newsForm.title = ""; await load(); emit("toast", "消息已保存"); }
async function saveMarket() { await apiPost("/api/market", marketForm); emit("toast", "市场快照已保存"); }
onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>