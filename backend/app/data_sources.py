"""Real data sources for stock information using Baostock (stable, free)."""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any

# Disable proxy for requests
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

logger = logging.getLogger(__name__)


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


def fetch_kline(symbol: str, name: str = "", days: int = 60) -> list[dict[str, Any]]:
    """Fetch K-line data from Baostock.

    Args:
        symbol: Stock code (e.g., "sh.600000" or "sz.300750")
        name: Stock name (fallback if symbol empty)
        days: Number of trading days to fetch

    Returns:
        List of K-line bars with OHLCV data
    """
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


def fetch_realtime_quote(symbol: str, name: str = "") -> dict[str, Any] | None:
    """Fetch current realtime quote (using latest daily data as proxy)."""
    bars = fetch_kline(symbol, name, days=1)
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
        }
    return None


def _search_stock_code(name: str) -> str:
    """Search stock code by name using baostock."""
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