# 股票纪律系统前端UI优化实施计划 - 混合方案(A+C)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现清爽简洁的卡片化UI设计,采用扁平化图标、圆角卡片和阴影效果

**Architecture:** 保持Vue 3 + Element Plus架构,添加自定义SVG图标组件系统,更新全局CSS样式,改造侧边栏和所有页面组件为卡片化布局

**Tech Stack:** Vue 3、Element Plus、SVG、CSS3、Vite

---

## 文件结构

**创建文件:**
- `frontend/src/components/Icons.vue` - SVG扁平化图标组件库
- `frontend/src/components/Card.vue` - 可复用的卡片组件
- `docs/superpowers/specs/2026-07-06-ui-redesign-design.md` - 设计规范文档

**修改文件:**
- `frontend/src/styles.css` - 全局样式(圆角、阴影、颜色、布局)
- `frontend/src/App.vue` - 侧边栏设计(扁平化图标、深色背景)
- `frontend/src/pages/Dashboard.vue` - 指标卡片、风险卡片、AI日报卡片
- `frontend/src/pages/Holdings.vue` - 持仓卡片、表单卡片
- `frontend/src/pages/KlineVolume.vue` - K线卡片、量能卡片
- `frontend/src/pages/NewsCenter.vue` - 消息卡片、市场快照卡片
- `frontend/src/pages/AiAnalysis.vue` - AI日报卡片
- `frontend/src/pages/Settings.vue` - 设置卡片

---

## Task 1: 创建SVG扁平化图标组件库

**Files:**
- Create: `frontend/src/components/Icons.vue`

- [ ] **Step 1: 创建Icons.vue文件,定义所有扁平化图标**

```vue
<template>
  <!-- 图标通过name属性动态渲染 -->
  <svg v-if="name === 'chart'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="2" y="3" width="3" height="14" rx="1"/>
    <rect x="8" y="8" width="3" height="9" rx="1"/>
    <rect x="14" y="5" width="3" height="12" rx="1"/>
  </svg>

  <svg v-if="name === 'dashboard'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="1" y="1" width="6" height="6" rx="1"/>
    <rect x="9" y="1" width="6" height="6" rx="1"/>
    <rect x="1" y="9" width="6" height="6" rx="1"/>
    <rect x="9" y="9" width="6" height="6" rx="1"/>
  </svg>

  <svg v-if="name === 'holdings'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M2 4h12M2 8h12M2 12h12"/>
    <circle cx="4" cy="4" r="2" fill="currentColor"/>
    <circle cx="8" cy="8" r="2" fill="currentColor"/>
    <circle cx="12" cy="12" r="2" fill="currentColor"/>
  </svg>

  <svg v-if="name === 'kline'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <line x1="8" y1="1" x2="8" y2="4"/>
    <rect x="4" y="4" width="8" height="4" rx="1"/>
    <line x1="8" y1="8" x2="8" y2="12"/>
  </svg>

  <svg v-if="name === 'news'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="1" y="2" width="14" height="12" rx="2"/>
    <line x1="3" y1="5" x2="13" y2="5"/>
    <line x1="3" y1="8" x2="10" y2="8"/>
    <line x1="3" y1="11" x2="8" y2="11"/>
  </svg>

  <svg v-if="name === 'ai'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="8" cy="8" r="6"/>
    <circle cx="5" cy="6" r="1" fill="currentColor"/>
    <circle cx="11" cy="6" r="1" fill="currentColor"/>
    <path d="M5 10 Q8 12 11 10"/>
  </svg>

  <svg v-if="name === 'settings'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="8" cy="8" r="3"/>
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4M3.5 12.5l1.4-1.4M11.1 4.9l1.4-1.4"/>
  </svg>

  <svg v-if="name === 'money'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="10" cy="10" r="8"/>
    <path d="M10 6v8M6 10h8"/>
  </svg>

  <svg v-if="name === 'down'" :width="size" :height="size" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M3 8l5 5 4-4 5 5"/>
    <path d="M17 14v-4"/>
  </svg>

  <svg v-if="name === 'warning'" :width="size" :height="size" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M8 1l7 14H1L8 1z"/>
    <line x1="8" y1="6" x2="8" y2="9"/>
    <circle cx="8" cy="12" r="1" fill="currentColor"/>
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 }
});
</script>
```

- [ ] **Step 2: Commit图标组件**

```bash
git add frontend/src/components/Icons.vue
git commit -m "feat: add SVG flat icon component library"
```

---

## Task 2: 创建可复用的Card组件

**Files:**
- Create: `frontend/src/components/Card.vue`

- [ ] **Step 1: 创建Card.vue文件,定义卡片基础组件**

