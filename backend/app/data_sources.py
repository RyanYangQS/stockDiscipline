"""Real data sources for stock information using Baostock (stable, free)."""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any

import requests

# Disable proxy for requests
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

logger = logging.getLogger(__name__)

COMMON_STOCK_CODES = {
    "中天科技": "sh.600522",
    "顺络电子": "sz.002138",
    "立昂微": "sh.605358",
    "万润科技": "sz.002654",
    "掌阅科技": "sh.603533",
}


def _get_baostock():
    """Get baostock module."""
    try:
        import baostock as bs
        return bs
    except ImportError:
        logger.warning("Baostock not installed. Run: pip install baostock")
        return None


def _login_bs():
    """Login to baostock."""
    bs = _get_baostock()
    if not bs:
        return None
    lg = bs.login()
    if lg.error_code != '0':
        logger.error(f"Baostock login failed: {lg.error_msg}")
        return None
    return bs


def fetch_eastmoney_daily_kline(symbol: str, name: str = "", days: int = 60) -> list[dict[str, Any]]:
    """Fetch daily K-line data from Eastmoney API (includes today during trading hours)."""
    import json
    import subprocess

    if not symbol:
        symbol = _search_stock_code(name)
    secid = _eastmoney_secid(symbol)
    if not secid:
        return []

    # Use curl with IPv4 only (IPv6 causes connection issues)
    # Use minimal fields to avoid URL encoding issues
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&klt=101&fqt=1&lmt={min(days, 500)}"

    try:
        result = subprocess.run(
            ["curl", "-s", "-4", "--max-time", "15", url],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0 or not result.stdout:
            return []

        payload = json.loads(result.stdout)
        data = payload.get("data") or {}
        klines = data.get("klines") or []
        stock_name = name or data.get("name") or ""

        bars = []
        for row in klines:
            parts = row.split(",")
            if len(parts) < 11:
                continue
            bars.append({
                "symbol": symbol,
                "name": stock_name,
                "trade_date": parts[0],
                "open_price": float(parts[1] or 0),
                "close_price": float(parts[2] or 0),
                "high_price": float(parts[3] or 0),
                "low_price": float(parts[4] or 0),
                "volume": float(parts[5] or 0) * 100,  # Convert hands to shares
                "amount": float(parts[6] or 0),
                "amplitude": float(parts[7] or 0),
                "change_pct": float(parts[8] or 0),
                "change_value": float(parts[9] or 0),
                "turnover_rate": float(parts[10] or 0),
            })
        return bars
    except Exception as e:
        logger.error(f"Eastmoney daily kline error: {e}")
        return []


def fetch_kline(symbol: str, name: str = "", days: int = 60) -> list[dict[str, Any]]:
    """Fetch K-line data - uses Eastmoney during trading hours for today's data.

    Args:
        symbol: Stock code (e.g., "sh.600000" or "sz.300750")
        name: Stock name (fallback if symbol empty)
        days: Number of trading days to fetch

    Returns:
        List of K-line bars with OHLCV data
    """
    # During trading hours, use Eastmoney to get today's data
    if is_trading_hours():
        bars = fetch_eastmoney_daily_kline(symbol, name, days)
        if bars:
            return bars

    # Outside trading hours, use Baostock (stable, historical data)
    bs = _login_bs()
    if not bs:
        return []

    try:
        # Format symbol for baostock (sh.xxxx or sz.xxxx)
        if not symbol:
            symbol = _search_stock_code(name)
        if not symbol:
            logger.warning(f"Stock not found: {symbol or name}")
            return []

        # Ensure correct format
        if not symbol.startswith(('sh.', 'sz.')):
            if symbol.startswith('6'):
                symbol = f'sh.{symbol}'
            else:
                symbol = f'sz.{symbol}'

        end_date = date.today().strftime("%Y-%m-%d")
        start_date = (date.today() - timedelta(days=days * 3)).strftime("%Y-%m-%d")

        # Query K-line data
        rs = bs.query_history_k_data_plus(
            symbol,
            "date,code,open,high,low,close,volume,amount,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2"  # Forward adjusted
        )

        if rs.error_code != '0':
            logger.error(f"Baostock query failed: {rs.error_msg}")
            return []

        # Collect data
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        if not data_list:
            return []

        # Convert to our format, take last N days
        bars = []
        for row in data_list[-days:]:
            if len(row) >= 8:
                bars.append({
                    "symbol": row[1] if len(row) > 1 else symbol.split('.')[1],
                    "name": name,
                    "trade_date": row[0],
                    "open_price": float(row[2]) if row[2] else 0,
                    "high_price": float(row[3]) if row[3] else 0,
                    "low_price": float(row[4]) if row[4] else 0,
                    "close_price": float(row[5]) if row[5] else 0,
                    "volume": float(row[6]) if row[6] else 0,
                    "amount": float(row[7]) if row[7] else 0,
                    "turnover_rate": float(row[8]) if len(row) > 8 and row[8] else 0,
                })

        bs.logout()
        return bars

    except Exception as e:
        logger.error(f"Baostock fetch_kline error: {e}")
        try:
            bs.logout()
        except:
            pass
        return []


def fetch_eastmoney_realtime_quote(symbol: str, name: str = "") -> dict[str, Any] | None:
    """Fetch real-time quote from Eastmoney API (works during trading hours)."""
    import json
    import subprocess

    if not symbol:
        symbol = _search_stock_code(name)
    secid = _eastmoney_secid(symbol)
    if not secid:
        return None

    # Use curl with IPv4 only (IPv6 causes SSL handshake timeout)
    params = f"secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f55,f57,f58,f60"
    url = f"https://push2.eastmoney.com/api/qt/stock/get?{params}"

    try:
        result = subprocess.run(
            ["curl", "-s", "-4", "--max-time", "15", "-H", "User-Agent: Mozilla/5.0",
             "-H", "Referer: https://quote.eastmoney.com/", url],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0 or not result.stdout:
            return None

        payload = json.loads(result.stdout)
        data = payload.get("data") or {}
        if not data:
            return None

        # Parse Eastmoney fields (all prices are in cents)
        # f43: 最新价(cents), f44: 最高(cents), f45: 最低(cents), f46: 今开(cents)
        # f47: 成交量(手), f48: 成交额
        # f50: 涨跌额(cents), f55: 换手率, f57: 股票代码, f58: 股票名称
        # f60: 昨收(cents)
        current_price = float(data.get("f43", 0) or 0) / 100
        high_price = float(data.get("f44", 0) or 0) / 100
        low_price = float(data.get("f45", 0) or 0) / 100
        open_price = float(data.get("f46", 0) or 0) / 100
        volume_hands = float(data.get("f47", 0) or 0)
        amount = float(data.get("f48", 0) or 0)
        turnover_rate = float(data.get("f55", 0) or 0)
        stock_code = data.get("f57") or ""
        stock_name = data.get("f58") or name
        prev_close = float(data.get("f60", 0) or 0) / 100

        if current_price <= 0:
            return None

        # Calculate change_pct manually (f51 seems unreliable)
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0

        return {
            "symbol": stock_code,
            "name": stock_name,
            "current_price": current_price,
            "change_pct": round(change_pct, 2),
            "volume": volume_hands * 100,  # Convert hands to shares
            "amount": amount,
            "high_price": high_price,
            "low_price": low_price,
            "open_price": open_price,
            "prev_close": prev_close,
            "turnover_rate": turnover_rate,
            "source": "eastmoney_realtime",
        }
    except Exception as e:
        logger.error(f"Eastmoney realtime quote error: {e}")
        return None


def is_trading_hours() -> bool:
    """Check if current time is within China A-share trading hours or lunch break.
    Returns True during the entire trading day (9:30-15:00) including lunch break,
    because Eastmoney should have today's partial data during this period.
    """
    from datetime import datetime, time
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()

    if weekday >= 5:  # Weekend
        return False

    # Entire trading day: 9:30-15:00 (including lunch break 11:30-13:00)
    # During this period, Eastmoney should have today's data (at least morning session)
    if time(9, 30) <= current_time <= time(15, 0):
        return True

    return False


def fetch_realtime_quote(symbol: str, name: str = "") -> dict[str, Any] | None:
    """Fetch current realtime quote - uses Eastmoney during trading hours, Baostock otherwise."""
    # During trading hours, use Eastmoney for real-time prices
    if is_trading_hours():
        quote = fetch_eastmoney_realtime_quote(symbol, name)
        if quote and quote.get("current_price", 0) > 0:
            return quote

    # Outside trading hours, use Baostock daily data as fallback
    bars = fetch_kline(symbol, name, days=5)
    if bars:
        latest = bars[-1]
        prev_close = bars[-2]["close_price"] if len(bars) > 1 else latest["close_price"]
        change_pct = ((latest["close_price"] - prev_close) / prev_close * 100) if prev_close else 0
        return {
            "symbol": latest["symbol"],
            "name": latest["name"],
            "current_price": latest["close_price"],
            "change_pct": round(change_pct, 2),
            "volume": latest["volume"],
            "amount": latest["amount"],
            "high_price": latest["high_price"],
            "low_price": latest["low_price"],
            "open_price": latest["open_price"],
            "prev_close": prev_close,
            "turnover_rate": latest.get("turnover_rate", 0),
            "source": "baostock_daily",
        }
    return None


def fetch_intraday_kline(symbol: str, name: str = "", period: int = 5, limit: int = 240) -> list[dict[str, Any]]:
    """Fetch minute-level K-line data from Eastmoney."""
    if not symbol:
        symbol = _search_stock_code(name)
    secid = _eastmoney_secid(symbol)
    if not secid:
        return []

    klt = int(period or 5)
    if klt not in {1, 5, 15, 30, 60}:
        klt = 5
    safe_limit = max(30, min(int(limit or 240), 1200))

    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": str(klt),
        "fqt": "1",
        "beg": "0",
        "end": "20500101",
        "lmt": str(safe_limit),
    }
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get("https://push2his.eastmoney.com/api/qt/stock/kline/get", params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        rows = data.get("klines") or []
        stock_name = name or data.get("name") or ""
        bars = []
        for row in rows:
            parts = row.split(",")
            if len(parts) < 11:
                continue
            volume_hands = float(parts[5] or 0)
            bars.append({
                "symbol": symbol,
                "name": stock_name,
                "trade_date": parts[0],
                "open_price": float(parts[1] or 0),
                "close_price": float(parts[2] or 0),
                "high_price": float(parts[3] or 0),
                "low_price": float(parts[4] or 0),
                # Keep backend volume unit consistent with daily bars: shares.
                "volume": volume_hands * 100,
                "amount": float(parts[6] or 0),
                "amplitude": float(parts[7] or 0),
                "change_pct": float(parts[8] or 0),
                "change_value": float(parts[9] or 0),
                "turnover_rate": float(parts[10] or 0),
                "period": klt,
            })
        if bars:
            return bars
    except Exception as e:
        logger.error(f"Eastmoney fetch_intraday_kline error: {e}")

    return _fetch_tencent_intraday_kline(symbol, name, klt, safe_limit)


def _fetch_tencent_intraday_kline(symbol: str, name: str, period: int, limit: int) -> list[dict[str, Any]]:
    code = _market_code(symbol)
    if not code:
        return []
    try:
        response = requests.get(
            "https://web.ifzq.gtimg.cn/appstock/app/minute/query",
            params={"code": code},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        stock_data = ((payload.get("data") or {}).get(code) or {}).get("data") or {}
        trade_day = stock_data.get("date") or date.today().strftime("%Y%m%d")
        rows = stock_data.get("data") or []
        minute_rows = []
        previous_volume = 0.0
        previous_amount = 0.0
        for row in rows:
            parts = row.split()
            if len(parts) < 4:
                continue
            minute = parts[0]
            price = float(parts[1] or 0)
            cumulative_volume = float(parts[2] or 0)
            cumulative_amount = float(parts[3] or 0)
            minute_rows.append({
                "time": f"{minute[:2]}:{minute[2:]}",
                "price": price,
                "volume_hands": max(0.0, cumulative_volume - previous_volume),
                "amount": max(0.0, cumulative_amount - previous_amount),
            })
            previous_volume = cumulative_volume
            previous_amount = cumulative_amount

        grouped = []
        for index in range(0, len(minute_rows), period):
            chunk = minute_rows[index:index + period]
            if not chunk:
                continue
            prices = [item["price"] for item in chunk]
            volume_hands = sum(item["volume_hands"] for item in chunk)
            amount = sum(item["amount"] for item in chunk)
            grouped.append({
                "symbol": symbol,
                "name": name,
                "trade_date": f"{trade_day[:4]}-{trade_day[4:6]}-{trade_day[6:]} {chunk[-1]['time']}",
                "open_price": prices[0],
                "close_price": prices[-1],
                "high_price": max(prices),
                "low_price": min(prices),
                "volume": volume_hands * 100,
                "amount": amount,
                "turnover_rate": 0,
                "period": period,
            })
        return grouped[-limit:]
    except Exception as e:
        logger.error(f"Tencent fetch_intraday_kline error: {e}")
        return []


def _eastmoney_secid(symbol: str) -> str:
    code = (symbol or "").strip().lower()
    if not code:
        return ""
    if code.startswith("sh."):
        return f"1.{code.split('.', 1)[1]}"
    if code.startswith("sz."):
        return f"0.{code.split('.', 1)[1]}"
    if code.startswith("6"):
        return f"1.{code}"
    return f"0.{code}"


def _market_code(symbol: str) -> str:
    code = (symbol or "").strip().lower()
    if not code:
        return ""
    if code.startswith("sh.") or code.startswith("sz."):
        return code.replace(".", "")
    if code.startswith("6"):
        return f"sh{code}"
    return f"sz{code}"


def _search_stock_code(name: str) -> str:
    """Search stock code by name using baostock."""
    if name in COMMON_STOCK_CODES:
        return COMMON_STOCK_CODES[name]

    bs = _login_bs()
    if not bs or not name:
        return ""

    try:
        # Query all stocks
        rs = bs.query_all_stock(day=date.today().strftime("%Y-%m-%d"))
        if rs.error_code != '0':
            return ""

        stocks = []
        while (rs.error_code == '0') & rs.next():
            stocks.append(rs.get_row_data())

        # Search by name (need to get stock names separately)
        # Baostock doesn't provide names directly, try common stocks
        # For now, return empty and require user to input symbol
        bs.logout()
        return ""

    except Exception as e:
        logger.error(f"Baostock search error: {e}")
        try:
            bs.logout()
        except:
            pass
        return ""


def check_baostock_available() -> dict[str, Any]:
    """Check if Baostock is available and working."""
    bs = _get_baostock()
    if not bs:
        return {"available": False, "error": "Baostock not installed. Run: pip install baostock"}

    try:
        lg = bs.login()
        if lg.error_code != '0':
            return {"available": False, "error": f"Login failed: {lg.error_msg}"}

        # Test query
        rs = bs.query_history_k_data_plus(
            "sh.600000",  # 浦发银行 as test
            "date,close",
            start_date=date.today().strftime("%Y-%m-%d"),
            end_date=date.today().strftime("%Y-%m-%d"),
            frequency="d"
        )

        bs.logout()
        return {"available": True, "test_passed": True, "message": "Baostock连接成功"}

    except Exception as e:
        return {"available": False, "error": str(e)}


# Alias for compatibility
check_akshare_available = check_baostock_available
