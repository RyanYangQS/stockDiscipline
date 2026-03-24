"""
Pydantic Schemas - API请求和响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 股票相关 ====================

class StockBase(BaseModel):
    """股票基础模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")


class StockResponse(StockBase):
    """股票响应模型"""
    id: int
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    is_st: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 选股相关 ====================

class ScreeningRequest(BaseModel):
    """选股请求模型"""
    rules: List[str] = Field(default_factory=list, description="规则ID列表")
    market: str = Field(default="all", description="市场筛选: all/sh/sz")
    sort_by: str = Field(default="score", description="排序字段")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")


class StockPoolItem(BaseModel):
    """选股池项"""
    code: str
    name: str
    price: float
    change_pct: float
    signal_type: str
    score: int
    volume_ratio: Optional[float] = None
    reason: Optional[str] = None


class ScreeningResponse(BaseModel):
    """选股响应模型"""
    total: int
    items: List[StockPoolItem]
    screened_at: datetime


# ==================== K线相关 ====================

class KLineRequest(BaseModel):
    """K线请求模型"""
    code: str = Field(..., description="股票代码")
    period: str = Field(default="daily", description="周期: daily/weekly/minute")
    count: int = Field(default=60, ge=1, le=500, description="数据条数")


class KLineItem(BaseModel):
    """K线数据项"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: Optional[float] = None


class KLineResponse(BaseModel):
    """K线响应模型"""
    code: str
    name: str
    period: str
    data: List[KLineItem]


# ==================== 持仓相关 ====================

class PositionCreate(BaseModel):
    """创建持仓请求"""
    stock_code: str
    stock_name: str
    cost_price: float = Field(..., gt=0, description="成本价")
    quantity: int = Field(..., gt=0, description="持仓数量")
    buy_date: datetime


class PositionResponse(BaseModel):
    """持仓响应模型"""
    id: int
    stock_code: str
    stock_name: str
    cost_price: float
    quantity: int
    current_price: Optional[float] = None
    profit: Optional[float] = None
    profit_pct: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    status: str
    
    class Config:
        from_attributes = True


# ==================== 信号相关 ====================

class SignalResponse(BaseModel):
    """信号响应模型"""
    id: int
    stock_code: str
    signal_type: str
    signal_name: str
    price: float
    priority: str
    reason: Optional[str] = None
    is_triggered: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 规则相关 ====================

class RuleCreate(BaseModel):
    """创建规则请求"""
    name: str
    category: str
    rule_type: str
    condition: str
    description: Optional[str] = None


class RuleResponse(BaseModel):
    """规则响应模型"""
    id: int
    name: str
    category: str
    rule_type: str
    condition: str
    description: Optional[str] = None
    is_system: bool
    is_enabled: bool
    priority: int
    
    class Config:
        from_attributes = True


# ==================== 市场概览 ====================

class MarketOverview(BaseModel):
    """市场概览响应"""
    up_count: int = Field(..., description="上涨家数")
    down_count: int = Field(..., description="下跌家数")
    flat_count: int = Field(..., description="平盘家数")
    total_count: int = Field(..., description="总股票数")
    limit_up_count: int = Field(..., description="涨停数")
    limit_down_count: int = Field(..., description="跌停数")
    updated_at: datetime
