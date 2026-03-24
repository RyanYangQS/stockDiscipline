/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Trade',
    component: () => import('@/views/TradePanel.vue'),
    meta: { title: '交易面板' }
  },
  {
    path: '/screening',
    name: 'Screening',
    component: () => import('@/views/StockScreening.vue'),
    meta: { title: 'AI选股' }
  },
  {
    path: '/rules',
    name: 'Rules',
    component: () => import('@/views/RuleConfig.vue'),
    meta: { title: '规则配置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
