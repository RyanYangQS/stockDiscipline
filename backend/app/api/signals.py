"""
信号相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import Signal, Position
from app.schemas import SignalResponse
from app.services import stock_service, signal_engine

router = APIRouter(prefix="/api/signal", tags=["信号"])


@router.get("/list/{code}", response_model=List[SignalResponse])
async def get_signals(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取股票信号列表
    """
    result = await db.execute(
        select(Signal).where(Signal.stock_code == code).order_by(Signal.created_at.desc()).limit(20)
    )
    signals = result.scalars().all()
    return signals


@router.get("/analyze/{code}")
async def analyze_signals(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    分析股票信号
    
    根据K线数据和持仓情况生成买卖信号建议
    """
    # 获取K线数据
    kline_data = await stock_service.get_kline_data(code, "daily", 60)
    
    if not kline_data:
        raise HTTPException(status_code=404, detail="未找到K线数据")
    
    # 查询持仓
    result = await db.execute(
        select(Position).where(Position.stock_code == code, Position.status == "holding")
    )
    position = result.scalar_one_or_none()
    
    position_dict = None
    if position:
        position_dict = {
            'cost_price': position.cost_price,
            'quantity': position.quantity,
            'stop_loss_price': position.stop_loss_price
        }
    
    # 分析信号
    signals = await signal_engine.analyze_signals(code, kline_data, position_dict)
    
    return {
        'code': code,
        'signals': signals,
        'analyzed_at': kline_data[-1]['timestamp'] if kline_data else None
    }


@router.get("/risk/{code}")
async def check_position_risk(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查持仓风险
    """
    # 查询持仓
    result = await db.execute(
        select(Position).where(Position.stock_code == code, Position.status == "holding")
    )
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(status_code=404, detail="未找到持仓")
    
    # 获取当前价格
    quote = await stock_service.get_realtime_quote(code)
    current_price = quote['price'] if quote else position.cost_price
    
    # 检查风险
    from app.services import risk_engine
    risk_result = risk_engine.check_position_risk(
        {'cost_price': position.cost_price, 'quantity': position.quantity},
        current_price
    )
    
    return {
        'code': code,
        'position': {
            'cost_price': position.cost_price,
            'quantity': position.quantity,
            'current_price': current_price
        },
        'risk': risk_result
    }
