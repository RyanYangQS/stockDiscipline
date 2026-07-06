from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, load_llm_config


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