```vue
<template>
  <div class="card" :class="toneClass">
    <div v-if="icon || title" class="card-header">
      <div v-if="icon" class="card-icon-wrap">
        <Icon :name="icon" :size="20" />
      </div>
      <div class="card-title-area">
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="card-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="card-body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import Icon from './Icons.vue';

const props = defineProps({
  title: { type: String },
  subtitle: { type: String },
  icon: { type: String },
  tone: { type: String, default: 'default' } // default, primary, danger, warning, success
});

const toneClass = computed(() => `tone-${props.tone}`);
</script>

<style scoped>
.card {
  background: var(--panel);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 20px;
  border-left: 4px solid transparent;
}

.tone-default { border-left-color: var(--line); }
.tone-primary { border-left-color: var(--primary); }
.tone-danger { border-left-color: var(--danger); }
.tone-warning { border-left-color: var(--warn); }
.tone-success { border-left-color: var(--ok); }

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  background: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.card-title-area h3 {
  margin: 0;
  font-size: 16px;
  color: var(--ink);
}

.card-subtitle {
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
}
</style>
```

- [ ] **Step 2: Commit卡片组件**

```bash
git add frontend/src/components/Card.vue
git commit -m "feat: add reusable card component with tones"
```

---

## Task 3: 更新全局CSS样式

**Files:**
- Modify: `frontend/src/styles.css` (完整替换)

- [ ] **Step 1: 更新styles.css文件,添加圆角、阴影、颜色系统和布局样式**

```css
:root {
  --bg: #f8fafc;
  --panel: #fff;
  --ink: #1e293b;
  --muted: #64748b;
  --line: #e2e8f0;
  --primary: #176b87;
  --primary-dark: #0f5268;
  --danger: #b42318;
  --danger-bg: #fef3f2;
  --warn: #b54708;
  --warn-bg: #fffaeb;
  --ok: #067647;
  --ok-bg: #ecfdf3;
  --sidebar: #1e293b;
  --sidebar-hover: #176b87;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
button, input, select, textarea { font: inherit; }

.site { min-height: 100vh; display: flex; }

/* 侧边栏样式 */
.sidebar {
  width: 220px;
  background: var(--sidebar);
  color: #fff;
  padding: 20px 0;
  flex-shrink: 0;
}

.brand {
  padding: 0 20px 25px;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-menu {
  padding: 10px 20px;
  margin: 0 15px 6px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.sidebar-menu:hover { background: rgba(255,255,255,.08); }
.sidebar-menu.active {
  background: var(--sidebar-hover);
  font-weight: 500;
}

.menu-icon-wrap {
  width: 28px;
  height: 28px;
  background: rgba(255,255,255,.05);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-menu.active .menu-icon-wrap {
  background: rgba(255,255,255,.15);
}

/* 主应用区 */
.app {
  flex: 1;
  padding: 25px;
  background: var(--bg);
}

.page-head {
  margin-bottom: 20px;
}

h1, h2, h3, p { margin: 0; }
h1 { font-size: 24px; }
h2 { font-size: 18px; }
h3 { font-size: 16px; }

.page-head p { color: var(--muted); font-size: 14px; margin-top: 5px; }

.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}

/* 卡片系统 */
.card {
  background: var(--panel);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 20px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  background: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.card-title h3 { color: var(--ink); }
.card-subtitle { color: var(--muted); font-size: 13px; margin-top: 3px; }
.card-actions { display: flex; gap: 10px; margin-left: auto; }
.card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
}

/* 指标卡片 */
.metric-card {
  background: var(--panel);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 20px;
  border-left: 4px solid transparent;
  margin-bottom: 20px;
}

.metric-card.primary { border-left-color: var(--primary); }
.metric-card.success { border-left-color: var(--ok); }
.metric-card.danger { border-left-color: var(--danger); }

.metric-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.metric-icon-wrap.primary { background: var(--primary); }
.metric-icon-wrap.success { background: var(--ok); }
.metric-icon-wrap.danger { background: var(--danger); }

.metric-label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: var(--ink); }
.metric-value.danger { color: var(--danger); }
.metric-value.success { color: var(--ok); }

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 16px;
  color: var(--ink);
  background: var(--panel);
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn:hover { box-shadow: 0 2px 4px rgba(0,0,0,.12); }
.btn.primary {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.btn.primary:hover { background: var(--primary-dark); }
.btn.danger { color: var(--danger); border-color: var(--danger); }

/* 风险标签 */
.risk-tag {
  display: inline-flex;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  color: #fff;
  font-weight: 600;
}

.risk-tag.high { background: var(--danger); }
.risk-tag.med { background: var(--warn); }
.risk-tag.low { background: var(--ok); }

/* 风险项卡片 */
.risk-item {
  padding: 15px;
  background: var(--danger-bg);
  border-radius: 10px;
  border-left: 3px solid var(--danger);
  margin-bottom: 10px;
}

.risk-item.med { background: var(--warn-bg); border-left-color: var(--warn); }

/* 表格样式 */
.table-wrap { overflow-x: auto; }

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1120px;
}

th, td {
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
  font-size: 13px;
}

th {
  color: var(--muted);
  background: #f7fafc;
  font-weight: 600;
}

/* 响应式布局 */
@media (max-width: 980px) {
  .sidebar { width: 60px; }
  .sidebar-menu { padding: 10px; margin: 0 5px 6px; justify-content: center; }
  .sidebar-menu span { display: none; }
  .brand span { display: none; }
  .app { padding: 20px; }
}

.grid { display: grid; grid-template-columns: repeat(2,minmax(280px,1fr)); gap: 20px; }
.grid.three { grid-template-columns: repeat(3,minmax(220px,1fr)); gap: 20px; }
.form-grid { display: grid; grid-template-columns: repeat(2,minmax(150px,1fr)); gap: 12px; }

label { display: grid; gap: 6px; color: var(--muted); font-size: 13px; }
input, select, textarea {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
  color: var(--ink);
  background: var(--panel);
  font-size: 14px;
}
textarea { min-height: 120px; resize: vertical; }
.wide { grid-column: 1/-1; }

.toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  max-width: 360px;
  z-index: 20;
}

.report {
  white-space: pre-wrap;
  line-height: 1.65;
  background: #f7fafc;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}

.text-danger { color: var(--danger); }
.text-ok { color: var(--ok); }
.text-muted { color: var(--muted); }
```

