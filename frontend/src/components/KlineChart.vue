<template>
  <div class="chart-shell">
    <div ref="chartEl" class="chart"></div>
    <div v-if="hoverData" class="trade-tooltip" :style="tooltipStyle">
      <div class="tooltip-row"><span>时间</span><strong>{{ hoverData.dateText }}</strong></div>
      <div class="tooltip-row"><span>开盘</span><em :class="priceClass(hoverData.open, hoverData.prevClose)">{{ price(hoverData.open) }}</em></div>
      <div class="tooltip-row"><span>收盘</span><em :class="priceClass(hoverData.close, hoverData.prevClose)">{{ price(hoverData.close) }}</em></div>
      <div class="tooltip-row"><span>最高</span><em :class="priceClass(hoverData.high, hoverData.prevClose)">{{ price(hoverData.high) }}</em></div>
      <div class="tooltip-row"><span>最低</span><em :class="priceClass(hoverData.low, hoverData.prevClose)">{{ price(hoverData.low) }}</em></div>
      <div class="tooltip-row"><span>涨跌幅</span><em :class="changeClass(hoverData.changePct)">{{ signedPct(hoverData.changePct) }}</em></div>
      <div class="tooltip-row"><span>涨跌额</span><em :class="changeClass(hoverData.changeValue)">{{ signedPrice(hoverData.changeValue) }}</em></div>
      <div class="tooltip-row"><span>成交量</span><strong>{{ volume(hoverData.volume) }}</strong></div>
      <div class="tooltip-row"><span>成交额</span><strong>{{ amount(hoverData.turnover) }}</strong></div>
      <div class="tooltip-row"><span>振幅</span><strong>{{ pct(hoverData.amplitude) }}</strong></div>
      <div class="tooltip-row"><span>换手率</span><strong>{{ pct(hoverData.turnoverRate) }}</strong></div>
    </div>
  </div>
</template>

<script setup>
import {
  ActionType,
  CandleTooltipRectPosition,
  CandleType,
  dispose,
  init,
  LineType,
  PolygonType,
  TooltipShowRule,
  TooltipShowType
} from "klinecharts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  bars: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: "daily"
  }
});
const emit = defineEmits(["requestMoreHistory"]);

const chartEl = ref(null);
const hoverData = ref(null);
const tooltipPosition = ref({ left: 16, top: 16 });
let chart = null;
let resizeObserver = null;
let chartData = [];
let askedMoreHistory = false;

const maColors = ["#9ca3af", "#f59e0b", "#ff00ff", "#067a38", "#1683e8"];

const tooltipStyle = computed(() => ({
  left: `${tooltipPosition.value.left}px`,
  top: `${tooltipPosition.value.top}px`
}));

