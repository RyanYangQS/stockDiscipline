from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
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
    return f"""你是一个严格执行交易纪律的个人股票量能分析助手。

请根据以下数据输出每日持仓操作分析，要求：
1. 只围绕量能、消息面、持仓纪律、K线成交结构分析。
2. 对每只持仓给出：情景判断、风险等级、今日动作、减仓触发、止损触发、是否允许加仓。
3. 明确识别恐慌性下跌、主力出货、主力洗盘、利好兑现、利空释放。
4. 不要给确定性预测，不要承诺收益。
5. 弱势跟风票默认禁止加仓；触发纪律时卖出建议优先于买入理由。
6. 最后给出明日盘前检查清单。

输入数据：
{compact}
"""


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
    prompt = build_daily_prompt(context)

    if not key:
        return DeepSeekResult(
            provider="local",
            model="local-discipline-summary",
            status="missing_api_key",
            content=build_local_report(context),
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
            content=f"DeepSeek 调用失败：{exc}\n\n以下为本地纪律分析：\n\n{build_local_report(context)}",
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

