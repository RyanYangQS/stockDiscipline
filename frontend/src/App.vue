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
  <!-- Price Alert Notification -->
  <div v-if="priceAlerts.length" class="price-alert-container">
    <div v-for="alert in priceAlerts" :key="alert.id" class="price-alert" :class="alert.type" @click="dismissAlert(alert.id)">
      <div class="alert-icon">
        <span v-if="alert.type === 'up'">📈</span>
        <span v-else>📉</span>
      </div>
      <div class="alert-content">
        <div class="alert-title">{{ alert.name }}</div>
        <div class="alert-detail">
          <span class="alert-change">{{ alert.changeText }}</span>
          <span class="alert-price">{{ alert.price }}元</span>
        </div>
      </div>
      <button class="alert-close">×</button>
    </div>
  </div>
  <el-alert v-if="toastText" class="toast" :title="toastText" type="success" show-icon :closable="false" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Icon from "./components/Icons.vue";
import Dashboard from "./pages/Dashboard.vue";
import Holdings from "./pages/Holdings.vue";
import KlineVolume from "./pages/KlineVolume.vue";
import NewsCenter from "./pages/NewsCenter.vue";
import Settings from "./pages/Settings.vue";
import { apiGet } from "./services/api";

const current = ref("dashboard");
const toastText = ref("");
const priceAlerts = ref([]);
let timer = null;
let alertTimer = null;
let alertIdCounter = 0;

const nav = [
  { key: "dashboard", label: "数据总览", icon: "dashboard", desc: "持仓、量能、消息面、AI日报和纪律风险总控", component: Dashboard },
  { key: "holdings", label: "持仓建议", icon: "holdings", desc: "按附件表格输出到价位就执行的操作计划", component: Holdings },
  { key: "kline", label: "K线量能", icon: "kline", desc: "基于 KLineCharts 的专业K线与成交量分析", component: KlineVolume },
  { key: "news", label: "市场分析", icon: "ai", desc: "消息面、AI日报和市场智能分析", component: NewsCenter },
  { key: "settings", label: "系统设置", icon: "settings", desc: "DeepSeek、数据源和运行状态", component: Settings }
];

const active = computed(() => nav.find((item) => item.key === current.value) || nav[0]);

function toast(message) {
  toastText.value = message;
  clearTimeout(timer);
  timer = setTimeout(() => {
    toastText.value = "";
  }, 2600);
}

// Get dismissed alerts key for today
function getDismissedKey() {
  const today = new Date().toISOString().slice(0, 10);
  return `dismissed_alerts_${today}`;
}

// Load dismissed alerts from localStorage (per-day)
function loadDismissedAlerts() {
  const key = getDismissedKey();
  try {
    return JSON.parse(localStorage.getItem(key) || '[]');
  } catch {
    return [];
  }
}

// Save dismissed alert to localStorage
function saveDismissedAlert(stockName, alertType) {
  const key = getDismissedKey();
  const dismissed = loadDismissedAlerts();
  dismissed.push(`${stockName}_${alertType}`);
  localStorage.setItem(key, JSON.stringify(dismissed));
}

// Price alert monitoring - only for significant changes (>5%)
async function checkPriceAlerts() {
  try {
    const positions = await apiGet("/api/positions");
    const dismissed = loadDismissedAlerts();

    for (const p of positions) {
      // intraday_change_pct is daily change from yesterday's close
      // Use higher threshold (5%) for meaningful alerts
      const dailyChange = p.intraday_change_pct || 0;

      const alertKey = `${p.name}_${dailyChange >= 5 ? 'up' : 'down'}`;
      if (dismissed.includes(alertKey)) continue; // Skip if already dismissed

      // Alert threshold: daily change > 5% (significant movement)
      if (dailyChange >= 5) {
        addAlert({
          name: p.name,
          type: 'up',
          changeText: `涨幅 +${dailyChange.toFixed(2)}%`,
          price: p.current_price.toFixed(2),
          dismissedKey: alertKey
        });
      } else if (dailyChange <= -5) {
        addAlert({
          name: p.name,
          type: 'down',
          changeText: `跌幅 ${dailyChange.toFixed(2)}%`,
          price: p.current_price.toFixed(2),
          dismissedKey: alertKey
        });
      }
    }
  } catch (err) {
    // Silent fail for alert check
  }
}

function addAlert(alertData) {
  // Avoid duplicate alerts for same stock+type in current session
  const exists = priceAlerts.value.find(a => a.name === alertData.name && a.type === alertData.type);
  if (exists) return;

  const alert = {
    id: ++alertIdCounter,
    ...alertData
  };
  priceAlerts.value.push(alert);
}

function dismissAlert(id) {
  const alert = priceAlerts.value.find(a => a.id === id);
  if (alert && alert.dismissedKey) {
    // Save to localStorage so it doesn't reappear today
    saveDismissedAlert(alert.name, alert.type);
  }
  priceAlerts.value = priceAlerts.value.filter(a => a.id !== id);
}

function startAlertMonitor() {
  // Check for price alerts every 60 seconds during trading hours
  alertTimer = setInterval(checkPriceAlerts, 60000);
  // Initial check after 5 seconds
  setTimeout(checkPriceAlerts, 5000);
}

function stopAlertMonitor() {
  if (alertTimer) {
    clearInterval(alertTimer);
    alertTimer = null;
  }
}

onMounted(startAlertMonitor);
onBeforeUnmount(stopAlertMonitor);
</script>

<style scoped>
/* Price Alert Container - fixed top right */
.price-alert-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 280px;
}

.price-alert {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
  animation: slideIn 0.3s ease;
}

.price-alert:hover {
  transform: translateX(-5px);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Rising alert - red (A股上涨色) */
.price-alert.up {
  border-left: 4px solid #dc2626;
  background: linear-gradient(to right, rgba(220, 38, 38, 0.05), white);
}

.price-alert.up .alert-icon {
  color: #dc2626;
}

.price-alert.up .alert-change {
  color: #dc2626;
}

/* Falling alert - green (A股下跌色) */
.price-alert.down {
  border-left: 4px solid #16a34a;
  background: linear-gradient(to right, rgba(22, 163, 74, 0.05), white);
}

.price-alert.down .alert-icon {
  color: #16a34a;
}

.price-alert.down .alert-change {
  color: #16a34a;
}

.alert-icon {
  font-size: 20px;
  margin-right: 12px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
}

.alert-detail {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
}

.alert-change {
  font-weight: 600;
}

.alert-price {
  color: #6b7280;
}

.alert-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 4px;
  margin-left: 8px;
}

.alert-close:hover {
  color: #4b5563;
}
</style>
