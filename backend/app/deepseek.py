from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .db import load_llm_config


Transport = Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]]


@dataclass
class DeepSeekResult:
    provider: str
    model: str
    status: str
    content: str
    raw_response: str


def default_transport(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def build_volume_analysis_prompt(stock_name: str, metrics: dict[str, Any], analysis: dict[str, Any], bars: list[dict[str, Any]], quote: dict[str, Any] | None = None) -> str:
    """Build prompt for stock-specific volume analysis."""
    recent_bars_summary = []
    for bar in bars[-10:]:
        recent_bars_summary.append({
            "date": bar.get("trade_date", ""),
            "close": bar.get("close_price", 0),
            "volume": bar.get("volume", 0),
            "turnover_rate": bar.get("turnover_rate", 0),
        })

    prompt = f"""你是一个严格执行交易纪律的股票量能分析专家。请对 {stock_name} 进行深入的量能分析。

## 基本信息
- 股票名称: {stock_name}
- 分析日期: {metrics.get('trade_date', '')}
- 数据范围: 近{metrics.get('bars_count', 30)}根K线

## 技术指标数据
### 量能指标
- 最新成交量: {metrics['volume_metrics']['last_volume']}
- 5日平均成交量: {metrics['volume_metrics']['avg_volume_5']}
- 10日平均成交量: {metrics['volume_metrics']['avg_volume_10']}
- 20日平均成交量: {metrics['volume_metrics']['avg_volume_20']}
- 量比(5日): {metrics['volume_metrics']['volume_ratio_5']}
- 量比(10日): {metrics['volume_metrics']['volume_ratio_10']}
- 量比(20日): {metrics['volume_metrics']['volume_ratio_20']}
- 换手率: {metrics['volume_metrics']['last_turnover_rate']}%
- 成交额: {metrics['volume_metrics']['last_amount']}

### 价格指标
- 最新收盘价: {metrics['price_metrics']['last_close']}
- 今日涨跌幅: {metrics['price_metrics']['change_pct']}%
- 5日涨跌幅: {metrics['price_metrics']['change_5d']}%
- 10日涨跌幅: {metrics['price_metrics']['change_10d']}%
- 20日涨跌幅: {metrics['price_metrics']['change_20d']}%
- 今日振幅: {metrics['price_metrics']['amplitude']}%

### 均线系统
- MA5: {metrics['ma_metrics']['ma5']}
- MA10: {metrics['ma_metrics']['ma10']}
- MA20: {metrics['ma_metrics']['ma20']}
- 股价与MA5偏离: {metrics['ma_metrics']['price_vs_ma5']}%
- 均线状态: {metrics['ma_metrics']['ma_trend']}

### 识别的形态
- 量价形态: {', '.join(metrics['patterns']['volume_price_patterns']) or '无明显特殊形态'}
- K线形态: {', '.join(metrics['patterns']['kline_patterns']) or '标准K线'}
- 连续上涨天数: {metrics['patterns']['consecutive_up']}
- 连续下跌天数: {metrics['patterns']['consecutive_down']}

### 位置指标
- 近20日最高价: {metrics['position_metrics']['recent_20_high']}
- 近20日最低价: {metrics['position_metrics']['recent_20_low']}
- 距离高点: {metrics['position_metrics']['distance_from_high']}%
- 距离低点: {metrics['position_metrics']['distance_from_low']}%

## Python自动分析结果
### 风险信号
"""
    for signal in analysis.get("risk_signals", []):
        prompt += f"- [{signal['severity']}风险] {signal['type']}: {signal['description']}\n"

    prompt += "\n### 机会信号\n"
    for signal in analysis.get("opportunity_signals", []):
        prompt += f"- [{signal['severity']}机会] {signal['type']}: {signal['description']}\n"

    prompt += f"""
### 总体判断
- 风险等级: {analysis['risk_level']}
- 操作建议: {analysis['action_suggestion']}
- 量能状态: {analysis['summary']['volume_ratio_status']}
- 换手状态: {analysis['summary']['turnover_status']}
- 趋势状态: {analysis['summary']['trend_status']}
- 价格位置: {analysis['summary']['price_position']}

## 近10日K线摘要
```json
{json.dumps(recent_bars_summary, ensure_ascii=False, indent=2)}
```

## 实时行情(如有)
"""
    if quote:
        prompt += f"""
- 当前价: {quote.get('current_price', 'N/A')}
- 今日涨跌: {quote.get('change_pct', 'N/A')}%
"""
    else:
        prompt += "- 无实时行情数据\n"

    prompt += """
## 分析要求
请基于以上数据进行专业分析，输出包含以下部分:

### 1. 量能结构分析
分析成交量变化趋势、量价配合关系、换手率含义

### 2. 价格与均线分析
分析均线支撑/压力情况、价格偏离程度、趋势强弱

### 3. K线形态解读
解读关键K线形态的技术含义、主力行为推测

### 4. 风险与机会评估
综合评估当前持仓风险和潜在机会，给出具体量化指标

### 5. 操作建议
给出明日操作策略，包括:
- 是否适合持有/加仓/减仓
- 关键触发价位(止损、减仓、加仓)
- 需要关注的信号(放量、缩量、突破、跌破)

### 6. 风险提示
列出需要警惕的风险点，不要给出确定性预测或承诺收益

分析风格要求:
- 严格遵守交易纪律原则
- 优先考虑风险控制，其次才是机会把握
- 不做确定性预测，用概率语言描述
- 关注主力行为迹象，但不做过度推断
"""
    return prompt


def build_daily_prompt(context: dict[str, Any]) -> str:
    compact = json.dumps(context, ensure_ascii=False, indent=2)
    return f"""你是一个严格执行交易纪律的个人持仓管理助手。

这是总览页“最新 AI 日报”，只能输出总体持仓纪律建议。不要写个股K线技术分析，不要逐根K线分析，不要长篇解释。

请根据以下数据输出简短、可执行的日报，格式固定：

# 每日持仓纪律建议
## 总体
- 用 1-2 条说明当前组合风险、仓位态度、是否需要降风险。

## 今日动作
- 每只持仓只写一行：股票名：持有/减仓/止损/禁止加仓/观察 + 触发条件。

## 纪律红线
- 写 2-4 条今天必须遵守的交易纪律。

要求：
1. 触发纪律时，卖出/减仓优先于买入理由。
2. 弱势跟风票默认禁止加仓；深度浮亏禁止扩大仓位。
3. 可以提及消息面和量能风险，但不要展开成个股K线量能报告。
4. 不给确定性预测，不承诺收益。

输入数据：
{compact}
"""


def build_market_prompt(context: dict[str, Any]) -> str:
    compact = json.dumps(context, ensure_ascii=False, indent=2)
    return f"""你是一个谨慎的A股消息面与市场热点分析助手。

这是“智能市场分析”页面的报告，只分析消息面、市场热点、政策事件、行业变化及其对当前持仓的影响。不要输出个股K线量能分析，不要写买卖点技术报告，不要逐根K线解释。

请按以下格式输出，内容尽量短而可执行：

# 市场消息面分析
## 今日关键信息
- 归纳 3-5 条市场热点、政策、事件或风险。

## 对持仓的影响
- 每只受影响持仓一行：股票名：利好/利空/中性/待确认 + 影响逻辑 + 今日应对。

## 风险识别
- 明确标注是否存在恐慌性下跌、主力出货、主力洗盘、利好兑现、利空释放等场景；没有证据时写“未确认”。

## 交易纪律建议
- 给出 3-5 条可执行建议，必须包含不追涨、不补弱、止损/减仓触发优先。

输入数据：
{compact}
"""


def build_position_analysis_prompt(position: dict[str, Any], context: dict[str, Any], kline_summary: dict[str, Any] | None = None) -> str:
    """Build prompt for individual position analysis."""
    pnl_ratio = position.get("pnl_ratio", 0)
    pnl_pct = pnl_ratio * 100

    prompt = f"""你是一个严格执行交易纪律的股票持仓分析专家。请对以下持仓生成操作建议。

## 持仓基本信息
- 股票名称: {position['name']}
- 股票代码: {position.get('symbol', 'N/A')}
- 持仓数量: {position['quantity']}股
- 成本价: {position['cost_price']}元
- 当前价: {position['current_price']}元
- 浮亏/浮盈: {pnl_pct:.1f}% ({'亏损' if pnl_ratio < 0 else '盈利'})
- 标的分类: {position.get('category', '观察仓')}
- 行业: {position.get('sector', 'N/A')}
- 备注: {position.get('note', '无')}

## 消息面情况
"""
    if context.get("news"):
        news = context["news"]
        prompt += f"""
- 最近消息: {news.get('title', '无')}
- 消息情绪: {news.get('sentiment', '中性')}
- 消息情景: {news.get('scenario', '无')}
- 重要程度: {news.get('importance', '普通')}
"""
    else:
        prompt += "- 无近期消息记录\n"

    prompt += "\n## 量能情况\n"
    if context.get("volume"):
        vol = context["volume"]
        prompt += f"""
- 量能状态: {vol.get('volume_state', '未录入')}
- 量比: {vol.get('volume_ratio', 1)}
- 换手率: {vol.get('turnover_rate', 0)}%
- 买入评分: {vol.get('buy_watch_score', 50)}分
- 卖出风险: {vol.get('sell_risk_score', 50)}分
- 筹码收集: {vol.get('accumulation_score', 50)}分
"""
    else:
        prompt += "- 无量能快照记录\n"

    prompt += "\n## K线概况\n"
    if kline_summary:
        prompt += f"""
- 近期趋势: 5日涨跌{kline_summary.get('change_5d', 0)*100:.1f}%，20日涨跌{kline_summary.get('change_20d', 0)*100:.1f}%
- 量能对比: 5日/20日均量比{kline_summary.get('volume_ratio_5_20', 1):.2f}
- 近期高点: {kline_summary.get('recent_high', 'N/A')}元
- 近期低点: {kline_summary.get('recent_low', 'N/A')}元
"""
    else:
        prompt += "- 无K线数据\n"

    prompt += """
## 纪律规则(必须严格遵守)
1. 弱势跟风票默认禁止加仓
2. 深度浮亏(-15%以上)禁止扩大仓位
3. 卖出/减仓建议优先于新的买入理由
4. 监管/退市/财务造假等硬风险禁止新开仓
5. 利好兑现+高换手+放量滞涨 → 优先按主力出货风险处理

## 输出要求(JSON格式)
请输出以下字段，每项必须有明确数值或描述:

```json
{
  "scenario": "情景判断(如: 正常持仓观察/主力出货风险/恐慌性下跌观察等)",
  "risk_level": "风险等级(高/中高/中/低)",
  "trim_trigger": "减仓触发价和执行方案(具体价格+股数)",
  "stop_trigger": "止损触发价和执行方案(具体价格+执行方式)",
  "add_reference": "加仓参考(具体条件+价格区间，或'禁止加仓')",
  "action_advice": "操作建议(一句话概括核心操作)",
  "discipline_passed": 1或0(是否通过纪律检查)",
  "reason": "判断依据(简述关键因素)"
}
```

注意:
- 所有价格必须是具体数值，不要用模糊表述
- 触发价要考虑当前价格和成本价的合理偏离
- 严格按纪律规则判断，不做乐观假设
- 禁止预测股价走势，只给出触发条件和应对方案
"""
    return prompt


def call_deepseek_for_position(
    position: dict[str, Any],
    context: dict[str, Any],
    kline_summary: dict[str, Any] | None = None,
    transport: Transport = default_transport,
    timeout: int = 30,
) -> dict[str, Any]:
    """Call DeepSeek for position-specific advice."""
    db_config = load_llm_config()
    key = db_config.get("api_key") if db_config else DEEPSEEK_API_KEY
    selected_model = db_config.get("model") if db_config else DEEPSEEK_MODEL
    selected_base_url = (db_config.get("base_url") if db_config else DEEPSEEK_BASE_URL).rstrip("/") if db_config else DEEPSEEK_BASE_URL.rstrip("/")

    # Calculate pnl_ratio if not provided
    cost = float(position.get("cost_price", 0))
    current = float(position.get("current_price", 0))
    pnl_ratio = position.get("pnl_ratio") or ((current - cost) / cost if cost else 0)

    position_with_pnl = {**position, "pnl_ratio": pnl_ratio}

    if not key:
        # Fallback to local rules
        from .advice import build_advice, Context
        ctx = Context(context.get("news"), context.get("volume"))
        return build_advice(position_with_pnl, ctx)

    prompt = build_position_analysis_prompt(position_with_pnl, context, kline_summary)

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "你是严格的股票持仓纪律分析师，只输出JSON格式建议，不做预测。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    try:
        raw = transport(f"{selected_base_url}/chat/completions", headers, payload, timeout)
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            advice = json.loads(json_match.group())
        else:
            advice = json.loads(content)

        # Ensure all required fields exist
        return {
            "position_id": position["id"],
            "advice_date": date.today().isoformat() if 'date' in dir(date) else "2026-07-06",
            "pnl_ratio": pnl_ratio,
            "pnl_ratio_text": f"{pnl_ratio*100:+.1f}%",
            "risk_level": advice.get("risk_level", "中"),
            "scenario": advice.get("scenario", "正常持仓观察"),
            "trim_trigger": advice.get("trim_trigger", "反弹减仓观察"),
            "stop_trigger": advice.get("stop_trigger", "按纪律止损"),
            "add_reference": advice.get("add_reference", "禁止加仓"),
            "action_advice": advice.get("action_advice", "观察等待"),
            "reason": advice.get("reason", "AI分析建议"),
            "discipline_passed": int(advice.get("discipline_passed", 1)),
            "provider": "deepseek",
            "model": selected_model,
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        # Fallback to local rules on error
        from .advice import build_advice, Context
        ctx = Context(context.get("news"), context.get("volume"))
        local_advice = build_advice(position_with_pnl, ctx)
        local_advice["provider"] = "local_fallback"
        local_advice["error"] = str(exc)
        return local_advice


def call_deepseek_for_volume(
    stock_name: str,
    metrics: dict[str, Any],
    analysis: dict[str, Any],
    bars: list[dict[str, Any]],
    quote: dict[str, Any] | None = None,
    transport: Transport = default_transport,
    timeout: int = 60,
) -> DeepSeekResult:
    """Call DeepSeek for stock-specific volume analysis."""
    db_config = load_llm_config()
    key = db_config.get("api_key") if db_config else DEEPSEEK_API_KEY
    selected_model = db_config.get("model") if db_config else DEEPSEEK_MODEL
    selected_base_url = (db_config.get("base_url") if db_config else DEEPSEEK_BASE_URL).rstrip("/") if db_config else DEEPSEEK_BASE_URL.rstrip("/")

    if not key:
        return DeepSeekResult(
            provider="local",
            model="local-volume-analysis",
            status="missing_api_key",
            content=build_local_volume_report(stock_name, metrics, analysis),
            raw_response="",
        )

    prompt = build_volume_analysis_prompt(stock_name, metrics, analysis, bars, quote)

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "你是专业的股票量能分析师，严格遵守交易纪律，不做确定性预测，优先考虑风险控制。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        raw = transport(f"{selected_base_url}/chat/completions", headers, payload, timeout)
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return DeepSeekResult(
            provider="deepseek",
            model=selected_model,
            status="ok" if content else "empty_response",
            content=content or "DeepSeek 返回为空，请检查模型或接口响应。",
            raw_response=json.dumps(raw, ensure_ascii=False),
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        return DeepSeekResult(
            provider="deepseek",
            model=selected_model,
            status="error",
            content=f"DeepSeek 调用失败：{exc}\n\n以下为本地技术分析：\n\n{build_local_volume_report(stock_name, metrics, analysis)}",
            raw_response=str(exc),
        )


def build_local_volume_report(stock_name: str, metrics: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Build local volume analysis report when API key is not available."""
    lines = [f"# {stock_name} 量能分析报告", ""]
    lines.append("## 技术指标概览")
    lines.append(f"- 最新收盘: {metrics['price_metrics']['last_close']}元")
    lines.append(f"- 今日涨跌: {metrics['price_metrics']['change_pct']}%")
    lines.append(f"- 量比(5日): {metrics['volume_metrics']['volume_ratio_5']}")
    lines.append(f"- 换手率: {metrics['volume_metrics']['last_turnover_rate']}%")
    lines.append(f"- 均线状态: {metrics['ma_metrics']['ma_trend']}")
    lines.append("")

    lines.append("## 量价形态")
    patterns = metrics['patterns']['volume_price_patterns']
    if patterns:
        lines.append(f"- 识别形态: {', '.join(patterns)}")
    else:
        lines.append("- 量价配合正常，无明显特殊形态")
    lines.append("")

    lines.append("## K线形态")
    kline_patterns = metrics['patterns']['kline_patterns']
    if kline_patterns:
        lines.append(f"- K线特征: {', '.join(kline_patterns)}")
    else:
        lines.append("- 标准K线形态")
    lines.append("")

    lines.append("## 风险信号")
    for signal in analysis.get("risk_signals", []):
        lines.append(f"- [{signal['severity']}] {signal['type']}: {signal['description']}")
    if not analysis.get("risk_signals"):
        lines.append("- 未检测到显著风险信号")
    lines.append("")

    lines.append("## 机会信号")
    for signal in analysis.get("opportunity_signals", []):
        lines.append(f"- [{signal['severity']}] {signal['type']}: {signal['description']}")
    if not analysis.get("opportunity_signals"):
        lines.append("- 未检测到明显机会信号")
    lines.append("")

    lines.append("## 总体判断")
    lines.append(f"- 风险等级: {analysis['risk_level']}")
    lines.append(f"- 建议操作: {analysis['action_suggestion']}")
    lines.append("")

    lines.append("## 操作建议")
    lines.append("- 本报告为本地技术分析生成，未配置API Key")
    lines.append("- 建议配置DeepSeek API Key获取更详细的分析")
    lines.append("- 当前建议仅供参考，请结合市场实际情况决策")
    lines.append("")

    lines.append("## 风险提示")
    lines.append("- 技术分析仅供参考，不构成投资建议")
    lines.append("- 股市有风险，投资需谨慎")
    lines.append("- 请结合消息面、基本面综合判断")

    return "\n".join(lines)


def call_deepseek(
    context: dict[str, Any],
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    transport: Transport = default_transport,
    timeout: int = 40,
    report_type: str = "daily",
) -> DeepSeekResult:
    # Try to load active config from database first
    db_config = load_llm_config()
    if db_config and not api_key:
        api_key = db_config.get("api_key") or DEEPSEEK_API_KEY
        model = model or db_config.get("model") or DEEPSEEK_MODEL
        base_url = base_url or db_config.get("base_url") or DEEPSEEK_BASE_URL
    else:
        key = api_key if api_key is not None else DEEPSEEK_API_KEY
        selected_model = model or DEEPSEEK_MODEL
        selected_base_url = (base_url or DEEPSEEK_BASE_URL).rstrip("/")

    key = api_key if api_key is not None else DEEPSEEK_API_KEY
    selected_model = model or DEEPSEEK_MODEL
    selected_base_url = (base_url or DEEPSEEK_BASE_URL).rstrip("/")
    prompt = build_market_prompt(context) if report_type == "market" else build_daily_prompt(context)
    local_builder = build_local_market_report if report_type == "market" else build_local_report

    if not key:
        return DeepSeekResult(
            provider="local",
            model="local-market-summary" if report_type == "market" else "local-discipline-summary",
            status="missing_api_key",
            content=local_builder(context),
            raw_response="",
        )

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "你是谨慎、纪律优先的股票量能分析助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        raw = transport(f"{selected_base_url}/chat/completions", headers, payload, timeout)
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return DeepSeekResult(
            provider="deepseek",
            model=selected_model,
            status="ok" if content else "empty_response",
            content=content or "DeepSeek 返回为空，请检查模型或接口响应。",
            raw_response=json.dumps(raw, ensure_ascii=False),
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        return DeepSeekResult(
            provider="deepseek",
            model=selected_model,
            status="error",
            content=f"DeepSeek 调用失败：{exc}\n\n以下为本地分析：\n\n{local_builder(context)}",
            raw_response=str(exc),
        )


def build_local_report(context: dict[str, Any]) -> str:
    advice = context.get("advice", [])
    news = context.get("news", [])
    volume = context.get("volume", [])
    lines = ["# 每日纪律分析报告", ""]
    lines.append("## 总体判断")
    high_risk = [item for item in advice if item.get("risk_level") == "高"]
    blocked = [item for item in advice if not int(item.get("discipline_passed", 1))]
    lines.append(f"- 当前持仓 {len(advice)} 只，高风险 {len(high_risk)} 只，纪律拦截 {len(blocked)} 只。")
    lines.append(f"- 今日消息 {len(news)} 条，量能快照 {len(volume)} 条。")
    lines.append("- 未配置 DeepSeek API Key，本报告由本地纪律规则生成。")
    lines.append("")
    lines.append("## 持仓动作")
    for item in advice:
        lines.append(
            f"- {item['name']}：{item.get('scenario', '观察')}，{item.get('action_advice', '')}；"
            f"减仓：{item.get('trim_trigger', '')}；止损：{item.get('stop_trigger', '')}。"
        )
    lines.append("")
    lines.append("## 明日盘前检查")
    lines.extend(
        [
            "- 检查是否有监管、业绩、减持、停复牌等硬风险公告。",
            "- 高风险和弱势跟风票不允许补仓。",
            "- 若出现放量滞涨或利好兑现，优先减仓而不是追涨。",
            "- 所有操作必须先写触发价和失败条件。",
        ]
    )
    return "\n".join(lines)


def build_local_market_report(context: dict[str, Any]) -> str:
    news = context.get("news", [])
    positions = context.get("positions", [])
    market = context.get("market", [])
    holding_news = [item for item in news if item.get("name")]
    market_news = [item for item in news if not item.get("name")]
    lines = ["# 市场消息面分析", ""]
    lines.append("## 今日关键信息")
    if market_news:
        for item in market_news[:5]:
            lines.append(f"- {item.get('title', '')}（{item.get('source', '未知来源')}，{item.get('sentiment', '中性')}）")
    else:
        lines.append("- 暂无可靠市场热点抓取结果，先按谨慎观察处理。")
    if market:
        lines.append(f"- 已记录市场快照 {len(market)} 条，可结合指数状态和热点板块复核。")
    lines.append("")
    lines.append("## 对持仓的影响")
    for pos in positions:
        related = [item for item in holding_news if item.get("name") == pos.get("name")]
        if related:
            first = related[0]
            lines.append(f"- {pos.get('name')}：{first.get('sentiment', '中性')}，关注“{first.get('title', '')}”；未确认前不追涨。")
        else:
            lines.append(f"- {pos.get('name')}：暂无直接消息，按原纪律持仓，弱势票禁止补仓。")
    lines.append("")
    lines.append("## 风险识别")
    lines.append("- 恐慌性下跌/主力出货/洗盘只能在价格、量能和消息共同确认后执行，不凭单条消息判断。")
    lines.append("- 利好兑现叠加高换手放量滞涨时，优先按减仓风险处理。")
    lines.append("")
    lines.append("## 交易纪律建议")
    lines.append("- 不追热点，不补弱势跟风票。")
    lines.append("- 有硬风险公告的标的先降风险，再讨论机会。")
    lines.append("- 所有买卖动作只按触发价执行，不做盘中情绪交易。")
    return "\n".join(lines)
