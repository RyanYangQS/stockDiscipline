<template>
  <el-container class="site">
    <el-aside width="220px" class="sidebar">
      <div class="brand">
        <div class="brand-icon"><Icon name="chart" :size="20" /></div>
        <span>Stock Discipline</span>
      </div>
      <nav class="sidebar-nav">
        <div v-for="item in nav" :key="item.key" class="sidebar-menu" :class="{ active: current === item.key }" @click="current = item.key">
          <div class="menu-icon-wrap"><Icon :name="item.icon" :size="16" /></div>
          <span>{{ item.label }}</span>
        </div>
      </nav>
    </el-aside>
    <el-main class="app">
      <header class="page-head">
        <div>
          <h1>{{ active.label }}</h1>
          <p>{{ active.desc }}</p>
        </div>
      </header>
      <component :is="active.component" @toast="toast" />
    </el-main>
  </el-container>
  <el-alert v-if="toastText" class="toast" :title="toastText" type="success" show-icon :closable="false" />
</template>

<script setup>
import { computed, ref } from "vue";
import Icon from "./components/Icons.vue";
import Dashboard from "./pages/Dashboard.vue";
import Holdings from "./pages/Holdings.vue";
import KlineVolume from "./pages/KlineVolume.vue";
import NewsCenter from "./pages/NewsCenter.vue";
import Settings from "./pages/Settings.vue";

const current = ref("dashboard");
const toastText = ref("");
let timer = null;

const nav = [
  { key: "dashboard", label: "总览", icon: "dashboard", desc: "持仓、量能、消息面、AI日报和纪律风险总控", component: Dashboard },
  { key: "holdings", label: "持仓建议", icon: "holdings", desc: "按附件表格输出到价位就执行的操作计划", component: Holdings },
  { key: "kline", label: "K线量能", icon: "kline", desc: "基于 KLineCharts 的专业K线与成交量分析", component: KlineVolume },
  { key: "news", label: "智能市场分析", icon: "ai", desc: "消息面、AI日报和市场智能分析", component: NewsCenter },
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
