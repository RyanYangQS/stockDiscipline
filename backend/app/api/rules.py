"""
规则相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import TradeRule
from app.schemas import RuleCreate, RuleResponse

router = APIRouter(prefix="/api/rule", tags=["规则"])


@router.get("/system", response_model=List[RuleResponse])
async def get_system_rules(db: AsyncSession = Depends(get_db)):
    """
    获取系统默认规则
    """
    result = await db.execute(
        select(TradeRule).where(TradeRule.is_system == True)
    )
    rules = result.scalars().all()
    return rules


@router.get("/custom", response_model=List[RuleResponse])
async def get_custom_rules(db: AsyncSession = Depends(get_db)):
    """
    获取自定义规则
    """
    result = await db.execute(
        select(TradeRule).where(TradeRule.is_system == False)
    )
    rules = result.scalars().all()
    return rules


@router.post("/create", response_model=RuleResponse)
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建自定义规则
    """
    rule = TradeRule(
        name=rule_data.name,
        category=rule_data.category,
        rule_type=rule_data.rule_type,
        condition=rule_data.condition,
        description=rule_data.description,
        is_system=False,
        is_enabled=True
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return rule


@router.put("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    切换规则启用状态
    """
    result = await db.execute(
        select(TradeRule).where(TradeRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    rule.is_enabled = not rule.is_enabled
    await db.commit()
    
    return {"message": "状态已更新", "is_enabled": rule.is_enabled}


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除自定义规则
    """
    result = await db.execute(
        select(TradeRule).where(TradeRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    if rule.is_system:
        raise HTTPException(status_code=400, detail="系统规则不可删除")
    
    await db.delete(rule)
    await db.commit()
    
    return {"message": "删除成功"}