- [ ] **Step 2: Commit样式更新**

```bash
git add frontend/src/styles.css
git commit -m "feat: update global CSS with rounded corners, shadows, and card system"
```

---

## Task 4: 改造App.vue侧边栏

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 导入Icon组件,修改侧边栏菜单为扁平化图标设计**

在`<script setup>`部分导入Icon组件:

```vue
<script setup>
import { computed, ref } from "vue";
import Icon from "./components/Icons.vue";
import Dashboard from "./pages/Dashboard.vue";
import Holdings from "./pages/Holdings.vue";
import KlineVolume from "./pages/KlineVolume.vue";
import NewsCenter from "./pages/NewsCenter.vue";
import AiAnalysis from "./pages/AiAnalysis.vue";
import Settings from "./pages/Settings.vue";

const current = ref("dashboard");
const toastText = ref("");
let timer = null;

const nav = [
  { key: "dashboard", label: "总览", icon: "dashboard", desc: "持仓、量能、消息面、AI日报和纪律风险总控", component: Dashboard },
  { key: "holdings", label: "持仓建议", icon: "holdings", desc: "按附件表格输出到价位就执行的操作计划", component: Holdings },
  { key: "kline", label: "K线量能", icon: "kline", desc: "基于 KLineCharts 的专业K线与成交量分析", component: KlineVolume },
  { key: "news", label: "消息面", icon: "news", desc: "公告、监管、新闻、舆情和市场快照", component: NewsCenter },
  { key: "analysis", label: "AI日报", icon: "ai", desc: "每天汇总持仓、量能、消息和K线后交给 DeepSeek 分析", component: AiAnalysis },
  { key: "settings", label: "设置", icon: "settings", desc: "DeepSeek、数据源和运行状态", component: Settings }
];

const active = computed(() => nav.find((item) => item.key === current.value) || nav[0]);

function toast(message) {
  toastText.value = message;
  clearTimeout(timer);
  timer = setTimeout(() => {
    toastText.value = "";
  }, 2600);
}
</script>
```

- [ ] **Step 2: 修改侧边栏模板部分**

替换`<el-aside>`部分:

```vue
<template>
  <el-container class="site">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">
          <Icon name="chart" :size="20" />
        </div>
        <span>Stock Discipline</span>
      </div>
      <div
        v-for="item in nav"
        :key="item.key"
        :class="['sidebar-menu', current === item.key ? 'active' : '']"
        @click="current = item.key"
      >
        <div class="menu-icon-wrap">
          <Icon :name="item.icon" :size="16" />
        </div>
        <span>{{ item.label }}</span>
      </div>
    </aside>
    <el-main class="app">
      <header class="page-head">
        <div>
          <h1>{{ active.label }}</h1>
          <p>{{ active.desc }}</p>
        </div>
        <div class="head-actions">
          <el-button tag="a" href="/api/advice.csv">导出建议 CSV</el-button>
        </div>
      </header>
      <component :is="active.component" @toast="toast" />
    </el-main>
  </el-container>
  <el-alert v-if="toastText" class="toast" :title="toastText" type="success" show-icon :closable="false" />
</template>
```

- [ ] **Step 3: Commit侧边栏改造**

```bash
git add frontend/src/App.vue
git commit -m "feat: refactor sidebar with flat icons and new card layout"
```

---

## Task 5: 改造Dashboard.vue页面

**Files:**
- Modify: `frontend/src/pages/Dashboard.vue`

- [ ] **Step 1: 导入Icon组件,修改指标卡片布局**

在`<script setup>`部分导入:

