export function money(value) {
  return Number(value || 0).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

export function pct(value) {
  const n = Number(value || 0) * 100;
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export function today() {
  return new Date().toISOString().slice(0, 10);
}

// Map Chinese risk levels to CSS class names
// 高=red, 中高=yellow, 中=gray, 低=green
export function riskClass(risk) {
  if (risk === "高") return "is-high";
  if (risk === "中高") return "is-medium-high";
  if (risk === "中") return "is-medium";
  if (risk === "低") return "is-low";
  return "is-medium"; // default
}

