"""Web scrapers for stock news and market information."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# BeautifulSoup and requests - lazy import
def _get_bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup4 not installed, scraping unavailable")
        return None

def _get_requests():
    try:
        import requests
        return requests
    except ImportError:
        logger.warning("requests not installed, scraping unavailable")
        return None


def scrape_eastmoney_news(symbol: str, name: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """Scrape stock news from East Money (东方财富).

    Args:
        symbol: Stock code (e.g., "300750")
        name: Stock name (fallback if symbol empty)
        limit: Maximum number of news items

    Returns:
        List of news items with title, source, sentiment, url, published_at
    """
    requests = _get_requests()
    bs4 = _get_bs4()
    if not requests or not bs4:
        return []

    try:
        stock_code = symbol or _search_code_eastmoney(name)
        if not stock_code:
            return []

        # East Money news URL
        url = f"https://guba.eastmoney.com/list,{stock_code}.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = bs4(response.text, "html.parser")
        news_items = []

        # Parse news list
        for item in soup.select(".newsitem")[:limit]:
            try:
                title_elem = item.select_one("a.title")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")

                # Parse date
                date_elem = item.select_one(".time")
                pub_date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")

                # Infer sentiment from title keywords
                sentiment = _infer_sentiment(title)

                news_items.append({
                    "symbol": stock_code,
                    "name": name,
                    "title": title,
                    "source": "东方财富",
                    "sentiment": sentiment,
                    "url": f"https://guba.eastmoney.com{href}" if href.startswith("/") else href,
                    "published_at": pub_date,
                })

            except Exception as e:
                logger.debug(f"Parse news item error: {e}")
                continue

        return news_items

    except Exception as e:
        logger.error(f"East Money scrape error: {e}")
        return []


def scrape_cls_news(limit: int = 20) -> list[dict[str, Any]]:
    """Scrape market-wide news from CLS (财联社).

    Returns:
        List of market news items
    """
    requests = _get_requests()
    bs4 = _get_bs4()
    if not requests or not bs4:
        return []

    try:
        url = "https://www.cls.cn/telegraph"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = bs4(response.text, "html.parser")
        news_items = []

        # Parse telegraph items
        for item in soup.select(".telegraph-item")[:limit]:
            try:
                title = item.get_text(strip=True)
                if not title:
                    continue

                # Parse time
                time_elem = item.select_one(".time")
                pub_time = time_elem.get_text(strip=True) if time_elem else datetime.now().strftime("%H:%M")
                pub_date = datetime.now().strftime("%Y-%m-%d")

                sentiment = _infer_sentiment(title)

                news_items.append({
                    "symbol": "",
                    "name": "",
                    "title": title,
                    "source": "财联社",
                    "sentiment": sentiment,
                    "url": "https://www.cls.cn/telegraph",
                    "published_at": f"{pub_date} {pub_time}",
                })

            except Exception as e:
                logger.debug(f"Parse CLS item error: {e}")
                continue

        return news_items

    except Exception as e:
        logger.error(f"CLS scrape error: {e}")
        return []


def scrape_sina_finance(limit: int = 15) -> list[dict[str, Any]]:
    """Scrape market hotspots from Sina Finance (新浪财经).

    Returns:
        List of market hotspot news
    """
    requests = _get_requests()
    bs4 = _get_bs4()
    if not requests or not bs4:
        return []

    try:
        url = "https://finance.sina.com.cn/realstock/company/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = bs4(response.text, "html.parser")
        news_items = []

        # Parse news list
        for item in soup.select(".news-item")[:limit]:
            try:
                title_elem = item.select_one("a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")

                sentiment = _infer_sentiment(title)

                news_items.append({
                    "symbol": "",
                    "name": "",
                    "title": title,
                    "source": "新浪财经",
                    "sentiment": sentiment,
                    "url": href,
                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                })

            except Exception as e:
                logger.debug(f"Parse Sina item error: {e}")
                continue

        return news_items

    except Exception as e:
        logger.error(f"Sina scrape error: {e}")
        return []


def _search_code_eastmoney(name: str) -> str:
    """Search stock code by name on East Money."""
    requests = _get_requests()
    if not requests:
        return ""

    try:
        url = "https://searchapi.eastmoney.com/api/suggest/get"
        params = {"input": name, "type": "14"}
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data.get("Data"):
            for item in data["Data"]:
                if item.get("Name") == name:
                    return item.get("Code", "")

        return ""
    except Exception as e:
        logger.debug(f"East Money search error: {e}")
        return ""


def _infer_sentiment(title: str) -> str:
    """Infer sentiment from title keywords."""
    positive_keywords = ["利好", "业绩", "增长", "盈利", "涨停", "突破", "新高", "收购", "中标"]
    negative_keywords = ["利空", "亏损", "跌停", "暴跌", "监管", "处罚", "减持", "风险", "违规", "退市"]
    neutral_keywords = ["公告", "发布", "披露", "报告"]

    for kw in negative_keywords:
        if kw in title:
            return "重大利空" if kw in ["退市", "违规", "处罚"] else "利空"

    for kw in positive_keywords:
        if kw in title:
            return "重大利好" if kw in ["涨停", "突破"] else "利好"

    return "中性"


def scrape_all_holdings_news(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scrape news for all holdings.

    Args:
        positions: List of position dicts with symbol/name

    Returns:
        Combined list of all scraped news
    """
    all_news = []

    # Scrape holdings-related news
    for pos in positions[:5]:  # Limit to first 5 to avoid too many requests
        symbol = pos.get("symbol", "")
        name = pos.get("name", "")
        if name:
            news = scrape_eastmoney_news(symbol, name, limit=5)
            all_news.extend(news)

    # Scrape market-wide news
    cls_news = scrape_cls_news(limit=10)
    sina_news = scrape_sina_finance(limit=10)
    all_news.extend(cls_news)
    all_news.extend(sina_news)

    return all_news


def check_scraper_available() -> dict[str, Any]:
    """Check if scraping dependencies are available."""
    requests = _get_requests()
    bs4 = _get_bs4()

    if not requests or not bs4:
        return {
            "available": False,
            "error": "requests/BeautifulSoup4 not installed. Run: pip install requests beautifulsoup4"
        }

    return {"available": True, "test_passed": True}