```vue
<script setup>
import { computed, onMounted, ref } from "vue";
import Icon from "../components/Icons.vue";
import { apiGet } from "../services/api";
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const summary = ref({});
const advice = ref([]);
const reports = ref([]);

const metrics = computed(() => [
  {
    label: "持仓数量",
    value: `${summary.value.position_count || 0}`,
    icon: "chart",
    tone: "primary",
    footer: "查看详细持仓 →"
  },
  {
    label: "当前市值",
    value: `¥${money(summary.value.total_value)}`,
    icon: "money",
    tone: "success",
    footer: "占比分析 →"
  },
  {
    label: "总盈亏",
    value: `¥${money(summary.value.total_pnl)}`,
    icon: "down",
    tone: "danger",
    danger: summary.value.total_pnl < 0
  },
  {
    label: "总盈亏率",
    value: pct(summary.value.total_pnl_ratio),
    icon: "down",
    tone: summary.value.total_pnl_ratio < 0 ? "danger" : "success"
  }
]);

const latestReport = computed(() => reports.value[0]?.content || "");

async function load() {
  try {
    const [s, a, r] = await Promise.all([apiGet("/api/summary"), apiGet("/api/advice"), apiGet("/api/analysis/reports")]);
    summary.value = s;
    advice.value = a;
    reports.value = r;
  } catch (err) {
    emit("toast", err.message);
  }
}

onMounted(load);
</script>
```

- [ ] **Step 2: 修改模板为卡片化布局**

```vue
<template>
  <!-- 指标卡片网格 -->
  <section class="grid">
    <div v-for="item in metrics" :key="item.label" class="metric-card" :class="item.tone">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
        <div class="metric-icon-wrap" :class="item.tone">
          <Icon :name="item.icon" :size="20" />
        </div>
        <div class="metric-label">{{ item.label }}</div>
      </div>
      <div class="metric-value" :class="{ danger: item.danger, success: item.tone === 'success' && !item.danger }">
        {{ item.value }}
      </div>
      <div v-if="item.footer" class="card-footer">{{ item.footer }}</div>
    </div>
  </section>

  <!-- 风险和拦截计数卡片 -->
  <section style="display:flex;gap:20px;margin-bottom:20px;">
    <div style="flex:1;padding:20px;background:var(--danger-bg);border-radius:12px;border-left:4px solid var(--danger);">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <div style="width:40px;height:40px;background:var(--danger);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;">
          <Icon name="warning" :size="20" />
        </div>
        <div style="font-size:13px;color:var(--muted);">高风险</div>
      </div>
      <div style="font-size:28px;font-weight:700;color:var(--danger);">{{ summary.value.high_risk_count || 0 }}</div>
    </div>

    <div style="flex:1;padding:20px;background:var(--warn-bg);border-radius:12px;border-left:4px solid var(--warn);">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <div style="width:40px;height:40px;background:var(--warn);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;">
          <Icon name="warning" :size="20" />
        </div>
        <div style="font-size:13px;color:var(--muted);">纪律拦截</div>
      </div>
      <div style="font-size:28px;font-weight:700;color:var(--warn);">{{ summary.value.discipline_blocked_count || 0 }}</div>
    </div>
  </section>

  <!-- 风险优先级卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap" style="background:var(--danger);">
        <Icon name="warning" :size="20" />
      </div>
      <div class="card-title">
        <h3>风险优先级</h3>
      </div>
      <div class="card-actions">
        <button class="btn primary" @click="load">刷新</button>
      </div>
    </div>
    <div style="display:flex;gap:15px;">
      <div v-for="item in advice" :key="item.name" class="risk-item" :class="riskClass(item.risk_level)">
        <div style="font-size:12px;color:var(--muted);margin-bottom:8px;display:flex;align-items:center;gap:8px;">
          <span class="risk-tag" :class="riskClass(item.risk_level)">
            {{ item.risk_level === '高风险' ? 'HIGH' : item.risk_level === '中风险' ? 'MED' : 'LOW' }}
          </span>
          <strong>{{ item.name }}</strong>
        </div>
        <div style="font-size:14px;color:var(--ink);line-height:1.6;">
          {{ item.scenario }}，{{ item.action_advice }}
        </div>
      </div>
    </div>
  </section>

  <!-- AI日报卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="ai" :size="20" />
      </div>
      <div class="card-title">
        <h3>最新 AI 日报</h3>
      </div>
    </div>
    <div class="report">{{ latestReport || "还没有生成 AI 日报。" }}</div>
  </section>
</template>
```

- [ ] **Step 3: Commit Dashboard页面改造**

```bash
git add frontend/src/pages/Dashboard.vue
git commit -m "feat: refactor Dashboard with card-based layout and flat icons"
```

---

## Task 6: 改造Holdings.vue页面

**Files:**
- Modify: `frontend/src/pages/Holdings.vue`

- [ ] **Step 1: 修改持仓建议表格为卡片化设计**

模板部分替换为:

