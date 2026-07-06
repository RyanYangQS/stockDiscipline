from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .advice import Context, build_advice
from .db import connect, row_to_dict, rows_to_dicts, utc_now
from .deepseek import call_deepseek


SAMPLE_POSITIONS = [
    {
        "symbol": "sh.600522",
        "name": "中天科技",
        "quantity": 1200,
        "cost_price": 54.61,
        "current_price": 47.00,
        "category": "核心赛道",
        "sector": "通信/新能源",
        "note": "来自附件样例",
    },
    {
        "symbol": "sz.002138",
        "name": "顺络电子",
        "quantity": 200,
        "cost_price": 74.52,
        "current_price": 60.89,
        "category": "核心赛道",
        "sector": "电子元件",
        "note": "来自附件样例",
    },
    {
        "symbol": "sh.605358",
        "name": "立昂微",
        "quantity": 500,
        "cost_price": 69.43,
        "current_price": 57.50,
        "category": "核心赛道",
        "sector": "半导体",
        "note": "来自附件样例",
    },
    {
        "symbol": "sz.002654",
        "name": "万润科技",
        "quantity": 200,
        "cost_price": 22.61,
        "current_price": 18.80,
        "category": "弱势跟风",
        "sector": "科技题材",
        "note": "来自附件样例",
    },
    {
        "symbol": "sh.603533",
        "name": "掌阅科技",
        "quantity": 200,
        "cost_price": 20.32,
        "current_price": 18.46,
        "category": "弱势跟风",
        "sector": "AI/传媒",
        "note": "来自附件样例",
    },
]


def seed_if_empty() -> None:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM positions").fetchone()["c"]
        if not total:
            now = utc_now()
            for item in SAMPLE_POSITIONS:
                conn.execute(
                    """
                    INSERT INTO positions
                    (symbol, name, quantity, cost_price, current_price, category, sector, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["symbol"],
                        item["name"],
                        item["quantity"],
                        item["cost_price"],
                        item["current_price"],
                        item["category"],
                        item["sector"],
                        item["note"],
                        now,
                        now,
                    ),
                )
        seed_kline_if_empty(conn)
        backfill_sample_symbols(conn)


def backfill_sample_symbols(conn) -> None:
    """Fill stock codes for existing seeded positions created before symbols existed."""
    now = utc_now()
    for item in SAMPLE_POSITIONS:
        conn.execute(
            """
            UPDATE positions
            SET symbol = ?, updated_at = ?
            WHERE name = ? AND (symbol = '' OR symbol IS NULL)
            """,
            (item["symbol"], now, item["name"]),
        )


def list_positions() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM positions ORDER BY id").fetchall())


def create_position(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO positions
            (symbol, name, quantity, cost_price, current_price, category, sector, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("symbol", ""),
                payload["name"],
                int(payload["quantity"]),
                float(payload["cost_price"]),
                float(payload["current_price"]),
                payload.get("category", "观察仓"),
                payload.get("sector", ""),
                payload.get("note", ""),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM positions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def get_position(position_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if row is None:
        raise KeyError("position not found")
    return row_to_dict(row)


def update_position(position_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_position(position_id)
    merged = {**current, **payload}
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE positions
            SET symbol = ?, name = ?, quantity = ?, cost_price = ?, current_price = ?,
                category = ?, sector = ?, note = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                merged.get("symbol", ""),
                merged["name"],
                int(merged["quantity"]),
                float(merged["cost_price"]),
                float(merged["current_price"]),
                merged.get("category", "观察仓"),
                merged.get("sector", ""),
                merged.get("note", ""),
                now,
                position_id,
            ),
        )
    return get_position(position_id)


def delete_position(position_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM positions WHERE id = ?", (position_id,))


def create_news(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO news_items
            (symbol, name, title, source, sentiment, importance, scenario, url, published_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("symbol", ""),
                payload.get("name", ""),
                payload["title"],
                payload.get("source", ""),
                payload.get("sentiment", "中性"),
                int(payload.get("importance", 50)),
                payload.get("scenario", ""),
                payload.get("url", ""),
                payload.get("published_at", date.today().isoformat()),
                now,
            ),
        )
        row = conn.execute("SELECT * FROM news_items WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def get_news(news_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM news_items WHERE id = ?", (news_id,)).fetchone()
    if row is None:
        raise KeyError("news not found")
    return row_to_dict(row)


def list_news() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM news_items ORDER BY id DESC LIMIT 200").fetchall())


def create_volume(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO volume_snapshots
            (symbol, name, trade_date, volume_state, volume_ratio, turnover_rate,
             buy_watch_score, sell_risk_score, accumulation_score, active_net, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("symbol", ""),
                payload.get("name", ""),
                payload.get("trade_date", date.today().isoformat()),
                payload.get("volume_state", ""),
                float(payload.get("volume_ratio", 1)),
                float(payload.get("turnover_rate", 0)),
                int(payload.get("buy_watch_score", 50)),
                int(payload.get("sell_risk_score", 50)),
                int(payload.get("accumulation_score", 50)),
                float(payload.get("active_net", 0)),
                now,
            ),
        )
        row = conn.execute("SELECT * FROM volume_snapshots WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def list_volume() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM volume_snapshots ORDER BY id DESC LIMIT 200").fetchall())


def seed_kline_if_empty(conn) -> None:
    total = conn.execute("SELECT COUNT(*) AS c FROM kline_bars").fetchone()["c"]
    if total:
        return
    today = date.today()
    now = utc_now()
    for idx, item in enumerate(SAMPLE_POSITIONS):
        base = float(item["current_price"])
        for offset in range(70, 0, -1):
            trade_date = (today - timedelta(days=offset)).isoformat()
            drift = (70 - offset) * 0.015
            wave = ((offset % 9) - 4) * 0.18
            close_price = max(1, base * (0.9 + drift / 10) + wave)
            open_price = close_price * (1 + (((offset % 5) - 2) * 0.004))
            high_price = max(open_price, close_price) * (1.012 + (idx % 3) * 0.002)
            low_price = min(open_price, close_price) * (0.988 - (idx % 2) * 0.002)
            volume = 800000 + (70 - offset) * 12000 + (offset % 7) * 90000 + idx * 70000
            conn.execute(
                """
                INSERT OR IGNORE INTO kline_bars
                (symbol, name, trade_date, open_price, high_price, low_price, close_price,
                 volume, amount, turnover_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["symbol"],
                    item["name"],
                    trade_date,
                    round(open_price, 2),
                    round(high_price, 2),
                    round(low_price, 2),
                    round(close_price, 2),
                    round(volume, 2),
                    round(volume * close_price, 2),
                    round(1.2 + (offset % 8) * 0.18, 2),
                    now,
                ),
            )


