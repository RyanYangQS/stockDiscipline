<template>
  <div class="rules-page">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
              <polyline points="16 7 22 7 22 13"></polyline>
            </svg>
          </span>
          <span class="logo-text">镇金仓</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            交易面板
          </router-link>
          <router-link to="/screening" class="nav-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <circle cx="12" cy="12" r="6"></circle>
              <circle cx="12" cy="12" r="2"></circle>
            </svg>
            AI选股
          </router-link>
          <router-link to="/rules" class="nav-btn active">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            规则配置
          </router-link>
        </nav>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-content">
      <div class="rules-container">
        <el-tabs v-model="activeTab">
          <!-- 系统规则 -->
          <el-tab-pane label="系统默认规则" name="system">
            <div class="tab-header">
              <p class="tab-desc">系统内置规则根据您的《个人股票交易纪律系统规则》自动导入，无法删除或修改核心参数。</p>
            </div>
            <el-table :data="systemRules" row-key="id" height="calc(100vh - 220px)" style="width: 100%">
              <el-table-column prop="name" label="规则名称" width="140" />
              <el-table-column prop="category" label="分类" width="100">
                <template #default="{ row }">
                  <div v-memo="[row.id, row.category]">
                    <el-tag :type="row.category === 'exclude' ? 'danger' : row.category === 'core' ? 'success' : 'warning'" size="small">
                      {{ row.category === 'exclude' ? '排除' : row.category === 'core' ? '核心' : '风控' }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="规则说明" />
              <el-table-column prop="is_enabled" label="状态" width="120">
                <template #default="{ row }">
                  <div v-memo="[row.id, row.is_enabled]">
                    <span 
                      class="status-tag"
                      :class="row.is_enabled ? 'status-enabled' : 'status-disabled'"
                    >
                      {{ row.is_enabled ? '已启用' : '已禁用' }}
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <div v-memo="[row.id, row.is_enabled]">
                    <button 
                      class="custom-btn"
                      :class="row.is_enabled ? 'btn-danger' : 'btn-success'"
                      @click="toggleSystemRule(row)"
                    >
                      {{ row.is_enabled ? '禁用' : '启用' }}
                    </button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 自定义规则 -->
          <el-tab-pane label="自定义规则" name="custom">
            <div class="tab-header">
              <p class="tab-desc">创建您个人的选股规则，补充或替代系统规则</p>
              <el-button type="primary" size="small" @click="addCustomRule">+ 新增规则</el-button>
            </div>
            <el-table :data="customRules" height="calc(100vh - 280px)" style="width: 100%">
              <el-table-column prop="name" label="规则名称" width="140">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.name" size="small" />
                  <span v-else>{{ row.name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="condition" label="条件" width="180">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.condition" size="small" placeholder="如: PE < 20" />
                  <span v-else>{{ row.condition }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="说明">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.description" size="small" />
                  <span v-else>{{ row.description }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_enabled" label="状态" width="80">
                <template #default="{ row }">
                  <el-switch v-model="row.is_enabled" @change="toggleRule(row)" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <template v-if="row.editing">
                      <el-button type="success" size="small" @click="saveRule(row)">保存</el-button>
                      <el-button type="default" size="small" @click="row.editing = false">取消</el-button>
                    </template>
                    <template v-else>
                      <el-button type="primary" size="small" @click="row.editing = true">编辑</el-button>
                      <el-button type="danger" size="small" @click="deleteRule(row)">删除</el-button>
                    </template>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="customRules.length === 0" class="empty-state">
              <div class="empty-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="12" y1="18" x2="12" y2="12"></line>
                  <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
              </div>
              <p>暂无自定义规则</p>
            </div>
          </el-tab-pane>

          <!-- 风控规则 -->
          <el-tab-pane label="风控规则" name="risk">
            <div class="tab-header">
              <p class="tab-desc warning">以下风控参数经过历史验证，修改可能导致风险扩大。</p>
            </div>
            <el-table :data="riskRules" height="calc(100vh - 280px)" style="width: 100%">
              <el-table-column prop="name" label="规则名称" width="160" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="value" label="当前值" width="100">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.value" size="small" style="width: 70px" />
                  <span v-else class="value">{{ row.value }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="default" label="默认值" width="100" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <template v-if="row.editing">
                      <el-button type="success" size="small" @click="saveRiskRule(row)">保存</el-button>
                      <el-button type="default" size="small" @click="row.editing = false">取消</el-button>
                    </template>
                    <template v-else>
                      <el-button type="primary" size="small" @click="row.editing = true">修改</el-button>
                      <el-button type="default" size="small" @click="resetRiskRule(row)">重置</el-button>
                    </template>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </main>
  </div>
</template>

<script setup>
/**
 * 规则配置视图
 */
import { ref, onMounted, nextTick } from 'vue'
import { getSystemRules, getCustomRules, createRule, toggleRule, deleteRule } from '@/api/rule'
import { ElMessage } from 'element-plus'

const activeTab = ref('system')
const systemRules = ref([])
const customRules = ref([])

const riskRules = ref([
  { name: '最大止损比例', description: '单笔交易最大浮亏止损线', value: '8%', default: '8%', editing: false },
  { name: '止盈阶梯1', description: '浮盈达到此比例触发第一级止盈', value: '3%', default: '3%', editing: false },
  { name: '止盈阶梯2', description: '浮盈达到此比例触发第二级止盈', value: '5%', default: '5%', editing: false },
  { name: '止盈阶梯3', description: '浮盈达到此比例触发移动止盈', value: '10%', default: '10%', editing: false },
  { name: '连续亏损限仓', description: '连续亏损日后限制仓位', value: '30%', default: '30%', editing: false },
  { name: '单日最大回撤', description: '单日账户最大回撤预警线', value: '5%', default: '5%', editing: false }
])

const loadSystemRules = async () => {
  try {
    const data = await getSystemRules()
    systemRules.value = data || []
  } catch (e) {
    console.error('加载系统规则失败', e)
  }
}

const loadCustomRules = async () => {
  try {
    const data = await getCustomRules()
    customRules.value = (data || []).map(r => ({ ...r, editing: false }))
  } catch (e) {
    console.error('加载自定义规则失败', e)
  }
}

const addCustomRule = () => {
  customRules.value.push({
    name: '',
    condition: '',
    description: '',
    category: 'custom',
    rule_type: 'filter',
    is_enabled: true,
    editing: true,
    isNew: true
  })
}

const saveRule = async (rule) => {
  if (!rule.name || !rule.condition) {
    ElMessage.warning('请填写完整的规则信息')
    return
  }
  
  try {
    if (rule.isNew) {
      await createRule({
        name: rule.name,
        condition: rule.condition,
        description: rule.description,
        category: 'custom',
        rule_type: 'filter'
      })
      ElMessage.success('规则创建成功')
    }
    rule.editing = false
    loadCustomRules()
  } catch (e) {
    console.error('保存规则失败', e)
  }
}

const deleteRuleConfirm = async (rule) => {
  try {
    if (!rule.isNew) {
      await deleteRule(rule.id)
    }
    const idx = customRules.value.indexOf(rule)
    if (idx > -1) {
      customRules.value.splice(idx, 1)
    }
    ElMessage.success('规则已删除')
  } catch (e) {
    console.error('删除规则失败', e)
  }
}

const toggleRuleStatus = async (rule) => {
  try {
    await toggleRule(rule.id)
    ElMessage.success('状态已更新')
  } catch (e) {
    console.error('更新状态失败', e)
    rule.is_enabled = !rule.is_enabled
  }
}

/**
 * 切换系统规则的启用/禁用状态
 * @param {Object} rule - 要切换状态的规则对象
 */
const toggleSystemRule = (rule) => {
  rule.is_enabled = !rule.is_enabled
}

const saveRiskRule = (rule) => {
  rule.editing = false
  ElMessage.success('风控规则已保存')
}

const resetRiskRule = (rule) => {
  rule.value = rule.default
  ElMessage.info('已重置为默认值')
}

onMounted(() => {
  loadSystemRules()
  loadCustomRules()
})
</script>

<style lang="scss" scoped>
.rules-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0d0d1a 100%);
}

.header {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(20px);
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .logo-icon {
    font-size: 26px;
  }
  
  .logo-text {
    font-size: 17px;
    font-weight: 700;
    background: linear-gradient(135deg, #7c83fd, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}

.header-nav {
  display: flex;
  gap: 4px;
  margin-left: 32px;
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
  border-radius: 10px;
  
  .nav-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    transition: all 0.25s;
    
    svg {
      flex-shrink: 0;
      vertical-align: middle;
    }
    
    &:hover {
      color: rgba(255, 255, 255, 0.85);
      background: rgba(255, 255, 255, 0.05);
    }
    
    &.active {
      background: linear-gradient(135deg, rgba(124, 131, 253, 0.2), rgba(168, 85, 247, 0.15));
      color: #fff;
    }
  }
}

.main-content {
  padding: 24px;
}

.rules-container {
  max-width: 1200px;
  margin: 0 auto;
  background: linear-gradient(145deg, rgba(22, 25, 40, 0.8), rgba(15, 18, 30, 0.9));
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px;
  
  // Tab样式优化
  :deep(.el-tabs__nav-wrap::after) {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    font-weight: 500;
    padding: 0 20px;
    height: 44px;
    line-height: 44px;
    
    &:hover {
      color: rgba(255, 255, 255, 0.8);
    }
    
    &.is-active {
      color: #667eea;
      font-weight: 600;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #667eea;
    height: 3px;
  }
  
  // 表格按钮样式优化
  :deep(.el-button--small) {
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border: none;
    transition: none !important;
    animation: none !important;
    
    &.el-button--primary {
      background: #3b82f6;
      color: #ffffff;
      
      &:hover {
        background: #2563eb;
        color: #ffffff;
      }
    }
    
    &.el-button--success,
    &.btn-success {
      background: #10b981;
      color: #ffffff;
      
      &:hover {
        background: #059669;
        color: #ffffff;
      }
    }
    
    &.el-button--danger,
    &.btn-danger {
      background: #ef4444;
      color: #ffffff;
      
      &:hover {
        background: #dc2626;
        color: #ffffff;
      }
    }
    
    &.el-button--default {
      background: #4b5563;
      color: #ffffff;
      
      &:hover {
        background: #374151;
        color: #ffffff;
      }
    }
  }
  
  // Switch样式
  :deep(.el-switch) {
    &.is-disabled {
      opacity: 0.5;
    }
  }
  
  // Tag样式
  :deep(.el-tag) {
    transition: none !important;
    animation: none !important;
  }
  
  // 表格样式
  :deep(.el-table) {
    background: transparent;
    transform: translateZ(0);
    will-change: transform;
    backface-visibility: hidden;
    
    // 全局禁用表格内所有动画
    * {
      transition: none !important;
      animation: none !important;
    }
    
    th.el-table__cell {
      background: rgba(255, 255, 255, 0.03);
      color: rgba(255, 255, 255, 0.7);
      font-weight: 600;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    td.el-table__cell {
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .el-table__row {
      &:hover {
        background: rgba(255, 255, 255, 0.02);
      }
    }
    
    // 禁用表格行过渡动画
    .el-table__row,
    .el-table__body tr {
      transition: none !important;
      animation: none !important;
    }
    
    // 禁用单元格过渡动画
    .el-table__cell {
      transition: none !important;
      animation: none !important;
    }
  }
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .tab-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    
    &.warning {
      padding: 10px 14px;
      background: rgba(245, 158, 11, 0.1);
      border-radius: 8px;
      color: #f59e0b;
    }
  }
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  
  * {
    transition: none !important;
    animation: none !important;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
  
  .empty-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    opacity: 0.6;
  }
}

.value {
  color: #a78bfa;
  font-weight: 700;
}

// 状态标签样式
.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  
  &.status-enabled {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
  }
  
  &.status-disabled {
    background: rgba(107, 114, 128, 0.2);
    color: #9ca3af;
  }
}

// 自定义按钮样式
.custom-btn {
  font-size: 13px;
  font-weight: 600;
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: none !important;
  animation: none !important;
  
  &.btn-success {
    background: #10b981;
    color: #ffffff;
    
    &:hover {
      background: #059669;
    }
  }
  
  &.btn-danger {
    background: #ef4444;
    color: #ffffff;
    
    &:hover {
      background: #dc2626;
    }
  }
}
</style>