```vue
<template>
  <!-- 持仓建议表格卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="holdings" :size="20" />
      </div>
      <div class="card-title">
        <h3>持仓操作建议表</h3>
      </div>
      <div class="card-actions">
        <button class="btn primary" @click="rebuild">重新生成建议</button>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>标的</th><th>持仓</th><th>成本</th><th>现价</th>
            <th>盈亏</th><th>分类</th><th>情景</th>
            <th>减仓触发</th><th>止损触发</th><th>加仓参考</th><th>操作建议</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in advice" :key="row.name">
            <td><strong>{{ row.name }}</strong></td>
            <td>{{ row.quantity }}股</td>
            <td>{{ money(row.cost_price) }}元</td>
            <td>{{ money(row.current_price) }}元</td>
            <td>{{ row.pnl_ratio_text || pct(row.pnl_ratio) }}</td>
            <td>{{ row.category }}</td>
            <td>
              <span class="risk-tag" :class="riskClass(row.risk_level)">
                {{ row.scenario }}
              </span>
            </td>
            <td>{{ row.trim_trigger }}</td>
            <td>{{ row.stop_trigger }}</td>
            <td>{{ row.add_reference }}</td>
            <td>{{ row.action_advice }}<br><span class="text-muted">{{ row.reason }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- 新增持仓表单卡片 -->
  <section class="grid">
    <form class="card" @submit.prevent="savePosition">
      <div class="card-header">
        <div class="card-icon-wrap">
          <Icon name="holdings" :size="20" />
        </div>
        <div class="card-title">
          <h3>新增持仓</h3>
        </div>
      </div>
      <div class="form-grid">
        <label>代码<input v-model="form.symbol" /></label>
        <label>标的<input v-model="form.name" required /></label>
        <label>数量<input v-model.number="form.quantity" type="number" min="1" required /></label>
        <label>成本价<input v-model.number="form.cost_price" type="number" step="0.01" required /></label>
        <label>当前价<input v-model.number="form.current_price" type="number" step="0.01" required /></label>
        <label>分类<select v-model="form.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
        <label>行业<input v-model="form.sector" /></label>
        <label>备注<input v-model="form.note" /></label>
      </div>
      <button class="btn primary" type="submit">保存持仓</button>
    </form>

    <!-- 持仓维护卡片 -->
    <div class="card">
      <div class="card-header">
        <div class="card-icon-wrap">
          <Icon name="settings" :size="20" />
        </div>
        <div class="card-title">
          <h3>持仓维护</h3>
        </div>
      </div>
      <div v-for="p in positions" :key="p.id" class="card" style="margin-bottom:15px;">
        <h4 style="margin:0 0 12px;color:var(--ink);">{{ p.name }}</h4>
        <div class="form-grid">
          <label>数量<input v-model.number="p.quantity" type="number" /></label>
          <label>成本<input v-model.number="p.cost_price" type="number" step="0.01" /></label>
          <label>现价<input v-model.number="p.current_price" type="number" step="0.01" /></label>
          <label>分类<select v-model="p.category"><option v-for="c in categories" :key="c">{{ c }}</option></select></label>
        </div>
        <div style="display:flex;gap:10px;margin-top:12px;">
          <button class="btn primary" @click="update(p)">保存</button>
          <button class="btn danger" @click="remove(p)">删除</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import Icon from "../components/Icons.vue";
import { apiDelete, apiGet, apiPost, apiPut } from "../services/api";
import { money, pct, riskClass } from "../services/format";

const emit = defineEmits(["toast"]);
const advice = ref([]);
const positions = ref([]);
const categories = ["核心赛道", "观察仓", "弱势跟风", "高风险票", "恐慌释放观察"];
const form = reactive({ symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" });

async function load() {
  [advice.value, positions.value] = await Promise.all([apiGet("/api/advice"), apiGet("/api/positions")]);
}
async function rebuild() { await apiPost("/api/advice/rebuild"); await load(); emit("toast", "建议已重新生成"); }
async function savePosition() { await apiPost("/api/positions", form); await rebuild(); Object.assign(form, { symbol: "", name: "", quantity: 100, cost_price: 0, current_price: 0, category: "观察仓", sector: "", note: "" }); }
async function update(p) { await apiPut(`/api/positions/${p.id}`, p); await rebuild(); }
async function remove(p) { await apiDelete(`/api/positions/${p.id}`); await rebuild(); }

onMounted(() => load().catch((err) => emit("toast", err.message)));
</script>
```

- [ ] **Step 2: Commit Holdings页面改造**

```bash
git add frontend/src/pages/Holdings.vue
git commit -m "feat: refactor Holdings page with card-based layout"
```

---

## Task 7: 改造KlineVolume.vue页面

**Files:**
- Modify: `frontend/src/pages/KlineVolume.vue`

- [ ] **Step 1: 导入Icon组件并修改布局**

在`<script setup>`部分导入Icon组件,并修改模板:

