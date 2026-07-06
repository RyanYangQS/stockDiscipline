from __future__ import annotations

import csv
import io
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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


def json_bytes(payload) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def build_advice_csv(rows: list[dict]) -> bytes:
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


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


class Handler(BaseHTTPRequestHandler):
    server_version = "StockDiscipline/1.0"

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def _handle(self, method: str):
        try:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                payload = self._route_api(method, parsed.path, parse_qs(parsed.query))
                self._send_json(payload)
                return
            self._serve_static(parsed.path)
        except ApiError as exc:
            self._send_json({"error": exc.message}, status=exc.status)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _route_api(self, method: str, path: str, query: dict):
        if method == "GET" and path == "/api/health":
            return {"ok": True, "app": "stock-discipline"}
        if method == "GET" and path == "/api/summary":
            return dashboard_summary()
        if method == "GET" and path == "/api/positions":
            return list_positions()
        if method == "POST" and path == "/api/positions":
            return create_position(self._read_json())
        if path.startswith("/api/positions/"):
            position_id = self._path_id(path, "/api/positions/")
            if method == "PUT":
                return update_position(position_id, self._read_json())
            if method == "DELETE":
                delete_position(position_id)
                return {"deleted": True}
        if method == "GET" and path == "/api/news":
            return list_news()
        if method == "POST" and path == "/api/news":
            return create_news(self._read_json())
        if method == "GET" and path == "/api/volume":
            return list_volume()
        if method == "POST" and path == "/api/volume":
            return create_volume(self._read_json())
        if method == "GET" and path == "/api/kline":
            return list_kline(
                name=query.get("name", [""])[0],
                symbol=query.get("symbol", [""])[0],
                limit=int(query.get("limit", ["160"])[0]),
            )
        if method == "POST" and path == "/api/kline":
            return create_kline(self._read_json())
        if method == "GET" and path == "/api/market":
            return list_market_snapshots()
        if method == "POST" and path == "/api/market":
            return save_market_snapshot(self._read_json())
        if method == "GET" and path == "/api/advice":
            return list_advice()
        if method == "POST" and path == "/api/advice/rebuild":
            return rebuild_advice()
        if method == "GET" and path == "/api/advice.csv":
            self._send_csv(list_advice())
            return None
        if method == "GET" and path == "/api/analysis/reports":
            return list_analysis_reports()
        if method == "POST" and path == "/api/analysis/daily":
            return create_daily_analysis(self._read_json())
        if method == "GET" and path == "/api/settings/deepseek":
            return deepseek_status()
        if method == "GET" and path == "/api/llm/configs":
            return list_llm_configs()
        if method == "POST" and path == "/api/llm/configs":
            return create_llm_config(self._read_json())
        if path.startswith("/api/llm/config/"):
            config_id = self._path_id(path, "/api/llm/config/")
            if method == "GET":
                return get_llm_config(config_id)
            if method == "PUT":
                return update_llm_config(config_id, self._read_json())
            if method == "DELETE":
                delete_llm_config(config_id)
                return {"deleted": True}
            if method == "POST" and path.endswith("/activate"):
                return set_active_llm_config(config_id)
            if method == "POST" and path.endswith("/test"):
                return test_llm_config(config_id)
        if method == "GET" and path == "/api/data/status":
            return check_akshare_available()
        if method == "GET" and path.startswith("/api/kline/realtime"):
            # Parse symbol from path like /api/kline/realtime/300750
            parts = path.split("/")
            symbol = parts[-1] if len(parts) > 4 and parts[-1].isdigit() else query.get("symbol", [""])[0]
            name = query.get("name", [""])[0]
            days = int(query.get("days", ["60"])[0])
            return {"bars": fetch_kline(symbol, name, days)}
        if method == "GET" and path.startswith("/api/quote/"):
            symbol = self._path_id(path, "/api/quote/") if path.split("/")[-1].isdigit() else ""
            symbol = symbol or query.get("symbol", [""])[0]
            name = query.get("name", [""])[0]
            quote = fetch_realtime_quote(str(symbol), name)
            return quote or {"error": "quote not found"}
        raise ApiError(404, "api not found")

    def _path_id(self, path: str, prefix: str) -> int:
        value = path.removeprefix(prefix).strip("/")
        if not value.isdigit():
            raise ApiError(400, "invalid id")
        return int(value)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ApiError(400, f"invalid json: {exc}") from exc

    def _send_json(self, payload, status: int = 200):
        if payload is None:
            return
        body = json_bytes(payload)
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_csv(self, rows: list[dict]):
        body = build_advice_csv(rows)
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="holding_advice.csv"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str):
        if path == "/":
            path = "/index.html"
        clean = Path(path.lstrip("/"))
        static_root = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else FRONTEND_DIR
        target = (static_root / clean).resolve()
        root = static_root.resolve()
        if not str(target).startswith(str(root)) or not target.exists() or target.is_dir():
            target = static_root / "index.html"
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix == ".js":
            content_type = "application/javascript"
        if target.suffix == ".css":
            content_type = "text/css"
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    init_db()
    seed_if_empty()
    rebuild_advice()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Stock Discipline running at http://{host}:{port}")
    server.serve_forever()
