"""
股票相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas import (
    ScreeningRequest, ScreeningResponse, StockPoolItem,
    KLineRequest, KLineResponse, KLineItem,
    MarketOverview, BidAskResponse,
    IntradayItem, IntradayResponse,
    MinuteKLineItem, MinuteKLineResponse
)
from app.services import stock_service, screening_engine
from datetime import datetime

router = APIRouter(prefix="/api/stock", tags=["股票"])


@router.post("/screening", response_model=ScreeningResponse)
async def screen_stocks(
    request: ScreeningRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    AI选股接口
    
    根据规则筛选符合条件的股票标的
    """
    results = await screening_engine.screen_stocks(
        rules=request.rules,
        market=request.market,
        limit=request.limit
    )
    
    items = [StockPoolItem(**r) for r in results]
    
    return ScreeningResponse(
        total=len(items),
        items=items,
        screened_at=datetime.now()
    )


@router.get("/kline/{code}", response_model=KLineResponse)
async def get_kline(
    code: str,
    period: str = "daily",
    count: int = 60,
    db: AsyncSession = Depends(get_db)
):
    """
    获取K线数据
    
    Args:
        code: 股票代码
        period: 周期 daily/weekly
        count: 数据条数
    """
    klines = await stock_service.get_kline_data(code, period, count)
    
    if not klines:
        raise HTTPException(status_code=404, detail="未找到K线数据")
    
    items = [KLineItem(**k) for k in klines]
    
    # 获取股票名称
    quote = await stock_service.get_realtime_quote(code)
    name = quote['name'] if quote else code
    
    return KLineResponse(
        code=code,
        name=name,
        period=period,
        data=items
    )


@router.get("/realtime/{code}")
async def get_realtime(code: str):
    """
    获取实时行情
    
    Args:
        code: 股票代码
    """
    quote = await stock_service.get_realtime_quote(code)
    
    if not quote:
        raise HTTPException(status_code=404, detail="未找到股票")
    
    return quote


@router.get("/market/overview", response_model=MarketOverview)
async def get_market_overview():
    """
    获取市场概览
    
    返回涨跌家数等市场统计数据
    """
    overview = await stock_service.get_market_overview()
    return MarketOverview(**overview)


@router.get("/bid-ask/{code}", response_model=BidAskResponse)
async def get_bid_ask(code: str):
    """
    获取盘口数据(买卖五档)
    
    Args:
        code: 股票代码
    """
    bid_ask = await stock_service.get_bid_ask_data(code)
    
    if not bid_ask:
        raise HTTPException(status_code=404, detail="未找到盘口数据")
    
    return BidAskResponse(**bid_ask)


@router.get("/intraday/{code}", response_model=IntradayResponse)
async def get_intraday(code: str):
    """
    获取分时数据
    
    Args:
        code: 股票代码
    """
    intraday = await stock_service.get_intraday_data(code)
    
    if not intraday:
        raise HTTPException(status_code=404, detail="未找到分时数据")
    
    items = [IntradayItem(**item) for item in intraday]
    
    # 获取股票名称
    quote = await stock_service.get_realtime_quote(code)
    name = quote['name'] if quote else code
    
    return IntradayResponse(
        code=code,
        name=name,
        data=items
    )


@router.get("/minute-kline/{code}", response_model=MinuteKLineResponse)
async def get_minute_kline(
    code: str,
    period: str = "5",
    count: int = 48
):
    """
    获取分钟K线数据
    
    Args:
        code: 股票代码
        period: 周期 1/5/15/30/60分钟
        count: 数据条数
    """
    klines = await stock_service.get_minute_kline(code, period, count)
    
    if not klines:
        raise HTTPException(status_code=404, detail="未找到分钟K线数据")
    
    items = [MinuteKLineItem(**k) for k in klines]
    
    # 获取股票名称
    quote = await stock_service.get_realtime_quote(code)
    name = quote['name'] if quote else code
    
    return MinuteKLineResponse(
        code=code,
        name=name,
        period=period,
        data=items
    )
