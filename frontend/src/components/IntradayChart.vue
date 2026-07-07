<template>
  <div class="intraday-chart-wrapper">
    <div ref="chartContainer" class="chart-container"></div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch, computed } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  basePrice: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['request-more-data']);

const chartContainer = ref(null);
const loading = ref(false);
let chartInstance = null;

// 计算均价
const averagePrice = computed(() => {
  if (!props.data || props.data.length === 0) return 0;
  
  const totalAmount = props.data.reduce((sum, item) => sum + (item.amount || 0), 0);
  const totalVolume = props.data.reduce((sum, item) => sum + (item.volume || 0), 0);
  
  if (totalVolume === 0) return props.basePrice;
  return totalAmount / totalVolume;
});

// 计算涨跌幅范围（±10%自适应）
const priceRange = computed(() => {
  if (!props.basePrice || props.basePrice === 0) {
    return { min: -10, max: 10 };
  }
  
  const rangePercent = 10; // ±10%
  return {
    min: -rangePercent,
    max: rangePercent
  };
});

// 转换数据为ECharts格式
const chartData = computed(() => {
  if (!props.data || props.data.length === 0) return [];
  
  return props.data.map(item => {
    const changePercent = props.basePrice > 0 
      ? ((item.close_price - props.basePrice) / props.basePrice * 100)
      : 0;
    
    return {
      time: item.trade_date || item.time,
      value: changePercent,
      price: item.close_price,
      volume: item.volume
    };
  });
});

// 均价线数据（相对于基准价的涨跌幅）
const avgLineData = computed(() => {
  if (!props.data || props.data.length === 0 || props.basePrice === 0) return [];
  
  const avgPercent = ((averagePrice.value - props.basePrice) / props.basePrice * 100);
  
  // 均价线是一条水平线
  return chartData.value.map(item => ({
    time: item.time,
    value: avgPercent
  }));
});

// 初始化图表
function initChart() {
  if (!chartContainer.value) return;
  
  chartInstance = echarts.init(chartContainer.value);
  
  const option = {
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params) => {
        if (!params || params.length === 0) return '';
        
        const timeParam = params[0];
        const priceParam = params.find(p => p.seriesName === '价格涨跌');
        const avgParam = params.find(p => p.seriesName === '均价线');
        const volParam = params.find(p => p.seriesName === '成交量');
        
        const time = timeParam.name;
        const price = priceParam?.data?.price || 0;
        const changePercent = priceParam?.data?.value || 0;
        const avgPercent = avgParam?.data?.value || 0;
        const volume = volParam?.data?.volume || 0;
        
        return `
          <div style="font-size: 14px; padding: 5px;">
            <div style="font-weight: bold; margin-bottom: 8px;">${time}</div>
            <div style="color: ${changePercent >= 0 ? '#ef5350' : '#26a69a'};">
              当前价: ${price.toFixed(2)}元 (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)
            </div>
            <div style="color: #ff9800;">
              均价: ${averagePrice.value.toFixed(2)}元 (${avgPercent >= 0 ? '+' : ''}${avgPercent.toFixed(2)}%)
            </div>
            <div style="color: #888;">
              成交量: ${(volume / 10000).toFixed(0)}万手
            </div>
          </div>
        `;
      }
    },
    legend: {
      data: ['价格涨跌', '均价线'],
      top: 10,
      textStyle: {
        color: '#888'
      }
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        top: '15%',
        height: '60%'
      },
      {
        left: '10%',
        right: '8%',
        top: '80%',
        height: '15%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: chartData.value.map(item => item.time),
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: {
          color: '#888',
          fontSize: 12,
          interval: Math.floor(chartData.value.length / 6) // 显示约6个时间点
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#ddd',
            type: 'dashed'
          }
        }
      },
      {
        type: 'category',
        gridIndex: 1,
        data: chartData.value.map(item => item.time),
        boundaryGap: false,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '涨跌幅(%)',
        min: priceRange.value.min,
        max: priceRange.value.max,
        position: 'right',
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: {
          color: '#888',
          formatter: '{value}%'
        },
        splitLine: {
          lineStyle: {
            color: '#ddd',
            type: 'dashed'
          }
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(255, 255, 255, 0.05)', 'rgba(255, 255, 255, 0.1)']
          }
        }
      },
      {
        type: 'value',
        name: '0%',
        position: 'left',
        show: true,
        axisLine: {
          show: true,
          onZero: true,
          lineStyle: {
            color: '#888',
            type: 'solid',
            width: 2
          }
        },
        axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false }
      },
      {
        type: 'value',
        name: '成交量',
        gridIndex: 1,
        splitNumber: 2,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          show: true,
          color: '#888',
          formatter: (value) => `${(value / 10000).toFixed(0)}万`
        },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '价格涨跌',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: (params) => {
            const lastValue = chartData.value[chartData.value.length - 1]?.value || 0;
            return lastValue >= 0 ? '#ef5350' : '#26a69a';
          }
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 83, 80, 0.3)' },
            { offset: 1, color: 'rgba(239, 83, 80, 0.05)' }
          ])
        },
        data: chartData.value.map(item => ({
          value: item.value,
          price: item.price,
          volume: item.volume
        }))
      },
      {
        name: '均价线',
        type: 'line',
        smooth: false,
        symbol: 'none',
        lineStyle: {
          width: 1,
          color: '#ff9800',
          type: 'dashed'
        },
        data: avgLineData.value.map(item => ({
          value: item.value
        }))
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 2,
        itemStyle: {
          color: (params) => {
            const dataIndex = params.dataIndex;
            const currentValue = chartData.value[dataIndex]?.value || 0;
            return currentValue >= 0 ? '#ef5350' : '#26a69a';
          }
        },
        data: chartData.value.map(item => ({
          value: item.volume,
          volume: item.volume
        }))
      }
    ]
  };
  
  chartInstance.setOption(option);
}

// 更新图表数据
function updateChart() {
  if (!chartInstance) return;
  
  chartInstance.setOption({
    xAxis: [
      { data: chartData.value.map(item => item.time) },
      { data: chartData.value.map(item => item.time) }
    ],
    series: [
      {
        data: chartData.value.map(item => ({
          value: item.value,
          price: item.price,
          volume: item.volume
        }))
      },
      {
        data: avgLineData.value.map(item => ({
          value: item.value
        }))
      },
      {
        data: chartData.value.map(item => ({
          value: item.volume,
          volume: item.volume
        }))
      }
    ]
  });
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart();
}, { deep: true });

// 监听窗口大小变化
function handleResize() {
  if (chartInstance) {
    chartInstance.resize();
  }
}

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  window.removeEventListener('resize', handleResize);
});

defineExpose({
  updateChart
});
</script>

<style scoped>
.intraday-chart-wrapper {
  position: relative;
  width: 100%;
  height: 500px;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(26, 26, 26, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #ef5350;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-overlay span {
  margin-top: 10px;
  color: #888;
  font-size: 14px;
}
</style>