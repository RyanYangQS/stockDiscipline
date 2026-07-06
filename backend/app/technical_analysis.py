"""Technical analysis for stock K-line and volume data."""
from __future__ import annotations

from typing import Any


def calculate_volume_metrics(bars: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate volume-related technical metrics from K-line bars."""
    if len(bars) < 5:
        return {"error": "数据不足，需要至少5根K线"}

    volumes = [float(bar.get("volume", 0)) for bar in bars]
    closes = [float(bar.get("close_price", 0)) for bar in bars]
    highs = [float(bar.get("high_price", 0)) for bar in bars]
    lows = [float(bar.get("low_price", 0)) for bar in bars]
    opens = [float(bar.get("open_price", 0)) for bar in bars]
    turnover_rates = [float(bar.get("turnover_rate", 0)) for bar in bars]
    amounts = [float(bar.get("amount", 0)) for bar in bars]

    # Last bar metrics
    last_bar = bars[-1]
    prev_bar = bars[-2] if len(bars) >= 2 else bars[-1]

    last_volume = volumes[-1]
    last_close = closes[-1]
    last_open = opens[-1]
    last_high = highs[-1]
    last_low = lows[-1]
    last_amount = amounts[-1]
    last_turnover_rate = turnover_rates[-1] if turnover_rates else 0

    prev_close = closes[-2] if len(closes) >= 2 else last_close

    # Volume ratios
    avg_volume_5 = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else last_volume
    avg_volume_10 = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else avg_volume_5
    avg_volume_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else avg_volume_10

    volume_ratio_5 = last_volume / avg_volume_5 if avg_volume_5 else 1
    volume_ratio_10 = last_volume / avg_volume_10 if avg_volume_10 else 1
    volume_ratio_20 = last_volume / avg_volume_20 if avg_volume_20 else 1

    # Price changes
    change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close else 0
    change_5d = ((last_close - closes[-6]) / closes[-6] * 100) if len(closes) >= 6 and closes[-6] else 0
    change_10d = ((last_close - closes[-11]) / closes[-11] * 100) if len(closes) >= 11 and closes[-11] else 0
    change_20d = ((last_close - closes[-21]) / closes[-21] * 100) if len(closes) >= 21 and closes[-21] else 0

    # Amplitude (volatility)
    amplitude = ((last_high - last_low) / prev_close * 100) if prev_close else 0
    avg_amplitude_5 = sum((highs[i] - lows[i]) / closes[i-1] * 100 for i in range(-5, 0) if i > -len(closes) and closes[i-1]) / 5

    # MA (Moving Average)
    ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else last_close
    ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10

    # Price position relative to MA
    price_vs_ma5 = ((last_close - ma5) / ma5 * 100) if ma5 else 0
    price_vs_ma10 = ((last_close - ma10) / ma10 * 100) if ma10 else 0
    price_vs_ma20 = ((last_close - ma20) / ma20 * 100) if ma20 else 0

    # Trend patterns
    consecutive_up = 0
    consecutive_down = 0
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] > closes[i - 1]:
            consecutive_up += 1
        else:
            break
    for i in range(len(closes) - 1, 0, -1):
        if closes[i] < closes[i - 1]:
            consecutive_down += 1
        else:
            break

    # Volume-price relationship patterns
    volume_price_patterns = []

    # 放量上涨 (volume increase with price increase)
    if volume_ratio_5 > 1.5 and change_pct > 2:
        volume_price_patterns.append("放量上涨")
    elif volume_ratio_5 > 1.3 and change_pct > 1:
        volume_price_patterns.append("温和放量上涨")

    # 放量下跌
    if volume_ratio_5 > 1.5 and change_pct < -2:
        volume_price_patterns.append("放量下跌")
    elif volume_ratio_5 > 1.3 and change_pct < -1:
        volume_price_patterns.append("温和放量下跌")

    # 缩量上涨
    if volume_ratio_5 < 0.7 and change_pct > 1:
        volume_price_patterns.append("缩量上涨")

    # 缩量下跌
    if volume_ratio_5 < 0.7 and change_pct < -1:
        volume_price_patterns.append("缩量下跌")

    # 放量滞涨
    if volume_ratio_5 > 2 and abs(change_pct) < 1:
        volume_price_patterns.append("放量滞涨")

    # 高换手率
    if last_turnover_rate > 10:
        volume_price_patterns.append(f"超高换手率({last_turnover_rate:.2f}%)")
    elif last_turnover_rate > 5:
        volume_price_patterns.append(f"高换手率({last_turnover_rate:.2f}%)")

    # K-line patterns
    kline_patterns = []

    # 长上影线
    upper_shadow = last_high - max(last_open, last_close)
    body = abs(last_close - last_open)
    if upper_shadow > body * 2 and body > 0:
        kline_patterns.append("长上影线(抛压明显)")

    # 长下影线
    lower_shadow = min(last_open, last_close) - last_low
    if lower_shadow > body * 2 and body > 0:
        kline_patterns.append("长下影线(支撑明显)")

    # 跳空
    if last_open > prev_bar.get("high_price", last_open):
        kline_patterns.append("向上跳空")
    elif last_open < prev_bar.get("low_price", last_open):
        kline_patterns.append("向下跳空")

    # 大阳线/大阴线
    if change_pct > 5 and last_close > last_open:
        kline_patterns.append("大阳线")
    elif change_pct < -5 and last_close < last_open:
        kline_patterns.append("大阴线")

    # Recent high/low
    recent_20_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
    recent_20_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
    distance_from_high = ((last_close - recent_20_high) / recent_20_high * 100) if recent_20_high else 0
    distance_from_low = ((last_close - recent_20_low) / recent_20_low * 100) if recent_20_low else 0

    # Trend strength
    ma_trend = ""
    if ma5 > ma10 > ma20:
        ma_trend = "多头排列"
    elif ma5 < ma10 < ma20:
        ma_trend = "空头排列"
    elif ma5 > ma10 and ma10 < ma20:
        ma_trend = "均线纠缠(趋势不明)"
    else:
        ma_trend = "均线震荡"

    return {
        "volume_metrics": {
            "last_volume": last_volume,
            "avg_volume_5": round(avg_volume_5, 2),
            "avg_volume_10": round(avg_volume_10, 2),
            "avg_volume_20": round(avg_volume_20, 2),
            "volume_ratio_5": round(volume_ratio_5, 2),
            "volume_ratio_10": round(volume_ratio_10, 2),
            "volume_ratio_20": round(volume_ratio_20, 2),
            "last_amount": last_amount,
            "last_turnover_rate": round(last_turnover_rate, 2),
        },
        "price_metrics": {
            "last_close": round(last_close, 2),
            "last_open": round(last_open, 2),
            "last_high": round(last_high, 2),
            "last_low": round(last_low, 2),
            "prev_close": round(prev_close, 2),
            "change_pct": round(change_pct, 2),
            "change_5d": round(change_5d, 2),
            "change_10d": round(change_10d, 2),
            "change_20d": round(change_20d, 2),
            "amplitude": round(amplitude, 2),
            "avg_amplitude_5": round(avg_amplitude_5, 2),
        },
        "ma_metrics": {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "price_vs_ma5": round(price_vs_ma5, 2),
            "price_vs_ma10": round(price_vs_ma10, 2),
            "price_vs_ma20": round(price_vs_ma20, 2),
            "ma_trend": ma_trend,
        },
        "patterns": {
            "volume_price_patterns": volume_price_patterns,
            "kline_patterns": kline_patterns,
            "consecutive_up": consecutive_up,
            "consecutive_down": consecutive_down,
        },
        "position_metrics": {
            "recent_20_high": round(recent_20_high, 2),
            "recent_20_low": round(recent_20_low, 2),
            "distance_from_high": round(distance_from_high, 2),
            "distance_from_low": round(distance_from_low, 2),
        },
        "trade_date": last_bar.get("trade_date", ""),
        "bars_count": len(bars),
    }


def analyze_volume_signals(metrics: dict[str, Any]) -> dict[str, Any]:
    """Analyze volume signals for trading recommendations."""
    signals = []
    risk_signals = []
    opportunity_signals = []

    volume_metrics = metrics.get("volume_metrics", {})
    price_metrics = metrics.get("price_metrics", {})
    ma_metrics = metrics.get("ma_metrics", {})
    patterns = metrics.get("patterns", {})

    volume_ratio = volume_metrics.get("volume_ratio_5", 1)
    turnover_rate = volume_metrics.get("last_turnover_rate", 0)
    change_pct = price_metrics.get("change_pct", 0)
    ma_trend = ma_metrics.get("ma_trend", "")
    price_vs_ma5 = ma_metrics.get("price_vs_ma5", 0)

    # Risk signals
    if "放量滞涨" in patterns.get("volume_price_patterns", []):
        risk_signals.append({
            "type": "放量滞涨",
            "severity": "高",
            "description": "成交量显著放大但股价涨幅有限，可能为主力出货信号",
        })

    if turnover_rate > 10:
        risk_signals.append({
            "type": "超高换手率",
            "severity": "高",
            "description": f"换手率{turnover_rate:.2f}%超过10%，筹码剧烈交换，需警惕主力出货或对倒",
        })

    if "放量下跌" in patterns.get("volume_price_patterns", []):
        risk_signals.append({
            "type": "放量下跌",
            "severity": "中高",
            "description": "成交量放大伴随下跌，抛压明显，短期可能继续调整",
        })

    if price_vs_ma5 < -5 and ma_trend == "空头排列":
        risk_signals.append({
            "type": "跌破均线支撑",
            "severity": "中",
            "description": f"股价低于MA5{abs(price_vs_ma5):.2f}%，均线空头排列，趋势偏弱",
        })

    if patterns.get("consecutive_down", 0) >= 4:
        risk_signals.append({
            "type": "连续下跌",
            "severity": "中",
            "description": f"连续{patterns['consecutive_down']}日下跌，技术形态偏弱",
        })

    # Opportunity signals
    if "缩量下跌" in patterns.get("volume_price_patterns", []):
        opportunity_signals.append({
            "type": "缩量下跌",
            "severity": "低",
            "description": "下跌过程中成交量萎缩，可能接近调整尾声，关注企稳信号",
        })

    if "温和放量上涨" in patterns.get("volume_price_patterns", []):
        opportunity_signals.append({
            "type": "温和放量上涨",
            "severity": "中",
            "description": "量价配合健康，上涨趋势有望延续",
        })

    if ma_trend == "多头排列" and price_vs_ma5 > 0:
        opportunity_signals.append({
            "type": "均线多头排列",
            "severity": "中",
            "description": "MA5>MA10>MA20且股价在MA5上方，趋势向好",
        })

    if patterns.get("consecutive_up", 0) >= 3 and volume_ratio > 1:
        opportunity_signals.append({
            "type": "连续放量上涨",
            "severity": "中",
            "description": f"连续{patterns['consecutive_up']}日放量上涨，上涨动能较强",
        })

    if "长下影线" in patterns.get("kline_patterns", []):
        opportunity_signals.append({
            "type": "长下影线支撑",
            "severity": "低",
            "description": "长下影线显示下方支撑较强，关注支撑位有效性",
        })

    # Overall assessment
    risk_level = "低"
    if len(risk_signals) >= 2:
        risk_level = "高"
    elif len(risk_signals) == 1:
        severity = risk_signals[0].get("severity", "低")
        if severity in ["高", "中高"]:
            risk_level = "中高"
        else:
            risk_level = "中"

    action_suggestion = "观望"
    if risk_level in ["高", "中高"]:
        action_suggestion = "考虑减仓或止损观望"
    elif len(opportunity_signals) >= 2 and ma_trend == "多头排列":
        action_suggestion = "可保持仓位，关注后续量能变化"
    elif ma_trend == "空头排列" and change_pct > 0:
        action_suggestion = "反弹观望，不急于加仓"
    elif "缩量下跌" in patterns.get("volume_price_patterns", []):
        action_suggestion = "等待企稳信号后再考虑介入"

    return {
        "signals": signals,
        "risk_signals": risk_signals,
        "opportunity_signals": opportunity_signals,
        "risk_level": risk_level,
        "action_suggestion": action_suggestion,
        "summary": {
            "volume_ratio_status": "放量" if volume_ratio > 1.3 else ("缩量" if volume_ratio < 0.7 else "正常"),
            "turnover_status": "高换手" if turnover_rate > 5 else ("超高换手" if turnover_rate > 10 else "正常换手"),
            "trend_status": ma_trend,
            "price_position": "强势" if price_vs_ma5 > 3 else ("弱势" if price_vs_ma5 < -3 else "震荡"),
        },
    }