def list_kline(name: str = "", symbol: str = "", limit: int = 160) -> list[dict[str, Any]]:
    with connect() as conn:
        if name or symbol:
            rows = conn.execute(
                """
                SELECT * FROM kline_bars
                WHERE (name = ? AND ? != '') OR (symbol = ? AND ? != '')
                ORDER BY trade_date DESC LIMIT ?
                """,
                (name, name, symbol, symbol, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM kline_bars ORDER BY trade_date DESC LIMIT ?", (limit,)).fetchall()
    return list(reversed(rows_to_dicts(rows)))


def create_kline(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO kline_bars
            (symbol, name, trade_date, open_price, high_price, low_price, close_price,
             volume, amount, turnover_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, name, trade_date) DO UPDATE SET
                open_price = excluded.open_price,
                high_price = excluded.high_price,
                low_price = excluded.low_price,
                close_price = excluded.close_price,
                volume = excluded.volume,
                amount = excluded.amount,
                turnover_rate = excluded.turnover_rate
            """,
            (
                payload.get("symbol", ""),
                payload.get("name", ""),
                payload.get("trade_date", date.today().isoformat()),
                float(payload["open_price"]),
                float(payload["high_price"]),
                float(payload["low_price"]),
                float(payload["close_price"]),
                float(payload.get("volume", 0)),
                float(payload.get("amount", 0)),
                float(payload.get("turnover_rate", 0)),
                now,
            ),
        )
        row = conn.execute(
            """
            SELECT * FROM kline_bars
            WHERE symbol = ? AND name = ? AND trade_date = ?
            """,
            (payload.get("symbol", ""), payload.get("name", ""), payload.get("trade_date", date.today().isoformat())),
        ).fetchone()
        return row_to_dict(row)


def list_market_snapshots() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM market_snapshots ORDER BY snapshot_date DESC LIMIT 60").fetchall())


def save_market_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    snapshot_date = payload.get("snapshot_date", date.today().isoformat())
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO market_snapshots
            (snapshot_date, index_state, market_volume_state, limit_up_count, limit_down_count,
             hot_sectors, risk_events, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date) DO UPDATE SET
                index_state = excluded.index_state,
                market_volume_state = excluded.market_volume_state,
                limit_up_count = excluded.limit_up_count,
                limit_down_count = excluded.limit_down_count,
                hot_sectors = excluded.hot_sectors,
                risk_events = excluded.risk_events,
                updated_at = excluded.updated_at
            """,
            (
                snapshot_date,
                payload.get("index_state", ""),
                payload.get("market_volume_state", ""),
                int(payload.get("limit_up_count", 0)),
                int(payload.get("limit_down_count", 0)),
                payload.get("hot_sectors", ""),
                payload.get("risk_events", ""),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM market_snapshots WHERE snapshot_date = ?", (snapshot_date,)).fetchone()
        return row_to_dict(row)


def latest_context(position: dict[str, Any]) -> Context:
    name = position["name"]
    symbol = position.get("symbol", "")
    with connect() as conn:
        news = conn.execute(
            """
            SELECT * FROM news_items
            WHERE (name = ? AND name != '') OR (symbol = ? AND symbol != '')
            ORDER BY importance DESC, id DESC LIMIT 1
            """,
            (name, symbol),
        ).fetchone()
        volume = conn.execute(
            """
            SELECT * FROM volume_snapshots
            WHERE (name = ? AND name != '') OR (symbol = ? AND symbol != '')
            ORDER BY trade_date DESC, id DESC LIMIT 1
            """,
            (name, symbol),
        ).fetchone()
    return Context(row_to_dict(news), row_to_dict(volume))


def rebuild_advice() -> list[dict[str, Any]]:
    positions = list_positions()
    today = date.today().isoformat()
    output: list[dict[str, Any]] = []
    with connect() as conn:
        conn.execute("DELETE FROM advice_records WHERE advice_date = ?", (today,))
        for position in positions:
            advice = build_advice(position, latest_context(position))
            conn.execute(
                """
                INSERT INTO advice_records
                (position_id, advice_date, pnl_ratio, risk_level, scenario, trim_trigger,
                 stop_trigger, add_reference, action_advice, reason, discipline_passed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    advice["position_id"],
                    advice["advice_date"],
                    advice["pnl_ratio"],
                    advice["risk_level"],
                    advice["scenario"],
                    advice["trim_trigger"],
                    advice["stop_trigger"],
                    advice["add_reference"],
                    advice["action_advice"],
                    advice["reason"],
                    advice["discipline_passed"],
                    utc_now(),
                ),
            )
            output.append({**position, **advice})
    return output


def list_advice() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT p.id as position_id, p.symbol, p.name, p.quantity, p.cost_price, p.current_price, p.category, p.sector, p.note,
                   a.advice_date, a.pnl_ratio, a.risk_level, a.scenario, a.trim_trigger,
                   a.stop_trigger, a.add_reference, a.action_advice, a.reason, a.discipline_passed
            FROM advice_records a
            JOIN positions p ON p.id = a.position_id
            WHERE a.advice_date = (SELECT MAX(advice_date) FROM advice_records)
            ORDER BY
              CASE a.risk_level WHEN '高' THEN 1 WHEN '中高' THEN 2 WHEN '中' THEN 3 ELSE 4 END,
              p.id
            """
        ).fetchall()
    if not rows:
        return rebuild_advice()
    result = rows_to_dicts(rows)
    for item in result:
        item["pnl_ratio_text"] = f"{item['pnl_ratio'] * 100:+.1f}%"
    return result


def dashboard_summary() -> dict[str, Any]:
    positions = list_positions()
    advice = list_advice()
    total_cost = sum(float(p["cost_price"]) * int(p["quantity"]) for p in positions)
    total_value = sum(float(p["current_price"]) * int(p["quantity"]) for p in positions)
    high_risk = sum(1 for item in advice if item.get("risk_level") == "高")
    blocked = sum(1 for item in advice if not int(item.get("discipline_passed", 1)))
    return {
        "position_count": len(positions),
        "total_cost": total_cost,
        "total_value": total_value,
        "total_pnl": total_value - total_cost,
        "total_pnl_ratio": (total_value - total_cost) / total_cost if total_cost else 0,
        "high_risk_count": high_risk,
        "discipline_blocked_count": blocked,
        "latest_advice_count": len(advice),
    }


def kline_summary_for(name: str, symbol: str = "") -> dict[str, Any]:
    bars = list_kline(name=name, symbol=symbol, limit=30)
    if not bars:
        return {"name": name, "bars": 0}
    closes = [float(item["close_price"]) for item in bars]
    volumes = [float(item["volume"]) for item in bars]
    last = bars[-1]
    avg_volume_5 = sum(volumes[-5:]) / min(5, len(volumes))
    avg_volume_20 = sum(volumes[-20:]) / min(20, len(volumes))
    return {
        "name": name,
        "bars": len(bars),
        "last_date": last["trade_date"],
        "last_close": last["close_price"],
        "change_5d": (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 and closes[-6] else 0,
        "volume_ratio_5_20": avg_volume_5 / avg_volume_20 if avg_volume_20 else 1,
        "recent_high": max(float(item["high_price"]) for item in bars[-20:]),
        "recent_low": min(float(item["low_price"]) for item in bars[-20:]),
    }


def build_analysis_context() -> dict[str, Any]:
    advice = list_advice()
    positions = list_positions()
    return {
        "date": date.today().isoformat(),
        "summary": dashboard_summary(),
        "positions": positions,
        "advice": advice,
        "news": list_news()[:50],
        "volume": list_volume()[:50],
        "market": list_market_snapshots()[:10],
        "kline_summary": [kline_summary_for(item["name"], item.get("symbol", "")) for item in positions],
        "discipline_rules": [
            "弱势跟风票禁止补仓",
            "深度浮亏默认禁止扩大仓位",
            "卖出/减仓建议优先于新的买入理由",
            "监管、退市、财务造假、债务违约等硬风险默认禁止新开仓",
            "利好兑现叠加高换手放量滞涨，优先按主力出货风险处理",
        ],
    }


def create_daily_analysis(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    context = build_analysis_context()
    extra_note = payload.get("extra_note", "")
    if extra_note:
        context["extra_note"] = extra_note
    result = call_deepseek(context)
    now = utc_now()
    prompt = "" if result.provider == "local" else "see raw prompt context in build_analysis_context"
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO analysis_reports
            (report_date, provider, model, status, prompt, content, raw_response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date.today().isoformat(),
                result.provider,
                result.model,
                result.status,
                prompt,
                result.content,
                result.raw_response,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM analysis_reports WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def list_analysis_reports() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM analysis_reports ORDER BY id DESC LIMIT 50").fetchall())


def deepseek_status() -> dict[str, Any]:
    from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
    from .db import load_llm_config

    db_config = load_llm_config()
    if db_config:
        return {
            "configured": bool(db_config.get("api_key")),
            "base_url": db_config.get("base_url", DEEPSEEK_BASE_URL),
            "model": db_config.get("model", DEEPSEEK_MODEL),
            "provider": db_config.get("provider", "deepseek"),
            "source": "database",
            "key_hint": "已配置(数据库)" if db_config.get("api_key") else "未配置",
        }
    return {
        "configured": bool(DEEPSEEK_API_KEY),
        "base_url": DEEPSEEK_BASE_URL,
        "model": DEEPSEEK_MODEL,
        "source": "env",
        "key_hint": "已配置(环境变量)" if DEEPSEEK_API_KEY else "未配置，请设置环境变量 DEEPSEEK_API_KEY",
    }


def list_llm_configs() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT id, provider, display_name, api_key, base_url, model, is_active, created_at, updated_at FROM llm_config ORDER BY id").fetchall())


def create_llm_config(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO llm_config (provider, display_name, api_key, base_url, model, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["provider"],
                payload["display_name"],
                payload.get("api_key", ""),
                payload.get("base_url", ""),
                payload["model"],
                int(payload.get("is_active", 0)),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM llm_config WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def get_llm_config(config_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM llm_config WHERE id = ?", (config_id,)).fetchone()
    if row is None:
        raise KeyError("llm config not found")
    return row_to_dict(row)


def update_llm_config(config_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_llm_config(config_id)
    merged = {**current, **payload}
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE llm_config SET provider = ?, display_name = ?, api_key = ?, base_url = ?, model = ?, is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                merged["provider"],
                merged["display_name"],
                merged.get("api_key", ""),
                merged.get("base_url", ""),
                merged["model"],
                int(merged.get("is_active", 0)),
                now,
                config_id,
            ),
        )
    return get_llm_config(config_id)


def delete_llm_config(config_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM llm_config WHERE id = ?", (config_id,))


def set_active_llm_config(config_id: int) -> dict[str, Any]:
    with connect() as conn:
        conn.execute("UPDATE llm_config SET is_active = 0")
        conn.execute("UPDATE llm_config SET is_active = 1 WHERE id = ?", (config_id,))
    return get_llm_config(config_id)


def test_llm_config(config_id: int) -> dict[str, Any]:
    """Test LLM config connection by sending a simple request."""
    config = get_llm_config(config_id)
    api_key = config.get("api_key")
    base_url = config.get("base_url", "").rstrip("/")
    model = config.get("model")

    if not api_key:
        return {"success": False, "error": "API key not configured"}

    import json
    import urllib.request
    import urllib.error

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(f"{base_url}/chat/completions", data=data, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body)
            return {"success": True, "model": model, "response_preview": result.get("choices", [{}])[0].get("message", {}).get("content", "")[:50]}
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": f"HTTP {exc.code}: {exc.read().decode()[:100]}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
