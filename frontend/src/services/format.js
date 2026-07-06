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

export function riskClass(risk) {
  if (risk === "高") return "danger";
  if (risk === "中高") return "warn";
  return "ok";
}