function initChart() {
  if (!chartEl.value) return;
  if (chart) {
    cleanupChartBindings();
    dispose(chart);
    chart = null;
  }
  chart = init(chartEl.value);
  if (!chart) return;
  chart.setOffsetRightDistance(0);
  chart.setMaxOffsetRightDistance(0);
  chart.setRightMinVisibleBarCount(1);
  chart.setCustomApi({
    formatBigNumber: formatBigNumberCN
  });
  chart.setStyles({
    grid: {
      show: true,
      horizontal: { show: true, color: "#e5e7eb", size: 1, style: LineType.Solid, dashedValue: [] },
      vertical: { show: true, color: "#edf0f3", size: 1, style: LineType.Solid, dashedValue: [] }
    },
    candle: {
      type: CandleType.CandleUpStroke,
      bar: {
        upColor: "#ffffff",
        downColor: "#008000",
        noChangeColor: "#ffffff",
        upBorderColor: "#ff1f1f",
        downBorderColor: "#008000",
        noChangeBorderColor: "#666666",
        upWickColor: "#ff1f1f",
        downWickColor: "#008000",
        noChangeWickColor: "#666666"
      },
      priceMark: {
        high: { show: true, color: "#111827" },
        low: { show: true, color: "#111827" },
        last: { show: true, line: { show: false }, text: { show: true } }
      },
      tooltip: {
        showRule: TooltipShowRule.FollowCross,
        showType: TooltipShowType.Rect,
        custom: tooltipLegend,
        rect: {
          position: CandleTooltipRectPosition.Fixed,
          offsetLeft: 8,
          offsetTop: 8,
          offsetRight: 8,
          offsetBottom: 8,
          paddingLeft: 0,
          paddingTop: 0,
          paddingRight: 0,
          paddingBottom: 0,
          color: "transparent",
          borderColor: "transparent",
          borderSize: 0,
          borderRadius: 0
        },
        text: { color: "transparent", size: 1, family: "Arial", weight: "normal" }
      }
    },
    indicator: {
      ohlc: { upColor: "#ff1f1f", downColor: "#008000", noChangeColor: "#333333" },
      bars: [
        {
          style: PolygonType.Fill,
          borderStyle: LineType.Solid,
          borderSize: 1,
          borderDashedValue: [],
          upColor: "#ff1f1f",
          downColor: "#008000",
          noChangeColor: "#666666"
        }
      ],
      lines: maColors.map((color) => ({
        show: true,
        color,
        size: 1.5,
        style: LineType.Solid,
        dashedValue: [],
        smooth: true
      })),
      tooltip: {
        showRule: TooltipShowRule.Always,
        showType: TooltipShowType.Standard,
        showName: true,
        showParams: true,
        defaultValue: "--",
        text: { color: "#333333", size: 12, family: "Arial", weight: "normal", marginLeft: 6, marginTop: 4, marginRight: 6, marginBottom: 4 },
        icons: []
      }
    },
    xAxis: {
      axisLine: { show: true, color: "#9ca3af", size: 1 },
      tickText: { color: "#111827", size: 12 }
    },
    yAxis: {
      axisLine: { show: true, color: "#9ca3af", size: 1 },
      tickText: { color: "#111827", size: 12 }
    },
    crosshair: {
      show: true,
      horizontal: {
        show: true,
        line: { show: false, color: "transparent", size: 0, style: LineType.Solid, dashedValue: [] },
        text: { show: false }
      },
      vertical: {
        show: true,
        line: { show: false, color: "transparent", size: 0, style: LineType.Solid, dashedValue: [] },
        text: { show: false }
      }
    },
    separator: { color: "#a3a3a3", size: 1, fill: true, activeBackgroundColor: "#e5e7eb" }
  });
  chart.createIndicator({ name: "MA", calcParams: props.mode === "daily" ? [5, 10, 20, 30, 60] : [5, 10, 20] }, true, { id: "candle_pane" });
  chart.createIndicator({ name: "VOL", calcParams: [5, 10] }, false, { id: "volume_pane", height: 150, minHeight: 110 });
  chart.subscribeAction(ActionType.OnVisibleRangeChange, handleVisibleRangeChange);
  chartEl.value.addEventListener("mousemove", handleChartMouseMove);
  chartEl.value.addEventListener("mouseleave", clearHoverData);
  resizeObserver = new ResizeObserver(() => {
    if (chart) chart.resize();
  });
  resizeObserver.observe(chartEl.value);
  if (props.bars.length) {
    updateData();
  }
}

function updateData() {
  if (!chart) return;
  const previousData = chartData;
  const previousRange = chart.getVisibleRange();
  const previousLast = previousData.at(-1)?.timestamp;
  const previousFirst = previousData[0]?.timestamp;
  if (!props.bars.length) {
    chart.clearData();
    chartData = [];
    hoverData.value = null;
    return;
  }
  chartData = props.bars.map((bar, index, list) => {
    const open = Number(bar.open_price) || 0;
    const high = Number(bar.high_price) || 0;
    const low = Number(bar.low_price) || 0;
    const close = Number(bar.close_price) || 0;
    const prevClose = index > 0 ? Number(list[index - 1].close_price) || close : close;
    const changeValue = close - prevClose;
    const rawVolume = Number(bar.volume) || 0;
    const volumeHands = rawVolume / 100;
    return {
      timestamp: toTimestamp(bar.trade_date),
      dateText: bar.trade_date,
      open,
      high,
      low,
      close,
      prevClose,
      changeValue,
      changePct: prevClose ? (changeValue / prevClose) * 100 : 0,
      amplitude: prevClose ? ((high - low) / prevClose) * 100 : 0,
      turnoverRate: Number(bar.turnover_rate) || 0,
      rawVolume,
      volume: volumeHands,
      turnover: Number(bar.amount || 0)
    };
  });
  chart.applyNewData(chartData);
  const isPrependingHistory =
    previousData.length > 0 &&
    chartData.length > previousData.length &&
    previousLast === chartData.at(-1)?.timestamp &&
    previousFirst !== chartData[0]?.timestamp;
  nextTick(() => {
    if (!chart) return;
    chart.resize();
    chart.setOffsetRightDistance(0);
    chart.setMaxOffsetRightDistance(0);
    if (isPrependingHistory) {
      const added = chartData.length - previousData.length;
      chart.scrollToDataIndex(Math.max(0, Math.round(previousRange.from) + added), 0);
    } else {
      chart.scrollToRealTime(0);
    }
    askedMoreHistory = false;
  });
}

