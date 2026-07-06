# UI Redesign Design Specification - 混合方案(A+C)

## Design Style
混合方案(A+C): 简洁现代风格 + 卡片化交互设计 + 扁平化图标 + 深色模式自动切换

## Core Elements

### 颜色系统

**浅色模式变量:**
- Background: `#f8fafc` (浅灰)
- Sidebar: `#1e293b` (深色)
- Primary: `#176b87` (蓝绿)
- Success: `#067647` (绿)
- Danger: `#b42318` (红)
- Warning: `#b54708` (橙)
- Panel: `#fff` (白)
- Ink: `#1e293b` (深色文字)
- Muted: `#64748b` (次要文字)

**深色模式自动切换:**
使用 `@media (prefers-color-scheme: dark)` 检测系统偏好
- Background: `#0f172a` (深色背景)
- Panel: `#1e293b` (深色面板)
- Ink: `#f1f5f9` (浅色文字)
- Muted: `#94a3b8` (浅色次要文字)
- Sidebar保持深色背景不变

### 圆角和阴影
- Card: 12px圆角 + `0 2px 8px rgba(0,0,0,.08)` 阴影
- Icons: 8px圆角容器
- Buttons: 8px圆角
- Inputs: 8px圆角
- Risk tags: 4px圆角

### 扁平化图标
所有图标使用SVG扁平化设计,包括:
- chart (柱状图)
- dashboard (四宫格)
- holdings (持仓线)
- kline (蜡烛图)
- news (文档)
- ai (笑脸机器人)
- settings (齿轮)
- money (货币)
- down (下跌箭头)
- warning (警告三角)

### 卡片组件
**Card.vue特性:**
- 左侧色块标识(4px宽): default, primary, danger, warning, success
- 顶部图标容器(40px圆角,背景色匹配tone)
- 标题和副标题区域
- 操作按钮区域(actions slot)
- 底部交互提示(footer slot)
- 圆角12px + 阴影

### 响应式布局
- 大屏(>980px): 220px侧边栏 + 多列卡片网格
- 小屏(<980px): 60px侧边栏 + 单列卡片
- 侧边栏收缩:隐藏文字,只显示图标

### 交互效果
- 侧边栏菜单hover: `rgba(255,255,255,.08)` 背景
- 侧边栏active: `#176b87` 背景 + 加粗
- 按钮:hover阴影效果
- 输入框:focus-visible outline
- 过渡动画: background 0.2s

## Implementation Files

**创建文件:**
- `frontend/src/components/Icons.vue` - SVG扁平化图标组件库
- `frontend/src/components/Card.vue` - 可复用卡片组件

**修改文件:**
- `frontend/src/styles.css` - 全局CSS(圆角、阴影、深色模式)
- `frontend/src/App.vue` - 侧边栏扁平化图标改造
- `frontend/src/pages/Dashboard.vue` - 指标卡片、风险卡片
- `frontend/src/pages/Holdings.vue` - 持仓表格、表单卡片
- `frontend/src/pages/KlineVolume.vue` - K线图、量能表单卡片
- `frontend/src/pages/NewsCenter.vue` - 消息录入、快照卡片
- `frontend/src/pages/AiAnalysis.vue` - AI日报卡片
- `frontend/src/pages/Settings.vue` - 设置配置卡片

## Git Commits

**完成的commits:**
1. `13cc379` - feat: add SVG flat icon component library
2. `6722d60` - feat: add reusable card component with tones
3. `4a79e0d` - fix: make Card icon background respect tone prop
4. `b3d2669` - feat: update global CSS with rounded corners, shadows, and dark mode support
5. `6ac2c27` - fix: improve CSS with dark mode support, accessibility, and DRY principles
6. `63b8bfd` - App.vue sidebar transformation
7. `4905584` - Dashboard.vue card layout
8. `626f527` - Holdings.vue card layout
9. `288d814` - KlineVolume.vue card layout
10. `caa980f` - NewsCenter.vue card layout
11. `1562f6e` - AiAnalysis.vue card layout
12. `9623150` - Settings.vue card layout

## Testing Results

**验证通过:**
- ✅ Dev server运行成功 (http://127.0.0.1:5176)
- ✅ 所有组件正确渲染
- ✅ SVG图标正确显示
- ✅ 卡片圆角和阴影效果正常
- ✅ 侧边栏导航功能正常
- ✅ 深色模式根据系统偏好自动切换
- ✅ 响应式布局正常(<980px侧边栏收缩)
- ✅ 生产构建成功(dist目录生成)

## Accessibility

**可访问性改进:**
- 添加`:focus-visible`焦点样式(按钮、输入框)
- 使用CSS变量确保颜色对比度
- 语义化HTML结构
- 键盘导航支持

## Browser Compatibility

**兼容性:**
- CSS Custom Properties: 所有现代浏览器
- CSS Grid/Flexbox: 所有现代浏览器
- prefers-color-scheme: 所有现代浏览器
- :focus-visible: 所有现代浏览器

## Design Principles

**设计原则:**
1. **简洁现代**: 清爽的浅灰背景,不使用渐变色
2. **扁平化图标**: 所有图标使用SVG扁平化设计,无拟物元素
3. **卡片化布局**: 圆角卡片 + 阴影,营造层次感
4. **深色模式**: 自动根据系统偏好切换,侧边栏保持深色
5. **响应式**: 移动端侧边栏收缩,卡片单列布局
6. **一致性**: 统一的CSS变量系统,统一的组件接口
7. **可访问性**: 焦点样式,颜色对比度,键盘导航

## Usage Examples

**图标使用:**
```vue
<Icon name="dashboard" :size="16" />
<Icon name="chart" :size="20" />
```

**卡片使用:**
```vue
<Card title="指标卡片" icon="chart" tone="primary">
  <div class="metric-value">¥52,340</div>
  <template #footer>查看详情 →</template>
</Card>

<Card title="风险警告" icon="warning" tone="danger">
  高风险持仓...
  <template #actions>
    <button class="btn primary">刷新</button>
  </template>
</Card>
```

**深色模式:**
系统会自动检测并切换,无需手动设置。主内容区切换为深色,侧边栏保持深色背景。

---

**实施完成时间:** 2026-07-06
**验证状态:** 所有测试通过,生产就绪