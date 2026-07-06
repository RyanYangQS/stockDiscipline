"""Real data sources for stock information using AKShare."""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from typing import Any

# Disable proxy for AKShare requests (common issue in China)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

logger = logging.getLogger(__name__)

# AKShare functions - lazy import to avoid startup errors
def _get_akshare():
    try:
        import akshare as ak
        return ak
    except ImportError:
        logger.warning("AKShare not installed, real data unavailable")
        return None


def fetch_kline(symbol: str, name: str = "", days: int = 60) -> list[dict[str, Any]]:
    """Fetch K-line data from AKShare.

    Args:
        symbol: Stock symbol (e.g., "300750")
        name: Stock name (fallback if symbol empty)
        days: Number of trading days to fetch

    Returns:
        List of K-line bars with OHLCV data
    """
    ak = _get_akshare()
    if not ak:
        return []

    try:
        # Try symbol first, then search by name if needed
        stock_code = symbol or _search_stock_code(name)
        if not stock_code:
            logger.warning(f"Stock not found: {symbol or name}")
            return []

        # Fetch daily K-line data
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=(date.today() - timedelta(days=days * 2)).strftime("%Y%m%d"),
            end_date=date.today().strftime("%Y%m%d"),
            adjust="qfq"  # Forward adjusted for dividends
        )

        if df.empty:
            return []

        # Convert to our format
        bars = []
        for _, row in df.tail(days).iterrows():
            bars.append({
                "symbol": stock_code,
                "name": name or _get_stock_name(stock_code),
                "trade_date": str(row["日期"]),
                "open_price": float(row["开盘"]),
                "high_price": float(row["最高"]),
                "low_price": float(row["最低"]),
                "close_price": float(row["收盘"]),
                "volume": float(row["成交量"]),
                "amount": float(row["成交额"]),
                "turnover_rate": float(row.get("换手率", 0)) if "换手率" in row else 0,
            })

        return bars

    except Exception as e:
        logger.error(f"AKShare fetch_kline error: {e}")
        return []


def fetch_realtime_quote(symbol: str, name: str = "") -> dict[str, Any] | None:
    """Fetch current realtime quote from AKShare.

    Returns:
        Dict with current_price, volume_ratio, turnover_rate, etc.
    """
    ak = _get_akshare()
    if not ak:
        return None

    try:
        stock_code = symbol or _search_stock_code(name)
        if not stock_code:
            return None

        # Real-time quote
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == stock_code]

        if row.empty:
            return None

        quote = row.iloc[0]
        return {
            "symbol": stock_code,
            "name": str(quote["名称"]),
            "current_price": float(quote["最新价"]),
            "change_pct": float(quote["涨跌幅"]),
            "volume": float(quote["成交量"]),
            "amount": float(quote["成交额"]),
            "high_price": float(quote["最高"]),
            "low_price": float(quote["最低"]),
            "open_price": float(quote["今开"]),
            "prev_close": float(quote["昨收"]),
        }

    except Exception as e:
        logger.error(f"AKShare fetch_realtime_quote error: {e}")
        return None


def _search_stock_code(name: str) -> str:
    """Search stock code by name using AKShare."""
    ak = _get_akshare()
    if not ak or not name:
        return ""

    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["名称"] == name]
        if row.empty:
            # Try partial match
            row = df[df["名称"].str.contains(name, na=False)]
        if row.empty:
            return ""
        return str(row.iloc[0]["代码"])
    except Exception as e:
        logger.error(f"AKShare search error: {e}")
        return ""


def _get_stock_name(code: str) -> str:
    """Get stock name by code."""
    ak = _get_akshare()
    if not ak:
        return ""

    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if row.empty:
            return ""
        return str(row.iloc[0]["名称"])
    except Exception as e:
        logger.error(f"AKShare get name error: {e}")
        return ""


def check_akshare_available() -> dict[str, Any]:
    """Check if AKShare is available and working."""
    ak = _get_akshare()
    if not ak:
        return {"available": False, "error": "AKShare not installed. Run: pip install akshare"}

    try:
        # Test with a known stock
        df = ak.stock_zh_a_spot_em()
        return {"available": True, "stocks_count": len(df), "test_passed": True}
    except Exception as e:
        return {"available": False, "error": str(e)}