"""FastAPI server for Stock Discipline."""
from __future__ import annotations

import csv
import io
import mimetypes
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import DEFAULT_HOST, DEFAULT_PORT, FRONTEND_DIR, FRONTEND_DIST_DIR
from .data_sources import check_akshare_available, fetch_kline, fetch_realtime_quote
from .db import init_db
from .repository import (
    create_daily_analysis,
    create_kline,
    create_llm_config,
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
from .web_scraper import check_scraper_available, scrape_all_holdings_news, scrape_cls_news, scrape_sina_finance

# Initialize database
init_db()
seed_if_empty()
rebuild_advice()

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
    cls_news = scrape_cls_news(limit=15)
    sina_news = scrape_sina_finance(limit=10)
    all_news = cls_news + sina_news
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
    return {"bars": fetch_kline(symbol, name, days)}


# === Quote ===

@app.get("/api/quote")
async def get_quote(name: str = "", symbol: str = ""):
    quote = fetch_realtime_quote(symbol or "", name)
    return quote or {"error": "quote not found"}


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


@app.get("/api/advice.csv")
async def get_advice_csv():
    rows = list_advice()
    output = io.StringIO()
    headers = [
        "标的", "持仓数量", "成本价", "当前参考价", "浮亏/浮盈比例",
        "标的分类", "减仓触发价", "止损触发价", "加仓参考价",
        "操作建议", "情景判断", "纪律通过"
    ]
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([
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
        ])
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=holding_advice.csv"}
    )


# === Analysis ===

@app.get("/api/analysis/reports")
async def get_analysis_reports():
    return list_analysis_reports()


@app.post("/api/analysis/daily")
async def post_daily_analysis(data: dict[str, Any] = None):
    return create_daily_analysis(data or {})


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