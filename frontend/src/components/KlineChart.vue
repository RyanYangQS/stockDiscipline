<template>
  <div ref="chartEl" class="chart"></div>
</template>

<script setup>
import { dispose, init } from "klinecharts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  bars: {
    type: Array,
    default: () => []
  }
});

const chartEl = ref(null);
let chart = null;
let resizeObserver = null;

function initChart() {
  if (!chartEl.value) return;
  if (chart) {
    dispose(chart);
    chart = null;
  }
  chart = init(chartEl.value);
  chart.setStyles({
    grid: {
      horizontal: { color: "#eef2f7" },
      vertical: { color: "#eef2f7" }
    },
    candle: {
      bar: {
        upColor: "#ef4444",
        downColor: "#16a34a",
        noChangeColor: "#64748b"
      },
      tooltip: {
        text: { color: "#334155" }
      }
    },
    xAxis: { axisLine: { color: "#d7dee8" } },
    yAxis: { axisLine: { color: "#d7dee8" } }
  });
  chart.createIndicator("VOL", false, { id: "candle_pane" });
  resizeObserver = new ResizeObserver(() => {
    if (chart) chart.resize();
  });
  resizeObserver.observe(chartEl.value);
  if (props.bars.length) {
    updateData();
  }
}

function updateData() {
  if (!chart || !props.bars.length) return;
  const data = props.bars.map((bar) => ({
    timestamp: new Date(`${bar.trade_date}T00:00:00`).getTime(),
    open: Number(bar.open_price) || 0,
    high: Number(bar.high_price) || 0,
    low: Number(bar.low_price) || 0,
    close: Number(bar.close_price) || 0,
    volume: Number(bar.volume) || 0,
    turnover: Number(bar.amount || 0)
  }));
  chart.applyNewData(data);
}

onMounted(initChart);
watch(() => props.bars, updateData, { deep: true });

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect();
  if (chart) dispose(chart);
});
</script>