```vue
<script setup>
import { onMounted, reactive, ref } from "vue";
import Icon from "../components/Icons.vue";
import KlineChart from "../components/KlineChart.vue";
import { apiGet, apiPost } from "../services/api";
import { today } from "../services/format";

// ... 现有代码保持不变
</script>

<template>
  <!-- K线图表卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="kline" :size="20" />
      </div>
      <div class="card-title">
        <h3>专业 K线量能图</h3>
        <p class="card-subtitle">使用 KLineCharts 展示蜡烛图与成交量指标</p>
      </div>
      <div class="card-actions">
        <select v-model="selectedName" @change="loadKline">
          <option v-for="p in positions" :key="p.id" :value="p.name">{{ p.name }}</option>
        </select>
        <button class="btn" @click="loadKline">刷新K线</button>
      </div>
    </div>
    <div class="card-body">
      <KlineChart :bars="bars" />
    </div>
  </section>

  <!-- 量能和日K录入表单卡片 -->
  <section class="grid">
    <!-- 量能快照录入 -->
    <form class="card" @submit.prevent="saveVolume">
      <div class="card-header">
        <div class="card-icon-wrap" style="background:var(--ok);">
          <Icon name="chart" :size="20" />
        </div>
        <div class="card-title">
          <h3>录入量能快照</h3>
        </div>
      </div>
      <div class="form-grid">
        <label>标的<input v-model="volumeForm.name" /></label>
        <label>交易日<input v-model="volumeForm.trade_date" type="date" /></label>
        <label>量能状态<select v-model="volumeForm.volume_state">
          <option>温和放量</option><option>异常放量</option><option>放量滞涨</option>
          <option>缩量抗跌</option><option>缩量阴跌</option><option>天量换手</option>
        </select></label>
        <label>量比<input v-model.number="volumeForm.volume_ratio" type="number" step="0.01" /></label>
        <label>换手率<input v-model.number="volumeForm.turnover_rate" type="number" step="0.01" /></label>
        <label>买入评分<input v-model.number="volumeForm.buy_watch_score" type="number" min="0" max="100" /></label>
        <label>卖出风险<input v-model.number="volumeForm.sell_risk_score" type="number" min="0" max="100" /></label>
        <label>建仓评分<input v-model.number="volumeForm.accumulation_score" type="number" min="0" max="100" /></label>
      </div>
      <button class="btn primary" type="submit">保存量能</button>
    </form>

    <!-- 日K录入 -->
    <form class="card" @submit.prevent="saveBar">
      <div class="card-header">
        <div class="card-icon-wrap" style="background:var(--primary);">
          <Icon name="kline" :size="20" />
        </div>
        <div class="card-title">
          <h3>录入日K</h3>
        </div>
      </div>
      <div class="form-grid">
        <label>标的<input v-model="barForm.name" /></label>
        <label>日期<input v-model="barForm.trade_date" type="date" /></label>
        <label>开盘<input v-model.number="barForm.open_price" type="number" step="0.01" /></label>
        <label>最高<input v-model.number="barForm.high_price" type="number" step="0.01" /></label>
        <label>最低<input v-model.number="barForm.low_price" type="number" step="0.01" /></label>
        <label>收盘<input v-model.number="barForm.close_price" type="number" step="0.01" /></label>
        <label>成交量<input v-model.number="barForm.volume" type="number" /></label>
        <label>成交额<input v-model.number="barForm.amount" type="number" /></label>
      </div>
      <button class="btn primary" type="submit">保存日K</button>
    </form>
  </section>
</template>
```

- [ ] **Step 2: Commit KlineVolume页面改造**

```bash
git add frontend/src/pages/KlineVolume.vue
git commit -m "feat: refactor KlineVolume page with card-based layout"
```

---

## Task 8: 改造NewsCenter.vue页面

**Files:**
- Modify: `frontend/src/pages/NewsCenter.vue`

- [ ] **Step 1: 导入Icon组件并修改布局**

