"""FastAPI server for Stock Discipline."""
from __future__ import annotations

import csv
import io
import json
import mimetypes
import threading
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import DEFAULT_HOST, DEFAULT_PORT, FRONTEND_DIR, FRONTEND_DIST_DIR
from .data_sources import check_akshare_available, fetch_intraday_kline, fetch_kline, fetch_realtime_quote
from .db import connect, init_db, utc_now
from .deepseek import call_deepseek, call_deepseek_for_volume
from .technical_analysis import analyze_volume_signals, calculate_volume_metrics
from .repository import (
    create_daily_analysis,
    create_kline,
    create_llm_config,
    create_market_analysis,
    create_news,
    create_position,
    create_volume,
    dashboard_summary,
    deepseek_status,
    delete_llm_config,
    delete_position,
    get_llm_config,
    list_analysis_reports,
    list_advice,
    list_kline,
    list_llm_configs,
    list_market_snapshots,
    list_news,
    list_positions,
    list_volume,
    rebuild_advice,
    seed_if_empty,
    save_market_snapshot,
    set_active_llm_config,
    test_llm_config,
    update_llm_config,
    update_position,
)
from .web_scraper import check_scraper_available, scrape_all_holdings_news, scrape_market_news_items


class ApiError(Exception):
    """Compatibility error used by legacy surface tests."""


class Handler:
    """Small compatibility shim for legacy path parsing tests."""

    def _path_id(self, path: str, prefix: str) -> int:
        value = path.removeprefix(prefix).strip("/")
        try:
            return int(value)
        except ValueError as exc:
            raise ApiError(f"invalid id: {value}") from exc


