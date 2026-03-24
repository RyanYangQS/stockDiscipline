# klinecharts 使用说明

## ❌ 错误的导入方式

```javascript
// ❌ 错误 - 会导致模块导出错误
import { klinecharts } from 'klinecharts'

// 使用时会报错
chart = klinecharts.init(chartRef.value)
```

**错误原因**: klinecharts库没有提供名为`klinecharts`的导出

## ✅ 正确的导入方式

```javascript
// ✅ 正确 - 按需导入
import { init, dispose } from 'klinecharts'

// 创建图表
const chart = init(chartRef.value, {
  theme: 'dark'
})

// 销毁图表
dispose(chartRef.value)
```

## 📚 完整示例

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { init, dispose } from 'klinecharts'

const chartRef = ref(null)
let chart = null

const initChart = () => {
  nextTick(() => {
    if (chartRef.value) {
      // 创建图表
      chart = init(chartRef.value, {
        theme: 'dark'
      })
      
      // 添加指标
      chart.createIndicator('MA', true, { calcParams: [5, 10, 20, 60] })
      chart.createIndicator('VOL', true, { height: 60 })
      
      // 设置数据
      chart.applyNewData([
        { timestamp: 1614153600000, open: 10, high: 15, low: 8, close: 12, volume: 1000 },
        // ...更多数据
      ])
    }
  })
}

onMounted(() => {
  initChart()
})

// 组件卸载时销毁图表
onBeforeUnmount(() => {
  if (chart && chartRef.value) {
    dispose(chartRef.value)
    chart = null
  }
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 500px;
}
</style>
```

## 🔧 常用API

### 初始化
```javascript
import { init, dispose } from 'klinecharts'

// 创建图表
const chart = init(domElement, options)
```

### 数据操作
```javascript
// 设置新数据
chart.applyNewData(dataList)

// 追加数据
chart.applyMoreData(dataList)

// 更新数据
chart.updateData(dataItem)
```

### 指标
```javascript
// 创建指标
chart.createIndicator('MA', true, { calcParams: [5, 10, 20] })
chart.createIndicator('MACD')
chart.createIndicator('RSI')

// 移除指标
chart.removeIndicator('MA')
```

### 样式
```javascript
// 设置主题
chart.setStyles({
  theme: 'dark',
  grid: {
    horizontal: { color: 'rgba(255,255,255,0.1)' }
  }
})
```

### 销毁
```javascript
// 销毁图表实例
dispose(domElement)
```

## 📖 官方文档

- 官网: https://klinecharts.com/
- GitHub: https://github.com/klinecharts/KLineChart
- 文档: https://klinecharts.com/guide

## ⚠️ 注意事项

1. **容器尺寸**: 图表容器必须有明确的宽高
2. **销毁图表**: 组件卸载时务必调用`dispose()`释放资源
3. **数据格式**: 时间戳为毫秒级
4. **异步渲染**: 使用`nextTick()`确保DOM已挂载

## 🐛 常见问题

### Q: 图表不显示?
A: 检查容器是否有宽高,使用`nextTick`确保DOM已渲染

### Q: 切换股票时图表残留?
A: 切换前先销毁旧图表:
```javascript
if (chart) {
  dispose(chartRef.value)
}
// 再创建新图表
```

### Q: 内存泄漏?
A: 确保在`onBeforeUnmount`中调用`dispose()`