function handleVisibleRangeChange(range) {
  if (props.mode !== "daily" || askedMoreHistory || !range || !chartData.length) return;
  if (Number(range.realFrom ?? range.from) <= 8) {
    askedMoreHistory = true;
    emit("requestMoreHistory");
  }
}

function handleChartMouseMove(event) {
  if (!chart || !chartEl.value || !chartData.length) {
    hoverData.value = null;
    return;
  }

  const rect = chartEl.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  if (x < 0 || y < 0 || x > rect.width || y > rect.height) {
    hoverData.value = null;
    return;
  }

  const point = chart.convertFromPixel([{ x, y }], { paneId: "candle_pane" })?.[0];
  const dataIndex = Math.round(Number(point?.dataIndex ?? -1));
  const item = chartData[dataIndex];
  if (!item) {
    hoverData.value = null;
    return;
  }

  tooltipPosition.value = {
    left: x < 230 ? Math.max(14, rect.width - 208) : 14,
    top: 18
  };
  hoverData.value = item;
}

function clearHoverData() {
  hoverData.value = null;
}

function tooltipLegend({ current }) {
  return [
    { title: "时间", value: current.dateText || "" },
    { title: "开", value: price(current.open) },
    { title: "高", value: price(current.high) },
    { title: "低", value: price(current.low) },
    { title: "收", value: price(current.close) }
  ];
}

function toTimestamp(value) {
  const text = String(value || "");
  const normalized = text.includes(" ") ? text.replace(" ", "T") : `${text}T00:00:00`;
  const timestamp = new Date(normalized).getTime();
  return Number.isFinite(timestamp) ? timestamp : Date.now();
}

function price(value) {
  return Number(value || 0).toFixed(2);
}

function signedPrice(value) {
  const number = Number(value || 0);
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}`;
}

function pct(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function signedPct(value) {
  const number = Number(value || 0);
  return `${number > 0 ? "+" : ""}${number.toFixed(2)}%`;
}

function volume(value) {
  const number = Number(value || 0);
  if (number >= 100000000) return `${(number / 100000000).toFixed(2)}亿`;
  return `${(number / 10000).toFixed(2)}万`;
}

function amount(value) {
  const number = Number(value || 0);
  if (number >= 100000000) return `${(number / 100000000).toFixed(2)}亿`;
  if (number >= 10000) return `${(number / 10000).toFixed(2)}万`;
  return number.toFixed(2);
}

function formatBigNumberCN(value) {
  const number = Number(value || 0);
  const sign = number < 0 ? "-" : "";
  const abs = Math.abs(number);
  if (abs >= 100000000) return `${sign}${(abs / 100000000).toFixed(2)}亿`;
  if (abs >= 10000) return `${sign}${(abs / 10000).toFixed(2)}万`;
  return `${sign}${abs.toFixed(2)}`;
}

function changeClass(value) {
  const number = Number(value || 0);
  if (number > 0) return "is-up";
  if (number < 0) return "is-down";
  return "";
}

function priceClass(value, prevClose) {
  return changeClass(Number(value || 0) - Number(prevClose || 0));
}

onMounted(initChart);
watch(() => props.bars, updateData, { deep: true });
watch(() => props.mode, async () => {
  hoverData.value = null;
  await nextTick();
  initChart();
});

onBeforeUnmount(() => {
  cleanupChartBindings();
  if (chart) {
    dispose(chart);
  }
});

function cleanupChartBindings() {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (chartEl.value) {
    chartEl.value.removeEventListener("mousemove", handleChartMouseMove);
    chartEl.value.removeEventListener("mouseleave", clearHoverData);
  }
  if (chart) {
    chart.unsubscribeAction(ActionType.OnVisibleRangeChange, handleVisibleRangeChange);
  }
}
</script>

<style scoped>
.chart-shell {
  position: relative;
}

.chart {
  width: 100%;
  height: min(62vh, 620px);
  min-height: 480px;
  border: 1px solid #9ca3af;
  border-radius: 2px;
  overflow: hidden;
  background: #ffffff;
}

.trade-tooltip {
  position: absolute;
  z-index: 5;
  width: 190px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid #bdbdbd;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.16);
  pointer-events: none;
  font-size: 14px;
  color: #333333;
}

.tooltip-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  align-items: baseline;
  min-height: 25px;
  line-height: 25px;
}

.tooltip-row span {
  color: #333333;
  font-weight: 600;
}

.tooltip-row strong,
.tooltip-row em {
  font-style: normal;
  text-align: right;
  font-weight: 700;
  color: #333333;
}

.tooltip-row .is-up {
  color: #ff0000;
}

.tooltip-row .is-down {
  color: #008000;
}

@media (max-width: 980px) {
  .chart {
    height: 520px;
    min-height: 520px;
  }
}
</style>
