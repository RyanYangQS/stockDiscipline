"""
持仓相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import Position
from app.schemas import PositionCreate, PositionResponse

router = APIRouter(prefix="/api/position", tags=["持仓"])


@router.get("/list", response_model=List[PositionResponse])
async def get_positions(db: AsyncSession = Depends(get_db)):
    """
    获取持仓列表
    """
    result = await db.execute(
        select(Position).where(Position.status == "holding")
    )
    positions = result.scalars().all()
    return positions


@router.post("/create", response_model=PositionResponse)
async def create_position(
    position_data: PositionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建持仓（录入持仓）
    """
    position = Position(
        stock_code=position_data.stock_code,
        stock_name=position_data.stock_name,
        cost_price=position_data.cost_price,
        quantity=position_data.quantity,
        buy_date=position_data.buy_date,
        # 计算8%止损价
        stop_loss_price=position_data.cost_price * 0.92,
        status="holding"
    )
    
    db.add(position)
    await db.commit()
    await db.refresh(position)
    
    return position


@router.delete("/{position_id}")
async def delete_position(
    position_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除持仓
    """
    result = await db.execute(
        select(Position).where(Position.id == position_id)
    )
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")
    
    await db.delete(position)
    await db.commit()
    
    return {"message": "删除成功"}
