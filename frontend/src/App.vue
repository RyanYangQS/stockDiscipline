<template>
  <el-container class="site">
    <el-aside width="220px" class="sidebar">
      <div class="brand">Stock Discipline</div>
      <el-menu :default-active="current" background-color="#111827" text-color="#d1d5db" active-text-color="#ffffff" @select="current = $event">
        <el-menu-item v-for="item in nav" :key="item.key" :index="item.key">{{ item.label }}</el-menu-item>
      </el-menu>
    </el-aside>
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

<script setup>
import { computed, ref } from "vue";
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
  { key: "dashboard", label: "总览", desc: "持仓、量能、消息面、AI日报和纪律风险总控", component: Dashboard },
  { key: "holdings", label: "持仓建议", desc: "按附件表格输出到价位就执行的操作计划", component: Holdings },
  { key: "kline", label: "K线量能", desc: "基于 KLineCharts 的专业K线与成交量分析", component: KlineVolume },
  { key: "news", label: "消息面", desc: "公告、监管、新闻、舆情和市场快照", component: NewsCenter },
  { key: "analysis", label: "AI日报", desc: "每天汇总持仓、量能、消息和K线后交给 DeepSeek 分析", component: AiAnalysis },
  { key: "settings", label: "设置", desc: "DeepSeek、数据源和运行状态", component: Settings }
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