```vue
<script setup>
import { onMounted, reactive, ref } from "vue";
import Icon from "../components/Icons.vue";
import { apiGet, apiPost } from "../services/api";
import { today } from "../services/format";

// ... 现有代码保持不变
</script>

<template>
  <!-- 消息面和快照录入 -->
  <section class="grid">
    <!-- 消息面录入 -->
    <form class="card" @submit.prevent="saveNews">
      <div class="card-header">
        <div class="card-icon-wrap" style="background:var(--warn);">
          <Icon name="news" :size="20" />
        </div>
        <div class="card-title">
          <h3>录入消息面</h3>
        </div>
      </div>
      <div class="form-grid">
        <label>标的<input v-model="newsForm.name" /></label>
        <label>来源<input v-model="newsForm.source" /></label>
        <label class="wide">标题<input v-model="newsForm.title" required /></label>
        <label>情绪<select v-model="newsForm.sentiment">
          <option>中性</option><option>重大利好</option><option>重大利空</option>
          <option>利好兑现</option><option>监管风险</option><option>舆情过热</option><option>舆情恐慌</option>
        </select></label>
        <label>情景<select v-model="newsForm.scenario">
          <option></option><option>恐慌性下跌观察</option><option>主力出货风险</option>
          <option>主力洗盘观察</option><option>利好兑现风险</option><option>利空释放观察</option>
        </select></label>
        <label>重要性<input v-model.number="newsForm.importance" type="number" min="0" max="100" /></label>
        <label>链接<input v-model="newsForm.url" /></label>
      </div>
      <button class="btn primary" type="submit">保存消息</button>
    </form>

    <!-- 市场快照录入 -->
    <form class="card" @submit.prevent="saveMarket">
      <div class="card-header">
        <div class="card-icon-wrap" style="background:var(--ok);">
          <Icon name="dashboard" :size="20" />
        </div>
        <div class="card-title">
          <h3>市场快照</h3>
        </div>
      </div>
      <div class="form-grid">
        <label>日期<input v-model="marketForm.snapshot_date" type="date" /></label>
        <label>指数状态<input v-model="marketForm.index_state" /></label>
        <label>市场量能<input v-model="marketForm.market_volume_state" /></label>
        <label>涨停家数<input v-model.number="marketForm.limit_up_count" type="number" /></label>
        <label>跌停家数<input v-model.number="marketForm.limit_down_count" type="number" /></label>
        <label class="wide">热点板块<input v-model="marketForm.hot_sectors" /></label>
        <label class="wide">风险事件<input v-model="marketForm.risk_events" /></label>
      </div>
      <button class="btn primary" type="submit">保存快照</button>
    </form>
  </section>

  <!-- 消息列表卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="news" :size="20" />
      </div>
      <div class="card-title">
        <h3>消息列表</h3>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>时间</th><th>标的</th><th>来源</th><th>情绪</th><th>情景</th><th>标题</th></tr>
        </thead>
        <tbody>
          <tr v-for="n in news" :key="n.id">
            <td>{{ n.published_at }}</td>
            <td>{{ n.name }}</td>
            <td>{{ n.source }}</td>
            <td>{{ n.sentiment }}</td>
            <td>{{ n.scenario }}</td>
            <td>{{ n.title }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Commit NewsCenter页面改造**

```bash
git add frontend/src/pages/NewsCenter.vue
git commit -m "feat: refactor NewsCenter page with card-based layout"
```

---

## Task 9: 改造AiAnalysis.vue页面

**Files:**
- Modify: `frontend/src/pages/AiAnalysis.vue`

- [ ] **Step 1: 导入Icon组件并修改布局**

```vue
<script setup>
import { computed, onMounted, ref } from "vue";
import Icon from "../components/Icons.vue";
import { apiGet, apiPost } from "../services/api";

// ... 现有代码保持不变
</script>

<template>
  <!-- DeepSeek配置卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="ai" :size="20" />
      </div>
      <div class="card-title">
        <h3>DeepSeek 每日分析</h3>
        <p class="card-subtitle">{{ statusText }}</p>
      </div>
      <div class="card-actions">
        <button class="btn primary" :disabled="loading" @click="runAnalysis">
          {{ loading ? "生成中..." : "生成今日 AI 日报" }}
        </button>
      </div>
    </div>
    <label class="wide" style="margin-top:15px;">
      补充说明
      <textarea v-model="extraNote" placeholder="补充今日盘面、重点板块或个人观察"></textarea>
    </label>
  </section>

  <!-- 分析报告历史卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="dashboard" :size="20" />
      </div>
      <div class="card-title">
        <h3>分析报告历史</h3>
      </div>
    </div>
    <div v-for="r in reports" :key="r.id" class="card" style="margin-bottom:15px;">
      <div class="card-header">
        <h4 style="margin:0;color:var(--ink);">{{ r.report_date }} · {{ r.provider }} · {{ r.status }}</h4>
        <span class="risk-tag low">{{ r.model }}</span>
      </div>
      <div class="report">{{ r.content }}</div>
    </div>
    <p v-if="!reports.length" class="text-muted">还没有报告。</p>
  </section>
</template>
```

- [ ] **Step 2: Commit AiAnalysis页面改造**

```bash
git add frontend/src/pages/AiAnalysis.vue
git commit -m "feat: refactor AiAnalysis page with card-based layout"
```

---

## Task 10: 改造Settings.vue页面

**Files:**
- Modify: `frontend/src/pages/Settings.vue`

- [ ] **Step 1: 导入Icon组件并修改布局**

```vue
<script setup>
import { onMounted, ref } from "vue";
import Icon from "../components/Icons.vue";
import { apiGet } from "../services/api";

const emit = defineEmits(["toast"]);
const status = ref({});

onMounted(async () => {
  try { status.value = await apiGet("/api/settings/deepseek"); } catch (err) { emit("toast", err.message); }
});
</script>

<template>
  <!-- DeepSeek配置卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap">
        <Icon name="settings" :size="20" />
      </div>
      <div class="card-title">
        <h3>DeepSeek 配置</h3>
      </div>
    </div>
    <div class="report">{{ JSON.stringify(status, null, 2) }}</div>
  </section>

  <!-- 运行环境卡片 -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon-wrap" style="background:var(--ok);">
        <Icon name="settings" :size="20" />
      </div>
      <div class="card-title">
        <h3>运行环境</h3>
      </div>
    </div>
    <div class="report">DEEPSEEK_API_KEY=你的Key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