def json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def build_advice_csv(rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO()
    headers = [
        "标的",
        "持仓数量",
        "成本价",
        "当前参考价",
        "浮亏/浮盈比例",
        "标的分类",
        "减仓触发价（分批执行）",
        "止损触发价（跌破刚性执行）",
        "加仓参考价（仅企稳后）",
        "操作建议",
        "情景判断",
        "纪律通过",
    ]
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(
            [
                row["name"],
                f"{row['quantity']}股",
                f"{float(row['cost_price']):.2f}元",
                f"{float(row['current_price']):.2f}元",
                row.get("pnl_ratio_text") or f"{float(row['pnl_ratio']) * 100:+.1f}%",
                row["category"],
                row["trim_trigger"],
                row["stop_trigger"],
                row["add_reference"],
                row["action_advice"],
                row["scenario"],
                "是" if int(row["discipline_passed"]) else "否",
            ]
        )
    return output.getvalue().encode("utf-8-sig")


def _resolve_stock_identity(name: str = "", symbol: str = "") -> tuple[str, str]:
    resolved_name = (name or "").strip()
    resolved_symbol = (symbol or "").strip()
    for position in list_positions():
        if resolved_name and position.get("name") == resolved_name:
            return resolved_name, resolved_symbol or position.get("symbol", "")
        if resolved_symbol and position.get("symbol") == resolved_symbol:
            return resolved_name or position.get("name", ""), resolved_symbol
    return resolved_name, resolved_symbol


def _save_kline_bars(bars: list[dict[str, Any]], name: str, symbol: str) -> int:
    saved = 0
    for bar in bars:
        payload = {
            **bar,
            "name": bar.get("name") or name,
            "symbol": bar.get("symbol") or symbol,
        }
        try:
            create_kline(payload)
            saved += 1
        except Exception:
            pass
    return saved


def build_realtime_kline_payload(
    name: str = "",
    symbol: str = "",
    days: int = 60,
    fetcher=fetch_kline,
) -> dict[str, Any]:
    from datetime import date
    safe_days = max(1, min(int(days or 60), 1000))
    resolved_name, resolved_symbol = _resolve_stock_identity(name, symbol)
    bars = fetcher(resolved_symbol, resolved_name, safe_days)
    if bars:
        saved = _save_kline_bars(bars, resolved_name, resolved_symbol)
        # Determine source based on whether today's data is included
        today_str = date.today().strftime("%Y-%m-%d")
        has_today = any(bar.get("trade_date") == today_str for bar in bars)
        source = "eastmoney_realtime" if has_today else "baostock"
        return {
            "bars": bars,
            "source": source,
            "name": resolved_name,
            "symbol": resolved_symbol,
            "saved": saved,
        }

    cached = list_kline(name=resolved_name or name, symbol=resolved_symbol or symbol, limit=safe_days)
    return {
        "bars": cached,
        "source": "local_cache" if cached else "empty",
        "name": resolved_name,
        "symbol": resolved_symbol,
        "message": "数据源未返回数据，已回退本地缓存" if cached else "数据源未返回数据，且本地缓存为空",
    }


def build_intraday_kline_payload(name: str = "", symbol: str = "", period: int = 5, limit: int = 240) -> dict[str, Any]:
    safe_limit = max(30, min(int(limit or 240), 1200))
    safe_period = int(period or 5)
    resolved_name, resolved_symbol = _resolve_stock_identity(name, symbol)
    bars = fetch_intraday_kline(resolved_symbol, resolved_name, safe_period, safe_limit)
    return {
        "bars": bars,
        "source": "eastmoney" if bars else "empty",
        "name": resolved_name,
        "symbol": resolved_symbol,
        "period": safe_period,
        "limit": safe_limit,
        "message": "" if bars else "东方财富分钟K未返回数据",
    }


def build_quote_payload(name: str = "", symbol: str = "") -> dict[str, Any]:
    resolved_name, resolved_symbol = _resolve_stock_identity(name, symbol)
    quote = fetch_realtime_quote(resolved_symbol or "", resolved_name)
    if quote:
        return {**quote, "source": "baostock"}

    cached = list_kline(name=resolved_name or name, symbol=resolved_symbol or symbol, limit=2)
    if cached:
        latest = cached[-1]
        previous = cached[-2] if len(cached) > 1 else latest
        prev_close = float(previous["close_price"])
        current = float(latest["close_price"])
        change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0
        return {
            "symbol": latest.get("symbol") or resolved_symbol,
            "name": latest.get("name") or resolved_name,
            "current_price": current,
            "change_pct": round(change_pct, 2),
            "volume": latest["volume"],
            "amount": latest["amount"],
            "high_price": latest["high_price"],
            "low_price": latest["low_price"],
            "open_price": latest["open_price"],
            "prev_close": prev_close,
            "source": "local_cache",
        }
    return {"error": "quote not found", "source": "empty"}


# Initialize database
init_db()
seed_if_empty()
rebuild_advice()


# === Background Price Scheduler ===

def is_trading_time() -> bool:
    """Check if current time is within trading hours (China A-shares)."""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()

    # Weekend: closed
    if weekday >= 5:  # Saturday=5, Sunday=6
        return False

    # Morning session: 9:30-11:30
    if time(9, 30) <= current_time <= time(11, 30):
        return True

    # Afternoon session: 13:00-15:00
    if time(13, 0) <= current_time <= time(15, 0):
        return True

    return False


def update_position_prices() -> int:
    """Update current prices for all positions from real-time quotes."""
    positions = list_positions()
    updated_count = 0
    for position in positions:
        try:
            quote = fetch_realtime_quote(position.get("symbol", ""), position.get("name", ""))
            if quote and quote.get("current_price"):
                update_position(position["id"], {"current_price": quote["current_price"]})
                updated_count += 1
        except Exception:
            pass
    return updated_count


def price_scheduler_loop():
    """Background thread that updates prices based on trading schedule."""
    import time as time_module

    while True:
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()

        # Calculate next update interval
        if weekday >= 5:  # Weekend
            # Sleep until Monday 9:15
            sleep_seconds = 3600  # Check every hour
        elif is_trading_time():
            # During trading: update every minute
            update_position_prices()
            sleep_seconds = 60
        elif time(9, 15) <= current_time < time(9, 30):
            # Pre-market: update once at 9:15
            update_position_prices()
            sleep_seconds = 900  # 15 minutes
        elif time(15, 0) < current_time <= time(15, 5):
            # After-market: update once at 15:05
            update_position_prices()
            sleep_seconds = 900  # 15 minutes
        else:
            # Outside trading hours: check every 30 minutes
            sleep_seconds = 1800

        time_module.sleep(sleep_seconds)


# Start background scheduler
price_thread = threading.Thread(target=price_scheduler_loop, daemon=True)
price_thread.start()


# Create FastAPI app
app = FastAPI(
    title="Stock Discipline",
    description="股票纪律管理系统 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Health & Summary ===

@app.get("/api/health")
async def health():
    return {"ok": True, "app": "stock-discipline"}


@app.get("/api/summary")
async def summary():
    return dashboard_summary()


# === Positions ===

@app.get("/api/positions")
async def get_positions():
    return list_positions()


@app.post("/api/positions")
async def post_position(data: dict[str, Any]):
    return create_position(data)


@app.put("/api/positions/{position_id}")
async def put_position(position_id: int, data: dict[str, Any]):
    return update_position(position_id, data)


@app.post("/api/positions/refresh-prices")
async def refresh_all_prices():
    """Refresh current prices for all positions from real-time quotes."""
    positions = list_positions()
    updated = []
    for position in positions:
        try:
            quote = fetch_realtime_quote(position.get("symbol", ""), position.get("name", ""))
            if quote and quote.get("current_price"):
                update_position(position["id"], {"current_price": quote["current_price"]})
                updated.append({
                    "name": position["name"],
                    "old_price": position["current_price"],
                    "new_price": quote["current_price"],
                })
        except Exception as exc:
            updated.append({
                "name": position["name"],
                "error": str(exc),
            })
    return {"updated": len(updated), "details": updated}


@app.delete("/api/positions/{position_id}")
async def delete_position_route(position_id: int):
    delete_position(position_id)
    return {"deleted": True}


# === News ===

@app.get("/api/news")
async def get_news():
    return list_news()


@app.post("/api/news")
async def post_news(data: dict[str, Any]):
    return create_news(data)


@app.post("/api/news/scrape")
async def scrape_news():
    positions = list_positions()
    news_items = scrape_all_holdings_news(positions)
    saved = []
    for item in news_items:
        try:
            saved.append(create_news(item))
        except Exception:
            pass
    return {"scraped": len(news_items), "saved": len(saved)}


@app.post("/api/news/scrape/market")
async def scrape_market_news():
    all_news = scrape_market_news_items(limit=25)
    saved = []
    for item in all_news:
        try:
            saved.append(create_news(item))
        except Exception:
            pass
    return {"scraped": len(all_news), "saved": len(saved)}


# === Volume ===

@app.get("/api/volume")
async def get_volume():
    return list_volume()


@app.post("/api/volume")
async def post_volume(data: dict[str, Any]):
    return create_volume(data)


# === Kline ===

@app.get("/api/kline")
async def get_kline(name: str = "", symbol: str = "", limit: int = 160):
    return list_kline(name=name, symbol=symbol, limit=limit)


@app.post("/api/kline")
async def post_kline(data: dict[str, Any]):
    return create_kline(data)


@app.get("/api/kline/realtime")
async def get_kline_realtime(name: str = "", symbol: str = "", days: int = 60):
    return build_realtime_kline_payload(name=name, symbol=symbol, days=days)


@app.get("/api/kline/intraday")
async def get_kline_intraday(name: str = "", symbol: str = "", period: int = 5, limit: int = 240):
    return build_intraday_kline_payload(name=name, symbol=symbol, period=period, limit=limit)


# === Quote ===

@app.get("/api/quote")
async def get_quote(name: str = "", symbol: str = ""):
    return build_quote_payload(name=name, symbol=symbol)


# === Market ===

@app.get("/api/market")
async def get_market():
    return list_market_snapshots()


@app.post("/api/market")
async def post_market(data: dict[str, Any]):
    return save_market_snapshot(data)


# === Advice ===

@app.get("/api/advice")
async def get_advice():
    return list_advice()


@app.post("/api/advice/rebuild")
async def rebuild_advice_route():
    return rebuild_advice()


@app.post("/api/advice/ai")
async def generate_ai_advice():
    """Generate position advice using AI for each holding."""
    from .deepseek import call_deepseek_for_position
    from .repository import kline_summary_for, latest_context, list_positions, utc_now

    positions = list_positions()
    if not positions:
        return {"advice": [], "message": "无持仓数据"}

    today = date.today().isoformat()
    results = []

    for position in positions:
        try:
            # Get context (news, volume)
            ctx = latest_context(position)
            context = {
                "news": ctx.latest_news if ctx else None,
                "volume": ctx.latest_volume if ctx else None,
            }

            # Get K-line summary if available
            kline_summary = kline_summary_for(position["name"], position.get("symbol", ""))

            # Call AI for position analysis
            advice = call_deepseek_for_position(position, context, kline_summary)

            # Save to database (INSERT OR REPLACE to update existing)
            with connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO advice_records
                    (position_id, advice_date, pnl_ratio, risk_level, scenario, trim_trigger,
                     stop_trigger, add_reference, action_advice, reason, discipline_passed, provider, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        advice.get("position_id", position["id"]),
                        today,
                        advice.get("pnl_ratio", 0),
                        advice.get("risk_level", "中"),
                        advice.get("scenario", "观察"),
                        advice.get("trim_trigger", ""),
                        advice.get("stop_trigger", ""),
                        advice.get("add_reference", ""),
                        advice.get("action_advice", ""),
                        advice.get("reason", ""),
                        int(advice.get("discipline_passed", 1)),
                        advice.get("provider", "deepseek"),
                        utc_now(),
                    ),
                )

            results.append({**position, **advice})
        except Exception as exc:
            # Fallback to local advice on error
            from .advice import build_advice, Context
            ctx = latest_context(position)
            local_advice = build_advice(position, ctx or Context(None, None))
            local_advice["provider"] = "local_fallback"
            local_advice["error"] = str(exc)

            # Save fallback to database
            with connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO advice_records
                    (position_id, advice_date, pnl_ratio, risk_level, scenario, trim_trigger,
                     stop_trigger, add_reference, action_advice, reason, discipline_passed, provider, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        local_advice.get("position_id", position["id"]),
                        today,
                        local_advice.get("pnl_ratio", 0),
                        local_advice.get("risk_level", "中"),
                        local_advice.get("scenario", "观察"),
                        local_advice.get("trim_trigger", ""),
                        local_advice.get("stop_trigger", ""),
                        local_advice.get("add_reference", ""),
                        local_advice.get("action_advice", ""),
                        local_advice.get("reason", ""),
                        int(local_advice.get("discipline_passed", 1)),
                        "local_fallback",
                        utc_now(),
                    ),
                )
            results.append({**position, **local_advice})

    return {"advice": results, "generated_at": today}


