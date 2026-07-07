"""Web scrapers for stock news and market information."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

MARKET_WATCH_TITLES = [
    "盘前关注：指数量能、北向/主力资金、涨跌停家数是否同步改善",
    "政策关注：留意通信、半导体、AI、传媒等持仓相关行业政策与监管变化",
    "风险关注：若热点高位放量滞涨，按利好兑现或主力出货风险优先处理",
    "纪律关注：市场恐慌下跌时先观察量能承接，不做情绪化补仓",
]

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
        stock_code = _plain_stock_code(symbol) or _search_code_eastmoney(name)
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
        response.encoding = response.apparent_encoding or response.encoding

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

        if not news_items:
            for title_elem in soup.select("a")[:300]:
                title = title_elem.get_text(" ", strip=True)
                href = title_elem.get("href", "")
                if not _looks_like_news_title(title, name):
                    continue
                if href and href.startswith("/"):
                    href = f"https://guba.eastmoney.com{href}"
                news_items.append({
                    "symbol": stock_code,
                    "name": name,
                    "title": title,
                    "source": "东方财富",
                    "sentiment": _infer_sentiment(title),
                    "url": href,
                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                })
                if len(news_items) >= limit:
                    break

        return _dedupe_news(news_items)[:limit]

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
        response.encoding = response.apparent_encoding or response.encoding

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

        if not news_items:
            for elem in soup.select("a, p, div")[:500]:
                title = elem.get_text(" ", strip=True)
                if not _looks_like_market_title(title):
                    continue
                news_items.append({
                    "symbol": "",
                    "name": "",
                    "title": title,
                    "source": "财联社",
                    "sentiment": _infer_sentiment(title),
                    "url": "https://www.cls.cn/telegraph",
                    "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                if len(news_items) >= limit:
                    break

        return _dedupe_news(news_items)[:limit]

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
        url = "https://finance.sina.com.cn/stock/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding

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

        if not news_items:
            for title_elem in soup.select("a")[:500]:
                title = title_elem.get_text(" ", strip=True)
                href = title_elem.get("href", "")
                if not _looks_like_market_title(title):
                    continue
                news_items.append({
                    "symbol": "",
                    "name": "",
                    "title": title,
                    "source": "新浪财经",
                    "sentiment": _infer_sentiment(title),
                    "url": href,
                    "published_at": datetime.now().strftime("%Y-%m-%d"),
                })
                if len(news_items) >= limit:
                    break

        return _dedupe_news(news_items)[:limit]

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


def _plain_stock_code(symbol: str) -> str:
    match = re.search(r"(\d{6})", symbol or "")
    return match.group(1) if match else ""


def _looks_like_news_title(title: str, name: str = "") -> bool:
    if not title or len(title) < 8 or len(title) > 120:
        return False
    if name and name in title:
        return True
    keywords = ["公告", "业绩", "减持", "增持", "中标", "投资", "监管", "风险", "披露", "合作", "订单", "涨停", "跌停"]
    return any(keyword in title for keyword in keywords)


def _looks_like_market_title(title: str) -> bool:
    if not title or len(title) < 10 or len(title) > 160:
        return False
    keywords = [
        "A股", "指数", "沪指", "创业板", "政策", "监管", "板块", "热点", "资金",
        "涨停", "跌停", "成交", "半导体", "通信", "AI", "传媒", "新能源", "利好", "利空",
    ]
    return any(keyword in title for keyword in keywords)


def _dedupe_news(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        title = item.get("title", "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        result.append(item)
    return result


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


def build_holding_watch_items(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = datetime.now().strftime("%Y-%m-%d")
    items = []
    for pos in positions[:5]:
        name = pos.get("name", "")
        if not name:
            continue
        items.append({
            "symbol": _plain_stock_code(pos.get("symbol", "")),
            "name": name,
            "title": f"{name}：今日重点核验公告、业绩预告、减持增持、监管问询和行业政策变化",
            "source": "系统关注项",
            "sentiment": "待确认",
            "importance": 60,
            "scenario": "待核验持仓消息",
            "url": "",
            "published_at": today,
        })
    return items


def build_market_watch_items(limit: int = 8) -> list[dict[str, Any]]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        {
            "symbol": "",
            "name": "",
            "title": title,
            "source": "系统关注项",
            "sentiment": "待确认",
            "importance": 55,
            "scenario": "市场热点待核验",
            "url": "",
            "published_at": now,
        }
        for title in MARKET_WATCH_TITLES[:limit]
    ]


def scrape_market_news_items(limit: int = 20) -> list[dict[str, Any]]:
    items = scrape_cls_news(limit=max(1, limit // 2)) + scrape_sina_finance(limit=max(1, limit // 2))
    items = _dedupe_news(items)
    if items:
        return items[:limit]
    return build_market_watch_items(limit=limit)


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

    if not any(item.get("name") for item in all_news):
        all_news.extend(build_holding_watch_items(positions))

    # Scrape market-wide news
    all_news.extend(scrape_market_news_items(limit=20))

    return _dedupe_news(all_news)


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