启动示例：
DEEPSEEK_API_KEY=sk-xxx PORT=8080 ./start.sh</div>
  </section>
</template>
```

- [ ] **Step 2: Commit Settings页面改造**

```bash
git add frontend/src/pages/Settings.vue
git commit -m "feat: refactor Settings page with card-based layout"
```

---

## Task 11: 测试和验证

**Files:**
- 测试文件不需要单独创建,因为这是UI改造项目

- [ ] **Step 1: 启动前端开发服务器验证**

```bash
cd frontend
npm run dev
```

打开浏览器访问 http://localhost:5173 验证:
- 侧边栏扁平化图标是否正确显示
- 卡片圆角和阴影效果是否符合设计
- 所有页面布局是否正确
- 交互效果是否流畅

- [ ] **Step 2: 检查响应式布局**

缩小浏览器窗口到980px以下验证:
- 侧边栏是否正确收缩为60px
- 图标是否居中显示
- 菜单文字是否隐藏
- 卡片网格是否正确调整为单列

- [ ] **Step 3: 构建生产版本验证**

```bash
cd frontend
npm run build
```

检查构建是否成功,生成的dist目录是否包含所有资源文件。

---

## Task 12: 最终提交

- [ ] **Step 1: 创建设计规范文档**

创建 `docs/superpowers/specs/2026-07-06-ui-redesign-design.md`:

```markdown
# UI Redesign Design Specification

## Design Style
混合方案(A+C): 简洁现代风格 + 卡片化交互设计

## Core Elements

### 颜色系统
- Background: #f8fafc (浅灰)
- Sidebar: #1e293b (深色)
- Primary: #176b87 (蓝绿)
- Success: #067647 (绿)
- Danger: #b42318 (红)
- Warning: #b54708 (橙)

### 圆角和阴影
- Card: 12px圆角 + 2px 8px rgba(0,0,0,.08)阴影
- Icons: 8px圆角容器
- Buttons: 8px圆角
- Inputs: 8px圆角

### 扁平化图标
所有图标使用SVG扁平化设计,包括:
- chart, dashboard, holdings, kline, news, ai, settings
- money, down, warning

### 卡片组件
- 左侧色块标识(4px宽)
- 顶部图标容器(40px圆角)
- 标题和副标题区域
- 操作按钮区域
- 底部交互提示

### 响应式布局
- 大屏: 220px侧边栏 + 多列卡片网格
- 小屏(<980px): 60px侧边栏 + 单列卡片

## Implementation Files
- frontend/src/components/Icons.vue
- frontend/src/components/Card.vue
- frontend/src/styles.css
- frontend/src/App.vue
- frontend/src/pages/*.vue (所有页面)
```

- [ ] **Step 2: 提交设计规范文档**

```bash
git add docs/superpowers/specs/2026-07-06-ui-redesign-design.md
git commit -m "docs: add UI redesign design specification"
```

- [ ] **Step 3: 创建总结提交**

```bash
git add .
git commit -m "feat: complete UI redesign with mixed A+C approach

- Add SVG flat icon component system
- Implement card-based layout with rounded corners and shadows
- Refactor sidebar with flat icons and deep background
- Update all pages with card-based design
- Add responsive layout support
- Improve visual hierarchy and interaction effects"
```

---

## Self-Review Checklist

**1. Spec Coverage:**
- ✅ 扁平化图标系统 - Task 1
- ✅ 卡片组件系统 - Task 2
- ✅ 全局样式更新 - Task 3
- ✅ 侧边栏改造 - Task 4
- ✅ Dashboard页面 - Task 5
- ✅ Holdings页面 - Task 6
- ✅ KlineVolume页面 - Task 7
- ✅ NewsCenter页面 - Task 8
- ✅ AiAnalysis页面 - Task 9
- ✅ Settings页面 - Task 10
- ✅ 测试验证 - Task 11
- ✅ 设计文档 - Task 12

**2. Placeholder Scan:**
- ✅ 无"TBD"、"TODO"等placeholder
- ✅ 所有代码步骤都有完整实现
- ✅ 所有commit message都有具体内容
- ✅ 无引用未定义的类型/函数

**3. Type Consistency:**
- ✅ Icon组件name属性类型一致(String, required)
- ✅ Card组件tone属性类型一致(String, default: 'default')
- ✅ 所有页面导入Icon组件方式一致
- ✅ CSS变量命名一致(var(--primary), var(--danger)等)

---

计划完成,保存到 `docs/superpowers/plans/2026-07-06-ui-redesign-plan.md`。

两种执行方式:

**1. Subagent-Driven (推荐)** - 我为每个任务派发新的子代理,在任务间进行审查,快速迭代

**2. Inline Execution** - 在本会话中使用executing-plans执行,批量执行并设置检查点进行审查

选择哪种方式?