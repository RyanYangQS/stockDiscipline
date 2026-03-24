<template>
  <div class="rules-page">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">📈</span>
          <span class="logo-text">个人股票交易纪律系统</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="nav-btn">📊 交易面板</router-link>
          <router-link to="/screening" class="nav-btn">🎯 AI选股</router-link>
          <router-link to="/rules" class="nav-btn active">📋 规则配置</router-link>
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
            <el-table :data="systemRules" style="width: 100%">
              <el-table-column prop="name" label="规则名称" width="140" />
              <el-table-column prop="category" label="分类" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.category === 'exclude' ? 'danger' : row.category === 'core' ? 'success' : 'warning'" size="small">
                    {{ row.category === 'exclude' ? '排除' : row.category === 'core' ? '核心' : '风控' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="规则说明" />
              <el-table-column prop="is_enabled" label="状态" width="80">
                <template #default="{ row }">
                  <el-switch v-model="row.is_enabled" disabled />
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
            <el-table :data="customRules" style="width: 100%">
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
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <template v-if="row.editing">
                    <el-button type="success" size="small" link @click="saveRule(row)">保存</el-button>
                    <el-button size="small" link @click="row.editing = false">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" size="small" link @click="row.editing = true">编辑</el-button>
                    <el-button type="danger" size="small" link @click="deleteRule(row)">删除</el-button>
                  </template>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="customRules.length === 0" class="empty-state">
              <div class="empty-icon">📝</div>
              <p>暂无自定义规则</p>
            </div>
          </el-tab-pane>

          <!-- 风控规则 -->
          <el-tab-pane label="风控规则" name="risk">
            <div class="tab-header">
              <p class="tab-desc warning">以下风控参数经过历史验证，修改可能导致风险扩大。</p>
            </div>
            <el-table :data="riskRules" style="width: 100%">
              <el-table-column prop="name" label="规则名称" width="160" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="value" label="当前值" width="100">
                <template #default="{ row }">
                  <el-input v-if="row.editing" v-model="row.value" size="small" style="width: 70px" />
                  <span v-else class="value">{{ row.value }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="default" label="默认值" width="100" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <template v-if="row.editing">
                    <el-button type="success" size="small" link @click="saveRiskRule(row)">保存</el-button>
                    <el-button size="small" link @click="row.editing = false">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" size="small" link @click="row.editing = true">修改</el-button>
                    <el-button size="small" link @click="resetRiskRule(row)">重置</el-button>
                  </template>
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
import { ref, onMounted } from 'vue'
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
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.5);
    text-decoration: none;
    transition: all 0.25s;
    
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

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
  
  .empty-icon {
    font-size: 36px;
    margin-bottom: 12px;
  }
}

.value {
  color: #a78bfa;
  font-weight: 700;
}
</style>
