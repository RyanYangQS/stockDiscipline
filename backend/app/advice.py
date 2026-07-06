from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


def money(value: float) -> str:
    if value >= 100:
        return f"{value:.1f}元"
    return f"{value:.2f}元"


def pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f}%"


def round_price(value: float) -> float:
    if value >= 50:
        return round(value * 2) / 2
    if value >= 20:
        return round(value * 10) / 10
    return round(value, 2)


def lot(quantity: int, ratio: float, min_lot: int = 100) -> int:
    raw = int(quantity * ratio)
    if raw < min_lot:
        return min_lot if quantity >= min_lot else quantity
    return max(min_lot, raw // min_lot * min_lot)


@dataclass
class Context:
    latest_news: dict[str, Any] | None
    latest_volume: dict[str, Any] | None


def infer_scenario(category: str, pnl_ratio: float, ctx: Context) -> str:
    news = ctx.latest_news or {}
    volume = ctx.latest_volume or {}
    news_scenario = news.get("scenario") or ""
    sentiment = news.get("sentiment") or ""
    volume_state = volume.get("volume_state") or ""
    sell_risk = int(volume.get("sell_risk_score") or 50)
    volume_ratio = float(volume.get("volume_ratio") or 1)

    if "监管" in sentiment or "重大利空" in sentiment or "高风险" in category:
        return "高风险退出"
    if "出货" in news_scenario or sell_risk >= 75 or ("放量滞涨" in volume_state and volume_ratio >= 1.8):
        return "主力出货风险"
    if "恐慌" in news_scenario or ("重大利空" in sentiment and volume_ratio >= 1.8):
        return "恐慌性下跌观察"
    if "洗盘" in news_scenario or ("缩量抗跌" in volume_state and "核心" in category):
        return "主力洗盘观察"
    if "利好兑现" in sentiment or "舆情过热" in sentiment:
        return "利好兑现风险"
    if pnl_ratio <= -0.15:
        return "深度浮亏纪律处理"
    if "弱势" in category:
        return "弱势跟风退出"
    return "正常持仓观察"


def build_advice(position: dict[str, Any], ctx: Context | None = None) -> dict[str, Any]:
    ctx = ctx or Context(None, None)
    quantity = int(position["quantity"])
    cost = float(position["cost_price"])
    current = float(position["current_price"])
    category = position.get("category") or "观察仓"
    pnl_ratio = (current - cost) / cost if cost else 0
    scenario = infer_scenario(category, pnl_ratio, ctx)

    sell_risk = int((ctx.latest_volume or {}).get("sell_risk_score") or 50)
    discipline_passed = 1
    risk_level = "中"

    if "弱势" in category:
        trim_1 = round_price(min(cost * 0.9, current * 1.065))
        trim_2 = round_price(min(cost * 0.95, current * 1.145))
        q1 = lot(quantity, 0.5)
        stop = round_price(current * 0.96)
        trim_trigger = f"{money(trim_1)}减{q1}股；{money(trim_2)}清仓剩余{quantity - q1}股"
        stop_trigger = f"有效跌破{money(stop)}直接全部止损"
        add_reference = "全程禁止加仓，无参考价"
        action = "弱势票优先退出：反弹分批减仓，跌破止损清仓，不做摊薄"
        discipline_passed = 0
        risk_level = "高"
    elif "高风险" in category or scenario == "高风险退出":
        stop = round_price(current * 0.98)
        trim_trigger = f"反弹至{money(round_price(current * 1.03))}优先减半；若消息风险未解除，择机清仓"
        stop_trigger = f"有效跌破{money(stop)}全部退出"
        add_reference = "监管/业绩/退市等硬风险未解除前禁止加仓"
        action = "高风险票不做等待，优先降低暴露"
        discipline_passed = 0
        risk_level = "高"
    elif sell_risk >= 70 or "出货" in scenario or "兑现" in scenario:
        q1 = lot(quantity, 0.5)
        trim_trigger = f"{money(round_price(current * 1.04))}减{q1}股；{money(round_price(current * 1.08))}再减{quantity - q1}股"
        stop_trigger = f"有效跌破{money(round_price(current * 0.96))}至少减仓{q1}股"
        add_reference = "出现主力出货/利好兑现风险，禁止加仓"
        action = "风险优先：反弹减仓，若继续放量滞涨则退出"
        discipline_passed = 0
        risk_level = "高"
    elif "核心" in category:
        q1 = lot(quantity, 0.25)
        q2 = lot(quantity, 0.25)
        rebound_1 = round_price(min(cost * 0.95, current * 1.10))
        rebound_2 = round_price(min(cost * 0.99, current * 1.16))
        stop = round_price(current * 0.955 if pnl_ratio <= -0.12 else current * 0.93)
        hold_qty = max(0, quantity - q1 - q2)
        trim_trigger = f"{money(rebound_1)}减{q1}股；{money(rebound_2)}再减{q2}股，最终保留{hold_qty}股"
        stop_trigger = f"有效跌破{money(stop)}，减仓{lot(quantity, 0.5)}股"
        add_line = round_price(current * 1.025)
        buy_low = round_price(current * 0.98)
        buy_high = round_price(current)
        add_qty = lot(quantity, 0.2)
        add_reference = f"当前禁止加仓；放量企稳站稳{money(add_line)}后，可在{money(buy_low)}-{money(buy_high)}区间小仓位补{add_qty}股做T"
        action = "核心仓先守纪律：反弹降成本，未放量企稳前不补仓"
        risk_level = "中高" if pnl_ratio <= -0.12 else "中"
    else:
        q1 = lot(quantity, 0.33)
        trim_trigger = f"{money(round_price(current * 1.06))}减{q1}股；{money(round_price(current * 1.12))}再评估是否保留底仓"
        stop_trigger = f"有效跌破{money(round_price(current * 0.95))}，减仓{lot(quantity, 0.5)}股"
        add_reference = f"仅在缩量抗跌后重新放量站稳{money(round_price(current * 1.03))}才允许小仓位试错"
        action = "观察仓不主动扩大，等量能确认后再处理"

    if pnl_ratio <= -0.15 and "弱势" not in category:
        action = "浮亏较深，禁止扩大仓位；优先等反弹减仓或按止损执行"
        risk_level = "高" if risk_level == "中高" else risk_level

    reason_parts = [
        f"当前盈亏{pct(pnl_ratio)}",
        f"标的分类为{category}",
        f"情景判断为{scenario}",
    ]
    if ctx.latest_news:
        reason_parts.append(f"消息面：{ctx.latest_news.get('sentiment', '中性')}")
    if ctx.latest_volume:
        reason_parts.append(
            f"量能：{ctx.latest_volume.get('volume_state', '未录入')}，卖出风险{sell_risk}分"
        )

    return {
        "position_id": position["id"],
        "advice_date": date.today().isoformat(),
        "pnl_ratio": pnl_ratio,
        "pnl_ratio_text": pct(pnl_ratio),
        "risk_level": risk_level,
        "scenario": scenario,
        "trim_trigger": trim_trigger,
        "stop_trigger": stop_trigger,
        "add_reference": add_reference,
        "action_advice": action,
        "reason": "；".join(reason_parts),
        "discipline_passed": discipline_passed,
    }