@app.get("/api/advice.csv")
async def get_advice_csv():
    rows = list_advice()
    return Response(
        content=build_advice_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=holding_advice.csv"}
    )


# === Analysis ===

@app.get("/api/analysis/reports")
async def get_analysis_reports(report_type: str = ""):
    return list_analysis_reports(report_type=report_type)


@app.post("/api/analysis/daily")
async def post_daily_analysis(data: dict[str, Any] = None):
    return create_daily_analysis(data or {})


@app.post("/api/analysis/market")
async def post_market_analysis(data: dict[str, Any] = None):
    return create_market_analysis(data or {})


@app.post("/api/analysis/volume")
async def post_volume_analysis(data: dict[str, Any] = None):
    """Perform stock-specific volume analysis using Python technical analysis + LLM."""
    data = data or {}
    stock_name = data.get("stock", "")
    bars = data.get("bars", [])
    quote = data.get("quote")

    if not stock_name:
        raise HTTPException(400, "缺少股票名称")

    if not bars or len(bars) < 5:
        raise HTTPException(400, "K线数据不足，需要至少5根K线")

    # Step 1: Calculate technical metrics using Python
    metrics = calculate_volume_metrics(bars)

    # Step 2: Analyze volume signals
    analysis = analyze_volume_signals(metrics)

    # Step 3: Call LLM for intelligent interpretation
    result = call_deepseek_for_volume(stock_name, metrics, analysis, bars, quote)

    # Step 4: Save report to database
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO analysis_reports
            (report_date, report_type, provider, model, status, prompt, content, raw_response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date.today().isoformat(),
                "volume",
                result.provider,
                result.model,
                result.status,
                f"volume analysis for {stock_name}",
                result.content,
                result.raw_response,
                utc_now(),
            ),
        )

    return {
        "stock": stock_name,
        "provider": result.provider,
        "model": result.model,
        "status": result.status,
        "content": result.content,
        "metrics": metrics,
        "signals": analysis,
        "report_id": cur.lastrowid,
    }


