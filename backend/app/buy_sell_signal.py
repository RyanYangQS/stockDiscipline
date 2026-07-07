"""买入卖出信号模型 - 综合量能、市场情绪、风险、AI分析"""
from __future__ import annotations

from datetime import date
from typing import Any


def calculate_buy_sell_signals(
    volume_metrics: dict[str, Any],
    price_metrics: dict[str, Any],
    ma_metrics: dict[str, Any],
    position_metrics: dict[str, Any],
    patterns: dict[str, Any],
    risk_level: str,
    action_suggestion: str,
) -> dict[str, Any]:
    """
    综合评分模型 - 计算买入/卖出信号强度
    
    Args:
        volume_metrics: 量能指标（量比、换手率、成交额等）
        price_metrics: 价格指标（涨跌幅、波动率等）
        ma_metrics: 均线指标（均线趋势、均线距离等）
        position_metrics: 位置指标（距高点、距低点等）
        patterns: 形态识别（量价形态、K线形态等）
        risk_level: 风险等级（高、中高、中、低）
        action_suggestion: AI操作建议（买入、卖出、持有等）
    
    Returns:
        dict: {
            "signal_type": "buy" | "sell" | "hold",
            "signal_strength": 0-100,
            "confidence": 0-100,
            "reasons": ["理由1", "理由2"],
            "risk_warnings": ["风险提示1"],
        }
    """
    
    # 初始化评分
    buy_score = 0
    sell_score = 0
    reasons = []
    warnings = []
    
    # 1. 量能评分（权重30%）
    volume_ratio = volume_metrics.get("volume_ratio_5", 1.0)
    turnover_rate = volume_metrics.get("last_turnover_rate", 0)
    
    # 放量上涨 - 强买入信号
    if volume_ratio > 2.0 and price_metrics.get("change_pct", 0) > 2:
        buy_score += 30
        reasons.append("放量上涨（量比>2,涨幅>2%）")
    elif volume_ratio > 1.5 and price_metrics.get("change_pct", 0) > 1:
        buy_score += 20
        reasons.append("温和放量上涨")
    
    # 缩量下跌 - 可能买入机会
    if volume_ratio < 0.7 and price_metrics.get("change_pct", 0) < -2:
        buy_score += 15
        reasons.append("缩量下跌，可能触底")
    
    # 极端放量 - 风险提示
    if volume_ratio > 3.0:
        warnings.append("极端放量，需警惕资金撤离")
        sell_score += 10
    
    # 2. 均线评分（权重25%）
    ma_trend = ma_metrics.get("ma_trend", "")
    
    if ma_trend == "多头排列":
        buy_score += 25
        reasons.append("均线多头排列")
    elif ma_trend == "空头排列":
        sell_score += 25
        reasons.append("均线空头排列")
    
    # 距离20日均线
    distance_from_ma20 = position_metrics.get("distance_from_high", 0)
    if distance_from_ma20 > 5:  # 距高点近
        sell_score += 15
        warnings.append("距离20日高点较近，回调风险")
    elif distance_from_ma20 < -10:  # 距高点远
        buy_score += 10
        reasons.append("距离高点较远，有反弹空间")
    
    # 3. 形态评分（权重20%）
    volume_patterns = patterns.get("volume_price_patterns", [])
    kline_patterns = patterns.get("kline_patterns", [])
    
    # 买入形态
    buy_patterns = ["放量突破", "底部放量", "金针探底", "阳包阴", "红三兵"]
    for pattern in volume_patterns + kline_patterns:
        if pattern in buy_patterns:
            buy_score += 20
            reasons.append(f"识别到买入形态：{pattern}")
    
    # 卖出形态
    sell_patterns = ["缩量阴跌", "顶部放量", "高位滞涨", "阴包阳", "三只乌鸦"]
    for pattern in volume_patterns + kline_patterns:
        if pattern in sell_patterns:
            sell_score += 20
            reasons.append(f"识别到卖出形态：{pattern}")
    
    # 4. 风险评分（权重15%）
    risk_map = {"高": 15, "中高": 10, "中": 5, "低": 0}
    sell_score += risk_map.get(risk_level, 0)
    
    if risk_level in ["高", "中高"]:
        warnings.append(f"风险等级{risk_level}，建议谨慎")
    
    # 5. AI建议评分（权重10%）
    if "买入" in action_suggestion or "加仓" in action_suggestion:
        buy_score += 10
        reasons.append("AI建议买入")
    elif "卖出" in action_suggestion or "减仓" in action_suggestion:
        sell_score += 10
        reasons.append("AI建议卖出")
    
    # 计算最终信号
    total_score = buy_score + sell_score
    if total_score == 0:
        signal_type = "hold"
        signal_strength = 0
        confidence = 50
        reasons.append("无明显信号，建议持有观望")
    elif buy_score > sell_score and buy_score >= 40:
        signal_type = "buy"
        signal_strength = min(100, buy_score)
        confidence = min(100, int((buy_score - sell_score) / buy_score * 100))
    elif sell_score > buy_score and sell_score >= 40:
        signal_type = "sell"
        signal_strength = min(100, sell_score)
        confidence = min(100, int((sell_score - buy_score) / sell_score * 100))
    else:
        signal_type = "hold"
        signal_strength = max(buy_score, sell_score)
        confidence = 50
        reasons.append("信号不明确，建议观望")
    
    return {
        "signal_type": signal_type,
        "signal_strength": signal_strength,
        "confidence": confidence,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "reasons": reasons,
        "risk_warnings": warnings,
        "trade_date": date.today().strftime("%Y-%m-%d"),
    }