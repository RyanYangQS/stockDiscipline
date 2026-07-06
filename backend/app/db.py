import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DATA_DIR, DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                cost_price REAL NOT NULL,
                current_price REAL NOT NULL,
                category TEXT NOT NULL DEFAULT '观察仓',
                sector TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                sentiment TEXT NOT NULL DEFAULT '中性',
                importance INTEGER NOT NULL DEFAULT 50,
                scenario TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS volume_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL DEFAULT '',
                trade_date TEXT NOT NULL,
                volume_state TEXT NOT NULL DEFAULT '',
                volume_ratio REAL NOT NULL DEFAULT 1,
                turnover_rate REAL NOT NULL DEFAULT 0,
                buy_watch_score INTEGER NOT NULL DEFAULT 50,
                sell_risk_score INTEGER NOT NULL DEFAULT 50,
                accumulation_score INTEGER NOT NULL DEFAULT 50,
                active_net REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS advice_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER NOT NULL,
                advice_date TEXT NOT NULL,
                pnl_ratio REAL NOT NULL,
                risk_level TEXT NOT NULL,
                scenario TEXT NOT NULL,
                trim_trigger TEXT NOT NULL,
                stop_trigger TEXT NOT NULL,
                add_reference TEXT NOT NULL,
                action_advice TEXT NOT NULL,
                reason TEXT NOT NULL,
                discipline_passed INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(position_id) REFERENCES positions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER,
                action TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                reason TEXT NOT NULL DEFAULT '',
                followed_discipline INTEGER NOT NULL DEFAULT 1,
                traded_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(position_id) REFERENCES positions(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS kline_bars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL DEFAULT '',
                trade_date TEXT NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume REAL NOT NULL DEFAULT 0,
                amount REAL NOT NULL DEFAULT 0,
                turnover_rate REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(symbol, name, trade_date)
            );

            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL UNIQUE,
                index_state TEXT NOT NULL DEFAULT '',
                market_volume_state TEXT NOT NULL DEFAULT '',
                limit_up_count INTEGER NOT NULL DEFAULT 0,
                limit_down_count INTEGER NOT NULL DEFAULT 0,
                hot_sectors TEXT NOT NULL DEFAULT '',
                risk_events TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'local',
                model TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ok',
                prompt TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                raw_response TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]