# === Settings ===

@app.get("/api/settings/deepseek")
async def get_deepseek_settings():
    return deepseek_status()


# === LLM Config ===

@app.get("/api/llm/configs")
async def get_llm_configs():
    return list_llm_configs()


@app.post("/api/llm/configs")
async def post_llm_config(data: dict[str, Any]):
    return create_llm_config(data)


@app.get("/api/llm/config/{config_id}")
async def get_llm_config_route(config_id: int):
    return get_llm_config(config_id)


@app.put("/api/llm/config/{config_id}")
async def put_llm_config(config_id: int, data: dict[str, Any]):
    return update_llm_config(config_id, data)


@app.delete("/api/llm/config/{config_id}")
async def delete_llm_config_route(config_id: int):
    delete_llm_config(config_id)
    return {"deleted": True}


@app.post("/api/llm/config/{config_id}/activate")
async def activate_llm_config(config_id: int):
    return set_active_llm_config(config_id)


@app.post("/api/llm/config/{config_id}/test")
async def test_llm_config_route(config_id: int):
    return test_llm_config(config_id)


# === Data Sources ===

@app.get("/api/data/status")
async def get_data_status():
    return check_akshare_available()


@app.get("/api/scraper/status")
async def get_scraper_status():
    return check_scraper_available()


# === Static Files ===

static_root = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else FRONTEND_DIR

@app.get("/")
async def index():
    index_file = static_root / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(404, "index.html not found")


# Mount static files
app.mount("/assets", StaticFiles(directory=static_root / "assets", check_dir=False), name="assets")
app.mount("/", StaticFiles(directory=static_root, html=True, check_dir=False), name="static")


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Run FastAPI server with uvicorn."""
    import uvicorn
    import socket

    # Try default port, then find available port if blocked
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Test if port is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.close()

            print(f"Stock Discipline running at http://{host}:{port}")
            print(f"API Documentation: http://{host}:{port}/docs")
            uvicorn.run(app, host=host, port=port)
            return
        except OSError as e:
            if e.errno == 48:  # Address already in use
                if attempt == 0:
                    print(f"Port {port} is in use, trying other ports...")
                port += 1
            else:
                raise

    raise OSError(f"No available ports in range {DEFAULT_PORT}-{DEFAULT_PORT + max_attempts}")
